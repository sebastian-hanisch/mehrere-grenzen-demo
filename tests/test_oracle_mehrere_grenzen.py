"""Orakel-Test mehrere-grenzen-demo (ORACLE-PLAYBOOK §2/§5, DEMO-PLAYBOOK §12): unabhängiger Rechenweg für das Label-Setting mit mehreren Größen.

Das Orakel zählt ALLE zulässigen Wege auf (Tiefensuche über Teilwege, ohne Dominanz, ohne Warteschlange) und prüft die Wiederholungsregel (ng-Gedächtnis) nach ihrer
Definition an der Wegfolge, nicht über die Bitmasken des Kerns. Es benutzt weder `price_r` noch `extend` noch `dominiert` des Kerns, nur die Daten der Instanz.

Geprüft werden (1) der beste Wert (und die Zulässigkeit des gefundenen Weges) für r = 1 bis 4, ng-Gedächtnis 1, 3 und elementar, bindende und nie bindende Grenzen und (2) bei ng-Gedächtnis 1 die Menge der
überlebenden Labels je Kunde gegen die Pareto-Front aller Weg-Labels (die Dominanzregel des Kerns streicht genau die dominierten und gleichen Labels). Zählungen des Kerns
(erzeugte Labels, Vergleiche) hängen von der Reihenfolge der Warteschlange ab und haben kein Orakel außer dem Handbeispiel. 80 Instanzen mit ganzen Zahlen (Gleichstände exakt, Verbrauch 0 vorkommend), feste Zufalls-Seeds, unter 10 s."""

import mgr_algorithm as A
from conftest import gitter_instanz


def ng_mengen(inst, k):
    """Nachbarschaften NG(j) nach der Definition: j und die k − 1 nächsten anderen Kunden (Gleichstand: kleinere Nummer)."""
    mengen = {}
    for j in range(1, inst.n + 1):
        andere = sorted((i for i in range(1, inst.n + 1) if i != j), key=lambda i: (inst.dist[j][i], i))
        mengen[j] = {j, *andere[: k - 1]}
    return mengen


def ng_zulaessig(folge, ng):
    """Ng-Regel nach der Definition: eine Wiederholung des Kunden v an Stelle p nach einem früheren Besuch an Stelle s ist verboten, wenn v in der Nachbarschaft jedes dazwischen liegenden Kunden steht."""
    p = len(folge) - 1
    for s in range(p):
        if folge[s] == folge[p] and all(folge[p] in ng[folge[x]] for x in range(s + 1, p)):
            return False
    return True


def orakel(inst, dual, k, cons, limits):
    """Alle zulässigen Wege: Rückgabe (bester Wert, Weg, {Kunde: Menge der Vektoren (Zeit, Kosten, Verbräuche) aller Teilwege})."""
    ng = ng_mengen(inst, k)
    m = len(limits)
    bester = [0, ()]
    vektoren = {j: set() for j in range(1, inst.n + 1)}

    def rec(folge, i, t, q, c):
        if folge:
            vektoren[i].add((t, c, tuple(q)))
            if t + inst.bedienzeit + inst.dist[i][0] <= inst.horizont:
                rc = c + inst.dist[i][0]
                if (rc, tuple(folge)) < (bester[0], bester[1] or (99,)) and rc < 0:
                    bester[0], bester[1] = rc, tuple(folge)
        for j in range(1, inst.n + 1):
            if folge and not ng_zulaessig(folge + [j], ng):
                continue
            q2 = [q[x] + cons[x][j] for x in range(m)]
            if any(q2[x] > limits[x] for x in range(m)):
                continue
            ank = t + (inst.bedienzeit if folge else 0) + inst.dist[i][j]
            if ank > inst.spaet[j]:
                continue
            rec(folge + [j], j, max(ank, inst.frueh[j]), q2, c + inst.dist[i][j] - dual[j])

    rec([], 0, 0, [0] * m, 0)
    return bester[0], bester[1], vektoren


