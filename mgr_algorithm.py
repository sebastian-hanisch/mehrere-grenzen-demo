"""Kern der Demo (nur Standardbibliothek): Label-Setting für das Pricing mit mehreren Größen (Zeit plus r − 1 Verbrauchsgrößen mit Obergrenze).

Ein Label beschreibt einen Teilweg vom Depot bis zu einem Kunden: [Zeit, Kosten, Verbrauch (Tupel), Gedächtnis (Bitmaske), Kunde, Vorgänger, tot].
Jede Regel ist eine eigene Funktion mit expliziten Ein- und Ausgaben (DEMO-PLAYBOOK 1b):

* `ng_masks`        Gedächtnis-Nachbarschaften (welche Wiederholungen verboten bleiben),
* `extend`          Erweiterungsregel: neuer Kunde, Zeitfenster, Verbrauchsgrenzen, Kosten, Gedächtnis,
* `dominiert`       Dominanzregel als Spezifikation (nur zum Prüfen und Erklären; der Kern rechnet dieselbe Regel in `insert_label` ohne Aufrufaufwand),
* `insert_label`    Dominanzprüfung eines neuen Labels gegen alle lebenden Labels am Kunden, zählt jeden ausgewerteten Test,
* `trace_route`     Rückverfolgung eines Weges über die Vorgänger,
* `price_r`         die Komposition: Warteschlange nach Zeit, ruft nur der Reihe nach auf (keine eigene Regel),
* `pruefe_route`    unabhängiger Prüfer einer fertigen Route (Fenster, Grenzen, Horizont, Gedächtnis),
* `route_kosten`    reduzierte Kosten einer Route, von Grund auf gerechnet.

Messgröße sind erzeugte Labels und Dominanzvergleiche; Sekunden zählt der Kern nicht. Kein Zustand außerhalb der Argumente; ein Abbruch
geschieht nur über die Obergrenze `max_labels` (deterministisch)."""

import heapq
from dataclasses import dataclass, field

from mgr_constants import EPS


@dataclass
class Ergebnis:
    """Ergebnis eines Pricing-Aufrufs."""

    routen: list                  # [(reduzierte Kosten, Route)], beste zuerst, nur negative reduzierte Kosten
    erzeugt: int                  # erzeugte Labels inklusive des Startlabels
    dominiert: int                # dominierte Labels (neue, die sofort wegfielen, und alte, die ein neues ablöste)
    vergleiche: int               # ausgewertete Dominanztests ("O gegen N" und "N gegen O" je einmal)
    abgebrochen: bool             # Obergrenze `max_labels` erreicht: dann sind die Zahlen unvollständig
    grenze_geschnitten: int       # Erweiterungen, die an einer Verbrauchsgrenze scheiterten (zuerst geprüft)
    fenster_geschnitten: int      # Erweiterungen, die am Zeitfenster scheiterten (nur nach bestandener Grenzprüfung)
    ueberlebende: tuple = field(default=())   # je Knoten die lebenden Labels als (Zeit, Kosten, Verbrauch)

    @property
    def bester_wert(self) -> float:
        """Kleinste reduzierte Kosten aller gefundenen Routen; 0, wenn keine Route negative reduzierte Kosten hat."""
        return self.routen[0][0] if self.routen else 0.0

    @property
    def anteil_dominiert(self) -> float:
        return self.dominiert / self.erzeugt if self.erzeugt else 0.0

    @property
    def vergleiche_je_label(self) -> float:
        return self.vergleiche / self.erzeugt if self.erzeugt else 0.0


def ng_masks(dist, n: int, k: int) -> list:
    """Gedächtnis-Nachbarschaft NG(j): der Kunde j selbst und seine k − 1 nächsten Kunden (Gleichstand: kleinere Nummer zuerst), als Bitmaske.

    k = 1: nur j selbst, verboten ist nur die sofortige Wiederholung. k = n: alle, die Route ist elementar."""
    masks = [0] * (n + 1)
    for j in range(1, n + 1):
        andere = sorted((i for i in range(1, n + 1) if i != j), key=lambda i: (dist[j][i], i))
        m = 1 << j
        for i in andere[: max(k - 1, 0)]:
            m |= 1 << i
        masks[j] = m
    return masks


