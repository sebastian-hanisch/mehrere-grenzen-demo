"""End-to-end-Rauchtest mit Streamlits AppTest: lädt app.py mit den Standardeinstellungen, klickt jeden Preset-Button, fährt jeden Regler an seine Grenzen, probiert jede Auswahl
und den Permalink und prüft, dass kein Python-Fehler auftritt und dass jedes Preset die erwartete Verdikt-Zeile zeigt (DEMO-PLAYBOOK §11a Punkt 7).
Expander werden nie per Index, sondern per Titel angesprochen."""

import os

import pytest
from streamlit.testing.v1 import AppTest

import mgr_baender as B
import mgr_constants as C
import mgr_presets as P

APP_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "app.py")
TIMEOUT = int(os.environ.get("APPTEST_TIMEOUT", "300"))  # unter Last (parallele Läufe) reichen 180 s nicht immer; Umgebungsvariable zum Anpassen
NBSP = " "


def _fresh_app() -> AppTest:
    at = AppTest.from_file(APP_PATH, default_timeout=TIMEOUT)
    at.run(timeout=TIMEOUT)
    assert not at.exception, [str(e) for e in at.exception]
    return at


def _verdicts(at) -> list:
    """Alle Verdikt- und Hinweisboxen (success, info, warning) als (Art, Text)."""
    return [(kind, e.value) for kind in ("success", "info", "warning") for e in getattr(at, kind)]


def _expander(at, title):
    return next(e for e in at.expander if e.label == title)


def test_app_loads_without_exception_and_shows_the_default_verdicts():
    at = _fresh_app()
    texte = [t for _k, t in _verdicts(at)]
    assert any(t.startswith("Im Handbeispiel (r = 1 bis 3): Anteil dominierter Labels 58,1") for t in texte)
    assert any(t.startswith("In dieser Instanz (r = 1 bis 4)") for t in texte)
    assert not at.error


def test_every_button_click_does_not_raise():
    labels = [b.label for b in _fresh_app().button]
    assert labels, "keine Buttons gefunden"
    for index, label in enumerate(labels):
        at = _fresh_app()
        at.button[index].click().run(timeout=TIMEOUT)
        assert not at.exception, (label, [str(e) for e in at.exception])


def test_every_slider_at_its_min_and_max_does_not_raise():
    for key in ("l_n", "l_breite"):
        for edge in ("min", "max"):
            at = _fresh_app()
            slider = at.sidebar.slider(key=key)
            slider.set_value(int(slider.min if edge == "min" else slider.max)).run(timeout=TIMEOUT)
            assert not at.exception, (key, edge, [str(e) for e in at.exception])


@pytest.mark.parametrize("key", [k for k, s in P.SETTING_SPECS.items() if s.choices is not None])
def test_every_choice_of_every_selection_control_does_not_raise(key):
    for wert in P.SETTING_SPECS[key].choices:
        at = _fresh_app()
        at.sidebar.radio(key=key).set_value(wert).run(timeout=TIMEOUT)
        assert not at.exception, (key, wert, [str(e) for e in at.exception])


def test_all_minima_and_all_maxima_together_do_not_raise():
    for edge in (0, -1):
        at = _fresh_app()
        for key, spec in P.SETTING_SPECS.items():
            if key == "l_seed":
                continue
            if spec.choices is not None:
                at.sidebar.radio(key=key).set_value(spec.choices[edge])
            else:
                at.sidebar.slider(key=key).set_value(int(spec.lo if edge == 0 else spec.hi))
        at.run(timeout=TIMEOUT)
        assert not at.exception, [str(e) for e in at.exception]


def test_seed_extremes_and_the_new_instance_button_do_not_raise():
    for seed in (0, C.SEED_MAX):
        at = _fresh_app()
        at.sidebar.number_input(key="l_seed").set_value(seed).run(timeout=TIMEOUT)
        assert not at.exception, seed
    at = _fresh_app()
    at.sidebar.button[-1].click().run(timeout=TIMEOUT)
    assert not at.exception and 0 <= at.session_state["l_seed"] <= C.SEED_MAX


def test_band_selection_controls_do_not_raise():
    for key, werte in (("b_typ", ("zufall", "cluster")), ("b_breite", (40, 100)), ("b_k", (1, 5)), ("b_art", ("fest1", "colgen", "fest"))):
        for wert in werte:
            at = _fresh_app()
            at.radio(key=key).set_value(wert).run(timeout=TIMEOUT)
            assert not at.exception, (key, wert, [str(e) for e in at.exception])


def test_band_cell_with_aborted_runs_shows_the_hint():
    at = _fresh_app()
    at.radio(key="b_typ").set_value("cluster")
    at.radio(key="b_breite").set_value(100)
    at.radio(key="b_k").set_value(5)
    at.radio(key="b_art").set_value("colgen").run(timeout=TIMEOUT)
    assert not at.exception
    hinweise = [w.value for w in at.warning if w.value.startswith("In dieser Zelle brachen")]
    erwartet = sum(z["abgebrochen"] for z in B.v11_tabelle("cluster", 100, 5, "colgen"))
    assert erwartet > 0 and len(hinweise) == 1 and f"brachen {erwartet} Läufe ab" in hinweise[0]


