"""Erzeugt data/baender_v11.json aus den vier Rohdateien der Messreihe (out_v11_<typ>_w<breite>.txt).

Aufruf (im Demo-Ordner):  python tools/baender_v11.py <Ordner mit den Rohdateien> [<out_v11_auswertung.txt>]

Jede Zeile der Rohdateien ist ein Lauf: Art (colgen = ganze Spaltenerzeugung, fest1 = ein Pricing-Aufruf mit den Dualpreisen der ersten Runde,
fest = ein Aufruf mit den Dualpreisen am Ende der Spaltenerzeugung bei nur der Zeit), Typ, n, Breite, Zufalls-Seed, ng-k, Grenze, r, untere Schranke,
Iterationen, Spalten, Pricing-Aufrufe, Labels, dominierte Labels, Anteil, Dominanzvergleiche, abgebrochen. Die JSON-Datei behält je Lauf
[Seed, Labels, dominiert, Vergleiche, Aufrufe, abgebrochen, Schranke] und nennt je Zelle die Quelldatei. Mit der zweiten Datei prüft das Skript, dass die
aus den Rohzeilen gerechneten Mediane mit den Tabellen der Auswertung übereinstimmen (Labels, Anteil dominiert, Vergleiche, Zahl der Instanzen, Abbrüche)."""

import json
import re
import statistics
import sys
from pathlib import Path

DATEIEN = {("zufall", 40): "out_v11_zufall_w40.txt", ("zufall", 100): "out_v11_zufall_w100.txt",
           ("cluster", 40): "out_v11_cluster_w40.txt", ("cluster", 100): "out_v11_cluster_w100.txt"}
GRENZE_NAME = {"-": "nur Zeit", "70": "bindend (70)", "140": "locker (140)", "1000000000": "nie bindend"}


def lies(ordner: Path) -> dict:
    zellen = {}
    for (typ, breite), name in DATEIEN.items():
        for zeile in (ordner / name).read_text(encoding="utf-8").splitlines():
            p = zeile.split()
            if not p or p[0] == "art" or len(p) != 17:
                continue
            art, _typ, n, w, seed, k, grenze, r = p[0], p[1], int(p[2]), int(p[3]), int(p[4]), int(p[5]), p[6], int(p[7])
            assert _typ == typ and w == breite and n == 30
            schranke = None if p[8] == "NA" else float(p[8])
            labels, dom, vergleiche, aufrufe, abgebr = int(p[12]), int(p[13]), int(p[15]), int(p[11]), int(p[16])
            schluessel = (typ, breite, k, art, GRENZE_NAME[grenze], r)
            z = zellen.setdefault(schluessel, {"quelle": name, "zeilen": []})
            z["zeilen"].append([seed, labels, dom, vergleiche, aufrufe, abgebr, schranke])
    for z in zellen.values():
        z["zeilen"].sort()
    return zellen


