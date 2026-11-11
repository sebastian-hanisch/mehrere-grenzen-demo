"""Jede Zahl der README (Abschnitt „Befunde“) wird hier nachgerechnet, mit denselben Auswertungsfunktionen wie in der App (DEMO-PLAYBOOK §4).

* Handbeispiel: exakte Zählungen des Kerns (ganze Zahlen; Anteile und Quotienten als Rechnung).
* Feste Messreihen: Mediane aus den Rohzeilen in data/*.json (Quelle: Messung der Vormessung; die Einzelwerte der Verbrauchsmodell-Reihe sind mit diesem Kern neu gerechnet,
  eine Stichprobe beider Reihen rechnet tests/test_baender.py nach). Mediane aus zwei mittleren Werten (x,5) werden wie in der Messung gerundet (Python rundet auf die gerade Zahl).
Zeiten stehen nirgends in der README und nirgends hier."""

from pathlib import Path

import mgr_baender as B
import mgr_constants as C
import mgr_evaluation as E
import mgr_scenario as S

README = (Path(__file__).resolve().parent.parent / "README.md").read_text(encoding="utf-8")


def _ganz(x):
    return round(x)


def _proz(x):
    return round(100 * x, 1)


# --- Handbeispiel -------------------------------------------------------------------------------------------------------------------------

def test_hand_example_never_binding_table():
    z = E.hand_zeilen(C.HAND_GRENZEN[0], "unabhängig")
    assert [x["erzeugt"] for x in z] == [31, 52, 64]
    assert [x["dominiert"] for x in z] == [18, 20, 19]
    assert [_proz(x["anteil"]) for x in z] == [_proz(18 / 31), _proz(20 / 52), _proz(19 / 64)] == [58.1, 38.5, 29.7]
    assert [x["vergleiche"] for x in z] == [51, 303, 622]
    assert [round(x["je_label"], 1) for x in z] == [1.6, 5.8, 9.7]
    assert [x["bester_wert"] for x in z] == [-30, -30, -30] and all(x["weg"] == (3, 4, 5, 2, 6) for x in z)
    assert [x["aufzaehlung_teilwege"] for x in z] == [88, 88, 88] and all(x["fehler"] is None for x in z)


def test_hand_example_binding_limits_table():
    z = E.hand_zeilen(C.HAND_GRENZEN[1], "unabhängig")
    assert [x["erzeugt"] for x in z] == [31, 33, 33] and [x["dominiert"] for x in z] == [18, 11, 9] and [x["vergleiche"] for x in z] == [51, 99, 112]
    assert [x["bester_wert"] for x in z] == [-30, -18, -18] and z[1]["weg"] == z[2]["weg"] == (3, 2, 5)
    assert [x["aufzaehlung_teilwege"] for x in z] == [88, 40, 38]
    assert [x["grenze_geschnitten"] for x in z] == [0, 51, 63]


def test_hand_example_eleven_of_eighteen_decisions_fail_at_r_3():
    paare = E.gebrochene_paare(C.HAND_GRENZEN[0], "unabhängig", 3)
    assert len(paare) == 18 and sum(1 for p in paare if not p["haelt"]) == 11


def test_hand_example_fahrerzeit_equal_to_load():
    z = E.hand_zeilen(C.HAND_GRENZEN[0], "gleich der Last")
    assert [(x["erzeugt"], x["dominiert"], x["vergleiche"]) for x in z[1:]] == [(52, 20, 303), (52, 20, 303)]


def test_hand_example_opposite_consumption_changes_dominance_but_not_the_label_count():
    z = E.hand_zeilen(C.HAND_GRENZEN[0], "gegenläufig")
    assert [(x["erzeugt"], x["dominiert"], x["vergleiche"]) for x in z] == [(31, 18, 51), (52, 20, 303), (52, 16, 342)]
    assert [x["bester_wert"] for x in z] == [-30, -30, -30]


