"""Gemeinsame Fixtures: die Mini-Instanz, an der jede Einheit von Hand geprüft wird (DEMO-PLAYBOOK §1b): das Handbeispiel der App.

Depot (5, 5) und sechs Kunden auf einem Gitter, Entfernung = Manhattan-Abstand = Fahrzeit, Bedienzeit 2, Horizont 36. Von Hand nachgerechnet, zum Beispiel:
Kunde 3 liegt bei (8, 9): Entfernung zum Depot 3 + 4 = 7, Fenster [7, 20], Dualpreis 14: Das Label „Weg 3“ hat Zeit 7, Kosten 7 − 14 = −7, Last 5, Fahrerzeit 4.
Von Kunde 1 (3, 2) nach Kunde 4 (9, 3): Entfernung 6 + 1 = 7; Label „Weg 1“ hat Zeit 5 und Kosten 5 − 10 = −5; Ankunft 5 + 2 + 7 = 14, Fenster [14, 28]:
Label „Weg 1 → 4“ hat Zeit 14, Kosten −5 + 7 − 12 = −10, Last 5 + 5 = 10, Fahrerzeit 1 + 3 = 4."""

import random
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import mgr_scenario as S  # noqa: E402
from mgr_scenario import Instanz  # noqa: E402


@pytest.fixture
def hand():
    return S.handbeispiel()


def gitter_instanz(seed: int):
    """Kleine zufällige Gitterinstanz mit ganzen Zahlen (4 bis 6 Kunden, Verbrauch auch 0, Fenster, Dualpreise) für die Orakeltests.

    Rückgabe (Instanz, Dualpreise, Verbrauch der drei zusätzlichen Größen). Alles ganzzahlig, damit Gleichstände exakt sind."""
    rng = random.Random(seed)
    n = rng.randint(4, 6)
    felder = rng.sample([(x, y) for x in range(10) for y in range(10) if (x, y) != (5, 5)], n)
    punkte = ((5, 5), *felder)
    dist = tuple(tuple(abs(a[0] - b[0]) + abs(a[1] - b[1]) for b in punkte) for a in punkte)
    horizont, svc = 36, 2
    frueh, spaet = [0], [horizont]
    for j in range(1, n + 1):
        e = rng.randint(dist[0][j], 22)
        spaet_max = horizont - svc - dist[0][j]
        frueh.append(e)
        spaet.append(min(spaet_max, e + rng.randint(3, 14)))
    last = (0,) + tuple(rng.randint(1, 6) for _ in range(n))
    inst = Instanz(n, punkte, dist, last, tuple(frueh), tuple(spaet), horizont, svc, 0.0)
    dual = (0,) + tuple(rng.randint(4, 16) for _ in range(n))
    cons = [list(last)] + [[0] + [rng.randint(0, 6) for _ in range(n)] for _ in range(2)]
    return inst, dual, cons
