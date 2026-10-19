"""Handgenome: direkte Output-Berechnung, kein Pass-through."""
from tools_cgp_curriculum import fitness_for

def make_genome(nodes):
    g = 0
    for i, (fn, x, y) in enumerate(nodes):
        g |= (fn | (x << 2) | (y << 6)) << (10 * i)
    return g

Z = (2, 0, 0)  # neutral: XOR(A0, A0) = 0

# Bits=1: s0 = XOR(A0, B0)
nodes_bits1 = [
    Z, Z, Z, Z, Z, Z, Z, Z, Z, Z, Z, Z, Z, Z,
    (2, 0, 3),  # k14 = XOR(A0, B0) = s0
    Z, Z, Z,
]

# Bits=2: k0=c1, k1=t1, k14=s0, k15=XOR(t1,c1)=s1
nodes_bits2 = [
    (0, 0, 3),   # k0 = AND(A0, B0) = c1
    (2, 1, 4),   # k1 = XOR(A1, B1) = t1
    Z, Z, Z, Z, Z, Z, Z, Z, Z, Z, Z, Z,
    (2, 0, 3),   # k14 = XOR(A0, B0) = s0
    (2, 7, 6),   # k15 = XOR(k1, k0) = XOR(t1,c1) = s1
    Z, Z,
]

# Bits=3: + k2=v1, k3=u1, k4=c2, k5=t2, k16=XOR(t2,c2)=s2
nodes_bits3 = [
    (0, 0, 3),   # k0 = c1
    (2, 1, 4),   # k1 = t1
    (0, 7, 6),   # k2 = AND(k1, k0) = v1
    (0, 1, 4),   # k3 = AND(A1, B1) = u1
    (1, 9, 8),   # k4 = OR(k3, k2) = c2
    (2, 2, 5),   # k5 = XOR(A2, B2) = t2
    Z, Z, Z, Z, Z, Z, Z, Z,
    (2, 0, 3),   # k14 = s0
    (2, 7, 6),   # k15 = s1
    (2, 11, 10), # k16 = XOR(k5, k4) = XOR(t2,c2) = s2
    Z,
]

# Bits=4: + k6=v2, k7=u2, k17=OR(u2,v2)=s3
nodes_bits4 = [
    (0, 0, 3),   # k0 = c1
    (2, 1, 4),   # k1 = t1
    (0, 7, 6),   # k2 = v1
    (0, 1, 4),   # k3 = u1
    (1, 9, 8),   # k4 = c2
    (2, 2, 5),   # k5 = t2
    (0, 11, 10), # k6 = AND(k5, k4) = v2
    (0, 2, 5),   # k7 = AND(A2, B2) = u2
    Z, Z, Z, Z, Z, Z,
    (2, 0, 3),   # k14 = s0
    (2, 7, 6),   # k15 = s1
    (2, 11, 10), # k16 = s2
    (1, 13, 12), # k17 = OR(k7, k6) = s3
]

for name, nodes, n in [
    ("Bits=1", nodes_bits1, 1),
    ("Bits=2", nodes_bits2, 2),
    ("Bits=3", nodes_bits3, 3),
    ("Bits=4", nodes_bits4, 4),
]:
    g = make_genome(nodes)
    print(f"{name}: fit={fitness_for(g, n):.4f}")
