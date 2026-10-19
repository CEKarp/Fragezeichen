# Fragezeichen

Ein cocotb-Harness, das einen genetischen Algorithmus gegen drei verschiedene
Verilog-DUTs laufen lässt — mit einer positiven Kontrolle, einer negativen
Kontrolle und einem ehrlichen Negativergebnis.

**Was das nicht ist:** kein Durchbruch in evolvierbarer Hardware. Was es ist:
ein funktionierendes Framework mit dokumentierten Grenzen.

## Die drei DUTs

| DUT | Genom | Ergebnis | Was es zeigt |
|-----|-------|----------|--------------|
| `mini_alu.v` | 8 wirksame Bits (Muxe) | 0.90 → 0.998 | Pipeline funktioniert, Gradient trivial |
| `blind_seed.v` | xorshift-Seed | flach ~0.02–0.25 | Negativkontrolle: kein Gradient, GA irrt |
| `cgp_alu.v` | 110 Bit (11 Gatter-Knoten) | 0.78 → 0.84, dann Plateau | Echte Epistasis, premature convergence |

## Das Bild

![Konvergenz](convergence.png)

Links `mini_alu`: schwarze Linie klettert, mit violettem cipher-Dip bei Gen 2–3
(der GA muss Bit 7 zerstören, um L3 zu lösen). Rechts `blind_seed`: graue Linie
flach, Zufallsspikes ohne Struktur.

## Reproduktion

```bash
python -m venv .venv && source .venv/bin/activate
pip install "cocotb>=1.9"
pkg install -y iverilog matplotlib python-numpy   # Termux; sonst apt/dnf
sed -i 's/include-system-site-packages = false/include-system-site-packages = true/' .venv/pyvenv.cfg

make clean && make DUT=mini_alu POP=8 GENS=15 EPS=4 SEED=1
cp results.json results_seed1.json

make clean && make DUT=blind_seed POP=8 GENS=15 EPS=4 SEED=1
cp results.json results_blind_seed1.json

python plot.py
```

## Der CGP-Befund

`cgp_alu.v` ist ein Cartesian-Genetic-Programming-DUT: 11 Knoten, jeder mit
4-Bit-Selektoren auf A/B/vorherige Knoten und einer 2-Bit-Funktion
(AND/OR/XOR/NAND). Genom = 110 Bit. Aufgabe: 3-Bit-Vergleich `A > B` über
alle 64 Eingabepaare.

### Was gemessen wurde

Mit Hamming-Fitness (Zahl der richtigen Paare):

| Aufgabe | Zufallssuche | GA (1+4, 1-3-Bit-Mutation) |
|---------|--------------|----------------------------|
| `ne3` (A≠B) | 0/10 gelöst | 1/10 |
| `gt2` (2-Bit) | 0/10 | 0/10 |
| `gt3` (3-Bit) | 0/10 | 0/10 |

Mit balanced Fitness (Mittel aus Sensitivität und Spezifität):

| Aufgabe | Zufallssuche | GA |
|---------|--------------|-----|
| `ne3` | 0/10 | **6/10** |
| `gt2` | 0/10 | **7/10** |
| `gt3` | 0/10 | 0/10 (Median 60/64) |

200.000 Evaluationen pro Lauf, 10 Seeds, `tools_cgp_modell.py`.

### Warum Hamming deceptive ist

`ne3` hat eine Klassenverteilung von 56:8. Die Konstante "1" macht
56/64 richtig — mehr als jede partielle XOR-Struktur. Der Fitness-Gradient
zeigt **weg** von der Lösung. Erst balancierte Fitness entwertet die
Konstanten und macht echte Struktur belohnbar.

### gt3: lösbar, aber nicht gefunden

Ein Handgenom (Ripple-Carry-Comparator, 10 Gatter in 11 Knoten) löst `gt3`:

    Modell:  64/64
    Verilog: 64/64  (VERIFY_GENOME=0x3fdebb70b294aa7a6071906060c2, fit=0.998)

Der GA findet diese Lösung nicht in 200.000 Evaluationen. Median 60/64,
Maximum 62/64 — nah dran, aber die letzten Bits erfordern eine grundlegend
andere Schaltung. Das ist premature convergence auf einem lokalen Optimum.

## Was das zeigt

1. **Das Harness funktioniert.** mini_alu konvergiert, blind_seed nicht.
2. **Der GA funktioniert auf richtigen Landschaften.** balanced Fitness
   löst ne3 und gt2.
