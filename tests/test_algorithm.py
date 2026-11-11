"""Kern gegen Handrechnung (DEMO-PLAYBOOK §1b): Erweiterungsregel, Dominanzregel, Zählung und das Handbeispiel in allen Fällen.

Die Erwartungswerte stehen als Rechnung da (siehe tests/conftest.py für die Rechnung von Hand); die Aufzählung ist ein anderer Rechenweg als das Label-Setting."""

import pytest

import mgr_algorithm as A
import mgr_constants as C
import mgr_evaluation as E
import mgr_scenario as S

NIE = [S.HAND_NIE, S.HAND_NIE]
BIND = list(S.HAND_GRENZEN_BINDEND)
VERB = S.hand_verbrauch("unabhängig")


def _start(r):
    return [0.0, 0.0, (0,) * (r - 1), 0, 0, -1, False]


def test_extend_start_to_customer_3_by_hand(hand):
    ng = A.ng_masks(hand.dist, hand.n, 1)
    neu, grund = A.extend(hand, S.HAND_DUAL, ng, _start(3), 3, VERB, NIE)
    assert grund is None
    assert neu[0] == 7 and neu[1] == 7 - 14 and neu[2] == (5, 4) and neu[4] == 3


def test_extend_customer_1_to_4_by_hand(hand):
    ng = A.ng_masks(hand.dist, hand.n, 1)
    l1, _ = A.extend(hand, S.HAND_DUAL, ng, _start(3), 1, VERB, NIE)
    assert (l1[0], l1[1], l1[2]) == (5, 5 - 10, (5, 1))
    l14, grund = A.extend(hand, S.HAND_DUAL, ng, l1, 4, VERB, NIE)
    assert grund is None
    assert (l14[0], l14[1], l14[2]) == (5 + 2 + 7, -5 + 7 - 12, (5 + 5, 1 + 3))   # Zeit 14, Kosten -10, Last 10, Fahrerzeit 4


def test_extend_waits_until_the_window_opens(hand):
    ng = A.ng_masks(hand.dist, hand.n, 1)
    l1, _ = A.extend(hand, S.HAND_DUAL, ng, _start(1), 1, VERB, NIE)      # Kunde 1: Entfernung 5, Fenster [5, 13]
    l5, _ = A.extend(hand, S.HAND_DUAL, ng, l1, 5, VERB, NIE)             # Entfernung 6 + 3 = 9: Ankunft 5 + 2 + 9 = 16, Fenster [23, 30]: warten bis 23
    assert l5[0] == 23


def test_extend_reasons_limit_and_window(hand):
    ng = A.ng_masks(hand.dist, hand.n, 1)
    l1, _ = A.extend(hand, S.HAND_DUAL, ng, _start(3), 1, VERB, NIE)
    assert A.extend(hand, S.HAND_DUAL, ng, l1, 3, VERB, [4, 99])[1] == "grenze"      # Last 5 + 5 = 10 > 4
    assert A.extend(hand, S.HAND_DUAL, ng, l1, 3, VERB, [10, 99])[1] is None         # Last 10 <= 10: die Grenze gilt inklusive (Ankunft 5 + 2 + 12 = 19 <= 20)
    l6, _ = A.extend(hand, S.HAND_DUAL, ng, _start(3), 6, VERB, NIE)                 # Zeit 25
    assert A.extend(hand, S.HAND_DUAL, ng, l6, 1, VERB, NIE)[1] == "fenster"         # Entfernung 3 + 3 = 6: Ankunft 25 + 2 + 6 = 33 > 13


def test_dominance_rule_truth_table():
    o = [14, -10, (10, 4), 0, 4, 0, False]
    assert A.dominiert(o, [14, -6, (10, 4), 0, 4, 0, False])           # gleich in Last und Fahrerzeit, kleinere Kosten
    assert not A.dominiert(o, [14, -6, (5, 3), 0, 4, 0, False])        # Last 10 > 5 und Fahrerzeit 4 > 3: bei r = 3 nicht mehr
    assert A.dominiert(o[:2] + [()] + o[3:], [14, -6, (), 0, 4, 0, False])   # r = 1: nur Kosten und Zeit
    assert not A.dominiert([15, -10, (), 0, 4, 0, False], [14, -6, (), 0, 4, 0, False])   # später: nicht dominiert
    assert A.dominiert([14, -6, (), 0, 4, 0, False], [14, -6, (), 0, 4, 0, False])   # gleich: dominiert (das neue Label fällt weg)
    assert not A.dominiert([14, -6, (), 0b10, 4, 0, False], [14, -6, (), 0b01, 4, 0, False])   # Gedächtnis keine Teilmenge


