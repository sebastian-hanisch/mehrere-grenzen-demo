"""Feste Messreihen (data/*.json): Zellen auswählen und Kennzahlen bilden (Median, Mittel, Maximum, Zahl fertiger und abgebrochener Läufe).

Nichts hier rechnet das Label-Setting neu; die Rohwerte je Instanz stehen in den JSON-Dateien, jede Zelle nennt ihre Quelldatei. Gerechnet wird nur
über die Instanzen einer Zelle. Zeilen abgebrochener Läufe zählen nicht in die Mediane (sie fehlen bei zähen Zellen, dort stützen sich die Zahlen auf weniger Instanzen)."""

import json
from functools import lru_cache
from pathlib import Path
from statistics import mean, median

import mgr_constants as C

DATA = Path(__file__).resolve().parent / "data"
ARTEN = {
    "fest1": "ein Pricing-Aufruf mit den Dualpreisen der ersten Runde",
    "colgen": "die ganze Spaltenerzeugung (alle Pricing-Aufrufe zusammen)",
    "fest": "ein Pricing-Aufruf mit den Dualpreisen am Ende der Spaltenerzeugung bei nur der Zeit",
}
TYPEN = {"zufall": "zufällig", "cluster": "gruppiert"}
V11_GRENZEN = ("bindend (70)", "locker (140)", "nie bindend")


@lru_cache(maxsize=None)
def _lade(name: str) -> dict:
    return json.loads((DATA / name).read_text(encoding="utf-8"))


@lru_cache(maxsize=None)
def _index_v11() -> dict:
    d = _lade(C.BAND_FILE_V11)
    return {(z["typ"], z["breite"], z["k"], z["art"], z["grenze"], z["r"]): z for z in d["zellen"]}


def v11_zelle(typ: str, breite: int, k: int, art: str, grenze: str, r: int) -> dict:
    """Rohzeilen einer Zelle der V11-Messreihe. Für r = 1 gibt es keine Grenze (nur Zeit): `grenze` wird dann ignoriert."""
    return _index_v11()[(typ, breite, k, art, "nur Zeit" if r == 1 else grenze, r)]


def _fertig(zeilen):
    return [z for z in zeilen if not z[5]]


def kennzahlen(zeilen: list, mit_aufrufen: bool = False) -> dict:
    """Kennzahlen einer Zelle aus ihren Rohzeilen [Seed, Labels, dominiert, Vergleiche, Aufrufe, abgebrochen, (Schranke)].

    Median, Mittel und Maximum der Labels; Median des Anteils dominierter Labels (Anteil je Instanz auf vier Stellen gerundet, wie in der Messung) und der
    Vergleiche je Label (je Instanz gebildet, dann Median); Zahl fertiger und abgebrochener Läufe. Leere Zelle (alle abgebrochen): Werte None."""
    ok = _fertig(zeilen)
    k = {"fertig": len(ok), "abgebrochen": len(zeilen) - len(ok)}
    if not ok:
        return {**k, "labels_median": None, "labels_mittel": None, "labels_max": None, "anteil_median": None,
                "vergleiche_median": None, "vergleiche_je_label": None, "aufrufe_median": None, "schranke_median": None}
    k.update(
        labels_median=median(z[1] for z in ok),
        labels_mittel=mean(z[1] for z in ok),
        labels_max=max(z[1] for z in ok),
        anteil_median=median(round(z[2] / z[1], 4) for z in ok),
        vergleiche_median=median(z[3] for z in ok),
        vergleiche_je_label=median(z[3] / z[1] for z in ok),
        aufrufe_median=median(z[4] for z in ok) if mit_aufrufen else None,
        schranke_median=median(z[6] for z in ok if len(z) > 6 and z[6] is not None) if mit_aufrufen and any(len(z) > 6 and z[6] is not None for z in ok) else None,
    )
    return k


