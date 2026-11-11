"""Kennzahlen, Verdikt-Logik und Auswertung der Läufe (Handbeispiel, Live-Rechnung, feste Messreihen).

Jedes Verdikt der App ist eine reine Funktion `verdict_*(...) -> (Art, Text)`; die App ruft `getattr(st, Art)(Text)`, `tests/test_verdicts.py` prüft Schwellen und jede Zahl im Text.
Zahlen im Text kommen aus der Rechnung (f-String), nie aus dem Kopf."""

import time
from dataclasses import dataclass

import mgr_algorithm as A
import mgr_baender as B
import mgr_constants as C
import mgr_scenario as S


# ---------------------------------------------------------------------------------------------------------------------------------
# Zahlenformat (Dezimalkomma, geschütztes Leerzeichen als Tausendertrenner)
# ---------------------------------------------------------------------------------------------------------------------------------

NBSP = " "


def fmt_int(x) -> str:
    return f"{round(x):,}".replace(",", NBSP).replace("-", "−")


def fmt_dec(x, stellen: int = 1) -> str:
    return f"{x:,.{stellen}f}".replace(",", NBSP).replace(".", ",").replace("-", "−")


def fmt_pct(anteil, stellen: int = 1) -> str:
    """Anteil (0 bis 1) als Prozentangabe mit Dezimalkomma."""
    return fmt_dec(100 * anteil, stellen) + NBSP + "%"


def weg_text(route) -> str:
    return " → ".join(str(j) for j in route) if route else "kein Weg mit negativen Kosten"


# ---------------------------------------------------------------------------------------------------------------------------------
# Handbeispiel
# ---------------------------------------------------------------------------------------------------------------------------------

@dataclass(frozen=True)
class HandSettings:
    r: int = 3
    grenzen: str = C.HAND_GRENZEN[0]
    modell: str = C.HAND_MODELLE[0]


def zusammenfassung(res: A.Ergebnis, r: int) -> dict:
    """Kennzahlen eines Pricing-Aufrufs als einfaches Wörterbuch (zum Anzeigen und Zwischenspeichern)."""
    return {
        "r": r, "erzeugt": res.erzeugt, "dominiert": res.dominiert, "anteil": res.anteil_dominiert, "vergleiche": res.vergleiche,
        "je_label": res.vergleiche_je_label, "bester_wert": res.bester_wert, "weg": res.routen[0][1] if res.routen else (),
        "abgebrochen": res.abgebrochen, "grenze_geschnitten": res.grenze_geschnitten, "fenster_geschnitten": res.fenster_geschnitten,
    }


def hand_lauf(r: int, grenzen: str, modell: str, mit_protokoll: bool = False):
    """Ein Pricing-Aufruf am Handbeispiel (ng-Gedächtnis 1). Rückgabe (Ergebnis, Protokoll oder None)."""
    protokoll = [] if mit_protokoll else None
    res = A.price_r(S.handbeispiel(), S.HAND_DUAL, 1, r, S.hand_verbrauch(modell), S.hand_grenzen(grenzen), trace=protokoll)
    return res, protokoll


def hand_zeilen(grenzen: str, modell: str) -> list:
    """Kennzahlen für r = 1, 2, 3 bei gleichen Grenzen und gleichem Verbrauchsmodell, dazu die Gegenprobe durch Aufzählung und die Prüfung des besten Weges.

    Je Zeile zusätzlich: `aufzaehlung_wert`, `aufzaehlung_teilwege` und `fehler` (None, wenn der beste Weg alle Regeln einhält und sein Wert mit der Aufzählung übereinstimmt)."""
    inst, cons, limits = S.handbeispiel(), None, None
    zeilen = []
    for r in range(C.HAND_R_MIN, C.HAND_R_MAX + 1):
        cons, limits = S.hand_verbrauch(modell), S.hand_grenzen(grenzen)
        res = A.price_r(inst, S.HAND_DUAL, 1, r, cons, limits)
        z = zusammenfassung(res, r)
        wert, _weg, teilwege = A.aufzaehlung(inst, S.HAND_DUAL, r, cons, limits)
        z["aufzaehlung_wert"], z["aufzaehlung_teilwege"] = wert, teilwege
        z["fehler"] = None
        if res.routen:
            z["fehler"] = A.pruefe_route(inst, res.routen[0][1], cons[: r - 1], limits[: r - 1], nachbarn_mengen(inst, 1))
        if z["fehler"] is None and abs(wert - res.bester_wert) > 1e-9:
            z["fehler"] = f"Aufzählung findet {wert}, das Label-Setting {res.bester_wert}"
        zeilen.append(z)
    return zeilen


