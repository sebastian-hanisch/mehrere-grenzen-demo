"""Konstanten: Regler-Grenzen, feste Annahmen, Farben und Presets.

Rechenaufwand am Regler-Maximum (DEMO-PLAYBOOK 1c): Ein Pricing-Aufruf erzeugt bei n = 30 Kunden, Breite 100, ng-Gedächtnis k = 5 und
vier Größen (Zeit plus drei) je nach Verbrauchsmodell einige zehntausend Labels; jedes neue Label wird mit allen lebenden Labels
am selben Kunden verglichen (Zahl der Vergleiche je Label bis in die Hunderte). Deshalb ist die Live-Rechnung auf LIVE_MAX_LABELS
Labels begrenzt (feste Zahl statt Zeitgrenze, damit der Abbruch reproduzierbar ist); größere Fälle stehen als feste Messreihen in data/.
"""

# ---------------------------------------------------------------------------------------------------------------------------------
# Instanz (Solomon-artig, nicht die Originalinstanzen): Quadrat 100 x 100, Zeit = Entfernung, Depot in der Mitte
# ---------------------------------------------------------------------------------------------------------------------------------
HORIZONT = 300.0          # spätester Rückkehrzeitpunkt zum Depot
BEDIENZEIT = 10.0         # je Kunde
LAST_MIN, LAST_MAX = 5, 25   # Nachfrage (Last) je Kunde, ganze Zahlen
EXTRA_MIN, EXTRA_MAX = 5, 25  # Verbrauch der Größen "Fahrerzeit" und "dritte Größe" im Modell "unabhängig"
GRENZE_STANDARD = 70      # "bindend": Obergrenze je zusätzlicher Größe (wie die Kapazität im Pricing der Reihe)
GRENZE_LOCKER = 140
GRENZE_NIE = 10 ** 9      # "nie bindend": reiner Dimensionseffekt
GRENZEN = {"bindend (70)": GRENZE_STANDARD, "locker (140)": GRENZE_LOCKER, "nie bindend": GRENZE_NIE}
GRENZEN_NAMEN = tuple(GRENZEN)
GROESSEN = ("Zeit", "Last", "Fahrerzeit", "dritte Größe")   # Index = Stelle in der Liste der Größen; r = Zahl der benutzten Größen
R_MIN, R_MAX = 1, 4
EPS = 1e-9

# Verbrauchsmodelle der zusätzlichen Größen (Last ist immer die Nachfrage)
MODELLE = ("unabhängig", "gleich der Last", "Last plus Rauschen", "gegenläufig")
MODELL_ERKLAERUNG = {
    "unabhängig": "Fahrerzeit und dritte Größe sind je Kunde zufällig (ganze Zahlen von 5 bis 25), unabhängig von der Last.",
    "gleich der Last": "Fahrerzeit und dritte Größe sind je Kunde gleich der Last (vollständig korreliert).",
    "Last plus Rauschen": "Fahrerzeit und dritte Größe sind Last plus ein Zufallswert von −4 bis 4, mindestens 1 (teilweise korreliert).",
    "gegenläufig": "Fahrerzeit ist 30 minus Last (je mehr Last, desto weniger Fahrerzeit); die dritte Größe ist unabhängig zufällig (5 bis 25).",
}
RAUSCH_SPANNE = 4
GEGENLAEUFIG_SUMME = 30   # = kleinste Last + größte Last (5 + 25)

# ---------------------------------------------------------------------------------------------------------------------------------
# Regler der Live-Rechnung (Experiment 3)
# ---------------------------------------------------------------------------------------------------------------------------------
LIVE_N_MIN, LIVE_N_MAX, LIVE_DEFAULT_N = 10, 30, 30
LIVE_BREITE_MIN, LIVE_BREITE_MAX, LIVE_DEFAULT_BREITE = 40, 100, 40   # Breite der Zeitfenster
LIVE_K_OPTIONEN = (1, 5)                                              # ng-Gedächtnis: 1 = nur sofortige Wiederholung verboten
LIVE_DEFAULT_K = 1
LIVE_DEFAULT_R = 4
LIVE_DEFAULT_GRENZE = "nie bindend"
LIVE_DEFAULT_MODELL = "unabhängig"
SEED_MAX, LIVE_DEFAULT_SEED = 999999, 0
LIVE_MAX_LABELS = 100_000       # Abbruch der Live-Rechnung: erzeugte Labels ...
LIVE_MAX_VERGLEICHE = 30_000_000  # ... oder Dominanztests; Zählungen, nie eine Zeitgrenze

