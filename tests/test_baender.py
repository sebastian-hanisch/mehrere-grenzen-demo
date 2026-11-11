"""Feste Messreihen (data/*.json): Aufbau, Auswertungsfunktionen und Stichproben, die mit dem Kern dieser Demo NEU gerechnet werden.

Wo die Bänder neu gerechnet werden können (ein Pricing-Aufruf mit den Dualpreisen der ersten Runde, Messart „fest1“ und die Verbrauchsmodell-Reihe), rechnet ein Test eine Stichprobe nach
und vergleicht Labels, dominierte Labels und Vergleiche mit der gespeicherten Zeile. Die ganze Spaltenerzeugung („colgen“) braucht einen LP-Löser und ist nur als Messwert gespeichert.
Liegt die Vormessung (label-setting-planung/vormessung) neben dem Demo-Ordner, vergleicht ein Test zusätzlich alle Zellen mit den Rohdateien."""

import json
from pathlib import Path

import pytest

import mgr_algorithm as A
import mgr_baender as B
import mgr_constants as C
import mgr_scenario as S

ROOT = Path(__file__).resolve().parent.parent
GRENZEN = {"bindend (70)": 70, "locker (140)": 140, "nie bindend": 10 ** 9}


def test_v11_file_has_240_cells_with_12_seeds_each():
    d = json.loads((ROOT / "data" / C.BAND_FILE_V11).read_text(encoding="utf-8"))
    assert len(d["zellen"]) == 240
    for z in d["zellen"]:
        assert [x[0] for x in z["zeilen"]] == list(range(12)) and z["quelle"].startswith("out_v11_")
        assert set(x[5] for x in z["zeilen"]) <= {0, 1}
    keys = {(z["typ"], z["breite"], z["k"], z["art"], z["grenze"], z["r"]) for z in d["zellen"]}
    assert len(keys) == 240                       # 2 Typen x 2 Breiten x 2 k x 3 Messarten x (1 + 3 Grenzen x 3 Stufen) Zellen


def test_p04_file_has_16_cells_with_12_seeds_each():
    d = json.loads((ROOT / "data" / C.BAND_FILE_P04).read_text(encoding="utf-8"))
    assert [(z["modell"], z["r"]) for z in d["zellen"]] == [(m, r) for m in C.MODELLE for r in (1, 2, 3, 4)]
    assert all([x[0] for x in z["zeilen"]] == list(range(12)) for z in d["zellen"])


def test_kennzahlen_on_a_handset_cell():
    zeilen = [[0, 100, 80, 1000, 5, 0, 500.0], [1, 200, 140, 4000, 7, 0, 600.0], [2, 300, 150, 9000, 9, 0, 700.0], [3, 999, 999, 9, 9, 1, None]]
    k = B.kennzahlen(zeilen, mit_aufrufen=True)
    assert (k["fertig"], k["abgebrochen"]) == (3, 1)
    assert (k["labels_median"], k["labels_mittel"], k["labels_max"]) == (200, 200, 300)
    assert k["anteil_median"] == pytest.approx(0.7)             # 0,8 / 0,7 / 0,5: der Median ist 0,7
    assert k["vergleiche_je_label"] == pytest.approx(20.0)      # 10 / 20 / 30: der Median ist 20
    assert (k["aufrufe_median"], k["schranke_median"]) == (7, 600.0)
    assert B.kennzahlen([[0, 1, 1, 1, 1, 1, None]])["labels_median"] is None      # alle abgebrochen: keine Zahlen


def test_sinking_counts_use_only_instances_finished_at_all_four_levels():
    je = B.anteile_je_instanz("cluster", 100, 5, "colgen", "nie bindend")
    assert len(je) == 5 and B.zahl_sinkend(je, 1, 4) == 5


def test_p04_equal_to_the_previous_level():
    assert B.p04_gleich_wie_vorstufe("gleich der Last", 3) == 12 and B.p04_gleich_wie_vorstufe("gleich der Last", 4) == 12
    assert B.p04_gleich_wie_vorstufe("unabhängig", 3) == 0


@pytest.mark.parametrize("typ, breite, k, grenze, r, seeds", [
    ("zufall", 40, 1, "nie bindend", 4, range(5)), ("zufall", 40, 1, "bindend (70)", 3, range(5)), ("zufall", 40, 5, "locker (140)", 2, range(4)),
    ("cluster", 40, 1, "bindend (70)", 4, range(4)), ("zufall", 100, 1, "nie bindend", 2, range(4)), ("zufall", 40, 5, "nie bindend", 1, range(5)),
])
def test_sample_of_the_v11_single_call_rows_is_recomputed_exactly(typ, breite, k, grenze, r, seeds):
    zeilen = {x[0]: x for x in B.v11_zelle(typ, breite, k, "fest1", grenze, r)["zeilen"]}
    for seed in seeds:
        inst = S.make_instance(C.BAENDER_N, seed, breite, gruppiert=(typ == "cluster"))
        res = A.price_r(inst, S.dualpreise_erste_runde(inst), k, r, S.verbrauch(inst, seed, "unabhängig"), S.grenzen_liste(GRENZEN[grenze]))
        assert [res.erzeugt, res.dominiert, res.vergleiche] == zeilen[seed][1:4], (typ, breite, k, grenze, r, seed)


@pytest.mark.parametrize("modell", C.MODELLE)
def test_sample_of_the_model_rows_is_recomputed_exactly(modell):
    for r, seeds in ((2, (0, 1, 2)), (3, (0,))):
        zeilen = {x[0]: x for x in B.p04_zeilen(modell, r)}
        for seed in seeds:
            inst = S.make_instance(30, seed, 100)
            res = A.price_r(inst, S.dualpreise_erste_runde(inst), 5, r, S.verbrauch(inst, seed, modell), S.grenzen_liste(C.GRENZE_NIE))
            assert [res.erzeugt, res.dominiert, res.vergleiche] == zeilen[seed][1:4], (modell, r, seed)


def test_all_cells_agree_with_the_raw_files_of_the_pre_measurement_if_present():
    vor = ROOT.parent / "label-setting-planung" / "vormessung"
    if not (vor / "out_v11_auswertung.txt").exists():
        pytest.skip("Vormessung liegt nicht neben dem Demo-Ordner")
    import importlib.util
    spec = importlib.util.spec_from_file_location("baender_v11_tool", ROOT / "tools" / "baender_v11.py")
    tool = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(tool)
    zellen = tool.lies(vor)
    d = json.loads((ROOT / "data" / C.BAND_FILE_V11).read_text(encoding="utf-8"))
    for z in d["zellen"]:
        assert zellen[(z["typ"], z["breite"], z["k"], z["art"], z["grenze"], z["r"])]["zeilen"] == z["zeilen"]
    assert tool.pruefe(zellen, vor / "out_v11_auswertung.txt") == 0