# --- Verbrauchsmodell-Reihe (ein Pricing-Aufruf, n = 30, zufällig, Breite 100, k = 5, nie bindend, 12 Instanzen) ---------------------------

def _p04(modell):
    return [B.p04_kennzahlen(modell, r) for r in (1, 2, 3, 4)]


def test_p04_independent_model_medians_and_growth():
    k = _p04("unabhängig")
    assert [_ganz(x["labels_median"]) for x in k] == [7672, 18176, 28249, 37692]
    assert [_ganz(k[i + 1]["labels_median"]) - _ganz(k[i]["labels_median"]) for i in range(3)] == [10504, 10073, 9443]
    assert [_ganz(x["vergleiche_median"]) for x in k] == [75968, 1089956, 3151492, 8131986]
    assert [round(k[i + 1]["vergleiche_median"] / k[i]["vergleiche_median"], 2) for i in range(3)] == [14.35, 2.89, 2.58]
    assert [_proz(x["anteil_median"]) for x in k] == [88.8, 84.4, 81.5, 76.8]
    assert [round(x["vergleiche_je_label"], 1) for x in k] == [10.2, 49.5, 114.6, 232.0]


def test_p04_equal_to_load_adds_no_labels_in_any_instance():
    k = _p04("gleich der Last")
    assert [_ganz(x["labels_median"]) for x in k] == [7672, 18176, 18176, 18176]
    assert [_ganz(x["vergleiche_median"]) for x in k] == [75968, 1089956, 1089956, 1089956]
    assert [_proz(x["anteil_median"]) for x in k] == [88.8, 84.4, 84.4, 84.4]
    assert B.p04_gleich_wie_vorstufe("gleich der Last", 3) == B.p04_gleich_wie_vorstufe("gleich der Last", 4) == 12


def test_p04_load_plus_noise():
    k = _p04("Last plus Rauschen")
    assert [_ganz(x["labels_median"]) for x in k[1:]] == [18176, 21598, 23988]
    assert [_ganz(x["vergleiche_median"]) for x in k[2:]] == [1610327, 2279018]
    assert [_proz(x["anteil_median"]) for x in k[1:]] == [84.4, 83.3, 82.0]
    ruesch = [k[i + 1]["labels_median"] / k[i]["labels_median"] for i in (1, 2)]
    unab = [_p04("unabhängig")[i + 1]["labels_median"] / _p04("unabhängig")[i]["labels_median"] for i in (1, 2)]
    assert [round(100 * (x - 1)) for x in ruesch] == [19, 11] and [round(100 * (x - 1)) for x in unab] == [55, 33]


def test_p04_opposite_model():
    k = _p04("gegenläufig")
    assert [_ganz(x["labels_median"]) for x in k[1:]] == [18176, 45087, 58421]
    assert [_ganz(x["vergleiche_median"]) for x in k[2:]] == [9386282, 20927735]
    assert [_proz(x["anteil_median"]) for x in k[1:]] == [84.4, 78.7, 74.5]
    assert k[2]["labels_median"] > _p04("unabhängig")[2]["labels_median"] and k[3]["labels_median"] > _p04("unabhängig")[3]["labels_median"]


# --- V11 (n = 30, 12 Instanzen je Zelle) ---------------------------------------------------------------------------------------------------

def _v11(typ, breite, k, art, grenze):
    return [B.v11_kennzahlen(typ, breite, k, art, grenze, r) for r in (1, 2, 3, 4)]


def test_v11_full_column_generation_random_width_100_k1_binding_limit():
    z = _v11("zufall", 100, 1, "colgen", "bindend (70)")
    assert [_proz(x["anteil_median"]) for x in z] == [91.0, 87.6, 83.7, 81.0]
    assert [round(x["vergleiche_je_label"], 1) for x in z] == [2.8, 7.4, 13.6, 17.9]
    assert all(x["fertig"] == 12 for x in z)


