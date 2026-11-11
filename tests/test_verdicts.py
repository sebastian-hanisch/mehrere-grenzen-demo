"""Verdikte an von Hand gesetzten Werten (DEMO-PLAYBOOK §12): jede Schwelle der Art und jede Zahl im Text steht hier.

Ein Verdikt ist eine reine Funktion (Art, Text) und bekommt Zeilen, nicht Zufalls-Seeds. Zahlen im Text sind mit Dezimalkomma und geschütztem Leerzeichen als Tausendertrenner formatiert."""

import mgr_evaluation as E

N = E.NBSP


def _z(r, erzeugt, dominiert, vergleiche, abgebrochen=False, wert=-30.0, grenze_geschnitten=0):
    return {"r": r, "erzeugt": erzeugt, "dominiert": dominiert, "anteil": dominiert / erzeugt, "vergleiche": vergleiche, "je_label": vergleiche / erzeugt,
            "bester_wert": wert, "abgebrochen": abgebrochen, "grenze_geschnitten": grenze_geschnitten}


HAND = [_z(1, 31, 18, 51), _z(2, 52, 20, 303), _z(3, 64, 19, 622)]


def test_formats_use_decimal_comma_thousands_space_and_true_minus():
    assert E.fmt_int(1234567) == f"1{N}234{N}567" and E.fmt_int(-30) == "−30"
    assert E.fmt_dec(5.8333, 1) == "5,8" and E.fmt_dec(-0.25, 2) == "−0,25" and E.fmt_dec(12345.6, 1) == f"12{N}345,6"
    assert E.fmt_pct(0.581) == f"58,1{N}%"
    assert E.weg_text((3, 4, 2)) == "3 → 4 → 2" and "kein Weg" in E.weg_text(())


def test_dominance_verdict_success_names_every_number():
    kind, text = E.verdict_dominanz(HAND, "im Handbeispiel")
    assert kind == "success"
    assert text.startswith("Im Handbeispiel (r = 1 bis 3)")
    assert f"58,1{N}% → 38,5{N}% → 29,7{N}%" in text and "1,6 → 5,8 → 9,7" in text and "31 → 52 → 64" in text
    assert "fällt der Anteil dominierter Labels, und die Vergleiche je Label steigen" in text


def test_dominance_verdict_info_when_the_share_does_not_fall():
    zeilen = [_z(1, 100, 50, 200), _z(2, 200, 120, 800)]      # Anteil 50 % -> 60 %: steigt
    kind, text = E.verdict_dominanz(zeilen, "in dieser Instanz")
    assert kind == "info" and "Aber der Anteil dominierter Labels fällt nicht bei jeder wirksamen Größe" in text and "Vergleiche je Label steigen nicht" not in text
    kind, text = E.verdict_dominanz([_z(1, 100, 50, 200), _z(2, 200, 80, 300)], "in dieser Instanz")    # Anteil 50 -> 40 fällt, je Label 2,0 -> 1,5 fällt
    assert kind == "info" and "die Vergleiche je Label steigen nicht bei jeder wirksamen Größe" in text


def test_dominance_verdict_flags_a_step_without_effect():
    zeilen = [_z(1, 31, 18, 51), _z(2, 52, 20, 303), _z(3, 52, 20, 303)]
    kind, text = E.verdict_dominanz(zeilen, "im Handbeispiel")
    assert kind == "success" and "Bei r = 3 ändert sich gegenüber der Stufe davor nichts" in text
    kind, text = E.verdict_dominanz([_z(1, 52, 20, 303), _z(2, 52, 20, 303)], "im Handbeispiel")
    assert kind == "info" and "ändern die zusätzlichen Größen nichts" in text and "(52)" in text and "(303)" in text


def test_dominance_verdict_one_row_and_aborted_rows():
    assert E.verdict_dominanz(HAND[:1], "im Handbeispiel")[0] == "info"
    kind, text = E.verdict_dominanz([HAND[0], _z(2, 100000, 1, 5, abgebrochen=True)], "in dieser Instanz")
    assert kind == "warning" and f"100{N}000 Labels erzeugt" in text and "r = 2" in text