3. **Fitness-Design ist der entscheidende Hebel.** Hamming → 0/10,
   balanced → 6-7/10. Gleicher GA, gleiches Budget.
4. **Einfache (1+4)-Evolution reicht nicht für epistatische Landschaften.**
   gt3 ist lösbar, aber 1-3-Bit-Mutation findet die Lösung nicht.

## Dateien

    host.py                  cocotb-Testbench + GA + 6 Tasks
    mini_alu.v               8-Bit-Mux-DUT (trivialer Gradient)
    blind_seed.v             xorshift-Stub (Negativkontrolle)
    cgp_alu.v                11-Knoten-CGP-DUT (110 Bit)
    tools_cgp_modell.py      Python-Modell, balanced/unbalanced Fitness
    plot.py                  convergence.png aus results_*.json
    Makefile                 DUT ?= mini_alu

## Lizenz

Die CGP-Ideen stammen von Miller, Thompson und Kollegen. Der Code ist
frei verwendbar.

## Strategievergleich: GA vs. Zufall vs. Curriculum

Gleiche Aufgabe (4-Bit-Addierer, 18 Knoten), gleiches Budget.
Zwei Budgets, um zu pruefen, ob Rechenzeit die Grenze ist.

| Stufe | 30k Evals | 100k Evals |
|-------|-----------|------------|
| Reine Zufallssuche | 0.6964 | 0.7232 |
| GA direkt (kein Curriculum) | 0.8177 | **0.8333** |
| GA + Curriculum (1-2-3-4 Bit) | 0.7034 | 0.7113 |
| GA + Curriculum + Random Restart | 0.7619 | 0.8135 |

Median ueber 3 bzw. 5 Seeds. 0/5 loesen den Addierer.

### Befunde

1. **Der GA ist besser als Zufall.** +0.11 bei beiden Budgets.
   Der erste saubere Beleg, dass Evolution hier etwas bringt.
2. **Das Curriculum schadet.** 0.71 mit vs 0.83 ohne.
   Die Population konvergiert auf jeder Stufe und kann die
   naechste nicht mehr lernen - Diversitaetsverlust.
3. **Random Restart repariert das fast.** 0.71 -> 0.81.
   Frischer Zufall bei Stagnation holt die Population raus.
4. **3,3x mehr Budget bringt fast nichts.** +0.01 bis +0.05.
   Die Landschaft ist bei 100k Evals gesaettigt.
5. **Niemand loest den Addierer.** Trotz Handgenom-Beweis
   (fit=1.0). Der GA findet die Loesung nicht.

### Was dieser Vergleich zeigt

Das Curriculum war eine intuitive, aber falsche Idee: "vom Einfachen
zum Schweren" zerstoert die Populationsdiversitaet. Der GA direkt
ist die bessere Strategie. Random Restart ist ein billiger Fix.

Die Grenze liegt nicht am Budget (100k Evals = +0.02 bis +0.05),
nicht an der Kapazitaet (Handgenom loest den 4-Bit-Addierer mit
18 Knoten), sondern an der Suchstrategie des einfachen GA auf
epistatischen Landschaften.

Was fehlt: groessere Populationen (POP=200+), mehr Knoten (30+),
neutrale Mutation als primaerer Operator, Inselmodelle. Das sind
Standard-CGP-Techniken, die hier nicht implementiert sind.

### Nachtrag: Die Diversitaets-Hypothese ist widerlegt

Die naheliegende Erklaerung fuer das schlechte Curriculum-Abschneiden
war Diversitaetsverlust. Der Fix: nach jeder Stufe einen Teil der
Population durch frische Genome ersetzen. Getestet mit 30% / 50% / 70%
Reset am Stufenuebergang, 5 Seeds, 30k Evals:

| Strategie | Median | Max |
|-----------|--------|-----|
| GA direkt | **0.8255** | **0.8393** |
| Curriculum (kein Reset) | 0.7034 | 0.7500 |
| Curr + Stagnation-Restart | 0.7619 | 0.8209 |
| Curr + Div-Reset 30% | 0.7272 | 0.7822 |
| Curr + Div-Reset 50% | 0.7034 | 0.8125 |
| Curr + Div-Reset 70% | 0.6880 | 0.7034 |

