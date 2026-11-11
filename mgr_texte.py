"""Längere Texte der App, die auch in der README stehen (ein Test vergleicht beide Fassungen) und der Formel-Expander.

Zahlen im Text kommen aus den festen Messreihen (`mgr_baender`), nicht aus dem Kopf."""

import mgr_baender as B
import mgr_constants as C
from mgr_evaluation import fmt_int


def assumptions_markdown() -> str:
    """Annahmen, Grenzen und bekannte Probleme (App-Expander und README-Abschnitt „Annahmen, Grenzen und bekannte Probleme“)."""
    a100, a40 = B.abbrueche_v11("cluster", 100), B.abbrueche_v11("cluster", 40)
    bei_r2 = B.abbrueche_v11("cluster", 100, 2) + B.abbrueche_v11("cluster", 40, 2)
    fest1 = sum(B.abbrueche_v11(typ, breite, art="fest1") for typ in ("zufall", "cluster") for breite in (40, 100))
    return f"""**Annahmen**

- Die Instanzen sind eigene, Solomon-artige Instanzen (Quadrat 100 × 100, Zeit = Entfernung, Bedienzeit {int(C.BEDIENZEIT)}, Horizont {int(C.HORIZONT)}), nicht die Originalinstanzen von Solomon.
- Jede zusätzliche Größe summiert den Verbrauch der besuchten Kunden und hat eine feste Obergrenze (70, 140 oder nie bindend).
- Die Messreihen benutzen 30 Kunden und unabhängige Zufallsverbräuche für Fahrerzeit und dritte Größe (ganze Zahlen von 5 bis 25); vier Verbrauchsmodelle gibt es nur in einer Zelle (Breite 100, ng-Gedächtnis 5, nie bindende Grenzen).
- Ein Pricing-Aufruf benutzt die Dualpreise der ersten Spaltenerzeugungsrunde (Preis je Kunde = Hin- und Rückweg vom Depot); die ganze Spaltenerzeugung der festen Messreihen hat einen Überdeckungs-Master.
- Gezählt werden erzeugte Labels und Dominanztests; Sekunden stehen nur zur Information da.

**Grenzen**

- Nicht gemessen: mehr als vier Größen, Instanzen mit mehr als 30 Kunden in dieser Messreihe, bidirektionales Labeling und Eimer-Verfahren mit mehreren Größen, Zeit statt Labels.
- Je Zelle 12 Instanzen, kein Konfidenzmaß; Mediane, Mittel und Maxima über höchstens 12 Werte.
- Bei gruppierten Instanzen brachen Läufe der ganzen Spaltenerzeugung ab ({a100} Läufe bei Breite 100, {a40} bei Breite 40; Grenze der Messung 60 s je Pricing-Aufruf und 300 s gesamt), nur bei lockerer oder nie bindender Grenze und bei r = 3 oder 4, außer {bei_r2} Läufen bei r = 2. Diese Zellen stützen sich auf weniger Instanzen, und zwar auf die schnelleren. Auch in der Reihe „ein Pricing-Aufruf“ brachen {fest1} Läufe ab (ebenfalls nur gruppiert, bei lockerer oder nie bindender Grenze und r ≥ 2); diese Zellen stützen sich ebenso auf die schnelleren Instanzen.
- Das Handbeispiel hat sechs Kunden; seine Zahlen sind ein Beispiel zum Nachrechnen, keine Verteilung.

**Bekannte Probleme und Unsicherheiten**

- Die Live-Rechnung bricht bei sehr großen Einstellungen an einer festen Obergrenze ab ({fmt_int(C.LIVE_MAX_LABELS)} erzeugte Labels oder {fmt_int(C.LIVE_MAX_VERGLEICHE)} Dominanztests); dann gibt es für diese Einstellung kein Verdikt. Die Obergrenze zählt, sie misst keine Sekunden.
- Die Zeitgrenzen der abgebrochenen Läufe der Messreihe hängen von der Auslastung des Rechners ab, die Zahlen der Labels nicht.
- Die Instanzen entstehen mit dem Zufallsgenerator von Python (`random.Random`), damit sie mit den festen Messreihen übereinstimmen; Stichproben der Messreihen werden in den Tests nachgerechnet.
- Erklärungen mit „weil“ sind Deutungen, soweit nicht ausdrücklich gemessen (zum Beispiel, dass bindende Grenzen die Label-Zahl über abgeschnittene Wege senken).
- Die Diagramme haben keine Auswahlfunktion; ein Mausklick auf sie bewirkt nichts."""