def test_correlation_verdict_hand():
    zeilen = []
    for modell, labels in (("unabhängig", (31, 52, 64)), ("gleich der Last", (31, 52, 52))):
        for r, l in zip((1, 2, 3), labels):
            zeilen.append({"modell": modell, **_z(r, l, 10, {31: 51, 52: 303, 64: 622}[l])})
    kind, text = E.verdict_korrelation_hand(zeilen)
    assert kind == "success" and "„gleich der Last“: 31 → 52 → 52 Labels, 51 → 303 → 303 Vergleiche" in text and "Beim Modell „gleich der Last“ ändert die dritte Größe nichts" in text
    kind, text = E.verdict_korrelation_hand([z for z in zeilen if z["modell"] == "unabhängig"])
    assert kind == "info" and "Bei keinem Modell bleibt die dritte Größe ohne Wirkung" in text


def test_p04_verdict_counts_instances_and_checks_that_other_models_add_labels():
    kind, text = E.verdict_p04(12, 12, [18176, 18176, 18176], {"unabhängig": 37692, "gegenläufig": 58421})
    assert kind == "success" and "in 12 von 12 Instanzen" in text and f"18{N}176 → 18{N}176 → 18{N}176" in text and "kommen Labels hinzu" in text
    kind, text = E.verdict_p04(11, 12, [18176, 18176, 18176], {"unabhängig": 37692})
    assert kind == "info" and "in 11 von 12 Instanzen" in text
    kind, text = E.verdict_p04(12, 12, [18176, 18176, 18176], {"unabhängig": 18000})
    assert kind == "info" and "nicht in jedem Modell" in text


def _tabelle(anteile_je_grenze):
    basis = {"grenze": "nur Zeit", "r": 1, "anteil_median": 0.9}
    zeilen = [basis]
    for g, werte in anteile_je_grenze.items():
        zeilen += [{"grenze": g, "r": r, "anteil_median": w} for r, w in zip((2, 3, 4), werte)]
    return zeilen


def test_bands_verdict_success_and_info():
    inst = {g: {"gesamt": 12, "1→2": 12, "2→3": 11, "3→4": 12} for g in ("bindend (70)", "locker (140)", "nie bindend")}
    fallend = {g: (0.8, 0.7, 0.6) for g in inst}
    kind, text = E.verdict_baender(_tabelle(fallend), inst, "fest1")
    assert kind == "success" and f"bindend (70): 90,0{N}% → 80,0{N}% → 70,0{N}% → 60,0{N}% (sinkt in 12, 11 und 12 von 12 Instanzen" in text
    steigend = {**fallend, "locker (140)": (0.8, 0.85, 0.6)}
    kind, _ = E.verdict_baender(_tabelle(steigend), inst, "fest1")
    assert kind == "info"
    kind, text = E.verdict_baender(_tabelle({**fallend, "nie bindend": (None, None, None)}), inst, "fest1")
    assert kind == "info" and "nie bindend: zu viele Abbrüche" in text


def test_binding_hand_verdict_warns_about_a_different_problem():
    nie = [_z(1, 31, 18, 51), _z(2, 52, 20, 303), _z(3, 64, 19, 622, wert=-30.0)]
    bind = [_z(1, 31, 18, 51), _z(2, 33, 11, 99, wert=-18.0, grenze_geschnitten=51), _z(3, 33, 9, 112, wert=-18.0, grenze_geschnitten=63)]
    kind, text = E.verdict_bindend_hand(nie, bind)
    assert kind == "warning" and "nur 33 statt 64 Labels" in text and "von −30 auf −18" in text and "63 Erweiterungen scheitern an einer Grenze" in text
    kind, text = E.verdict_bindend_hand(nie, nie)
    assert kind == "info" and "64 Labels mit und 64 ohne" in text


def test_binding_v11_verdict_compares_labels_and_calls():
    basis = {"labels_median": 433558, "aufrufe_median": 59.0}
    kind, text = E.verdict_bindend_v11(basis, {"labels_median": 175545, "aufrufe_median": 18.0})
    assert kind == "warning" and f"433{N}558 bei nur der Zeit gegen 175{N}545" in text and "59 statt 18 Pricing-Aufrufe" in text
    kind, text = E.verdict_bindend_v11(basis, {"labels_median": 500000, "aufrufe_median": 60.0})
    assert kind == "info" and "nicht weniger Labels" in text