def extend(inst, dual, ng, label, j: int, cons, limits):
    """Erweiterungsregel: Label am Knoten i um den Kunden j verlängern.

    Rückgabe (neues Label, Grund): Grund ist None, "grenze" (eine Verbrauchsgrenze wäre überschritten; geprüft wird zuerst) oder "fenster"
    (Ankunft nach dem Fensterende). Die Verbrauchsgrenzen gelten inklusive (Verbrauch = Grenze ist erlaubt). Warten bis zum Fensteranfang kostet nur Zeit."""
    t, c, q, mem, i = label[0], label[1], label[2], label[3], label[4]
    q2 = tuple(q[m] + cons[m][j] for m in range(len(q)))
    for m in range(len(q2)):
        if q2[m] > limits[m]:
            return None, "grenze"
    ank = t + (inst.bedienzeit if i != 0 else 0.0) + inst.dist[i][j]
    if ank > inst.spaet[j] + EPS:
        return None, "fenster"
    return [max(ank, inst.frueh[j]), c + inst.dist[i][j] - dual[j], q2, (mem & ng[j]) | (1 << j), j, None, False], None


def dominiert(o, n) -> bool:
    """Dominanzregel (Spezifikation): Label o dominiert Label n am selben Kunden, wenn Kosten, Zeit und jeder Verbrauch von o höchstens
    so groß sind wie von n und das Gedächtnis von o eine Teilmenge des Gedächtnisses von n ist."""
    return (o[1] <= n[1] + EPS and o[0] <= n[0] + EPS and (o[3] & ~n[3]) == 0
            and all(a <= b for a, b in zip(o[2], n[2])))


def insert_label(labels, am_knoten, neu):
    """Dominanzprüfung eines neuen Labels `neu` gegen die lebenden Labels `am_knoten` (Liste von Indizes in `labels`).

    1. Dominiert ein lebendes Label das neue, fällt das neue weg (Test "O gegen N", Abbruch beim ersten Treffer).
    2. Sonst dominiert das neue jedes lebende Label, das es dominieren kann (Test "N gegen O"); diese werden tot gesetzt.
    Rückgabe (Index des dominierenden alten Labels oder None, Liste der abgelösten alten Labels, lebende Labels danach ohne das neue, Zahl der Tests)."""
    c2, t2, q2, m2 = neu[1], neu[0], neu[2], neu[3]
    vergleiche = 0
    for oi in am_knoten:
        o = labels[oi]
        if o[6]:
            continue
        vergleiche += 1
        if o[1] <= c2 + EPS and o[0] <= t2 + EPS and (o[3] & ~m2) == 0:
            oq = o[2]
            ok = True
            for m in range(len(oq)):
                if oq[m] > q2[m]:
                    ok = False
                    break
            if ok:
                return oi, [], am_knoten, vergleiche
    lebend, abgeloest = [], []
    for oi in am_knoten:
        o = labels[oi]
        if o[6]:
            continue
        vergleiche += 1
        dom = c2 <= o[1] + EPS and t2 <= o[0] + EPS and (m2 & ~o[3]) == 0
        if dom:
            oq = o[2]
            for m in range(len(oq)):
                if q2[m] > oq[m]:
                    dom = False
                    break
        if dom:
            o[6] = True
            abgeloest.append(oi)
        else:
            lebend.append(oi)
    return None, abgeloest, lebend, vergleiche


def trace_route(labels, li: int) -> tuple:
    """Route (Kundennummern in Besuchsreihenfolge) eines Labels über die Vorgänger."""
    route = []
    while li != -1:
        route.append(labels[li][4])
        li = labels[li][5]
    return tuple(reversed(route))[1:]


