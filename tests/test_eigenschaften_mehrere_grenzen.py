"""Eigenschaftstests (ORACLE-PLAYBOOK §5.2): Aussagen, die für das Label-Setting mit mehreren Größen gelten müssen, ohne dass das richtige Ergebnis bekannt ist.

Jede Eigenschaft läuft über 20 bis 60 feste Gitterinstanzen (conftest.gitter_instanz) oder Solomon-artige Instanzen; sie gelten unter den genannten Voraussetzungen."""

import os
import subprocess
import sys
from pathlib import Path

import pytest
from conftest import gitter_instanz

import mgr_algorithm as A
import mgr_scenario as S

NIE = [10 ** 9] * 3
WURZEL = Path(__file__).resolve().parent.parent


def _zahlen(res):
    return (res.erzeugt, res.dominiert, res.vergleiche)


def test_an_additional_never_binding_size_does_not_change_the_best_value():
    """Eine nie bindende Größe schneidet keinen Weg ab: der beste Wert ist bei r = 1 bis 4 gleich (jedes ng-Gedächtnis)."""
    for seed in range(60):
        inst, dual, cons = gitter_instanz(seed)
        for k in (1, inst.n):
            werte = {A.price_r(inst, dual, k, r, cons, NIE).bester_wert for r in (1, 2, 3, 4)}
            assert len(werte) == 1, (seed, k, werte)


def test_tightening_a_limit_never_improves_the_value():
    for seed in range(60):
        inst, dual, cons = gitter_instanz(seed)
        for k in (1, 3):
            alt = A.price_r(inst, dual, k, 4, cons, [20, 20, 20]).bester_wert
            for grenzen in ([14, 20, 20], [14, 12, 20], [10, 10, 10], [6, 6, 6]):   # jede Stufe ist in jeder Größe höchstens so weit wie die vorige
                neu = A.price_r(inst, dual, k, 4, cons, grenzen).bester_wert
                assert neu >= alt, (seed, k, grenzen)
                alt = neu


def test_a_duplicated_size_changes_nothing():
    """Fahrerzeit = Last (und dritte Größe = Last) bei gleichen Grenzen ergibt dieselben Labels, dominierten Labels und Vergleiche wie ohne die Größe."""
    for seed in range(40):
        inst, dual, cons = gitter_instanz(seed)
        verb = [cons[0], list(cons[0]), list(cons[0])]
        for grenzen in ([10 ** 9] * 3, [9, 9, 9], [14, 14, 14]):
            for k in (1, 3):
                z2 = _zahlen(A.price_r(inst, dual, k, 2, verb, grenzen))
                assert z2 == _zahlen(A.price_r(inst, dual, k, 3, verb, grenzen)) == _zahlen(A.price_r(inst, dual, k, 4, verb, grenzen)), (seed, grenzen, k)


def test_swapping_the_additional_sizes_does_not_change_the_counts():
    """Die Reihenfolge der zusätzlichen Größen ist ohne Bedeutung (die Dominanz vergleicht alle, die Zählung zählt Tests, nicht ihre Einzelschritte)."""
    for seed in range(40):
        inst, dual, cons = gitter_instanz(seed)
        grenzen = [11, 7, 9]
        a = A.price_r(inst, dual, 1, 4, cons, grenzen)
        b = A.price_r(inst, dual, 1, 4, [cons[2], cons[0], cons[1]], [grenzen[2], grenzen[0], grenzen[1]])
        assert _zahlen(a) == _zahlen(b) and a.bester_wert == b.bester_wert, seed


def test_elementary_route_makes_never_binding_sizes_redundant():
    """Elementar (ng-Gedächtnis = n) und nie bindende Grenzen: die zusätzlichen Größen ändern weder Labels noch Vergleiche (Teilmengen-Argument der Formel im Expander)."""
    for seed in range(60):
        inst, dual, cons = gitter_instanz(seed)
        z = [_zahlen(A.price_r(inst, dual, inst.n, r, cons, NIE)) for r in (1, 2, 3, 4)]
        assert z[0] == z[1] == z[2] == z[3], (seed, z)