def v11_kennzahlen(typ: str, breite: int, k: int, art: str, grenze: str, r: int) -> dict:
    return kennzahlen(v11_zelle(typ, breite, k, art, grenze, r)["zeilen"], mit_aufrufen=(art == "colgen"))


def v11_tabelle(typ: str, breite: int, k: int, art: str) -> list:
    """Alle Zeilen einer Messart: je Grenze und r die Kennzahlen (r = 1 einmal als „nur Zeit“)."""
    zeilen = [{"grenze": "nur Zeit", "r": 1, **v11_kennzahlen(typ, breite, k, art, "nur Zeit", 1)}]
    for g in V11_GRENZEN:
        for r in (2, 3, 4):
            zeilen.append({"grenze": g, "r": r, **v11_kennzahlen(typ, breite, k, art, g, r)})
    return zeilen


def anteile_je_instanz(typ: str, breite: int, k: int, art: str, grenze: str) -> list:
    """Je Instanz (Seed, an dem alle vier Stufen r = 1 bis 4 fertig wurden) der Anteil dominierter Labels und die Labels bei r = 1, 2, 3, 4."""
    stufen = [{z[0]: z for z in _fertig(v11_zelle(typ, breite, k, art, grenze, r)["zeilen"])} for r in (1, 2, 3, 4)]
    seeds = sorted(set.intersection(*(set(s) for s in stufen)))
    return [{"seed": s, "anteil": [stufen[i][s][2] / stufen[i][s][1] for i in range(4)], "labels": [stufen[i][s][1] for i in range(4)]} for s in seeds]


def zahl_sinkend(instanzen: list, von: int, bis: int) -> int:
    """In wie vielen Instanzen ist der Anteil dominierter Labels bei Stufe `bis` kleiner als bei Stufe `von` (Stufen 1 bis 4)?"""
    return sum(1 for i in instanzen if i["anteil"][bis - 1] < i["anteil"][von - 1])


def abbrueche_v11(typ: str, breite: int, r: int | None = None, art: str = "colgen") -> int:
    """Zahl abgebrochener Läufe der Messart `art` (Standard: ganze Spaltenerzeugung) in allen Zellen eines Typs und einer Breite (beide ng-k, alle Grenzen; r = 1 bis 4 oder nur die Stufe `r`)."""
    d = _lade(C.BAND_FILE_V11)
    return sum(sum(1 for x in z["zeilen"] if x[5]) for z in d["zellen"]
               if z["typ"] == typ and z["breite"] == breite and z["art"] == art and (r is None or z["r"] == r))


# --- Verbrauchsmodelle (p04) ----------------------------------------------------------------------------------------------------------------

@lru_cache(maxsize=None)
def _index_p04() -> dict:
    return {(z["modell"], z["r"]): z for z in _lade(C.BAND_FILE_P04)["zellen"]}


def p04_zeilen(modell: str, r: int) -> list:
    return _index_p04()[(modell, r)]["zeilen"]


def p04_kennzahlen(modell: str, r: int) -> dict:
    zeilen = p04_zeilen(modell, r)
    return {
        "labels_median": median(z[1] for z in zeilen), "labels_mittel": mean(z[1] for z in zeilen), "labels_max": max(z[1] for z in zeilen),
        "anteil_median": median(round(z[2] / z[1], 4) for z in zeilen),
        "vergleiche_median": median(z[3] for z in zeilen), "vergleiche_je_label": median(z[3] / z[1] for z in zeilen),
        "instanzen": len(zeilen),
    }


def p04_tabelle() -> list:
    return [{"modell": m, "r": r, **p04_kennzahlen(m, r)} for m in C.MODELLE for r in (1, 2, 3, 4)]


def p04_gleich_wie_vorstufe(modell: str, r: int) -> int:
    """In wie vielen Instanzen sind die Labels bei r gleich denen bei r − 1?"""
    a = {z[0]: z[1] for z in p04_zeilen(modell, r - 1)}
    b = {z[0]: z[1] for z in p04_zeilen(modell, r)}
    return sum(1 for s in a if a[s] == b[s])
