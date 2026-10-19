"""tools_tasks.py — echte Aufgaben-Definitionen auf 64-Bit-Wahrheitstabellen."""
from tools_cgp_curriculum import eval_genome, M

def _tt(fn):
    return sum(int(fn(i >> 3, i & 7)) << i for i in range(64))

# 1-Bit-Aufgaben
T_NE3 = _tt(lambda a, b: int(a != b))
T_GT2 = _tt(lambda a, b: int((a & 3) > (b & 3)))
T_GT3 = _tt(lambda a, b: int(a > b))

# Addition, pro Ausgangsbit
T_ADD2 = [_tt(lambda a, b, bb=bb: ((a + b) >> bb) & 1) for bb in range(2)]
T_ADD3 = [_tt(lambda a, b, bb=bb: ((a + b) >> bb) & 1) for bb in range(3)]
T_ADD4 = [_tt(lambda a, b, bb=bb: ((a + b) >> bb) & 1) for bb in range(4)]

def _balanced(pred, target):
    tp = (pred & target & M).bit_count()
    tn = ((~pred) & (~target) & M).bit_count()
    fp = (pred & (~target) & M).bit_count()
    fn = ((~pred) & target & M).bit_count()
    a0 = tn / (tn + fp) if (tn + fp) else 0.0
    a1 = tp / (tp + fn) if (tp + fn) else 0.0
    return (a0 + a1) / 2

def fitness_for_task(g, task):
    outs = eval_genome(g)  # (k14, k15, k16, k17)
    if task == "ne3":
        return _balanced(outs[3], T_NE3)
    if task == "gt2":
        return _balanced(outs[3], T_GT2)
    if task == "gt3":
        return _balanced(outs[3], T_GT3)
    if task == "add2":
        return sum(_balanced(outs[i], T_ADD2[i]) for i in range(2)) / 2
    if task == "add3":
        return sum(_balanced(outs[i], T_ADD3[i]) for i in range(3)) / 3
    if task == "add4":
        return sum(_balanced(outs[i], T_ADD4[i]) for i in range(4)) / 4
    raise ValueError(task)