def test_non_elementary_route_is_where_the_sizes_matter():
    """Gegenstück: bei ng-Gedächtnis 1 und nie bindenden Grenzen ändert eine zusätzliche Größe in mindestens der Hälfte der Instanzen die Zählung (Zweig-Test: die Größe wird wirklich benutzt)."""
    geaendert = 0
    for seed in range(40):
        inst, dual, cons = gitter_instanz(seed)
        if _zahlen(A.price_r(inst, dual, 1, 1, cons, NIE)) != _zahlen(A.price_r(inst, dual, 1, 3, cons, NIE)):
            geaendert += 1
    assert geaendert >= 20


def test_every_limit_actually_changes_the_result_somewhere():
    """Zweig-Test (DEMO-PLAYBOOK §0): jede der drei zusätzlichen Größen mit enger Grenze ändert auf mindestens einer Instanz das Ergebnis gegenüber nie bindend."""
    for m in range(3):
        wirkt = False
        for seed in range(40):
            inst, dual, cons = gitter_instanz(seed)
            grenzen = [10 ** 9] * 3
            grenzen[m] = 6
            if _zahlen(A.price_r(inst, dual, 1, 4, cons, grenzen)) != _zahlen(A.price_r(inst, dual, 1, 4, cons, NIE)):
                wirkt = True
                break
        assert wirkt, f"Größe {m + 1} wird nie benutzt"


def test_every_returned_route_respects_all_limits_windows_and_the_memory():
    for seed in range(40):
        inst, dual, cons = gitter_instanz(seed)
        grenzen = [12, 9, 20]
        for k in (1, 3):
            nb = [set()]
            for j in range(1, inst.n + 1):
                andere = sorted((i for i in range(1, inst.n + 1) if i != j), key=lambda i: (inst.dist[j][i], i))
                nb.append({j, *andere[: k - 1]})
            for rc, route in A.price_r(inst, dual, k, 4, cons, grenzen).routen:
                assert A.pruefe_route(inst, route, cons, grenzen, nb) is None, (seed, route)
                assert A.route_kosten(inst, dual, route) == rc


def test_same_instance_same_numbers_in_two_processes_with_different_hash_seeds():
    """Das Ergebnis hängt nicht an der Reihenfolge von Mengen oder Wörterbüchern (Hash-Randomisierung): zwei Prozesse mit PYTHONHASHSEED 1 und 2."""
    code = (
        "import sys; sys.path.insert(0, sys.argv[1]);"
        "import mgr_algorithm as A, mgr_scenario as S;"
        "inst = S.make_instance(14, 3, 60); dual = S.dualpreise_erste_runde(inst); cons = S.verbrauch(inst, 3, 'Last plus Rauschen');"
        "r = A.price_r(inst, dual, 5, 4, cons, [70, 70, 70]);"
        "print(r.erzeugt, r.dominiert, r.vergleiche, r.routen[:2])"
    )
    ausgaben = []
    for hashseed in ("1", "2"):
        p = subprocess.run([sys.executable, "-c", code, str(WURZEL)], capture_output=True, text=True, env={**os.environ, "PYTHONHASHSEED": hashseed}, timeout=120)
        assert p.returncode == 0, p.stderr
        ausgaben.append(p.stdout)
    assert ausgaben[0] == ausgaben[1] and ausgaben[0].strip()


@pytest.mark.parametrize("modell", ["unabhängig", "gleich der Last", "Last plus Rauschen", "gegenläufig"])
def test_consumption_models_are_reproducible_and_nonnegative(modell):
    inst = S.make_instance(12, 5, 60)
    a, b = S.verbrauch(inst, 5, modell), S.verbrauch(inst, 5, modell)
    assert a == b and len(a) == 3
    assert all(len(x) == inst.n + 1 and x[0] == 0 and all(v >= 1 for v in x[1:]) for x in a)
