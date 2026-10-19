"""Enigma-Damen Co-Simulation: Host, Aufgaben, Fitness, Evolution (cocotb)."""
import os, json, random
import cocotb
from cocotb.clock import Clock
from cocotb.triggers import FallingEdge

T_RDY, T_OUT = 64, 256
OP_CALC, OP_FACT, OP_ASK_VAL, OP_REL, OP_ASK_CMP, OP_CIPHER, OP_ASK_KEY, OP_GT = 1,2,3,4,5,6,7,8

POP         = int(os.environ.get("POP", 12))
GENS        = int(os.environ.get("GENS", 30))
EPS         = int(os.environ.get("EPS", 6))
SEED        = int(os.environ.get("SEED", 1))
FEEDBACK    = int(os.environ.get("FEEDBACK", 0))
GENOME_BITS = int(os.environ.get("GENOME_BITS", 64))
TASKS       = os.environ.get("TASKS", "calc,mem,cmp,cmp_hard,cipher").split(",")


def rd(sig):
    try: return int(sig.value)
    except ValueError: return 0


class Bus:
    def __init__(self, dut): self.d = dut
    async def tick(self): await FallingEdge(self.d.CLK)
    def idle(self):
        d = self.d
        d.DIN.value = 0; d.DIN_V.value = 0; d.DIN_LAST.value = 0
        d.FB_OK.value = 0; d.FB_ERR.value = 0

    async def reset(self, genome):
        d = self.d
        self.idle()
        d.GENOME.value = genome
        d.RST_N.value = 0
        for _ in range(4): await self.tick()
        d.RST_N.value = 1
        await self.tick()

    async def send(self, nibs):
        d = self.d; n = 0
        while not rd(d.RDY):
            await self.tick(); n += 1
            if n > T_RDY: return False
        for i, x in enumerate(nibs):
            d.DIN.value = x; d.DIN_V.value = 1
            d.DIN_LAST.value = int(i == len(nibs) - 1)
            await self.tick()
        self.idle()
        return True

    async def wait_rdy(self):
        spurious = False
        for _ in range(T_RDY):
            await self.tick()
            if rd(self.d.DOUT_V): spurious = True
            if rd(self.d.RDY):    return True, spurious
        return False, spurious

    async def collect(self):
        lat = 0
        while not rd(self.d.DOUT_V):
            if lat >= T_OUT: return None
            await self.tick(); lat += 1
        out = []
        while rd(self.d.DOUT_V) and len(out) < 16:
            out.append(rd(self.d.DOUT)); await self.tick()
        return out, lat

    async def feedback(self, good):
        if not FEEDBACK: return
        self.d.FB_OK.value = int(good); self.d.FB_ERR.value = int(not good)
        await self.tick(); self.idle()

    async def tell(self, frame):
        if not await self.send(frame): return False
        ok, spurious = await self.wait_rdy()
        return ok and not spurious

    async def ask(self, frame, expected):
        if not await self.send(frame): return 0.0
        r = await self.collect()
        good = r is not None and r[0] == expected
        lat  = r[1] if r else 0
        ok, _ = await self.wait_rdy() if r is not None else (False, False)
        good = good and ok
        await self.feedback(good)
        return max(0.0, 1.0 - 0.001 * lat) if good else 0.0


async def ep_calc(bus, rng):
    a, b, o = rng.randrange(16), rng.randrange(16), rng.randrange(4)
    r = [a+b, a-b, a&b, a^b][o] & 0xFF
    return await bus.ask([OP_CALC, a, b, o], [r >> 4, r & 15])

async def ep_mem(bus, rng):
    k = rng.randint(2, 4)
    names = rng.sample(range(1, 16), k)
    vals  = [rng.randint(1, 15) for _ in names]
    for n, v in zip(names, vals):
        if not await bus.tell([OP_FACT, n, v]): return 0.0
    if rng.random() < 0.25:
        q = rng.choice([n for n in range(1, 16) if n not in names])
        exp = 0
    else:
        i = rng.randrange(k); q, exp = names[i], vals[i]
    return await bus.ask([OP_ASK_VAL, q], [exp])

async def ep_cmp(bus, rng):
    x, y = rng.sample(range(1, 16), 2)
    ax, ay = rng.sample(range(1, 16), 2)
    if not await bus.tell([OP_FACT, x, ax]): return 0.0
    if not await bus.tell([OP_FACT, y, ay]): return 0.0
    return await bus.ask([OP_ASK_CMP, x, y], [1 if ax > ay else 2])

