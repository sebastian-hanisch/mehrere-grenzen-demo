"""Szenario: Instanzen im Stil von Solomon (eigener Generator, nicht die Originalinstanzen) und das Handbeispiel mit sechs Kunden.

Alle Instanzen sind unveränderlich (Tupel). Zufall kommt nur über einen übergebenen `random.Random`, der aus dem Zufalls-Seed gebildet wird;
das ist derselbe Generator wie in der Messreihe, deren feste Zahlen in data/ liegen (Abschnitt „Abweichungen“ der README)."""

import math
import random
from dataclasses import dataclass

import mgr_constants as C


@dataclass(frozen=True)
class Instanz:
    """Depot = Knoten 0, Kunden 1..n. Zeit und Entfernung sind gleich; `last` ist die Nachfrage (Index 0 = Depot = 0)."""

    n: int
    punkte: tuple          # ((x, y), ...) mit dem Depot zuerst
    dist: tuple            # Entfernungsmatrix (n + 1) x (n + 1)
    last: tuple
    frueh: tuple           # früheste Bedienung je Kunde (Fensteranfang)
    spaet: tuple           # späteste Ankunft je Kunde (Fensterende)
    horizont: float
    bedienzeit: float
    breite: float = 0.0


def _matrix(punkte, metrik):
    return tuple(tuple(metrik(a, b) for b in punkte) for a in punkte)


def make_instance(n: int, seed: int, breite: float, gruppiert: bool = False) -> Instanz:
    """Solomon-artige Instanz: Depot (50, 50), n Kunden im Quadrat 100 x 100, Nachfrage 5 bis 25, Zeitfenster der Breite `breite`.

    Der Fenstermittelpunkt wird gleichverteilt zwischen frühestmöglicher und spätestmöglicher Ankunft gezogen und die Breite darum gelegt
    (an Anfang und Ende auf die erreichbaren Zeiten begrenzt). `gruppiert`: fünf Zentren, Kunden normalverteilt (Streuung 6) um ein Zentrum."""
    rng = random.Random(seed)
    if gruppiert:
        zentren = [(rng.uniform(15, 85), rng.uniform(15, 85)) for _ in range(5)]
        kunden = []
        for _ in range(n):
            cx, cy = rng.choice(zentren)
            kunden.append((min(100.0, max(0.0, rng.gauss(cx, 6))), min(100.0, max(0.0, rng.gauss(cy, 6)))))
    else:
        kunden = [(rng.uniform(0, 100), rng.uniform(0, 100)) for _ in range(n)]
    punkte = tuple([(50.0, 50.0)] + kunden)
    dist = _matrix(punkte, math.dist)
    last = tuple([0] + [rng.randint(C.LAST_MIN, C.LAST_MAX) for _ in range(n)])
    frueh = [0.0] * (n + 1)
    spaet = [C.HORIZONT] * (n + 1)
    for i in range(1, n + 1):
        lo = dist[0][i]
        hi = C.HORIZONT - C.BEDIENZEIT - dist[0][i]
        mitte = rng.uniform(lo, hi)
        frueh[i] = max(lo, mitte - breite / 2)
        spaet[i] = min(hi, mitte + breite / 2)
    return Instanz(n, punkte, dist, last, tuple(frueh), tuple(spaet), C.HORIZONT, C.BEDIENZEIT, float(breite))


def dualpreise_erste_runde(inst: Instanz) -> tuple:
    """Dualpreise der ersten Spaltenerzeugungsrunde: Startspalten sind die Einzelkunden-Fahrten Depot-i-Depot, ihre Kosten 2 d(0, i) sind die Preise."""
    return (0.0,) + tuple(2 * inst.dist[0][i] for i in range(1, inst.n + 1))