@pytest.mark.parametrize("r, labels, dominiert, vergleiche", [(1, 31, 18, 51), (2, 52, 20, 303), (3, 64, 19, 622)])
def test_hand_example_never_binding_counts(hand, r, labels, dominiert, vergleiche):
    res = A.price_r(hand, S.HAND_DUAL, 1, r, VERB, NIE)
    assert (res.erzeugt, res.dominiert, res.vergleiche) == (labels, dominiert, vergleiche)
    assert res.bester_wert == -30 and res.routen[0][1] == (3, 4, 5, 2, 6)
    assert res.anteil_dominiert == pytest.approx(dominiert / labels)
    assert res.vergleiche_je_label == pytest.approx(vergleiche / labels)


@pytest.mark.parametrize("r, labels, dominiert, vergleiche", [(2, 33, 11, 99), (3, 33, 9, 112)])
def test_hand_example_binding_counts_and_value(hand, r, labels, dominiert, vergleiche):
    res = A.price_r(hand, S.HAND_DUAL, 1, r, VERB, BIND)
    assert (res.erzeugt, res.dominiert, res.vergleiche) == (labels, dominiert, vergleiche)
    assert res.bester_wert == -18 and res.routen[0][1] == (3, 2, 5)


def test_binding_limits_give_fewer_labels_but_a_worse_value(hand):
    nie = A.price_r(hand, S.HAND_DUAL, 1, 3, VERB, NIE)
    bind = A.price_r(hand, S.HAND_DUAL, 1, 3, VERB, BIND)
    assert bind.erzeugt < nie.erzeugt and bind.bester_wert > nie.bester_wert
    assert bind.grenze_geschnitten > 0 and nie.grenze_geschnitten == 0


def test_enumeration_agrees_with_label_setting_in_all_six_cases(hand):
    for limits in (NIE, BIND):
        for r in (1, 2, 3):
            wert, weg, _teilwege = A.aufzaehlung(hand, S.HAND_DUAL, r, VERB, limits)
            res = A.price_r(hand, S.HAND_DUAL, 1, r, VERB, limits)
            assert wert == res.bester_wert
            assert weg == res.routen[0][1]


def test_enumeration_counts_partial_walks(hand):
    assert [A.aufzaehlung(hand, S.HAND_DUAL, r, VERB, lim)[2] for lim, r in ((NIE, 3), (BIND, 2), (BIND, 3))] == [88, 40, 38]


def test_fahrerzeit_equal_to_load_adds_no_labels_at_r_3(hand):
    verb = S.hand_verbrauch("gleich der Last")
    a = A.price_r(hand, S.HAND_DUAL, 1, 2, verb, NIE)
    b = A.price_r(hand, S.HAND_DUAL, 1, 3, verb, NIE)
    assert (a.erzeugt, a.dominiert, a.vergleiche) == (b.erzeugt, b.dominiert, b.vergleiche) == (52, 20, 303)


def test_eleven_of_eighteen_decisions_at_r_1_do_not_hold_at_r_3():
    paare = E.gebrochene_paare(C.HAND_GRENZEN[0], "unabhängig", 3)
    assert len(paare) == 18 and sum(1 for p in paare if not p["haelt"]) == 11
    erstes = next(p for p in paare if p["kunde"] == 4 and p["gewinner"] == (1, 4))
    assert erstes["verlierer"] == (4,) and erstes["grund"] == "Last 10 > 5, Fahrerzeit 4 > 3"


def test_trace_sums_to_the_counters_and_numbers_labels_in_creation_order(hand):
    protokoll = []
    res = A.price_r(hand, S.HAND_DUAL, 1, 3, VERB, NIE, trace=protokoll)
    tabelle = E.label_tabelle(protokoll)
    assert len(tabelle) == res.erzeugt and [z["id"] for z in tabelle] == list(range(res.erzeugt))
    assert sum(z["tests"] for z in tabelle) == res.vergleiche
    assert sum(1 for z in tabelle if z["von"] is not None) + sum(1 for z in tabelle if z["abgeloest_von"] is not None) == res.dominiert
    assert len(E.entscheidungen(protokoll)) == res.dominiert
    l9 = tabelle[9]
    assert l9["weg"] == (1, 4) and l9["zeit"] == 14 and l9["kosten"] == -10 and l9["verbrauch"] == (10, 4)


def test_every_decision_of_the_protocol_has_only_true_single_comparisons(hand):
    """Die Einzelvergleiche, die die App zu jeder Entscheidung zeigt, sind alle erfüllt (Gewinner höchstens so groß in jeder Größe)."""
    for modell in C.HAND_MODELLE:
        for r in (1, 2, 3):
            protokoll = []
            A.price_r(hand, S.HAND_DUAL, 1, r, S.hand_verbrauch(modell), NIE, trace=protokoll)
            tabelle = {z["id"]: z for z in E.label_tabelle(protokoll)}
            for gew, ver, _art in E.entscheidungen(protokoll):
                assert all(v["höchstens"] for v in E.vier_vergleiche(tabelle[gew], tabelle[ver], r)), (modell, r, gew, ver)


