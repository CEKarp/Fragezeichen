"""tools_mini_enigma.py — Mini-Enigma, GA mit vs. ohne Crib."""
import random

# Feste Rotor-Permutationen (4-Bit-Alphabet, 16 Symbole)
ROTORS = [
    [7, 3, 12, 1, 15, 8, 5, 10, 4, 14, 0, 11, 9, 6, 13, 2],
    [1, 15, 6, 11, 3, 9, 12, 4, 13, 7, 2, 14, 10, 0, 8, 5],
    [11, 4, 9, 2, 13, 7, 0, 15, 1, 10, 6, 12, 5, 8, 3, 14],
]
REFLECTOR = [15, 14, 13, 12, 11, 10, 9, 8, 7, 6, 5, 4, 3, 2, 1, 0]

def rotor_forward(rotor, pos, c):
    return rotor[(c + pos) % 16]

def rotor_backward(rotor, pos, c):
    return (rotor.index(c) - pos) % 16

def step(positions):
    """Odometrie: p0++ nach jedem Zeichen, p1++ bei Wrap, p2++ bei Wrap."""
    positions[0] = (positions[0] + 1) % 16
    if positions[0] == 0:
        positions[1] = (positions[1] + 1) % 16
        if positions[1] == 0:
            positions[2] = (positions[2] + 1) % 16

def encrypt(positions, plaintext):
    pos = positions[:]
    out = []
    for m in plaintext:
        step(pos)
        c = rotor_forward(ROTORS[0], pos[0], m)
        c = rotor_forward(ROTORS[1], pos[1], c)
        c = rotor_forward(ROTORS[2], pos[2], c)
        c = REFLECTOR[c]
        c = rotor_backward(ROTORS[2], pos[2], c)
        c = rotor_backward(ROTORS[1], pos[1], c)
        c = rotor_backward(ROTORS[0], pos[0], c)
        out.append(c)
    return out

def decrypt(positions, ciphertext):
    return encrypt(positions, ciphertext)

# Aufgabe vorbereiten
TRUE_KEY = [5, 9, 2]
PLAINTEXT = [1, 4, 7, 10, 13, 2, 5, 8, 11, 14, 3, 6, 9, 12, 15, 0]
CIPHER = encrypt(TRUE_KEY, PLAINTEXT)
import sys
CRIB_LEN = int(sys.argv[1]) if len(sys.argv) > 1 else 8

# Häufigkeitstabelle für Deutsch (4-Bit-Ersatz: gleichverteilt + Peak bei 0)
FREQ = {0: 0.18, 1: 0.10, 2: 0.08, 3: 0.07, 4: 0.06, 5: 0.06,
        6: 0.05, 7: 0.05, 8: 0.05, 9: 0.05, 10: 0.05, 11: 0.04,
        12: 0.04, 13: 0.04, 14: 0.04, 15: 0.04}

def fitness_with_crib(key):
    pos = list(key)
    plain = decrypt(pos, CIPHER[:CRIB_LEN])
    return sum(1 for p, t in zip(plain, PLAINTEXT[:CRIB_LEN]) if p == t) / CRIB_LEN

def fitness_without_crib(key):
    pos = list(key)
    plain = decrypt(pos, CIPHER)
    return sum(FREQ.get(p, 0) for p in plain) / len(plain)

def ga(fitness_fn, budget=20000, pop_size=30, seed=1):
    rng = random.Random(seed)
    pop = [tuple(rng.randrange(16) for _ in range(3)) for _ in range(pop_size)]
    best = max((fitness_fn(k), k) for k in pop)
    evals = pop_size
    while evals < budget and best[0] < 0.999:
        scored = sorted(((fitness_fn(k), k) for k in pop), reverse=True)
        evals += pop_size
        if scored[0][0] > best[0]:
            best = scored[0]
        n_elite = max(2, pop_size // 4)
        elite = [k for _, k in scored[:n_elite]]
        new_pop = list(elite)
        while len(new_pop) < pop_size:
            parent = rng.choice(elite)
            child = list(parent)
            for _ in range(rng.randint(1, 2)):
                i = rng.randrange(3)
                child[i] = (child[i] + rng.randint(1, 15)) % 16
            new_pop.append(tuple(child))
        pop = new_pop
    return best

def main():
    print(f"Wahre Key: {TRUE_KEY}   Crib-Laenge: {CRIB_LEN}/{len(PLAINTEXT)}")
    results_crib = [ga(fitness_with_crib, seed=s, budget=30000) for s in range(5)]
    solved = sum(1 for _, key in results_crib if list(key) == TRUE_KEY)
    fits = [fit for fit, _ in results_crib]
    print(f"  fit median={sorted(fits)[2]:.4f}  max={max(fits):.4f}  geloest={solved}/5")
    for fit, key in results_crib:
        mark = "  <-- TRUE KEY" if list(key) == TRUE_KEY else ""
        print(f"    fit={fit:.4f}  key={list(key)}{mark}")


if __name__ == "__main__":
    main()
