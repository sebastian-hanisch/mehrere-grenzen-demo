"""README gegen App und Tests: gleicher Annahmen-Text, Testzahl = Zahl der gesammelten Tests, jeder in der Zahl-zu-Test-Tabelle genannte Test existiert, keine Platzhalter."""

import re
import subprocess
import sys
from pathlib import Path

import mgr_texte as T

ROOT = Path(__file__).resolve().parent.parent
README = (ROOT / "README.md").read_text(encoding="utf-8")


def test_the_assumptions_text_of_the_app_is_in_the_readme_verbatim():
    assert T.assumptions_markdown() in README


def test_the_test_count_in_the_readme_is_the_number_of_collected_tests():
    p = subprocess.run([sys.executable, "-m", "pytest", "--collect-only", "-q", "-p", "no:cacheprovider", "tests"], cwd=ROOT, capture_output=True, text=True, timeout=300)
    gesammelt = int(re.search(r"(\d+) tests? collected", p.stdout).group(1))
    genannt = int(re.search(r"Die Suite hat (\d+) Tests", README).group(1))
    assert genannt == gesammelt


def test_every_test_named_in_the_number_to_test_table_exists():
    absatz = README[README.index("**Zahl → Test.**"):README.index("## Ehrliche Grenzen")]
    namen = re.findall(r"`(test_[a-z0-9_]+)`", absatz)
    quelle = (ROOT / "tests" / "test_claims.py").read_text(encoding="utf-8")
    assert len(namen) == 14 and all(f"def {n}(" in quelle for n in namen)


def test_no_placeholders_are_left():
    for datei in [ROOT / "README.md", ROOT / "app.py", *ROOT.glob("mgr_*.py")]:
        text = datei.read_text(encoding="utf-8")
        assert "@@" not in text and "TODO" not in text, datei.name