def test_trace_does_not_change_the_result(hand):
    ohne = A.price_r(hand, S.HAND_DUAL, 1, 3, VERB, NIE)
    mit = A.price_r(hand, S.HAND_DUAL, 1, 3, VERB, NIE, trace=[])
    assert (ohne.erzeugt, ohne.dominiert, ohne.vergleiche, ohne.routen) == (mit.erzeugt, mit.dominiert, mit.vergleiche, mit.routen)


def test_four_comparisons_of_a_decision():
    g = {"kosten": -10, "zeit": 14, "verbrauch": (10, 4)}
    v = {"kosten": -6, "zeit": 14, "verbrauch": (5, 3)}
    zeilen = E.vier_vergleiche(g, v, 3)
    assert [z["größe"] for z in zeilen] == ["Kosten", "Zeit", "Last", "Fahrerzeit"]
    assert [z["höchstens"] for z in zeilen] == [True, True, False, False]
    assert len(E.vier_vergleiche(g, v, 1)) == 2


def test_ng_masks_k1_is_the_customer_itself(hand):
    masks = A.ng_masks(hand.dist, hand.n, 1)
    assert masks == [0] + [1 << j for j in range(1, 7)]
    elementar = A.ng_masks(hand.dist, hand.n, 6)
    assert all(m == sum(1 << j for j in range(1, 7)) for m in elementar[1:])


def test_ng_masks_k3_contains_the_two_nearest_others(hand):
    m = A.ng_masks(hand.dist, hand.n, 3)
    # Kunde 5 bei (9, 5): Abstände zu 4: 2, zu 2: 2 (Tiefe 1 + 1), zu 6: 3; Gleichstand 4 und 2 -> beide, 6 nicht
    assert m[5] == (1 << 5) | (1 << 4) | (1 << 2)


def test_route_checker_accepts_the_best_route_and_names_violations(hand):
    nb = E.nachbarn_mengen(hand, 1)
    assert A.pruefe_route(hand, (3, 4, 5, 2, 6), VERB, NIE, nb) is None
    assert "(10 > 9) bei Kunde 5" in A.pruefe_route(hand, (3, 4, 5, 2, 6), VERB, BIND, nb)   # Fahrerzeit 4 + 3 + 3 = 10 > 9 beim dritten Kunden
    assert "Fensterende" in A.pruefe_route(hand, (6, 1), VERB, NIE, nb)
    assert "wiederholt" in A.pruefe_route(hand, (3, 3), VERB, NIE, nb)
    assert A.pruefe_route(hand, (), VERB, NIE, nb) == "leere Route"
    assert "existiert nicht" in A.pruefe_route(hand, (9,), VERB, NIE, nb)


def test_route_cost_is_computed_from_scratch(hand):
    # 0-3-4-5-2-6-0: 0-3: 7, 3-4: 1 + 6 = 7, 4-5: 2, 5-2: 1 + 1 = 2, 2-6: 2 + 1 = 3, 6-0: 1; Summe 22. Preise 14 + 12 + 9 + 11 + 6 = 52.
    assert A.route_kosten(hand, S.HAND_DUAL, (3, 4, 5, 2, 6)) == (7 + 7 + 2 + 2 + 3 + 1) - (14 + 12 + 9 + 11 + 6)


def test_label_cap_aborts_deterministically(hand):
    a = A.price_r(hand, S.HAND_DUAL, 1, 3, VERB, NIE, max_labels=20)
    b = A.price_r(hand, S.HAND_DUAL, 1, 3, VERB, NIE, max_labels=20)
    assert a.abgebrochen and (a.erzeugt, a.vergleiche) == (b.erzeugt, b.vergleiche) and a.erzeugt >= 20
    assert A.price_r(hand, S.HAND_DUAL, 1, 3, VERB, NIE, max_vergleiche=10).abgebrochen
    assert not A.price_r(hand, S.HAND_DUAL, 1, 3, VERB, NIE, max_labels=65, max_vergleiche=10 ** 6).abgebrochen


def test_worst_case_at_the_live_maximum_finishes_or_aborts_cleanly():
    """Hängetest am Regler-Maximum der Live-Rechnung (Zufalls-Seed 0: Breite 100, ng-Gedächtnis 5, vier Größen, nie bindend); kein Zeitvergleich, nur ein Netz gegen Hänger."""
    z = E.live_lauf(C.LIVE_N_MAX, C.LIVE_BREITE_MAX, 5, 4, C.GRENZE_NIE, "unabhängig", 0)
    assert z["abgebrochen"] or z["erzeugt"] > 1000
    assert z["fehler"] is None