def pareto(vektoren):
    """Nicht dominierte, verschiedene Vektoren (Zeit, Kosten, Verbräuche): v bleibt, wenn kein anderer Vektor w mit w <= v in allen Stellen existiert."""
    return {v for v in vektoren if not any(w != v and w[0] <= v[0] and w[1] <= v[1] and all(a <= b for a, b in zip(w[2], v[2])) for w in vektoren)}


def test_best_value_matches_enumeration_on_80_random_instances():
    fehler = []
    faelle = 0
    for seed in range(80):
        inst, dual, cons = gitter_instanz(seed)
        for k in (1, 3, inst.n):
            r = 1 + seed % 4
            limits = [[999] * 3, [8, 7, 9], [12, 9, 20]][(seed // 4) % 3]
            soll, weg, _ = orakel(inst, dual, k, cons[: r - 1], limits[: r - 1])
            res = A.price_r(inst, dual, k, r, cons, limits)
            faelle += 1
            if res.bester_wert != soll:
                fehler.append((seed, k, r, limits, res.bester_wert, soll))
            elif res.routen:
                # Bei gleichem Wert kann eine andere der gleich guten Routen herauskommen (gleiche Labels fallen weg): die Route des Kerns muss zulässig sein und den Wert haben.
                route = res.routen[0][1]
                nb = {j: m for j, m in ng_mengen(inst, k).items()}
                nb = [set()] + [nb[j] for j in range(1, inst.n + 1)]
                if A.pruefe_route(inst, route, cons[: r - 1], limits[: r - 1], nb) is not None or A.route_kosten(inst, dual, route) != soll:
                    fehler.append((seed, k, r, "Route", route))
    assert faelle == 240 and not fehler, fehler[:5]


def test_survivors_are_the_pareto_front_of_all_walk_labels_for_k1():
    for seed in range(80):
        inst, dual, cons = gitter_instanz(seed)
        r = 1 + seed % 4
        limits = [[999] * 3, [8, 7, 9], [12, 9, 20]][(seed // 4) % 3]
        _, _, vektoren = orakel(inst, dual, 1, cons[: r - 1], limits[: r - 1])
        res = A.price_r(inst, dual, 1, r, cons, limits)
        for j in range(1, inst.n + 1):
            assert set(res.ueberlebende[j]) == pareto(vektoren[j]), (seed, r, j)
            assert len(res.ueberlebende[j]) == len(set(res.ueberlebende[j]))   # keine doppelten Labels überleben


def test_orakel_agrees_with_the_hand_example(hand):
    """Das Orakel selbst am Handbeispiel prüfen: bester Wert −30 (nie bindend) und −18 (Last 12, Fahrerzeit 9), Weg 3-4-5-2-6 bzw. 3-2-5."""
    import mgr_scenario as S
    cons = S.hand_verbrauch("unabhängig")
    assert orakel(hand, S.HAND_DUAL, 1, cons, [999, 999])[:2] == (-30, (3, 4, 5, 2, 6))
    assert orakel(hand, S.HAND_DUAL, 1, cons, [12, 9])[:2] == (-18, (3, 2, 5))
    assert orakel(hand, S.HAND_DUAL, 1, [], [])[:2] == (-30, (3, 4, 5, 2, 6))


def test_orakel_ng_rule_follows_the_definition():
    ng = {1: {1, 2}, 2: {2, 1}, 3: {3}}
    assert not ng_zulaessig([1, 1], ng)               # sofortige Wiederholung immer verboten
    assert not ng_zulaessig([1, 2, 1], ng)            # 1 steht in der Nachbarschaft von 2: noch bekannt
    assert ng_zulaessig([1, 3, 1], ng)                # 1 steht nicht in der Nachbarschaft von 3: vergessen
    assert ng_zulaessig([1, 2, 3, 2], ng)             # 2 steht nicht in der Nachbarschaft von 3: vergessen
    assert not ng_zulaessig([3, 1, 2, 1], ng)         # die frühere Stelle von 1 liegt vor 3 und 2: nur 2 liegt dazwischen, und 1 steht in NG(2)