def price_r(inst, dual, k: int, r: int, cons, limits, max_routes: int = 15, max_labels=None, max_vergleiche=None, trace=None) -> Ergebnis:
    """Pricing: bester Weg mit negativen reduzierten Kosten bei r Größen (Zeit mit Fenstern plus r − 1 Verbrauchsgrößen).

    cons[m][j]: Verbrauch der zusätzlichen Größe m am Kunden j (Position 0 = Depot); limits[m]: ihre Obergrenze; nur die ersten r − 1 werden benutzt.
    k: ng-Gedächtnis (1 = nur sofortige Wiederholung verboten). max_labels, max_vergleiche: Obergrenzen für erzeugte Labels und Dominanztests (None = unbegrenzt);
    wird eine erreicht, endet die Rechnung und `abgebrochen` ist gesetzt (die Zahlen sind dann unvollständig). Beides sind Zählungen, keine Zeitgrenzen: der Abbruch ist reproduzierbar.
    trace: wenn eine Liste, werden Ereignisse angehängt (nur Beobachtung, ändert nichts):
      ("neu", Id, Vorgänger-Id, Kunde, Zeit, Kosten, Verbrauch, dominierende Id oder None, Zahl der Tests dieses Labels)
      ("ersetzt", Id des abgelösten alten Labels, Id des neuen Labels)."""
    n = inst.n
    m_extra = r - 1
    cons = [cons[m] for m in range(m_extra)]
    limits = [limits[m] for m in range(m_extra)]
    ng = ng_masks(inst.dist, n, k)
    # Label: [Zeit, Kosten, Verbrauch, Gedächtnis, Kunde, Vorgänger, tot]
    labels = [[0.0, 0.0, (0,) * m_extra, 0, 0, -1, False]]
    am_knoten = [[] for _ in range(n + 1)]
    heap = [(0.0, 0)]
    erzeugt, dominiert_n, vergleiche = 1, 0, 0
    grenze_gesch, fenster_gesch = 0, 0
    enden = []
    abgebrochen = False
    if trace is not None:
        trace.append(("neu", 0, -1, 0, 0.0, 0.0, (0,) * m_extra, None, 0))
    while heap:
        _, li = heapq.heappop(heap)
        lab = labels[li]
        if lab[6]:
            continue
        if (max_labels is not None and erzeugt >= max_labels) or (max_vergleiche is not None and vergleiche >= max_vergleiche):
            abgebrochen = True
            break
        i = lab[4]
        if i != 0 and lab[0] + inst.bedienzeit + inst.dist[i][0] <= inst.horizont:
            enden.append((lab[1] + inst.dist[i][0], li))
        for j in range(1, n + 1):
            if j == i or (lab[3] >> j) & 1:
                continue
            neu, grund = extend(inst, dual, ng, lab, j, cons, limits)
            if neu is None:
                if grund == "grenze":
                    grenze_gesch += 1
                else:
                    fenster_gesch += 1
                continue
            neu[5] = li
            erzeugt += 1
            nid = len(labels)
            von, abgeloest, lebend, v = insert_label(labels, am_knoten[j], neu)
            vergleiche += v
            if von is not None:
                dominiert_n += 1
                neu[6] = True
                labels.append(neu)   # die Nummer bleibt vergeben (Nummern = Reihenfolge der Erzeugung); das tote Label wird nie erweitert
                if trace is not None:
                    trace.append(("neu", nid, li, j, neu[0], neu[1], neu[2], von, v))
                continue
            dominiert_n += len(abgeloest)
            am_knoten[j] = lebend
            labels.append(neu)
            am_knoten[j].append(nid)
            heapq.heappush(heap, (neu[0], nid))
            if trace is not None:
                trace.append(("neu", nid, li, j, neu[0], neu[1], neu[2], None, v))
                for oi in abgeloest:
                    trace.append(("ersetzt", oi, nid))
    gefunden = {}
    for rc, li in enden:
        route = trace_route(labels, li)
        if rc < -1e-7 and route not in gefunden:
            gefunden[route] = rc
    routen = sorted((rc, route) for route, rc in gefunden.items())[:max_routes]
    ueberlebende = tuple(tuple((labels[x][0], labels[x][1], labels[x][2]) for x in am_knoten[j] if not labels[x][6]) for j in range(n + 1))
    return Ergebnis(routen, erzeugt, dominiert_n, vergleiche, abgebrochen, grenze_gesch, fenster_gesch, ueberlebende)


