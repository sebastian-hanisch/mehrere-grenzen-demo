"""Presets: Vollständigkeit, gültige Werte, Standard-Preset = Standardeinstellungen, Permalink-Begrenzung."""

import pytest

import mgr_constants as C
import mgr_presets as P


def test_every_preset_has_help_and_sets_every_control():
    assert set(C.PRESETS) == set(C.PRESET_HELP)
    for name, preset in C.PRESETS.items():
        assert set(preset) == set(P.SETTING_SPECS), name
        assert C.PRESET_HELP[name]


def test_preset_values_are_valid_for_their_controls():
    for name, preset in C.PRESETS.items():
        for key, value in preset.items():
            spec = P.SETTING_SPECS[key]
            if spec.choices is not None:
                assert value in spec.choices, (name, key, value)
            else:
                assert spec.lo <= value <= spec.hi, (name, key, value)


def test_default_preset_equals_the_default_settings():
    first = next(iter(C.PRESETS.values()))
    assert {k: spec.default for k, spec in P.SETTING_SPECS.items()} == first


def test_presets_differ_from_each_other_in_at_least_one_control():
    werte = [tuple(sorted(p.items())) for p in C.PRESETS.values()]
    assert len(set(werte)) == len(werte)


def test_url_parameters_are_unique():
    params = [s.url_param for s in P.SETTING_SPECS.values()]
    assert len(params) == len(set(params))


@pytest.mark.parametrize("key, roh, erwartet", [
    ("l_n", "500", C.LIVE_N_MAX), ("l_n", "-3", C.LIVE_N_MIN), ("l_n", "abc", None), ("l_breite", "70", 70),
    ("l_k", "5", 5), ("l_k", "3", None), ("l_r", "9", None), ("l_r", "2", 2),
    ("l_grenze", "nie bindend", "nie bindend"), ("l_grenze", "egal", None), ("h_modell", "gegenläufig", "gegenläufig"), ("l_seed", "12345678", C.SEED_MAX),
])
def test_permalink_values_are_clamped_or_rejected(key, roh, erwartet):
    assert P._begrenzt(P.SETTING_SPECS[key], roh) == erwartet


def test_hand_models_are_a_subset_of_the_consumption_models_and_limits_have_values():
    assert set(C.HAND_MODELLE) <= set(C.MODELLE)
    assert C.GRENZEN == {"bindend (70)": 70, "locker (140)": 140, "nie bindend": 10 ** 9}