**Kein Reset-Level rettet das Curriculum.** Das Problem ist tiefer:
die Population konvergiert auf jeder Stufe auf eine Struktur, die
fuer die naechste Stufe fundamental falsch ist. Mehr Zufall am
Uebergang hilft nicht, weil die Elite schon zu weit in die falsche
Richtung gelaufen ist.

GA direkt bleibt die beste Strategie. Das Curriculum ist damit
endgueltig als schaedlich belegt, nicht nur als "schlecht
implementiert".

## Mini-Enigma: Crib hilft, reicht aber nicht

Ein 4-Bit-Enigma (16 Symbole, 3 Rotoren, Reflektor, 4096 Keys)
als Test der Frage: reicht ein Crib, damit der GA den Schluessel
findet?

Wichtiger Hinweis vorab: die erste Version hatte einen Bug in
`rotor_backward` — die Maschine war nicht symmetrisch, der wahre
Schluessel gab `fit=0.0`. Erst nach der Verifikationszeile
(`fitness_with_crib(TRUE_KEY) == 1.0`) waren die Laeufe gueltig.
Alle frueheren Zahlen zum Mini-Enigma waren Artefakte des Bugs.

### Ergebnis nach dem Fix

10 Seeds, 100.000 Evals, Crib = bekannte Klartextzeichen:

| Crib | Median fit | Max | geloest |
|------|-----------|-----|---------|
| 8/16 | 0.7500 | 1.0 | 1/10 |
| 10/16 | 0.7000 | 1.0 | 2/10 |
| 12/16 | 0.6667 | 1.0 | 3/10 |
| 14/16 | 0.5714 | 1.0 | 3/10 |

### Was die gegenlaeufigen Trends bedeuten

Der Median **sinkt**, waehrend die Loesungsrate **steigt**. Das ist
kein Widerspruch: mehr Crib macht falsche Schluessel schlechter
(das Signal-Rausch-Verhaeltnis verbessert sich), waehrend der wahre
Schluessel bei 1.0 bleibt. Der Gradient wird steiler.

Aber: auch mit 14/16 Crib loest der GA nur 3 von 10 Mal. Das ist
derselbe Charakter wie bei `gt3` — der GA findet das Optimum, wenn
er zufaellig in die richtige Region startet, aber nicht zuverlaessig.

### Die Bruecke zur echten Enigma

Mehr Crib = steilerer Gradient = mehr Loesungen. Aber Evolution
allein reicht nicht fuer zuverlaessiges Loesen. Bletchley hatte
nicht nur Cribs, sondern **systematische Methoden** (Turing's Bombe:
alle Rotorpositionen durchprobieren, Crib an jeder Position testen).

Mit 26 Buchstaben statt 16 und ohne Odometrie waere der Suchraum
fuer den GA nochmal deutlich haerter. Die Bombe war keine
Rechenleistung — sie war ein anderer Suchalgorithmus.

## Parameter-Matrix: sechs Aufgaben, zwei Strategien

Echte Aufgaben-Definitionen in `tools_tasks.py` (ne3, gt2, gt3 als
Vergleicher; add2/add3/add4 als Additionen). 50.000 Evals, POP=30,
5 Seeds.

| Task | Zufall Median | GA Median | Delta | GA geloest |
|------|---------------|-----------|-------|------------|
| ne3 | 0.7857 | 0.7857 | +0.0000 | 0/5 |
| gt2 | 0.8667 | 0.8667 | +0.0000 | 0/5 |
| gt3 | 0.8333 | 0.8810 | +0.0477 | 0/5 |
| add2 | 0.8125 | 0.8750 | +0.0625 | **2/5** |
| add3 | 0.7292 | 0.8750 | **+0.1458** | 0/5 |
| add4 | 0.7195 | 0.8715 | **+0.1520** | 0/5 |

### Was die Matrix zeigt

1. **Der GA-Vorteil waechst mit der Schwierigkeit.** Bei ne3 (trivial)
   kein Unterschied, bei add3/add4 (schwer) +0.15. Der GA lohnt sich
   am meisten, wo die Aufgabe nicht durch Glueck loesbar ist.

2. **Die Kletter-Klippe bleibt.** Nur add2 wird geloest (2/5 Seeds).
   Alle anderen Aufgaben bleiben bei 0.87-0.88, egal wie nah an 1.0.