def hand_modell_zeilen(grenzen: str) -> list:
    """Für jedes Verbrauchsmodell des Handbeispiels die Kennzahlen bei r = 1, 2, 3."""
    return [{"modell": m, **z} for m in C.HAND_MODELLE for z in hand_zeilen(grenzen, m)]


def _weg_von(parent_of: dict, kunde_of: dict, lid: int) -> tuple:
    weg = []
    while lid != -1:
        weg.append(kunde_of[lid])
        lid = parent_of[lid]
    return tuple(reversed(weg))[1:]


def label_tabelle(protokoll: list) -> list:
    """Alle erzeugten Labels des Protokolls in Reihenfolge der Erzeugung (Nummern wie im Protokoll des Kerns).

    Je Zeile: id, weg, kunde, zeit, kosten, verbrauch (Tupel), von (Nummer des dominierenden Labels oder None), abgeloest_von (Nummer des Labels, das dieses später
    abgelöst hat, oder None), tests (Zahl der Dominanztests, die dieses Label beim Einfügen ausgelöst hat)."""
    parent_of, kunde_of, zeilen, index = {}, {}, [], {}
    for e in protokoll:
        if e[0] == "neu":
            _, lid, parent, kunde, zeit, kosten, q, von, tests = e
            parent_of[lid], kunde_of[lid] = parent, kunde
            zeile = {"id": lid, "weg": _weg_von(parent_of, kunde_of, lid), "kunde": kunde, "zeit": zeit, "kosten": kosten, "verbrauch": q,
                     "von": von, "abgeloest_von": None, "tests": tests}
            index[lid] = zeile
            zeilen.append(zeile)
        else:
            _, alt, neu = e
            index[alt]["abgeloest_von"] = neu
    return zeilen


def entscheidung_text(zeile: dict) -> str:
    if zeile["von"] is not None:
        return f"fällt weg: dominiert von L{zeile['von']}"
    if zeile["abgeloest_von"] is not None:
        return f"bleibt zunächst, entfällt später: dominiert von L{zeile['abgeloest_von']}"
    return "bleibt"


def entscheidungen(protokoll: list) -> list:
    """Jede Dominanzentscheidung als (Gewinner-Nummer, Verlierer-Nummer, Art), in der Reihenfolge ihres Auftretens.

    Art "neu verworfen": ein neues Label wurde von einem bestehenden dominiert; "alt abgelöst": ein neues Label dominierte ein bestehendes."""
    liste = []
    for e in protokoll:
        if e[0] == "neu" and e[7] is not None:
            liste.append((e[7], e[1], "neu verworfen"))
        elif e[0] == "ersetzt":
            liste.append((e[2], e[1], "alt abgelöst"))
    return liste


def vier_vergleiche(gewinner: dict, verlierer: dict, r: int) -> list:
    """Die Einzelvergleiche einer Dominanzentscheidung: je Größe Wert des Gewinners, Wert des Verlierers, ob der Gewinner höchstens so groß ist.

    Zeilen für Kosten, Zeit und die r − 1 Verbrauchsgrößen (bei r = 3 also vier Vergleiche)."""
    zeilen = [("Kosten", gewinner["kosten"], verlierer["kosten"]), ("Zeit", gewinner["zeit"], verlierer["zeit"])]
    for m in range(r - 1):
        zeilen.append((C.GROESSEN[m + 1], gewinner["verbrauch"][m], verlierer["verbrauch"][m]))
    return [{"größe": g, "gewinner": a, "verlierer": b, "höchstens": a <= b} for g, a, b in zeilen]