def pruefe(zellen: dict, auswertung: Path) -> int:
    """Vergleicht Mediane mit den Tabellen der Auswertung; gibt die Zahl der Abweichungen zurück."""
    text = auswertung.read_text(encoding="utf-8")
    abw, geprueft = 0, 0
    kopf = re.compile(r"### (zufall|cluster), n = 30, Breite (\d+), ng k = (\d+): (volle Spaltenerzeugung|ein Pricing-Aufruf, Dualpreise der ersten Runde|ein Pricing-Aufruf, Dualpreise der konvergierten)")
    art_von = {"volle Spaltenerzeugung": "colgen", "ein Pricing-Aufruf, Dualpreise der ersten Runde": "fest1", "ein Pricing-Aufruf, Dualpreise der konvergierten": "fest"}
    aktuell = None
    for zeile in text.splitlines():
        m = kopf.match(zeile)
        if m:
            aktuell = (m.group(1), int(m.group(2)), int(m.group(3)), art_von[m.group(4)], "colgen" in art_von[m.group(4)])
            continue
        if zeile.startswith("###"):
            aktuell = None
            continue
        if aktuell is None or not zeile.startswith("| ") or zeile.startswith("| Grenze") or zeile.startswith("|---"):
            continue
        zellenw = [c.strip() for c in zeile.strip().strip("|").split("|")]
        name, r = zellenw[0], int(zellenw[1])
        werte = [c.replace(" ", "").replace(" ", "") for c in zellenw[2:]]
        typ, breite, k, art, hat_aufrufe = aktuell
        z = zellen[(typ, breite, k, art, name, r)]["zeilen"]
        fertig = [x for x in z if not x[5]]
        erwartet_n, labels_med, anteil_med, vgl_med, vgl_je = int(werte[0]), int(werte[1]), float(werte[2]), int(werte[3]), float(werte[4])
        abgebr = int(werte[-1])
        mess_n = len(fertig)
        mess_labels = round(statistics.median(x[1] for x in fertig))
        mess_anteil = round(100 * statistics.median(round(x[2] / x[1], 4) for x in fertig), 1)
        mess_vgl = round(statistics.median(x[3] for x in fertig))
        mess_je = round(statistics.median(x[3] / x[1] for x in fertig), 1)
        ok = (mess_n, mess_labels, mess_anteil, mess_vgl, mess_je, len(z) - mess_n) == (erwartet_n, labels_med, anteil_med, vgl_med, vgl_je, abgebr)
        geprueft += 1
        if not ok:
            abw += 1
            print("ABWEICHUNG", aktuell[:4], name, r, (mess_n, mess_labels, mess_anteil, mess_vgl, mess_je), (erwartet_n, labels_med, anteil_med, vgl_med, vgl_je))
    print(f"Zeilen der Auswertung geprüft: {geprueft}, Abweichungen: {abw}")
    return abw


def main():
    ordner = Path(sys.argv[1])
    zellen = lies(ordner)
    if len(sys.argv) > 2:
        if pruefe(zellen, Path(sys.argv[2])):
            sys.exit("Abweichungen zur Auswertung, nichts geschrieben")
    out = {
        "beschreibung": ("Feste Messreihe V11 der Vormessung: n = 30 Kunden, Zeitfenster der Breite 40 und 100, Typen zufällig und gruppiert, ng-Gedächtnis k = 1 und 5, "
                         "12 Instanzen je Zelle (Zufalls-Seeds 0 bis 11), Verbrauch der Last = Nachfrage, Fahrerzeit und dritte Größe zufällig 5 bis 25 (unabhängig), "
                         "Grenze je zusätzlicher Größe 70, 140 oder 10^9 (nie bindend). Abbruchgrenze der Messung: 60 s je Pricing-Aufruf, 300 s gesamt."),
        "spalten": ["seed", "labels", "dominiert", "vergleiche", "aufrufe", "abgebrochen", "schranke"],
        "arten": {"colgen": "ganze Spaltenerzeugung (Summe aller Pricing-Aufrufe)", "fest1": "ein Pricing-Aufruf mit den Dualpreisen der ersten Runde",
                  "fest": "ein Pricing-Aufruf mit den Dualpreisen der Spaltenerzeugung bei nur der Zeit"},
        "zellen": [{"typ": t, "breite": b, "k": k, "art": a, "grenze": g, "r": r, "quelle": z["quelle"], "zeilen": z["zeilen"]}
                   for (t, b, k, a, g, r), z in sorted(zellen.items())],
    }
    ziel = Path(__file__).resolve().parent.parent / "data" / "baender_v11.json"
    ziel.parent.mkdir(exist_ok=True)
    ziel.write_text(json.dumps(out, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8", newline="\n")
    print(f"geschrieben: {ziel} ({len(out['zellen'])} Zellen, {sum(len(z['zeilen']) for z in out['zellen'])} Läufe)")


if __name__ == "__main__":
    main()