# Handbeispiel (Experimente 1, 2 und 5)
HAND_GRENZEN = ("nie bindend", "bindend (Last 12, Fahrerzeit 9)")
HAND_MODELLE = ("unabhängig", "gleich der Last", "gegenläufig")
HAND_R_MIN, HAND_R_MAX = 1, 3

# ---------------------------------------------------------------------------------------------------------------------------------
# Feste Messreihen (data/): 12 Instanzen je Zelle, Zufalls-Seeds 0 bis 11
# ---------------------------------------------------------------------------------------------------------------------------------
BAENDER_SEEDS = tuple(range(12))
BAENDER_N = 30
BAND_FILE_V11 = "baender_v11.json"
BAND_FILE_P04 = "baender_p04.json"

# ---------------------------------------------------------------------------------------------------------------------------------
# Farben (hell und dunkel lesbar)
# ---------------------------------------------------------------------------------------------------------------------------------
COLOR_KEPT = "#2F6B65"
COLOR_DOMINATED = "rgba(150,150,150,0.65)"
COLOR_LINE = "#4c78a8"
COLOR_LINE2 = "#e45756"
COLOR_LINE3 = "#f58518"
COLOR_LINE4 = "#72b7b2"
COLORS_BY_R = {1: "#4c78a8", 2: "#f58518", 3: "#e45756", 4: "#72b7b2"}

# ---------------------------------------------------------------------------------------------------------------------------------
# Presets (Schnellstart): jedes setzt ALLE Regler
# ---------------------------------------------------------------------------------------------------------------------------------
_BASIS = {
    "h_r": 3, "h_grenzen": "nie bindend", "h_modell": "unabhängig",
    "l_n": LIVE_DEFAULT_N, "l_breite": LIVE_DEFAULT_BREITE, "l_k": LIVE_DEFAULT_K, "l_r": LIVE_DEFAULT_R,
    "l_grenze": LIVE_DEFAULT_GRENZE, "l_modell": LIVE_DEFAULT_MODELL, "l_seed": LIVE_DEFAULT_SEED,
}
PRESETS = {
    "Grundfall: jede Grenze zählt mit": dict(_BASIS),
    "Bindende Grenzen": {**_BASIS, "h_grenzen": "bindend (Last 12, Fahrerzeit 9)", "l_grenze": "bindend (70)"},
    "Fahrerzeit gleich der Last": {**_BASIS, "h_modell": "gleich der Last", "l_modell": "gleich der Last"},
    "Gegenläufige Verbräuche": {**_BASIS, "h_modell": "gegenläufig", "l_modell": "gegenläufig", "l_r": 3},
    "Größtes Live-Beispiel": {**_BASIS, "l_breite": LIVE_BREITE_MAX, "l_k": 5},
}
PRESET_HELP = {
    "Grundfall: jede Grenze zählt mit": "Handbeispiel mit drei Größen (Zeit, Last, Fahrerzeit) und nie bindenden Grenzen; Live-Rechnung mit 30 Kunden, Fensterbreite 40, ng-Gedächtnis 1, unabhängigen Verbräuchen und vier Größen.",
    "Bindende Grenzen": "Handbeispiel mit Last höchstens 12 und Fahrerzeit höchstens 9, Live-Rechnung mit Grenze 70 je zusätzlicher Größe: die Grenzen schneiden Wege ab, es entstehen weniger Labels als bei nie bindenden Grenzen, aber das Problem ist ein anderes.",
    "Fahrerzeit gleich der Last": "Fahrerzeit und dritte Größe haben denselben Verbrauch wie die Last: die zusätzlichen Größen unterscheiden nichts Neues, die Labels wachsen nicht mehr.",
    "Gegenläufige Verbräuche": "Fahrerzeit ist (größte plus kleinste Last) minus Last: Wege mit viel Last verbrauchen wenig Fahrerzeit, mehr Labels bleiben unvergleichbar. Live mit drei Größen.",
    "Größtes Live-Beispiel": "Live-Rechnung mit Fensterbreite 100 und ng-Gedächtnis 5: die größte Einstellung der Live-Rechnung, rechnet einige Sekunden.",
}