def weg_verbrauch(weg, cons, r: int) -> tuple:
    """Summe des Verbrauchs der ersten r − 1 zusätzlichen Größen über die Kunden eines Weges."""
    return tuple(sum(cons[m][j] for j in weg) for m in range(r - 1))


def gebrochene_paare(grenzen: str, modell: str, r: int) -> list:
    """Dominanzentscheidungen bei r = 1 (nur Kosten und Zeit) und ihre Haltbarkeit, wenn die zusätzlichen Größen bis r mitzählen.

    Je Entscheidung: kunde, gewinner (Weg), verlierer (Weg), haelt (bleibt die Dominanz bei r Größen bestehen?) und grund (die verletzten Verbrauchsvergleiche)."""
    res, prot = hand_lauf(1, grenzen, modell, mit_protokoll=True)
    tabelle = {z["id"]: z for z in label_tabelle(prot)}
    cons = S.hand_verbrauch(modell)
    zeilen = []
    for gew, ver, _art in entscheidungen(prot):
        g, v = tabelle[gew], tabelle[ver]
        qg, qv = weg_verbrauch(g["weg"], cons, r), weg_verbrauch(v["weg"], cons, r)
        verletzt = [f"{C.GROESSEN[m + 1]} {qg[m]} > {qv[m]}" for m in range(r - 1) if qg[m] > qv[m]]
        zeilen.append({"kunde": g["kunde"], "gewinner": g["weg"], "verlierer": v["weg"], "gewinner_zeit": g["zeit"], "gewinner_kosten": g["kosten"],
                       "verlierer_zeit": v["zeit"], "verlierer_kosten": v["kosten"], "haelt": not verletzt, "grund": ", ".join(verletzt)})
    return zeilen


# ---------------------------------------------------------------------------------------------------------------------------------
# Live-Rechnung (Experiment 3)
# ---------------------------------------------------------------------------------------------------------------------------------

@dataclass(frozen=True)
class LiveSettings:
    n: int = C.LIVE_DEFAULT_N
    breite: int = C.LIVE_DEFAULT_BREITE
    k: int = C.LIVE_DEFAULT_K
    r: int = C.LIVE_DEFAULT_R
    grenze: str = C.LIVE_DEFAULT_GRENZE
    modell: str = C.LIVE_DEFAULT_MODELL
    seed: int = C.LIVE_DEFAULT_SEED


def nachbarn_mengen(inst, k: int) -> list:
    """Nachbarschaft NG(j) als Menge, unabhängig von der Bitmaske des Kerns gebildet (der Kunde selbst und die k − 1 nächsten, Gleichstand: kleinere Nummer)."""
    mengen = [set()]
    for j in range(1, inst.n + 1):
        andere = sorted((i for i in range(1, inst.n + 1) if i != j), key=lambda i: (inst.dist[j][i], i))
        mengen.append({j, *andere[: max(k - 1, 0)]})
    return mengen


