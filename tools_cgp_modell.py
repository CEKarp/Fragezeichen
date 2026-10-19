import random, sys
N = 11; G = 10 * N; M = (1 << 64) - 1
EV   = int(sys.argv[1]) if len(sys.argv) > 1 else 200000
TASK = sys.argv[2] if len(sys.argv) > 2 else "gt3"

def bit(v, j): return (v >> j) & 1
IN = [sum(bit(i >> 3, j) << i for i in range(64)) for j in range(3)] + \
     [sum(bit(i & 7, j) << i for i in range(64)) for j in range(3)]
f = {"gt3": lambda a, b: a > b,
     "ne3": lambda a, b: a != b,
     "gt2": lambda a, b: (a & 3) > (b & 3)}[TASK]
T = sum(int(f(i >> 3, i & 7)) << i for i in range(64))

def acc(g):
    s = IN[:]
    for i in range(N):
        fn = (g >> (10*i)) & 3
        x  = (g >> (10*i + 2)) & 15
        y  = (g >> (10*i + 6)) & 15
        a = s[x] if x < 6 + i else 0
        b = s[y] if y < 6 + i else 0
        s.append(a & b if fn == 0 else a | b if fn == 1
                 else a ^ b if fn == 2 else ~(a & b) & M)
    pred = s[-1]
    tp = (pred & T).bit_count()
    tn = ((~pred) & (~T) & M).bit_count()
    fp = (pred & (~T) & M).bit_count()
    fn = ((~pred) & T).bit_count()
    acc0 = tn / (tn + fp) if (tn + fp) > 0 else 0.0
    acc1 = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    return int(64 * (acc0 + acc1) / 2 + 0.5)

if TASK == "gt3":
    H = [(2,0,3),(0,6,0),(2,1,4),(2,1,7),(0,8,9),(2,7,10),
         (2,2,5),(2,2,11),(0,12,13),(2,11,14),(1,15,15)]
    gh = sum((fn | x << 2 | y << 6) << (10*i) for i, (fn, x, y) in enumerate(H))
    print("Handgenom:", acc(gh), "/64")

def run(mode, seed, lam=4):
    r = random.Random(seed)
    best = r.getrandbits(G); fb = acc(best); n = 1
    while n < EV and fb < 64:
        kids = []
        for _ in range(lam if mode == "ga" else 1):
            if mode == "rand":
                c = r.getrandbits(G)
            else:
                c = best
                for _ in range(r.randint(1, 3)):
                    c ^= 1 << r.randrange(G)
            kids.append((acc(c), c))
        n += len(kids)
        fc, c = max(kids, key=lambda t: t[0])
        if fc >= fb: best, fb = c, fc
    return fb, n

for mode in ("rand", "ga"):
    res = [run(mode, s) for s in range(10)]
    fit = sorted(x[0] for x in res)
    solved = sorted(x[1] for x in res if x[0] == 64)
    print(mode, "Median", fit[5], "Max", fit[-1],
          "| gelöst", len(solved), "/10 | Evals bis Lösung", solved)