def test_v11_full_column_generation_random_width_100_k1_never_binding():
    z = _v11("zufall", 100, 1, "colgen", "nie bindend")
    assert [_ganz(x["labels_median"]) for x in z] == [56652, 124109, 165980, 213880]
    assert [_proz(x["anteil_median"]) for x in z] == [91.0, 87.5, 84.9, 82.7]
    assert [round(x["vergleiche_je_label"], 1) for x in z] == [2.8, 13.5, 38.2, 101.3]


def test_v11_binding_limit_needs_fewer_labels_and_calls_in_the_full_column_generation():
    z = _v11("cluster", 100, 5, "colgen", "bindend (70)")
    assert [_ganz(x["labels_median"]) for x in z] == [433558, 212227, 200214, 175545]
    assert [_ganz(x["aufrufe_median"]) for x in z] == [59, 20, 20, 18]
    assert [round(x["schranke_median"], 1) for x in z] == [357.2, 502.0, 550.4, 558.2]
    assert all(x["fertig"] == 12 for x in z)


def test_v11_aborted_runs():
    assert (B.abbrueche_v11("cluster", 100), B.abbrueche_v11("cluster", 40), B.abbrueche_v11("zufall", 40), B.abbrueche_v11("zufall", 100)) == (41, 5, 0, 0)
    assert (B.abbrueche_v11("cluster", 100, 2), B.abbrueche_v11("cluster", 40, 2), B.abbrueche_v11("cluster", 100, 3) + B.abbrueche_v11("cluster", 100, 4)) == (2, 0, 39)
    assert B.abbrueche_v11("cluster", 40, 3) + B.abbrueche_v11("cluster", 40, 4) == 5
    for z in B._lade(C.BAND_FILE_V11)["zellen"]:   # Abbrüche gibt es nur bei gruppierten Instanzen, lockerer oder nie bindender Grenze und r >= 2
        if any(x[5] for x in z["zeilen"]):
            assert z["typ"] == "cluster" and z["grenze"] in ("locker (140)", "nie bindend") and z["r"] >= 2
    lockere = B.v11_kennzahlen("cluster", 100, 5, "colgen", "locker (140)", 4)
    nie = B.v11_kennzahlen("cluster", 100, 5, "colgen", "nie bindend", 4)
    assert (lockere["abgebrochen"], lockere["fertig"], nie["abgebrochen"], nie["fertig"]) == (6, 6, 7, 5)


def test_v11_share_of_dominated_labels_falls_in_every_instance_in_50_of_72_rows():
    voll, rest, groesster_rest = 0, 0, 0
    for typ in ("zufall", "cluster"):
        for breite in (40, 100):
            for k in (1, 5):
                for art in ("colgen", "fest1", "fest"):
                    for grenze in B.V11_GRENZEN:
                        je = B.anteile_je_instanz(typ, breite, k, art, grenze)
                        steigend = [len(je) - B.zahl_sinkend(je, a, b) for a, b in ((1, 2), (2, 3), (3, 4))]
                        if max(steigend) == 0:
                            voll += 1
                        else:
                            rest += 1
                            groesster_rest = max(groesster_rest, max(steigend))
    assert (voll, rest, groesster_rest) == (50, 22, 2)


def test_v11_cells_with_aborted_runs_have_fewer_than_12_finished_instances():
    z = B.v11_kennzahlen("cluster", 100, 5, "fest1", "nie bindend", 4)
    assert z["fertig"] + z["abgebrochen"] == 12 and z["fertig"] < 12


# --- Aussagen nach unabhängiger Prüfung: Einschränkungen, die die README und die App nennen --------------------------------------------------------

def test_labels_grow_about_linearly_with_slightly_shrinking_steps():
    k = _p04("unabhängig")
    schritte = [_ganz(k[i + 1]["labels_median"]) - _ganz(k[i]["labels_median"]) for i in range(3)]
    assert schritte == [10504, 10073, 9443] and schritte[0] > schritte[1] > schritte[2] and schritte[2] > 0.85 * schritte[0]
    assert "etwa linear in r (vier Stützstellen)" in README and "leicht abnehmend" in README