def verbrauch(inst: Instanz, seed: int, modell: str, anzahl: int = 3) -> list:
    """Verbrauch je Kunde der `anzahl` zusätzlichen Größen: Index 0 = Last, 1 = Fahrerzeit, 2 = dritte Größe (Position 0 = Depot = 0).

    Zufallsströme je Modell wie in der Messreihe (Seed-Versatz fest): "unabhängig" 10_000_019 + seed, die anderen Modelle 777_000 + seed."""
    last = list(inst.last)
    if modell == "unabhängig":
        rng = random.Random(10_000_019 + seed)
        return [last] + [[0] + [rng.randint(C.EXTRA_MIN, C.EXTRA_MAX) for _ in range(inst.n)] for _ in range(anzahl - 1)]
    rng = random.Random(777_000 + seed)
    if modell == "gleich der Last":
        return [last] + [list(last) for _ in range(anzahl - 1)]
    if modell == "Last plus Rauschen":
        zusatz = []
        for _ in range(anzahl - 1):
            zusatz.append([0] + [max(1, last[i] + rng.randint(-C.RAUSCH_SPANNE, C.RAUSCH_SPANNE)) for i in range(1, inst.n + 1)])
        return [last] + zusatz
    if modell == "gegenläufig":
        zweite = [0] + [C.GEGENLAEUFIG_SUMME - last[i] for i in range(1, inst.n + 1)]
        rest = [[0] + [rng.randint(C.EXTRA_MIN, C.EXTRA_MAX) for _ in range(inst.n)] for _ in range(anzahl - 2)]
        return [last, zweite] + rest
    raise ValueError(f"unbekanntes Verbrauchsmodell: {modell}")


def grenzen_liste(grenze: int, anzahl: int = 3) -> list:
    """Dieselbe Obergrenze für jede zusätzliche Größe."""
    return [grenze] * anzahl


# ---------------------------------------------------------------------------------------------------------------------------------
# Handbeispiel: Depot und sechs Kunden auf einem Gitter, Manhattan-Abstand, Fahrzeit = Entfernung (zum Nachrechnen mit dem Stift)
# ---------------------------------------------------------------------------------------------------------------------------------
HAND_PUNKTE = ((5, 5), (3, 2), (8, 6), (8, 9), (9, 3), (9, 5), (6, 5))
HAND_LAST = (0, 5, 4, 5, 5, 2, 6)
HAND_FAHRER = (0, 1, 2, 4, 3, 3, 3)
HAND_FRUEH = (0, 5, 23, 7, 14, 23, 25)
HAND_SPAET = (36, 13, 30, 20, 28, 30, 33)
HAND_DUAL = (0, 10, 11, 14, 12, 9, 6)
HAND_BEDIENZEIT, HAND_HORIZONT = 2, 36
HAND_GRENZEN_BINDEND = (12, 9)
HAND_NIE = 999


def handbeispiel() -> Instanz:
    """Das Handbeispiel als Instanz; die Zeitfenster stehen in `frueh` und `spaet`, die Dualpreise in HAND_DUAL."""
    dist = _matrix(HAND_PUNKTE, lambda a, b: abs(a[0] - b[0]) + abs(a[1] - b[1]))
    return Instanz(6, HAND_PUNKTE, dist, HAND_LAST, HAND_FRUEH, HAND_SPAET, HAND_HORIZONT, HAND_BEDIENZEIT, 0.0)


def hand_verbrauch(modell: str) -> list:
    """Verbrauch der zusätzlichen Größen im Handbeispiel: Last und Fahrerzeit (je nach Modell)."""
    if modell == "unabhängig":
        return [list(HAND_LAST), list(HAND_FAHRER)]
    if modell == "gleich der Last":
        return [list(HAND_LAST), list(HAND_LAST)]
    if modell == "gegenläufig":
        summe = min(HAND_LAST[1:]) + max(HAND_LAST[1:])
        return [list(HAND_LAST), [0] + [summe - HAND_LAST[i] for i in range(1, 7)]]
    raise ValueError(f"unbekanntes Verbrauchsmodell: {modell}")


def hand_grenzen(name: str) -> list:
    return [HAND_NIE, HAND_NIE] if name == C.HAND_GRENZEN[0] else list(HAND_GRENZEN_BINDEND)
