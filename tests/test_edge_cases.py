"""Randfälle, an denen Kernroutinen erfahrungsgemäß brechen (DEMO-PLAYBOOK §12): Verbrauch 0, Grenze genau gleich dem Verbrauch, Grenze unter jedem Einzelverbrauch,
r = 1 ohne Wirkung der Verbräuche, gleiche Verbräuche, n = 1 und n = 2, Gleichstand der Kosten, Obergrenze der Live-Rechnung."""

import mgr_algorithm as A
import mgr_constants as C
import mgr_evaluation as E
import mgr_scenario as S
from mgr_scenario import Instanz


def _linie(n, abstand=5, frueh=0, spaet=100, last=1):
    """Kunden 1..n auf einer Linie im Abstand `abstand` vom Depot (Manhattan, Bedienzeit 2, Horizont 200), Fenster weit offen."""
    punkte = tuple((abstand * i, 0) for i in range(n + 1))
    dist = tuple(tuple(abs(a[0] - b[0]) for b in punkte) for a in punkte)
    return Instanz(n, punkte, dist, (0,) + (last,) * n, (frueh,) * (n + 1), (200,) + (spaet,) * n, 200, 2, 0.0)


def test_n_equals_one_has_one_route_with_the_expected_value():
    inst = _linie(1)
    res = A.price_r(inst, (0, 20), 1, 3, [[0, 3], [0, 4]], [10, 10])
    assert res.routen == [(5 + 5 - 20, (1,))] and res.erzeugt == 2 and res.dominiert == 0 and res.vergleiche == 0


def test_n_equals_two_exactly_two_customers():
    inst = _linie(2)
    res = A.price_r(inst, (0, 20, 20), 2, 2, [[0, 3, 3]], [10])      # ng-Gedächtnis 2 = n: elementar; beide Wege 0-1-2-0 und 0-2-1-0 sind 5 + 5 + 10 = 20 lang
    assert res.bester_wert == 20 - 40 and res.routen[0][1] in ((1, 2), (2, 1))


def test_consumption_zero_at_a_customer_is_allowed_and_cumulative():
    inst = _linie(2)
    verb = [[0, 0, 4], [0, 0, 0]]
    res = A.price_r(inst, (0, 30, 30), 1, 3, verb, [4, 0])       # Verbrauch 0 gegen Grenze 0: erlaubt (inklusive); Last 4 gegen Grenze 4: erlaubt
    assert res.routen and A.pruefe_route(inst, res.routen[0][1], verb, [4, 0]) is None


def test_limit_exactly_equal_to_the_total_consumption_is_feasible():
    inst = _linie(2)
    verb = [[0, 5, 5]]
    assert A.price_r(inst, (0, 40, 40), 1, 2, verb, [10]).routen[0][1] in ((1, 2), (2, 1))
    knapp = A.price_r(inst, (0, 40, 40), 1, 2, verb, [9])
    assert all(len(route) == 1 for _rc, route in knapp.routen)         # mit Grenze 9 passen nicht beide Kunden


def test_limit_below_every_single_consumption_leaves_no_route():
    inst = _linie(3)
    res = A.price_r(inst, (0, 50, 50, 50), 1, 2, [[0, 5, 6, 7]], [4])
    assert res.routen == [] and res.bester_wert == 0.0 and res.erzeugt == 1
    assert res.grenze_geschnitten == 3 and res.fenster_geschnitten == 0


def test_r_equals_one_ignores_consumption_and_limits(hand):
    a = A.price_r(hand, S.HAND_DUAL, 1, 1, S.hand_verbrauch("unabhängig"), [0, 0])
    b = A.price_r(hand, S.HAND_DUAL, 1, 1, S.hand_verbrauch("gegenläufig"), [999, 999])
    assert (a.erzeugt, a.dominiert, a.vergleiche, a.routen) == (b.erzeugt, b.dominiert, b.vergleiche, b.routen)


def test_equal_consumption_in_all_sizes_behaves_like_one_size():
    """Mehrere Größen mit demselben Verbrauch und derselben Grenze: dieselbe Zählung wie mit einer Größe."""
    inst, dual = S.handbeispiel(), S.HAND_DUAL
    verb = [list(S.HAND_LAST)] * 2
    z1 = A.price_r(inst, dual, 1, 2, verb, [12, 12])
    z2 = A.price_r(inst, dual, 1, 3, verb, [12, 12])
    assert (z1.erzeugt, z1.dominiert, z1.vergleiche) == (z2.erzeugt, z2.dominiert, z2.vergleiche)


def test_equal_costs_keep_the_first_label_and_drop_the_equal_newcomer():
    """Gleichstand: zwei Wege mit gleicher Zeit, gleichen Kosten und gleichem Verbrauch am selben Kunden: das zweite Label fällt weg, nur eines überlebt."""
    punkte = ((0, 0), (3, 0), (0, 3), (3, 3))
    dist = tuple(tuple(abs(a[0] - b[0]) + abs(a[1] - b[1]) for b in punkte) for a in punkte)
    inst = Instanz(3, punkte, dist, (0, 1, 1, 1), (0, 0, 0, 0), (100,) * 4, 100, 0, 0.0)
    res = A.price_r(inst, (0, 1, 1, 100), 1, 2, [[0, 1, 1, 1]], [99])
    gleiche = [v for v in res.ueberlebende[3] if v == (6, (3 - 1) + (3 - 100), (2,))]   # Zeit 3 + 3, Kosten 2 − 97, Last 2
    assert len(gleiche) == 1 and res.dominiert >= 1


def test_a_customer_unreachable_in_time_is_never_visited():
    inst = _linie(2, spaet=3)       # Kunde 1 liegt 5 entfernt, Fensterende 3
    res = A.price_r(inst, (0, 99, 99), 1, 2, [[0, 1, 1]], [10])
    assert res.routen == [] and res.fenster_geschnitten >= 2


def test_live_run_aborts_cleanly_at_the_cap(monkeypatch):
    monkeypatch.setattr(C, "LIVE_MAX_LABELS", 300)
    z = E.live_lauf(20, 100, 5, 4, C.GRENZE_NIE, "unabhängig", 424242)
    assert z["abgebrochen"] and z["fehler"] is None and z["erzeugt"] >= 300
    kind, text = E.verdict_dominanz([E.live_lauf(20, 100, 5, 1, C.GRENZE_NIE, "unabhängig", 424242), z], "in dieser Instanz")
    assert kind == "warning" and "abgebrochen" in text


def test_live_run_at_the_smallest_setting_works():
    z = E.live_lauf(C.LIVE_N_MIN, C.LIVE_BREITE_MIN, 1, 4, C.GRENZE_STANDARD, "gegenläufig", 0)
    assert not z["abgebrochen"] and z["erzeugt"] >= 1 and z["fehler"] is None
