# Mehrere Grenzen: Zeit, Last, Fahrerzeit – Streamlit-Demo

**[→ Demo live ausprobieren](https://sebastianhanisch-mehrere-grenzen-demo.streamlit.app/)**

Interaktive **Konzepte-Demo** der Reihe „Ressourcenwege und Spaltenerzeugung“ im Portfolio von [Sebastian Hanisch](https://sebastianhanisch.net) (Operations Research und Machine Learning).
Im **Pricing** der Spaltenerzeugung sucht das **Label-Setting** den günstigsten Weg, der alle **Grenzen** einhält: Zeitfenster, Ladekapazität, Lenk- oder Fahrerzeit. Jeder Teilweg wird als **Label** festgehalten
(Kosten und alles, was er schon verbraucht hat); eine **Dominanzregel** streicht Labels, die am selben Kunden in keiner Hinsicht besser sind als ein anderes. Diese Demo zeigt, **was jede zusätzliche Grenze kostet**:
wie sich die Zahl der erzeugten Labels, der Anteil der dominierten Labels und die Zahl der Dominanzvergleiche ändern, wenn neben der Zeit Last, Fahrerzeit und eine dritte Größe begrenzt sind.

Die Grundlagen stehen in den Nachbardemos der Reihe: [weg-mit-grenzen-demo](https://github.com/sebastian-hanisch/weg-mit-grenzen-demo) (ein Weg mit Grenzen), [dominanz-labels-demo](https://github.com/sebastian-hanisch/dominanz-labels-demo) (die Dominanzregel)
und [zeitfenster-labeling-demo](https://github.com/sebastian-hanisch/zeitfenster-labeling-demo) (Zeitfenster und Warten); hier sind sie vorausgesetzt, Zeit ist immer die erste Größe. Als Anwendung dient
[crew-pairing-demo](https://github.com/sebastian-hanisch/crew-pairing-demo): Dort führt das Labeling Zeit, Lenkzeit und ununterbrochene Lenkzeit als Größen mit; die Wirkung zusätzlicher Größen auf Labels und Vergleiche wird dort nicht gemessen.
[multicriteria-demo](https://github.com/sebastian-hanisch/multicriteria-demo) zeigt Dominanz in zwei Kosten (Pareto-Front); hier steht Dominanz mit Verbrauch gegen Grenzen in bis zu vier Größen.
**Abgrenzung:** [hub-labeling-demo](https://github.com/sebastian-hanisch/hub-labeling-demo) (Kürzeste-Wege-Reihe) meint mit „Label“ etwas anderes, nämlich eine Liste von Hubs für Abstandsabfragen; hier ist ein Label ein Teilweg samt Verbrauch.

## Kernfrage

Was ändert sich im Label-Setting, wenn neben der Zeit weitere Größen begrenzt sind? Gemessen werden **erzeugte Labels** und **Dominanzvergleiche** (jeder ausgewertete Test „Label O dominiert Label N“ einmal; gezählt wird die Zahl der Tests, nicht ihr Aufwand).
Sekunden stehen nur zur Information in der App. **r** ist die Zahl der Größen: r = 1 nur Zeit (mit Zeitfenstern), r = 2 plus Last, r = 3 plus Fahrerzeit, r = 4 plus eine dritte Größe.

## Befunde und Korrekturen gegenüber dem Plan

- **In der gemessenen Zelle wachsen die Labels etwa linear in r (vier Stützstellen), nur die Vergleiche überlinear.** Der Plan erwartete für beide eine stärkere Zunahme als linear. Gemessen (ein Pricing-Aufruf, n = 30, zufällig, Breite 100, ng-Gedächtnis 5, nie bindend, unabhängige Verbräuche, Median über 12 Instanzen)
  wachsen die Labels etwa linear in r (Zuwächse 10 504, 10 073, 9 443, leicht abnehmend), die Vergleiche überlinear.
- **Bei korrelierten Verbräuchen stimmte die Erwartung „kein Sinken“ nur teilweise.** Bei vollständiger Korrelation (Fahrerzeit gleich der Last) kommen keine Labels hinzu; bei „Last plus Rauschen“ sinkt der Anteil dominierter Labels schwächer,
  bei gegenläufigen Verbräuchen stärker als bei unabhängigen.
- **Das Handbeispiel läuft nichtelementar** (ng-Gedächtnis 1), weil bei elementarer Rechnung die Teilmengen-Bedingung der besuchten Kunden jeden aufsummierten Verbrauch schon einschließt und die zusätzlichen Größen die Dominanz nicht verändern würden (Eigenschaftstest `test_elementary_route_makes_never_binding_sizes_redundant`).
- **Eine bindende Grenze erzeugt weniger Labels als dieselbe Rechnung ohne wirksame Grenze, aber nicht durch bessere Dominanz.** Sie schneidet Wege ab und macht die Aufgabe teurer (Experiment 5). Gegenüber nur der Zeit können es mehr oder weniger Labels sein (Tabelle, Zeile L).
- **Instanzen mit dem Zufallsgenerator von Python statt SplitMix64.** Die festen Messreihen stammen aus Instanzen, die `random.Random` erzeugt; damit sie nachrechenbar bleiben, benutzt die Demo denselben Generator (siehe Annahmen).

## Modell

- **Instanz:** eigene, Solomon-artige Instanzen, nicht die Originalinstanzen: Quadrat 100 × 100, Depot in der Mitte, Zeit = Entfernung, Bedienzeit 10, Horizont 300, Nachfrage 5 bis 25, Zeitfenster der Breite 40 bis 100 (Regler);
  Typen „zufällig“ und „gruppiert“ (fünf Zentren; nur in den Messreihen). Dazu das **Handbeispiel**: Depot und sechs Kunden auf einem Gitter, Manhattan-Abstand, Bedienzeit 2, Horizont 36, ganzzahlige Dualpreise.
- **Größen:** Zeit (mit Zeitfenstern), Last (= Nachfrage), Fahrerzeit, dritte Größe; jede zusätzliche Größe summiert den Verbrauch der besuchten Kunden und hat eine Obergrenze (70, 140 oder nie bindend).
- **Verbrauchsmodelle:** unabhängig (Fahrerzeit und dritte Größe zufällig 5 bis 25), gleich der Last, Last plus Rauschen (Zufall von −4 bis 4, mindestens 1), gegenläufig (Fahrerzeit = 30 minus Last, dritte Größe unabhängig).
- **Label und Dominanz:** Ein Label am Kunden hat Zeit, reduzierte Kosten, Verbrauch je Größe und das ng-Gedächtnis; es dominiert ein anderes, wenn Kosten, Zeit und jeder Verbrauch höchstens so groß sind und sein Gedächtnis eine Teilmenge ist.
  Die Formeln stehen im Expander „📐 Mathematische Formulierung“ der App.
- **Wiederholungen:** ng-Gedächtnis k = 1 merkt sich nur den zuletzt besuchten Kunden selbst (nichtelementar: die Wiederkehr nach einem anderen Kunden ist erlaubt), k = 5 merkt sich bis zu fünf nahe Kunden (den Kunden selbst eingerechnet).

## Methodik

- **Experiment 1 (Handbeispiel):** r = 1, 2, 3, nie bindende und bindende Grenzen (Last 12, Fahrerzeit 9); Protokoll jedes erzeugten Labels, jede Dominanzentscheidung mit ihren Einzelvergleichen, die Dominanzentscheidungen von r = 1, die bei mehr Größen nicht mehr gelten.
  Gegenprobe: eine Aufzählung aller zulässigen Wege ohne Dominanz findet denselben besten Wert.
- **Experiment 2 (Korrelation):** am Handbeispiel live, an einer festen Messreihe mit vier Verbrauchsmodellen (eine Zelle).
- **Experiment 3 (Größenregler):** ein Pricing-Aufruf live auf einer zufälligen Instanz (bis 30 Kunden) mit den Dualpreisen der ersten Runde (Preis je Kunde = Hin- und Rückweg vom Depot) für r = 1 bis 4.
  Der beste Weg wird vor der Anzeige unabhängig geprüft. Bei sehr großen Einstellungen bricht die Rechnung an einer festen Obergrenze ab (gezählt in Labels und Vergleichen, keine Zeitgrenze).
- **Experiment 4 (Bänder):** die feste Messreihe V11: 30 Kunden, Breite 40 und 100, zufällig und gruppiert, k = 1 und 5, je Zelle 12 Instanzen (Zufalls-Seeds 0 bis 11), drei Messarten (ein Pricing-Aufruf mit den Dualpreisen der ersten Runde, ganze Spaltenerzeugung,
  ein Aufruf mit den Dualpreisen am Ende der Spaltenerzeugung bei nur der Zeit). Median, Mittel und Maximum der Labels, Median des Anteils dominierter Labels und der Vergleiche je Label (je Instanz gebildet, dann Median), Zahl fertiger und abgebrochener Läufe.
- **Experiment 5 (bindende Grenze):** Handbeispiel live und V11 (gruppiert, Breite 100, k = 5, ganze Spaltenerzeugung).
- **Kern:** `mgr_algorithm.py`, jede Regel eine Funktion (Erweiterung, Dominanz, Einfügen mit Zählung, Rückverfolgung), Komposition `price_r`; Kopie und Umbenennung des Messkerns der Messreihen, Gleichheit der Zählungen mit ihm an 576 Instanzen und Einstellungen geprüft (Scratch-Lauf, nicht im Repo).

## Befunde (gemessen, keine Behauptungen)

„Median über 12 Instanzen“ meint die festen Zufalls-Seeds 0 bis 11; Mediane aus zwei mittleren Werten sind wie in der Messung gerundet. „Vergleiche je Label“ ist je Instanz Vergleiche geteilt durch Labels, davon der Median.

| Frage | Befund | Test |
|---|---|---|
| **Handbeispiel** (sechs Kunden, Fahrerzeit unabhängig, nie bindende Grenzen, ng-Gedächtnis 1): Was ändert sich mit r = 1, 2, 3? | Erzeugte Labels 31 → 52 → 64; dominierte Labels 18 → 20 → 19, also Anteil 58,1 → 38,5 → 29,7 %; Vergleiche 51 → 303 → 622 (je Label 1,6 → 5,8 → 9,7); bester Wert immer −30 (Weg 3-4-5-2-6). | A |
| Handbeispiel: Wie viele der Dominanzentscheidungen von r = 1 gelten bei r = 3 nicht mehr? | 11 von 18 (Fahrerzeit unabhängig, nie bindende Grenzen). | C |
| Handbeispiel mit bindenden Grenzen (Last höchstens 12, Fahrerzeit höchstens 9)? | r = 2 und r = 3: je 33 Labels (statt 52 und 64), 11 und 9 dominiert, 99 und 112 Vergleiche; bester Wert −18 (Weg 3-2-5) statt −30; 51 (r = 2) und 63 (r = 3) Erweiterungen scheitern an einer Grenze. Die Aufzählung zählt 88 (nie bindend) bzw. 40 und 38 Teilwege (bindend, r = 2 und 3), mit demselben besten Wert. | B |
| Handbeispiel, Fahrerzeit gleich der Last, nie bindend? | r = 2 und r = 3: je 52 Labels, 20 dominiert, 303 Vergleiche; die dritte Größe ändert nichts. | D |
| Handbeispiel, Fahrerzeit = 8 minus Last (gegenläufig), nie bindend? | r = 1, 2, 3: 31, 52, 52 Labels; dominiert 18, 20, 16; Vergleiche 51, 303, 342: Die Zahl der Labels bleibt bei r = 3, die dominierten Labels und die Vergleiche ändern sich. | E |
| **Ein Pricing-Aufruf, n = 30, zufällig, Breite 100, ng-Gedächtnis 5, nie bindend, unabhängige Verbräuche, Median über 12 Instanzen:** Wie wachsen Labels und Vergleiche mit r = 1 bis 4? | Labels 7 672 → 18 176 → 28 249 → 37 692 (Zuwächse 10 504, 10 073, 9 443: etwa linear in r bei vier Stützstellen, leicht abnehmend); Vergleiche 75 968 → 1 089 956 → 3 151 492 → 8 131 986 (Faktoren 14,35, 2,89, 2,58: überlinear); Anteil dominiert 88,8 → 84,4 → 81,5 → 76,8 %; Vergleiche je Label 10,2 → 49,5 → 114,6 → 232,0. | F |
| Dieselbe Zelle, Fahrerzeit und dritte Größe gleich der Last? | Labels 7 672 → 18 176 → 18 176 → 18 176, Vergleiche 1 089 956 bei r = 2 bis 4, Anteil dominiert bei r = 2 bis 4 jeweils 84,4 %; in 12 von 12 Instanzen sind die Labels bei r = 3 und r = 4 genau die von r = 2. | G |
| Dieselbe Zelle, Last plus Rauschen? | Labels 18 176 → 21 598 → 23 988 (r = 2, 3, 4; Zuwachs 19 % und 11 % statt 55 % und 33 % bei unabhängigen Verbräuchen), Vergleiche 1 610 327 und 2 279 018 (r = 3, 4), Anteil dominiert 84,4 → 83,3 → 82,0 %. | H |
| Dieselbe Zelle, gegenläufige Verbräuche? | Labels 18 176 → 45 087 → 58 421 (r = 2, 3, 4), Vergleiche 9 386 282 und 20 927 735 (r = 3, 4), Anteil dominiert 84,4 → 78,7 → 74,5 %: mehr Labels als bei unabhängigen Verbräuchen (eine Zelle; die Modelle ziehen die dritte Größe aus verschiedenen Zufallsströmen, der Vergleich schließt also auch Ziehungsunterschiede ein). | I |
| **Ganze Spaltenerzeugung, n = 30, zufällig, Breite 100, ng-Gedächtnis 1, Grenze 70 je zusätzlicher Größe, Median über 12 Instanzen:** Wie ändern sich Anteil und Vergleiche je Label mit r = 1 bis 4? | Anteil dominiert 91,0 → 87,6 → 83,7 → 81,0 %; Vergleiche je Label 2,8 → 7,4 → 13,6 → 17,9. | J |
| Dieselbe Zelle, nie bindende Grenze? | Labels 56 652 → 124 109 → 165 980 → 213 880; Anteil dominiert 91,0 → 87,5 → 84,9 → 82,7 %; Vergleiche je Label 2,8 → 13,5 → 38,2 → 101,3. | K |
| **Ganze Spaltenerzeugung, n = 30, gruppiert, Breite 100, ng-Gedächtnis 5, Grenze 70, 12 Instanzen:** Braucht die bindende Grenze mehr Labels? | In dieser Zelle weniger als bei nur der Zeit: Labels 433 558 (nur Zeit) → 212 227, 200 214, 175 545 (r = 2, 3, 4); Pricing-Aufrufe 59 → 20, 20, 18; die untere Schranke steigt von 357,2 auf 502,0, 550,4 und 558,2: die Aufgabe ist eine andere. In 3 der 8 Zellen der ganzen Spaltenerzeugung (zufällig, Breite 40 und 100, und gruppiert, Breite 40, jeweils ng-Gedächtnis 1) sind es bei r = 4 mit Grenze 70 mehr Labels als bei nur der Zeit (zufällig, Breite 40: 20 104 gegen 15 824; zufällig, Breite 100: 62 030 gegen 56 652; gruppiert, Breite 40: 44 684 gegen 42 266). Gegenüber der nie bindenden Grenze bei gleichem r sind es in allen 8 Zellen weniger. | L |
| Sinkt der Anteil dominierter Labels von Stufe zu Stufe in jeder Instanz? | In 50 von 72 Zeilen der V11-Messreihe (2 Typen × 2 Breiten × 2 Gedächtnisse × 3 Messarten × 3 Grenzen) ja in jeder fertigen Instanz (in 9 dieser 50 Zeilen sind es weniger als 12 Instanzen, bis herab zu 4, nur die bei allen vier Stufen fertigen, also die schnelleren); in den übrigen 22 Zeilen steigt er je Stufe in höchstens 2 Instanzen. | M |
| Wie viele Läufe der ganzen Spaltenerzeugung brachen in V11 ab? | Gruppiert, Breite 100: 41 Läufe; gruppiert, Breite 40: 5 Läufe; zufällig: keiner; nur bei gruppierten Instanzen, lockerer oder nie bindender Grenze und mit r ≥ 2; von den 46 abgebrochenen Läufen liegen 44 bei r = 3 oder 4 und 2 bei r = 2 (Breite 100, nie bindend). Gruppiert, Breite 100, ng-Gedächtnis 5, r = 4: 6 von 12 Läufen bei lockerer und 7 von 12 bei nie bindender Grenze. Auch in der Reihe „ein Pricing-Aufruf mit den Dualpreisen der ersten Runde“ brachen 46 Läufe ab (alle gruppiert, lockere oder nie bindende Grenze, r ≥ 2); die Zellen stützen sich dort auf die schnelleren Instanzen. | N |

**Zahl → Test.** Alle Zahlen der Tabelle stehen in `tests/test_claims.py` (exakt für die Zählungen des Handbeispiels, aus den Rohzeilen in `data/` für die Mediane):
A `test_hand_example_never_binding_table`, B `test_hand_example_binding_limits_table`, C `test_hand_example_eleven_of_eighteen_decisions_fail_at_r_3`, D `test_hand_example_fahrerzeit_equal_to_load`,
E `test_hand_example_opposite_consumption_changes_dominance_but_not_the_label_count`, F `test_p04_independent_model_medians_and_growth`, G `test_p04_equal_to_load_adds_no_labels_in_any_instance`, H `test_p04_load_plus_noise`, I `test_p04_opposite_model`,
J `test_v11_full_column_generation_random_width_100_k1_binding_limit`, K `test_v11_full_column_generation_random_width_100_k1_never_binding`, L `test_v11_binding_limit_needs_fewer_labels_and_calls_in_the_full_column_generation`,
M `test_v11_share_of_dominated_labels_falls_in_every_instance_in_50_of_72_rows`, N `test_v11_aborted_runs`.
Die Bänder selbst stammen aus den vor dem Bau gerechneten Messreihen („Vormessung“; Rohdateien `out_v11_*.txt`, `run_p04.log`); `tools/baender_v11.py` prüft beim Erzeugen jede der 240 Tabellenzeilen der Auswertung (Labels, Anteil, Vergleiche, fertige und abgebrochene Läufe), die Einzelwerte der Verbrauchsmodell-Reihe sind mit
`tools/messreihe_p04.py` neu gerechnet und stimmen in Median, Anteil und Vergleichen mit dem Log überein. `tests/test_baender.py` rechnet Stichproben beider Reihen mit dem Kern dieser Demo exakt nach. Nicht im Test, nur Messung dieser README (Scratch-Lauf, nicht im Repo): die 19 200 Vergleichsfälle des Orakels (siehe Tests) und die 576 Vergleichsfälle des Kerns mit dem Messkern der Vormessung (Zählungen gleich).

## Ehrliche Grenzen

Dieselben Annahmen, Grenzen und bekannten Probleme wie im Expander „⚠️ Annahmen, Grenzen und bekannte Probleme“ der App (ein Test vergleicht beide Fassungen):

**Annahmen**

- Die Instanzen sind eigene, Solomon-artige Instanzen (Quadrat 100 × 100, Zeit = Entfernung, Bedienzeit 10, Horizont 300), nicht die Originalinstanzen von Solomon.
- Jede zusätzliche Größe summiert den Verbrauch der besuchten Kunden und hat eine feste Obergrenze (70, 140 oder nie bindend).
- Die Messreihen benutzen 30 Kunden und unabhängige Zufallsverbräuche für Fahrerzeit und dritte Größe (ganze Zahlen von 5 bis 25); vier Verbrauchsmodelle gibt es nur in einer Zelle (Breite 100, ng-Gedächtnis 5, nie bindende Grenzen).
- Ein Pricing-Aufruf benutzt die Dualpreise der ersten Spaltenerzeugungsrunde (Preis je Kunde = Hin- und Rückweg vom Depot); die ganze Spaltenerzeugung der festen Messreihen hat einen Überdeckungs-Master.
- Gezählt werden erzeugte Labels und Dominanztests; Sekunden stehen nur zur Information da.

**Grenzen**

- Nicht gemessen: mehr als vier Größen, Instanzen mit mehr als 30 Kunden in dieser Messreihe, bidirektionales Labeling und Eimer-Verfahren mit mehreren Größen, Zeit statt Labels.
- Je Zelle 12 Instanzen, kein Konfidenzmaß; Mediane, Mittel und Maxima über höchstens 12 Werte.
- Bei gruppierten Instanzen brachen Läufe der ganzen Spaltenerzeugung ab (41 Läufe bei Breite 100, 5 bei Breite 40; Grenze der Messung 60 s je Pricing-Aufruf und 300 s gesamt), nur bei lockerer oder nie bindender Grenze und bei r = 3 oder 4, außer 2 Läufen bei r = 2. Diese Zellen stützen sich auf weniger Instanzen, und zwar auf die schnelleren. Auch in der Reihe „ein Pricing-Aufruf“ brachen 46 Läufe ab (ebenfalls nur gruppiert, bei lockerer oder nie bindender Grenze und r ≥ 2); diese Zellen stützen sich ebenso auf die schnelleren Instanzen.
- Das Handbeispiel hat sechs Kunden; seine Zahlen sind ein Beispiel zum Nachrechnen, keine Verteilung.

**Bekannte Probleme und Unsicherheiten**

- Die Live-Rechnung bricht bei sehr großen Einstellungen an einer festen Obergrenze ab (100 000 erzeugte Labels oder 30 000 000 Dominanztests); dann gibt es für diese Einstellung kein Verdikt. Die Obergrenze zählt, sie misst keine Sekunden.
- Die Zeitgrenzen der abgebrochenen Läufe der Messreihe hängen von der Auslastung des Rechners ab, die Zahlen der Labels nicht.
- Die Instanzen entstehen mit dem Zufallsgenerator von Python (`random.Random`), damit sie mit den festen Messreihen übereinstimmen; Stichproben der Messreihen werden in den Tests nachgerechnet.
- Erklärungen mit „weil“ sind Deutungen, soweit nicht ausdrücklich gemessen (zum Beispiel, dass bindende Grenzen die Label-Zahl über abgeschnittene Wege senken).
- Die Diagramme haben keine Auswahlfunktion; ein Mausklick auf sie bewirkt nichts.

## Tests

Die Suite hat 167 Tests (`pytest --collect-only -q tests`), alles unter `tests/`:

- **Kern** (`test_algorithm.py`): Erweiterungsregel, Dominanzregel, Zählung und Handbeispiel in allen Fällen gegen Handrechnung (Rechnung in `tests/conftest.py`), Gegenprobe durch Aufzählung, Protokoll, Prüfer der Route, Obergrenze, Hängetest am Regler-Maximum.
- **Orakel** (`test_oracle_mehrere_grenzen.py`): unabhängige Aufzählung aller zulässigen Wege mit der ng-Regel nach ihrer Definition; bester Wert für r = 1 bis 4, ng-Gedächtnis 1, 3 und elementar, bindende und nie bindende Grenzen an 240 Fällen (80 Instanzen mit ganzen Zahlen);
  bei ng-Gedächtnis 1 die überlebenden Labels je Kunde gegen die Pareto-Front aller Weg-Labels. Im Scratch-Lauf (nicht im Repo) 19 200 Fälle ohne Abweichung.
- **Eigenschaften** (`test_eigenschaften_mehrere_grenzen.py`): eine nie bindende Größe ändert den besten Wert nicht; engere Grenzen machen den Wert nie besser; eine doppelte Größe und das Vertauschen der Größen ändern die Zählung nicht;
  bei elementarer Rechnung sind nie bindende Größen überflüssig; jede Grenze wirkt auf mindestens einer Instanz; jede ausgegebene Route hält alle Regeln ein; gleiche Zahlen in zwei Prozessen mit verschiedener Hash-Randomisierung.
- **Randfälle** (`test_edge_cases.py`): n = 1, n = 2, Verbrauch 0, Grenze genau gleich dem Verbrauch, Grenze unter jedem Einzelverbrauch, r = 1 ohne Wirkung der Verbräuche, Gleichstand, Abbruch an der Obergrenze.
- **Messreihen und Aussagen** (`test_baender.py`, `test_claims.py`, `test_verdicts.py`, `test_readme.py`): Aufbau und Stichproben der Bänder, jede Zahl der README, jedes Verdikt mit Schwellen und Zahlen im Text, README gegen App-Text und Testzahl.
- **Oberfläche** (`test_app.py`, `test_layout.py`, `test_presets.py`, `test_footer.py`, `test_runtime_imports.py`): AppTest für Standard, jedes Preset (mit der erwarteten Verdikt-Zeile), Permalink, jeden Regler an Minimum und Maximum und jede Auswahl; Schnellstart in der Seitenleiste mit hervorgehobenem Preset;
  Footer; jeder Import steht in `requirements.txt`.

## Dateistruktur

| Datei | Zweck |
|---|---|
| `.github/workflows/tests.yml` | CI: Push, Pull Request, wöchentlicher Canary |
| `.gitignore` | venv, Caches, Streamlit-Secrets |
| `.streamlit/config.toml` | Streamlit-Einstellungen (keine Nutzungsstatistik) |
| `app.py` | Streamlit-App: Einleitung, fünf Experimente, Annahmen, Mathematik |
| `data/baender_v11.json` | Feste Messreihe V11 (240 Zellen, je Lauf Labels, dominierte Labels, Vergleiche, Aufrufe, Schranke; Quelldatei je Zelle) |
| `data/baender_p04.json` | Feste Messreihe der Verbrauchsmodelle (16 Zellen, je Lauf Labels, dominierte Labels, Vergleiche) |
| `mgr_algorithm.py` | Kern: Gedächtnis, Erweiterung, Dominanz, Einfügen mit Zählung, Pricing `price_r`, Prüfer, Aufzählung |
| `mgr_baender.py` | Auswertung der festen Messreihen (Median, Mittel, Maximum, Zählungen je Instanz) |
| `mgr_constants.py` | Regler-Grenzen, feste Annahmen, Farben, Presets |
| `mgr_evaluation.py` | Läufe (Handbeispiel, Live), Protokoll, Verdikte als reine Funktionen, Zahlenformat |
| `mgr_layout.py` | Fester Kopf (Stylesheet) |
| `mgr_presets.py` | Permalink (Begrenzen), Presets (Schnellstart in der Seitenleiste, aktives Preset hervorgehoben), Zufalls-Seed-Button |
| `mgr_scenario.py` | Instanzen (Solomon-artig), Verbrauchsmodelle, Handbeispiel |
| `mgr_texte.py` | Annahmen-Text (App und README) und Formel-Expander |
| `mgr_visualization.py` | Plotly-Abbildungen (Achsen gesperrt) |
| `requirements-dev.txt` | Laufzeit plus pytest |
| `requirements.txt` | Laufzeit-Bibliotheken (ungepinnt) |
| `tools/baender_v11.py` | erzeugt `data/baender_v11.json` aus den Rohdateien der Messreihe und prüft sie gegen die Auswertung |
| `tools/messreihe_p04.py` | rechnet die Verbrauchsmodell-Reihe mit dem Kern neu und prüft sie gegen das Log |
| `tests/` | Kern, Orakel, Eigenschaften, Randfälle, Messreihen, Zahlen der README, Verdikte, Oberfläche, Footer, Laufzeit-Importe |

## Bewusst nicht umgesetzt

- **Dualpreise aus einem Master:** die App benutzt die Dualpreise der ersten Runde; die ganze Spaltenerzeugung steht nur als feste Messreihe da (kein LP-Löser in der Demo).
- **Elementarität im Detail, Eimer-Verfahren, bidirektionales Labeling, Kantenstreichung:** nicht gemessen (siehe Grenzen). Elementar rechnet die Demo nur als Argument im Text und im Eigenschaftstest.
- **Subset-Row-Schnitte** als zusätzliche Größen: nicht umgesetzt.
- **Zeit statt Labels als Messgröße:** Sekunden stehen nur zur Information.
- **Mehr als vier Größen und mehr als 30 Kunden in den Messreihen.**

## Lokal ausführen

```bash
python3 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate

pip install -r requirements.txt
streamlit run app.py
```

## Tests ausführen

```bash
pip install -r requirements-dev.txt
pytest tests/ -v
```

Gebaut mit Streamlit und Plotly.

---

Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net) – Operations Research und Machine Learning ([Über mich](https://sebastianhanisch.net/ueber-mich.html)). Mehr zur Reihe: [Ressourcenwege: von der Grenze zur Verfahrenswahl](https://sebastianhanisch.net/konzepte-ressourcenwege.html).