MATH_LESEHILFE = r"""**Lesehilfe.** *Gegeben:* ein Depot und $n$ Kunden mit Entfernungen (gleich Fahrzeiten), Zeitfenstern, Dualpreisen und Verbräuchen in $r - 1$ zusätzlichen Größen mit Obergrenzen.
*Gesucht:* der Weg mit den kleinsten reduzierten Kosten, der alle Grenzen einhält, und die Zahl der Labels und Dominanzvergleiche, die das Label-Setting dafür braucht.

| Symbol | Bedeutung |
|---|---|
| $0, 1, \dots, n$ | Depot und Kunden |
| $d_{ij}$ | Entfernung von $i$ nach $j$ (gleich der Fahrzeit) |
| $s$ | Bedienzeit je Kunde (nicht am Depot) |
| $[e_j, l_j]$ | Zeitfenster des Kunden $j$; $H$: spätester Rückkehrzeitpunkt am Depot |
| $\pi_j$ | Dualpreis des Kunden $j$ ($\pi_0 = 0$) |
| $w_{mj}$, $W_m$ | Verbrauch der zusätzlichen Größe $m = 1, \dots, r - 1$ am Kunden $j$ und ihre Obergrenze |
| $N_j$ | Gedächtnis-Nachbarschaft des Kunden $j$: $j$ und seine $k - 1$ nächsten Kunden |
| $\ell = (t, c, q_1, \dots, q_{r-1}, M)$ | Label am Kunden $i$: Zeit, reduzierte Kosten, Verbrauch je Größe, Gedächtnis (Menge) |
"""

MATH_FORMELN = r"""**Erweiterung.** Ein Label $\ell$ am Knoten $i$ wird um den Kunden $j \notin M$ verlängert, wenn die Ankunft $a = t + s\,[i \ne 0] + d_{ij}$ höchstens $l_j$ ist und jede Grenze hält:

$$q_m + w_{mj} \le W_m \quad (m = 1, \dots, r - 1)$$

Das neue Label am Kunden $j$ hat

$$t' = \max(a, e_j), \qquad c' = c + d_{ij} - \pi_j, \qquad q'_m = q_m + w_{mj}, \qquad M' = (M \cap N_j) \cup \{j\}.$$

Ein Label am Kunden $i$ schließt eine Route, wenn $t + s + d_{i0} \le H$ gilt; ihre reduzierten Kosten sind $c + d_{i0}$.

**Dominanz.** Ein Label $\ell$ dominiert ein Label $\ell'$ am selben Kunden, wenn

$$c \le c', \qquad t \le t', \qquad q_m \le q'_m \;\;(m = 1, \dots, r - 1), \qquad M \subseteq M'.$$

*Warum das richtig ist:* Jede Fortsetzung, die für $\ell'$ zulässig ist, ist auch für $\ell$ zulässig (Zeit und Verbrauch von $\ell$ sind nicht größer, das Gedächtnis verbietet nicht mehr), und beide sammeln dieselben Kostenzuwächse. $\ell'$ kann also nie in einer billigeren Route enden als $\ell$ und darf gestrichen werden.

**Was gezählt wird.** *Erzeugte Labels* sind alle Labels, die eine Erweiterung hervorbringt (plus das Startlabel). *Dominanzvergleiche* sind alle ausgewerteten Tests „$\ell$ dominiert $\ell'$“: Für ein neues Label $\ell'$ wird zuerst gegen die lebenden Labels am Kunden getestet, bis eines es dominiert; sonst wird $\ell'$ gegen alle lebenden Labels getestet, ob es sie dominiert. Jede zusätzliche Größe fügt der Regel einen Vergleich $q_m \le q'_m$ hinzu.

**Elementarer Fall.** Ist $M$ die Menge der besuchten Kunden und sind die Verbräuche nicht negativ, folgt aus $M \subseteq M'$ schon $q_m = \sum_{j \in M} w_{mj} \le \sum_{j \in M'} w_{mj} = q'_m$. Bei elementarer Rechnung ändern nie bindende zusätzliche Größen deshalb weder die Labels noch die Zahl der Vergleiche; bei nichtelementarer Rechnung ($k < n$) ist das nicht so.

**Literatur.** Die Erweiterungsfunktionen und die Dominanz bei mehreren Größen sind Standard in der Literatur zu Kürzesten-Wege-Problemen mit Verbrauchsgrenzen. Als Standardreferenz gilt Irnich und Desaulniers (2005), Kapitel in dem Sammelband *Column Generation* (Springer); der Volltext wurde für diese Demo nicht eingesehen, Titel und Seiten sind nicht gegen die Quelle geprüft. Genannt wird sie bei Salani und Basso (2023, arXiv 2306.08622, PathWise), einer Bibliothek für das Kürzeste-Wege-Problem mit Verbrauchsgrenzen (nur die Zusammenfassung wurde für diese Demo erneut eingesehen). Keine Zahl dieser Demo stammt aus der Literatur."""