async def ep_cmp_hard(bus, rng):
    a, b, c = rng.sample(range(1, 16), 3)
    if not await bus.tell([OP_REL, a, b]): return 0.0
    if not await bus.tell([OP_REL, b, c]): return 0.0
    if rng.random() < 0.5:
        return await bus.ask([OP_ASK_CMP, a, c], [1])
    return await bus.ask([OP_ASK_CMP, c, a], [2])

async def ep_cipher(bus, rng, level):
    n = 16
    p_len = 1 if level == 1 else 4
    key   = [rng.randrange(16) for _ in range(p_len)]
    plain = [0]*n if level <= 2 else [i % 16 for i in range(n)]
    c = [plain[i] ^ key[i % p_len] for i in range(n)]
    if not await bus.tell([OP_CIPHER] + c): return 0.0
    return await bus.ask([OP_ASK_KEY, p_len], key)

async def ep_gt(bus, i):
    """Deterministisch: alle 64 (A,B)-Paare, einmal pro Genom."""
    a, b = divmod(i, 8)
    return await bus.ask([OP_GT, a, b], [int(a > b)])


async def evaluate(bus, genome, gen, level):
    all_tasks = {
        "calc":     lambda r: ep_calc(bus, r),
        "mem":      lambda r: ep_mem(bus, r),
        "cmp":      lambda r: ep_cmp(bus, r),
        "cmp_hard": lambda r: ep_cmp_hard(bus, r),
        "cipher":   lambda r: ep_cipher(bus, r, level),
        "gt":       None,
    }
    tasks = {k: v for k, v in all_tasks.items() if k in TASKS}
    res, ok = {}, {}
    for name, fn in tasks.items():
        n = 64 if name == "gt" else EPS
        scores = []
        for i in range(n):
            rng = random.Random(f"{SEED}-{gen}-{name}-{i}")
            await bus.reset(genome)
            scores.append(await (ep_gt(bus, i) if name == "gt" else fn(rng)))
        res[name] = sum(scores) / n
        ok[name]  = sum(s > 0 for s in scores) / n
    return sum(res.values()) / len(res), res, ok


def mutate(g, rng):
    for _ in range(rng.randint(1, 3)):
        g ^= 1 << rng.randrange(GENOME_BITS)
    return g


VERIFY_GENOME = os.environ.get("VERIFY_GENOME")


@cocotb.test()
async def evolution(dut):
    bus = Bus(dut); bus.idle()
    if VERIFY_GENOME:
        dut.GENOME.value = 0
        dut.RST_N.value = 0
        cocotb.start_soon(Clock(dut.CLK, 10, "ns").start())
        await bus.tick()
        g = int(VERIFY_GENOME, 16)
        fit, res, ok = await evaluate(bus, g, 0, 1)
        dut._log.info(f"VERIFY genome={VERIFY_GENOME} fit={fit:.4f} tasks={res}")
        return
    dut.RST_N.value = 0
    dut.GENOME.value = 1
    cocotb.start_soon(Clock(dut.CLK, 10, "ns").start())
    await bus.tick()

    rng = random.Random(SEED)
    pop = [rng.getrandbits(GENOME_BITS) for _ in range(POP)]
    level, history, best_ever = 1, [], (-1.0, 0)

    for gen in range(GENS):
        scored = []
        for g in pop:
            fit, res, ok = await evaluate(bus, g, gen, level)
            scored.append((fit, g, res, ok))
        scored.sort(key=lambda t: t[0], reverse=True)
        fit, g, res, ok = scored[0]
        if fit > best_ever[0]:
            best_ever = (fit, g)
        dut._log.info(
            f"Gen {gen:3d} | L{level} | best {fit:.4f} | genom {g:0{GENOME_BITS//4}x} | "
            + " ".join(f"{k}={v:.2f}" for k, v in res.items()))
        history.append({"gen": gen, "level": level, "fit": fit,
                        "genome": f"{g:0{GENOME_BITS//4}x}", "tasks": res, "success": ok})
        if "cipher" in ok and ok["cipher"] >= 0.95 and level < 3:
            level += 1
        elites = [t[1] for t in scored[:max(2, POP // 4)]]
        pop = elites + [mutate(rng.choice(elites), rng) for _ in range(POP - len(elites))]

    with open("results.json", "w") as f:
        json.dump({"best_fitness": best_ever[0],
                   "best_genome": f"{best_ever[1]:0{GENOME_BITS//4}x}",
                   "genome_bits": GENOME_BITS,
                   "tasks": TASKS,
                   "history": history}, f, indent=1)
    dut._log.info(f"Fertig. Bestes Genom {best_ever[1]:0{GENOME_BITS//4}x}, Fitness {best_ever[0]:.4f}")
