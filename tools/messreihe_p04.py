"""Rechnet die Messreihe „Verbrauchsmodelle“ neu und schreibt data/baender_p04.json.

Aufruf (im Demo-Ordner):  python tools/messreihe_p04.py [<run_p04.log>]

Ein Pricing-Aufruf je Instanz mit den Dualpreisen der ersten Runde, n = 30 Kunden, zufällige Instanzen, Zeitfenster der Breite 100, ng-Gedächtnis k = 5,
Grenzen nie bindend, 12 Instanzen (Zufalls-Seeds 0 bis 11), r = 1 bis 4 Größen, vier Verbrauchsmodelle. Die Einzelwerte (Labels, dominierte Labels, Dominanztests)
werden hier mit dem Kern der Demo neu gerechnet; die Mediane stimmen mit der Messung der Vormessung (run_p04.log) überein, das prüft das Skript, wenn die
Logdatei angegeben ist. Sekunden werden nicht gespeichert."""

import json
import re
import statistics
import sys
from pathlib import Path

WURZEL = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(WURZEL))

import mgr_algorithm as A  # noqa: E402
import mgr_constants as C  # noqa: E402
import mgr_scenario as S  # noqa: E402

BREITE, K, N = 100, 5, 30


def rechne() -> list:
    zellen = []
    for modell in C.MODELLE:
        for r in range(1, 5):
            zeilen = []
            for seed in C.BAENDER_SEEDS:
                inst = S.make_instance(N, seed, BREITE)
                dual = S.dualpreise_erste_runde(inst)
                res = A.price_r(inst, dual, K, r, S.verbrauch(inst, seed, modell), S.grenzen_liste(C.GRENZE_NIE))
                assert not res.abgebrochen
                zeilen.append([seed, res.erzeugt, res.dominiert, res.vergleiche])
            zellen.append({"modell": modell, "r": r, "zeilen": zeilen})
            print(modell, r, "Median Labels", statistics.median(z[1] for z in zeilen), flush=True)
    return zellen


def pruefe_log(zellen: list, log: Path) -> int:
    """Mediane (Labels, dominiert in %, Vergleiche) gegen die Tabellen des Logs."""
    abw, geprueft = 0, 0
    modell = None
    for zeile in log.read_text(encoding="utf-8").splitlines():
        m = re.match(r"Verbrauchsmodell: (.+)", zeile)
        if m:
            modell = m.group(1).strip()
            continue
        p = zeile.split()
        if modell and len(p) >= 5 and p[0].isdigit() and p[1].isdigit():
            r, labels, anteil, vgl = int(p[0]), int(p[1]), float(p[2]), int(p[3])
            z = next(c for c in zellen if c["modell"] == modell and c["r"] == r)["zeilen"]
            mess = (round(statistics.median(x[1] for x in z)), round(100 * statistics.median(x[2] / x[1] for x in z), 1), round(statistics.median(x[3] for x in z)))
            geprueft += 1
            if mess != (labels, anteil, vgl):
                abw += 1
                print("ABWEICHUNG", modell, r, mess, (labels, anteil, vgl))
    print(f"Zeilen des Logs geprüft: {geprueft}, Abweichungen: {abw}")
    return abw


def main():
    zellen = rechne()
    if len(sys.argv) > 1 and pruefe_log(zellen, Path(sys.argv[1])):
        sys.exit("Abweichungen zum Log, nichts geschrieben")
    out = {
        "beschreibung": ("Messreihe zu den Verbrauchsmodellen: ein Pricing-Aufruf je Instanz mit den Dualpreisen der ersten Runde, n = 30 Kunden, zufällig, Zeitfenster der Breite 100, "
                         "ng-Gedächtnis k = 5, Grenzen nie bindend, 12 Instanzen (Zufalls-Seeds 0 bis 11). Quelle der Mediane: run_p04.log der Vormessung; "
                         "die Einzelwerte sind mit tools/messreihe_p04.py neu gerechnet."),
        "spalten": ["seed", "labels", "dominiert", "vergleiche"],
        "breite": BREITE, "k": K, "n": N,
        "zellen": zellen,
    }
    ziel = WURZEL / "data" / "baender_p04.json"
    ziel.write_text(json.dumps(out, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8", newline="\n")
    print("geschrieben:", ziel)


if __name__ == "__main__":
    main()