def live_lauf(n: int, breite: int, k: int, r: int, grenze: int, modell: str, seed: int) -> dict:
    """Ein Pricing-Aufruf mit den Dualpreisen der ersten Runde auf einer zufälligen Instanz; Kennzahlen, geprüfter bester Weg und Rechenzeit (nur zur Information).

    Der beste Weg wird vor der Anzeige unabhängig geprüft (`pruefe_route`) und seine reduzierten Kosten von Grund auf nachgerechnet; weicht etwas ab, steht der Fehler im Ergebnis."""
    inst = S.make_instance(n, seed, breite)
    dual = S.dualpreise_erste_runde(inst)
    cons = S.verbrauch(inst, seed, modell)
    limits = S.grenzen_liste(grenze)
    t0 = time.perf_counter()
    res = A.price_r(inst, dual, k, r, cons, limits, max_labels=C.LIVE_MAX_LABELS, max_vergleiche=C.LIVE_MAX_VERGLEICHE)
    sekunden = time.perf_counter() - t0
    z = zusammenfassung(res, r)
    z["sekunden"] = sekunden
    z["fehler"] = None
    if res.routen and not res.abgebrochen:
        rc, route = res.routen[0]
        z["fehler"] = A.pruefe_route(inst, route, cons[: r - 1], limits[: r - 1], nachbarn_mengen(inst, k))
        if z["fehler"] is None and abs(A.route_kosten(inst, dual, route) - rc) > 1e-6:
            z["fehler"] = "reduzierte Kosten der Route stimmen nicht mit dem Label überein"
    return z


# ---------------------------------------------------------------------------------------------------------------------------------
# Verdikte (reine Funktionen)
# ---------------------------------------------------------------------------------------------------------------------------------

def _gleich(a: dict, b: dict) -> bool:
    return (a["erzeugt"], a["dominiert"], a["vergleiche"]) == (b["erzeugt"], b["dominiert"], b["vergleiche"])


def _gross(text: str) -> str:
    return text[:1].upper() + text[1:]


def _kette(werte, fmt) -> str:
    return " → ".join(fmt(w) for w in werte)


def verdict_dominanz(zeilen: list, ort: str) -> tuple:
    """Verdikt für Zeilen mit r = 1, 2, ... (Handbeispiel und Live-Rechnung): fällt der Anteil dominierter Labels, steigen die Vergleiche je Label?

    `ort` beschreibt, worauf sich die Aussage bezieht („im Handbeispiel“, „in dieser Instanz“)."""
    if len(zeilen) < 2:
        return "info", "Mit nur der Zeit als Größe gibt es nichts zu vergleichen. Wählen Sie mindestens zwei Größen, dann zeigt das Verdikt, wie sich der Anteil dominierter Labels und die Zahl der Vergleiche ändern."
    abg = next((z for z in zeilen if z["abgebrochen"]), None)
    if abg is not None:
        return "warning", (f"Bei r = {abg['r']} wurde die Rechnung an der Obergrenze der Live-Rechnung abgebrochen ({fmt_int(abg['erzeugt'])} Labels erzeugt, {fmt_int(abg['vergleiche'])} Vergleiche): "
                           "dafür gibt es kein Verdikt. Kleinere Einstellungen rechnen vollständig; größere Fälle stehen als feste Messreihen unten.")
    schritte = list(zip(zeilen, zeilen[1:]))
    if all(_gleich(a, b) for a, b in schritte):
        z = zeilen[-1]
        return "info", (f"{_gross(ort)} ändern die zusätzlichen Größen nichts: bei jedem r sind erzeugte Labels ({fmt_int(z['erzeugt'])}), dominierte Labels ({fmt_int(z['dominiert'])}) "
                        f"und Vergleiche ({fmt_int(z['vergleiche'])}) gleich. Eine Größe, die nichts Neues unterscheidet, kostet keine zusätzlichen Labels und Vergleiche.")
    wirksam = [(a, b) for a, b in schritte if not _gleich(a, b)]
    sinkt = all(b["anteil"] < a["anteil"] for a, b in wirksam)
    steigt = all(b["je_label"] > a["je_label"] for a, b in wirksam)
    text = (f"{_gross(ort)} (r = 1 bis {zeilen[-1]['r']}): Anteil dominierter Labels {_kette([z['anteil'] for z in zeilen], fmt_pct)}, "
            f"Vergleiche je Label {_kette([z['je_label'] for z in zeilen], fmt_dec)}, erzeugte Labels {_kette([z['erzeugt'] for z in zeilen], fmt_int)}.")
    ohne = [b["r"] for a, b in schritte if _gleich(a, b)]
    if ohne:
        text += f" Bei r = {', '.join(str(r) for r in ohne)} ändert sich gegenüber der Stufe davor nichts (gleiche Labels, dominierte Labels und Vergleiche)."
    if sinkt and steigt:
        return "success", text + " Mit jeder wirksamen Größe fällt der Anteil dominierter Labels, und die Vergleiche je Label steigen."
    teile = []
    if not sinkt:
        teile.append("der Anteil dominierter Labels fällt nicht bei jeder wirksamen Größe")
    if not steigt:
        teile.append("die Vergleiche je Label steigen nicht bei jeder wirksamen Größe")
    return "info", text + " Aber " + " und ".join(teile) + "."