def route_kosten(inst, dual, route) -> float:
    """Reduzierte Kosten einer Route: Weglänge (Depot, Route, Depot) minus die Dualpreise der besuchten Kunden; von Grund auf gerechnet."""
    folge = (0,) + tuple(route) + (0,)
    return sum(inst.dist[a][b] for a, b in zip(folge, folge[1:])) - sum(dual[j] for j in route)


def pruefe_route(inst, route, cons, limits, nachbarn=None):
    """Unabhängiger Prüfer: rechnet Zeiten und Verbräuche der Route von Grund auf. Rückgabe None, wenn die Route alle Regeln einhält, sonst der Text der Verletzung.

    Regeln: Kunden 1..n; jede Ankunft höchstens am Fensterende (warten bis zum Fensteranfang ist erlaubt); jede Verbrauchsgrenze inklusive;
    Rückkehr zum Depot bis zum Horizont; ng-Gedächtnis: `nachbarn[j]` = Menge NG(j); eine Wiederholung von j ist nur erlaubt, wenn zwischen den beiden Besuchen
    ein Kunde liegt, dessen Nachbarschaft j nicht enthält (bei k = 1 also nie direkt nacheinander)."""
    folge = tuple(route)
    if not folge:
        return "leere Route"
    t, vorher = 0.0, 0
    q = [0] * len(limits)
    for pos, j in enumerate(folge):
        if not 1 <= j <= inst.n:
            return f"Kunde {j} existiert nicht"
        t = t + (inst.bedienzeit if vorher != 0 else 0.0) + inst.dist[vorher][j]
        if t > inst.spaet[j] + EPS:
            return f"Ankunft {t:.2f} bei Kunde {j} nach dem Fensterende {inst.spaet[j]:.2f}"
        t = max(t, inst.frueh[j])
        for m in range(len(limits)):
            q[m] += cons[m][j]
            if q[m] > limits[m]:
                return f"Grenze {m + 1} überschritten ({q[m]} > {limits[m]}) bei Kunde {j}"
        vorher = j
    if t + inst.bedienzeit + inst.dist[vorher][0] > inst.horizont + EPS:
        return "Rückkehr zum Depot nach dem Horizont"
    if nachbarn is not None:
        for p in range(len(folge)):
            for s in range(p):
                if folge[s] == folge[p] and all(folge[p] in nachbarn[folge[x]] for x in range(s + 1, p)):
                    return f"Kunde {folge[p]} wiederholt, obwohl das Gedächtnis ihn noch kennt"
    return None


def aufzaehlung(inst, dual, r: int, cons, limits):
    """Gegenprobe durch Aufzählung (nur für kleine Instanzen, ng-Gedächtnis 1): alle Wege mit Zeitfenstern, Grenzen und Horizont, ohne sofortige Wiederholung.

    Ein anderer Rechenweg als das Label-Setting: Tiefensuche über alle Teilwege, ohne Dominanz. Rückgabe (bester Wert, bester Weg, Zahl der besuchten Teilwege
    einschließlich des leeren Weges am Depot); bester Wert 0 und leerer Weg, wenn kein Weg negative reduzierte Kosten hat."""
    m_extra = r - 1
    bester = [0.0, ()]
    besucht = [0]

    def rec(i, t, q, c, weg):
        besucht[0] += 1
        if i != 0 and t + inst.bedienzeit + inst.dist[i][0] <= inst.horizont:
            rc = c + inst.dist[i][0]
            if rc < bester[0] or (rc == bester[0] and rc < 0 and tuple(weg) < bester[1]):
                bester[0], bester[1] = rc, tuple(weg)
        for j in range(1, inst.n + 1):
            if j == i:
                continue
            q2 = [q[m] + cons[m][j] for m in range(m_extra)]
            if any(q2[m] > limits[m] for m in range(m_extra)):
                continue
            ank = t + (inst.bedienzeit if i != 0 else 0.0) + inst.dist[i][j]
            if ank > inst.spaet[j] + EPS:
                continue
            rec(j, max(ank, inst.frueh[j]), q2, c + inst.dist[i][j] - dual[j], weg + [j])

    rec(0, 0.0, [0] * m_extra, 0.0, [])
    return bester[0], bester[1], besucht[0]