3. **Metrik-Warnung:** balanced accuracy gibt bei stark unausgeglichenen
   Klassen (ne3: 56/8) auch fuer Zufallsgenome hohe Werte (0.79).
   Die absoluten Zahlen sind nur relativ aussagekraeftig, nicht absolut.

## Kapazitaet vs. Suchstrategie: 18 vs. 30 Knoten

Gleiche Matrix, gleiches Budget (50k Evals, POP=30, 5 Seeds), aber
CGP_NODES=30 statt 18. Die Frage: liegt die Grenze an der Kapazitaet
oder an der Suche?

| Task | 18K Median | 30K Median | 18K Max | 30K Max | 18K gel. | 30K gel. |
|------|-----------|-----------|---------|---------|----------|----------|
| ne3 | 0.7857 | 0.9286 | 0.9286 | 0.9286 | 0/5 | 0/5 |
| gt2 | 0.8667 | 0.9000 | 0.9500 | 0.9500 | 0/5 | 0/5 |
| gt3 | 0.8810 | 0.8810 | 0.8810 | 0.9286 | 0/5 | 0/5 |
| add2 | 0.8750 | **1.0000** | 1.0000 | 1.0000 | 2/5 | **3/5** |
| add3 | 0.8750 | 0.8750 | 0.9167 | 0.9583 | 0/5 | 0/5 |
| add4 | 0.8715 | 0.8554 | 0.8958 | 0.9251 | 0/5 | 0/5 |

### Antwort: beides

1. **Kapazitaet hilft.** add2 wird mit 30 Knoten zuverlaessiger geloest
   (3/5 statt 2/5, Median 1.0). add3 und add4 kommen naeher an 1.0
   (Max 0.9583 bzw. 0.9251).

2. **Kapazitaet reicht nicht.** 67% mehr Knoten bringen keine Loesung
   fuer add3/add4. Der letzte Sprung auf 1.0 bleibt aus.

3. **Der Preis von mehr Knoten.** add4-Median sinkt leicht (0.8715 auf
   0.8554): groesserer Suchraum bei gleicher Population. Der Max steigt,
   der Median sinkt - einige Seeds finden bessere Loesungen, andere
   verlieren sich.

Die Kletter-Klippe verschiebt sich mit mehr Kapazitaet, verschwindet
aber nicht. Das ist konsistent mit der gt3-Beobachtung: der GA kommt
nah heran (61/64, 59/64), aber der letzte Sprung braucht mehr als
mehr Platz.

## Overfitting-Test: Findet der GA Schaltungen oder Lookup-Tabellen?

Alle bisherigen Matrizen massen auf denselben 64 Paaren, auf denen der
GA optimierte. Ein GA mit 180-300 Bit Genom und nur 64 Trainingsfaellen
koennte statt einer Schaltung eine Lookup-Tabelle bauen. Das waere
Overfitting, kein Lernen.

Test: 48 Paare trainieren, 16 ungesehene testen. Gap = Train - Test.

| Task | Seeds mit Gap < 0.05 | Seeds mit Gap > 0.1 |
|------|----------------------|---------------------|
| gt3  | 0/5                  | 3/5                 |
| add2 | 3/5 (davon 1 mit 1.0/1.0) | 2/5             |
| add3 | 2/5                  | 2/5                 |
| add4 | 2/5                  | 2/5                 |

### Was das zeigt

1. **Manche Seeds finden echte Schaltungen.** add2 Seed 5 erreicht
   Train=1.0, Test=1.0 - die Loesung funktioniert auf ungesehenen
   Paaren. Das ist echte Addition, kein Lookup.

2. **Manche Seeds memorieren.** add2 Seed 3 erreicht Train=0.93,
   Test=0.72, Gap=+0.21. Der GA hat 48 Paare auswendig gelernt und
   scheitert auf den 16 neuen.

3. **Die absoluten Zahlen beider Matrizen sind zu optimistisch.**
   Sie mischen echte Schaltungen und Lookup-Tabellen. Die Deltas
   (GA vs. Zufall) bleiben gueltig, die Absolutwerte nicht.

Was haelt: mini_alu/blind_seed (kein CGP), Hamming-vs-balanced
(kein Datenleck), Curriculum-schadet (Vergleich zwischen Strategien),
GA>Zufall (Delta bleibt).

Was wackelt: die absoluten Fitnesswerte der Matrizen, die Aussage
"add3/add4 kommen naeher an 1.0" (teilweise Overfitting).