def verdict_korrelation_hand(zeilen: list) -> tuple:
    """Verdikt am Handbeispiel über die Verbrauchsmodelle: `zeilen` mit den Schlüsseln modell, r, erzeugt, dominiert, vergleiche (alle Modelle, r = 1 bis 3)."""
    je = {}
    for z in zeilen:
        je.setdefault(z["modell"], {})[z["r"]] = z
    teile, ohne = [], []
    for modell, rs in je.items():
        a, b, c = rs[1], rs[2], rs[3]
        teile.append(f"„{modell}“: {fmt_int(a['erzeugt'])} → {fmt_int(b['erzeugt'])} → {fmt_int(c['erzeugt'])} Labels, {fmt_int(a['vergleiche'])} → {fmt_int(b['vergleiche'])} → {fmt_int(c['vergleiche'])} Vergleiche")
        if _gleich(b, c):
            ohne.append(modell)
    text = "Labels und Vergleiche bei r = 1, 2, 3 im Handbeispiel: " + "; ".join(teile) + "."
    if ohne:
        text += f" Beim Modell „{ohne[0]}“ ändert die dritte Größe nichts: erzeugte Labels, dominierte Labels und Vergleiche bleiben gleich."
        return "success", text
    return "info", text + " Bei keinem Modell bleibt die dritte Größe ohne Wirkung."


def verdict_p04(modell_gleich: int, instanzen: int, labels_gleich: list, labels_andere: dict) -> tuple:
    """Verdikt der festen Verbrauchsmodell-Reihe: bei „gleich der Last“ in wie vielen Instanzen kommen bei r = 3 und r = 4 keine Labels hinzu?

    `modell_gleich`: Zahl der Instanzen (von `instanzen`), in denen bei r = 3 und r = 4 genau die Labels von r = 2 erzeugt wurden; `labels_gleich`: Median-Labels
    bei r = 2, 3, 4 für „gleich der Last“; `labels_andere`: Median-Labels bei r = 4 je anderem Modell."""
    andere = ", ".join(f"„{m}“ {fmt_int(v)}" for m, v in labels_andere.items())
    hinzu = all(v > labels_gleich[0] for v in labels_andere.values())
    text = (f"Bei „gleich der Last“ sind die Labels bei r = 3 und r = 4 in {modell_gleich} von {instanzen} Instanzen genau die von r = 2 (Median {fmt_int(labels_gleich[0])} → {fmt_int(labels_gleich[1])} → {fmt_int(labels_gleich[2])}). "
            f"Bei den übrigen Modellen (Median bei r = 4: {andere}) {'kommen Labels hinzu' if hinzu else 'kommen nicht in jedem Modell Labels hinzu'}.")
    return ("success" if modell_gleich == instanzen and hinzu else "info"), text