def test_binding_limit_has_fewer_labels_than_the_time_only_run_in_five_cells_and_more_in_three_of_eight():
    """Ganze Spaltenerzeugung, r = 4, Grenze 70 gegen nur die Zeit: weniger in 5, mehr in 3 der 8 Zellen; gegen die nie bindende Grenze (r = 4) weniger in allen 8."""
    mehr, weniger, gegen_nie = {}, 0, 0
    for typ in ("zufall", "cluster"):
        for breite in (40, 100):
            for k in (1, 5):
                nur_zeit = B.v11_kennzahlen(typ, breite, k, "colgen", "nur Zeit", 1)["labels_median"]
                bindend = B.v11_kennzahlen(typ, breite, k, "colgen", "bindend (70)", 4)["labels_median"]
                nie = B.v11_kennzahlen(typ, breite, k, "colgen", "nie bindend", 4)["labels_median"]
                gegen_nie += bindend < nie
                if bindend > nur_zeit:
                    mehr[(typ, breite, k)] = (_ganz(bindend), _ganz(nur_zeit))
                else:
                    weniger += 1
    assert (weniger, len(mehr), gegen_nie) == (5, 3, 8)
    assert mehr == {("zufall", 40, 1): (20104, 15824), ("zufall", 100, 1): (62030, 56652), ("cluster", 40, 1): (44684, 42266)}
    assert "In 3 der 8 Zellen der ganzen Spaltenerzeugung" in README and "20 104 gegen 15 824" in README and "62 030 gegen 56 652" in README and "44 684 gegen 42 266" in README
    assert "In dieser Zelle weniger als bei nur der Zeit" in README and "in allen 8 Zellen weniger" in README


def test_nine_of_the_fifty_always_falling_rows_rest_on_fewer_than_twelve_instances():
    kurz = []
    for typ in ("zufall", "cluster"):
        for breite in (40, 100):
            for k in (1, 5):
                for art in ("colgen", "fest1", "fest"):
                    for grenze in B.V11_GRENZEN:
                        je = B.anteile_je_instanz(typ, breite, k, art, grenze)
                        if max(len(je) - B.zahl_sinkend(je, a, b) for a, b in ((1, 2), (2, 3), (3, 4))) == 0 and len(je) < 12:
                            kurz.append(len(je))
    assert len(kurz) == 9 and min(kurz) == 4
    assert "ja in jeder fertigen Instanz (in 9 dieser 50 Zeilen sind es weniger als 12 Instanzen, bis herab zu 4" in README


def test_the_single_pricing_call_series_has_46_aborted_runs_like_the_full_column_generation():
    d = B._lade(C.BAND_FILE_V11)
    fest1 = [z for z in d["zellen"] if z["art"] == "fest1" and any(x[5] for x in z["zeilen"])]
    assert sum(sum(1 for x in z["zeilen"] if x[5]) for z in fest1) == 46
    assert all(z["typ"] == "cluster" and z["grenze"] in ("locker (140)", "nie bindend") and z["r"] >= 2 for z in fest1)
    assert sum(B.abbrueche_v11(t, b, art="fest1") for t in ("zufall", "cluster") for b in (40, 100)) == 46
    assert "brachen 46 Läufe ab (alle gruppiert, lockere oder nie bindende Grenze, r ≥ 2)" in README


def test_the_consumption_models_draw_the_third_size_from_different_random_streams():
    """Last plus Rauschen und gegenläufig ziehen aus 777 000 + Zufalls-Seed, unabhängig aus 10 000 019 + Zufalls-Seed: die dritte Größe unterscheidet sich schon deshalb."""
    inst = S.make_instance(12, 3, 100)
    unabhaengig = S.verbrauch(inst, 3, "unabhängig")[2]
    gegenlaeufig = S.verbrauch(inst, 3, "gegenläufig")[2]
    assert unabhaengig != gegenlaeufig and unabhaengig[0] == gegenlaeufig[0] == 0
    assert "verschiedenen Zufallsströmen" in README