def test_permalink_sets_the_controls_and_unusable_values_fall_back_to_the_default():
    at = AppTest.from_file(APP_PATH, default_timeout=TIMEOUT)
    at.query_params["n"] = "12"
    at.query_params["k"] = "5"
    at.query_params["g"] = "bindend (70)"
    at.query_params["m"] = "gibt es nicht"
    at.query_params["r"] = "2"
    at.run(timeout=TIMEOUT)
    assert not at.exception
    assert (at.session_state["l_n"], at.session_state["l_k"], at.session_state["l_grenze"], at.session_state["l_modell"], at.session_state["l_r"]) == (12, 5, "bindend (70)", C.LIVE_DEFAULT_MODELL, 2)


# je Preset: ein Satzanfang der erwarteten Verdikt-Zeile des Handbeispiels (Art, Anfang) und der Live-Rechnung; die Zahlen kommen aus dem Kern
ERWARTET = {
    "Grundfall: jede Grenze zählt mit": ("success", f"Im Handbeispiel (r = 1 bis 3): Anteil dominierter Labels 58,1{NBSP}% → 38,5{NBSP}% → 29,7{NBSP}%", f"In dieser Instanz (r = 1 bis 4): Anteil dominierter Labels 87,8{NBSP}%"),
    "Bindende Grenzen": ("success", f"Im Handbeispiel (r = 1 bis 3): Anteil dominierter Labels 58,1{NBSP}% → 33,3{NBSP}% → 27,3{NBSP}%", f"In dieser Instanz (r = 1 bis 4): Anteil dominierter Labels 87,8{NBSP}% → 80,2{NBSP}%"),
    "Fahrerzeit gleich der Last": ("success", f"Im Handbeispiel (r = 1 bis 3): Anteil dominierter Labels 58,1{NBSP}% → 38,5{NBSP}% → 38,5{NBSP}%", "Bei r = 3, 4 ändert sich gegenüber der Stufe davor nichts"),
    "Gegenläufige Verbräuche": ("success", f"Im Handbeispiel (r = 1 bis 3): Anteil dominierter Labels 58,1{NBSP}% → 38,5{NBSP}% → 30,8{NBSP}%", f"In dieser Instanz (r = 1 bis 3): Anteil dominierter Labels 87,8{NBSP}% → 77,9{NBSP}% → 70,0{NBSP}%"),
    "Größtes Live-Beispiel": ("success", f"Im Handbeispiel (r = 1 bis 3): Anteil dominierter Labels 58,1{NBSP}% → 38,5{NBSP}% → 29,7{NBSP}%", f"In dieser Instanz (r = 1 bis 4): Anteil dominierter Labels 88,3{NBSP}% → 83,0{NBSP}%"),
}


@pytest.mark.parametrize("name", list(C.PRESETS))
def test_each_preset_shows_the_expected_verdict_lines(name):
    at = _fresh_app()
    at.sidebar.button(key=f"preset_{name}").click().run(timeout=TIMEOUT)
    assert not at.exception, [str(e) for e in at.exception]
    art, hand, live = ERWARTET[name]
    texte = _verdicts(at)
    assert any(k == art and t.startswith(hand) for k, t in texte), (name, [t[:120] for _k, t in texte])
    assert any(live in t for _k, t in texte if t.startswith("In dieser Instanz")), (name, [t[:200] for _k, t in texte])
    for key, value in C.PRESETS[name].items():
        assert at.session_state[key] == value


def test_preset_without_effect_does_not_report_an_effect():
    """„Fahrerzeit gleich der Last“: die Live-Rechnung meldet ausdrücklich, dass die dritte und vierte Größe nichts ändern."""
    at = _fresh_app()
    at.sidebar.button(key="preset_Fahrerzeit gleich der Last").click().run(timeout=TIMEOUT)
    live = next(t for _k, t in _verdicts(at) if t.startswith("In dieser Instanz"))
    assert "Bei r = 3, 4 ändert sich gegenüber der Stufe davor nichts" in live
    assert "erzeugte Labels 682 → 2" in live and live.count("2" + NBSP + "136") == 3


def test_the_expanders_are_found_by_title_and_the_math_one_starts_with_the_reading_aid():
    at = _fresh_app()
    titel = [e.label for e in at.expander]
    assert "So funktioniert Mehrere Grenzen" in titel and "⚠️ Annahmen, Grenzen und bekannte Probleme" in titel
    mathe = _expander(at, "📐 Mathematische Formulierung")
    assert mathe.markdown[0].value.startswith("**Lesehilfe.**")
    assert "$$" in mathe.markdown[1].value


def test_app_text_of_assumptions_is_the_text_of_the_function():
    import mgr_texte as T
    at = _fresh_app()
    assert _expander(at, "⚠️ Annahmen, Grenzen und bekannte Probleme").markdown[0].value == T.assumptions_markdown()


def test_live_cap_message_appears_when_the_cap_is_reached(monkeypatch):
    monkeypatch.setattr(C, "LIVE_MAX_LABELS", 500)
    at = AppTest.from_file(APP_PATH, default_timeout=TIMEOUT)
    at.query_params["seed"] = "777"
    at.run(timeout=TIMEOUT)
    assert not at.exception
    assert any("an der Obergrenze der Live-Rechnung abgebrochen" in t for k, t in _verdicts(at) if k == "warning")