def verdict_baender(tabelle: list, instanzen: dict, art: str) -> tuple:
    """Verdikt der V11-Bänder für eine Zelle (Typ, Breite, k, Messart): je Grenze der Median-Anteil dominierter Labels bei r = 1 bis 4 und in wie vielen Instanzen er von Stufe zu Stufe sinkt.

    `tabelle`: Zeilen von `v11_tabelle`; `instanzen`: je Grenze (Name) die Zahlen sinkender Instanzen als {"gesamt": m, "1→2": a, "2→3": b, "3→4": c}."""
    basis = next(z for z in tabelle if z["r"] == 1)
    teile, alle_sinkend = [], True
    for g in B.V11_GRENZEN:
        zeilen = [basis] + [z for z in tabelle if z["grenze"] == g]
        if any(z["anteil_median"] is None for z in zeilen):
            teile.append(f"{g}: zu viele Abbrüche, kein Median")
            alle_sinkend = False
            continue
        a = [z["anteil_median"] for z in zeilen]
        sinkt = all(y < x for x, y in zip(a, a[1:]))
        alle_sinkend &= sinkt
        inst = instanzen[g]
        teile.append(f"{g}: {_kette(a, fmt_pct)} (sinkt in {inst['1→2']}, {inst['2→3']} und {inst['3→4']} von {inst['gesamt']} Instanzen von Stufe zu Stufe)")
    text = "Median des Anteils dominierter Labels bei r = 1, 2, 3, 4 – " + "; ".join(teile) + "."
    return ("success" if alle_sinkend else "info"), text


def verdict_bindend_hand(nie: list, bindend: list) -> tuple:
    """Handbeispiel: bei bindenden Grenzen weniger Labels, aber ein schlechterer bester Wert (`nie`, `bindend`: Zeilen für r = 1, 2, 3)."""
    n3, b3 = nie[2], bindend[2]
    if b3["erzeugt"] < n3["erzeugt"] and b3["bester_wert"] > n3["bester_wert"]:
        return "warning", (f"Bei r = 3 entstehen mit den Grenzen Last 12 und Fahrerzeit 9 nur {fmt_int(b3['erzeugt'])} statt {fmt_int(n3['erzeugt'])} Labels, "
                           f"aber der beste Wert verschlechtert sich von {fmt_int(n3['bester_wert'])} auf {fmt_int(b3['bester_wert'])}: Die Grenzen schneiden Wege ab ({fmt_int(b3['grenze_geschnitten'])} Erweiterungen scheitern an einer Grenze), "
                           "die Ersparnis an Labels ist eine Folge der Zulässigkeit und kein Gewinn der Dominanz. Die Aufgabe selbst ist eine andere geworden.")
    return "info", (f"Bei r = 3 entstehen {fmt_int(b3['erzeugt'])} Labels mit und {fmt_int(n3['erzeugt'])} ohne bindende Grenzen; der beste Wert ist {fmt_int(b3['bester_wert'])} gegen {fmt_int(n3['bester_wert'])}.")


def verdict_bindend_v11(basis: dict, bindend: dict) -> tuple:
    """V11 (ganze Spaltenerzeugung): Labels und Pricing-Aufrufe bei nur der Zeit gegen die Stufe r = 4 mit bindender Grenze (je Kennzahlen aus `kennzahlen`)."""
    a, b = basis, bindend
    if b["labels_median"] < a["labels_median"]:
        return "warning", (f"Mit bindender Grenze braucht die ganze Spaltenerzeugung in dieser Zelle weniger Labels: Median {fmt_int(a['labels_median'])} bei nur der Zeit gegen {fmt_int(b['labels_median'])} bei vier Größen, "
                           f"und {fmt_int(a['aufrufe_median'])} statt {fmt_int(b['aufrufe_median'])} Pricing-Aufrufe. Das liegt an der Zulässigkeit (die Grenze schneidet Wege ab), nicht an der Dominanz; die Aufgabe ist eine andere.")
    return "info", f"Mit dieser Grenze braucht die ganze Spaltenerzeugung nicht weniger Labels: Median {fmt_int(a['labels_median'])} gegen {fmt_int(b['labels_median'])}."
