"""Mehrere Grenzen: Zeit, Last, Fahrerzeit - interaktive Konzept-Demo
Sebastian Hanisch - Operations Research und Machine Learning

Was kostet jede zusätzliche Grenze im Label-Setting des Pricings? Handbeispiel Schritt für Schritt, Verbrauchsmodelle, Live-Rechnung und feste Messreihen.

Lauffähig mit: streamlit run app.py
"""

import streamlit as st

import mgr_baender as B
import mgr_constants as C
import mgr_evaluation as E
import mgr_scenario as S
import mgr_texte as T
import mgr_visualization as V
from mgr_layout import dunkles_design, kopf_css
from mgr_presets import (
    bounds,
    choices,
    init_session_state_defaults,
    load_permalink_settings,
    randomize_seed,
    sidebar_presets,
    sync_query_params,
)

st.set_page_config(page_title="Mehrere Grenzen – Sebastian Hanisch", layout="wide")


# --- Zwischenspeicher: alle Eingaben stehen im Schlüssel ----------------------------------------------------------------------------------

@st.cache_data(show_spinner=False)
def _hand_zeilen(grenzen, modell):
    return E.hand_zeilen(grenzen, modell)


@st.cache_data(show_spinner=False)
def _hand_modelle(grenzen):
    return E.hand_modell_zeilen(grenzen)


@st.cache_data(show_spinner=False)
def _hand_protokoll(r, grenzen, modell):
    res, prot = E.hand_lauf(r, grenzen, modell, mit_protokoll=True)
    return E.label_tabelle(prot), E.entscheidungen(prot)


@st.cache_data(show_spinner=False)
def _gebrochene_paare(grenzen, modell, r):
    return E.gebrochene_paare(grenzen, modell, r)


@st.cache_data(show_spinner=False, max_entries=60)
def _live(n, breite, k, r, grenze_name, modell, seed):
    return E.live_lauf(n, breite, k, r, C.GRENZEN[grenze_name], modell, seed)


# --- kleine Hilfen für Tabellen -----------------------------------------------------------------------------------------------------------

PROZENT = st.column_config.NumberColumn(format="%.1f %%")
GANZ = st.column_config.NumberColumn(format="%d")
EIN = st.column_config.NumberColumn(format="%.1f")


def _prozent(x):
    return None if x is None else 100 * x


def _zeilen_tabelle(zeilen):
    """Tabelle der Kennzahlen je r (Handbeispiel und Live-Rechnung)."""
    out = []
    for z in zeilen:
        ab = z["abgebrochen"]
        out.append({
            "r": z["r"], "Größen": ", ".join(C.GROESSEN[: z["r"]]),
            "erzeugte Labels": z["erzeugt"], "dominiert": None if ab else z["dominiert"], "Anteil dominiert": None if ab else _prozent(z["anteil"]),
            "Vergleiche": None if ab else z["vergleiche"], "Vergleiche je Label": None if ab else z["je_label"],
            "bester Wert": None if ab else z["bester_wert"], "bester Weg": "abgebrochen" if ab else E.weg_text(z["weg"]),
        })
    return out


TABELLE_SPALTEN = {"erzeugte Labels": GANZ, "dominiert": GANZ, "Anteil dominiert": PROZENT, "Vergleiche": GANZ, "Vergleiche je Label": EIN, "bester Wert": EIN}


# --- Kopf und Einleitung ------------------------------------------------------------------------------------------------------------------

st.html(kopf_css(dunkles_design()))
with st.container(key="kopf"):
    st.title("🧩 Mehrere Grenzen: Zeit, Last, Fahrerzeit")
st.markdown(
    """
Im **Pricing** der Spaltenerzeugung (zum Beispiel bei der Tourenplanung) sucht das **Label-Setting** den günstigsten Weg, der alle **Grenzen** einhält: Zeitfenster, Ladekapazität, Lenk- oder Fahrerzeit.
Jeder Teilweg wird als **Label** festgehalten (Kosten und alles, was er schon verbraucht hat); eine **Dominanzregel** streicht Labels, die am selben Kunden in keiner Hinsicht besser sind als ein anderes.
Diese Demo fragt: **Was ändert sich, wenn neben der Zeit weitere Größen begrenzt sind?** Gemessen werden die **erzeugten Labels** und die **Dominanzvergleiche**; Sekunden stehen nur zur Information da.

Weiter unten: fünf Abschnitte **🔬 Experiment**, dann **🚧 Wo die Annahmen enden** und die Expander **⚠️ Annahmen, Grenzen und bekannte Probleme** und **📐 Mathematische Formulierung**.
"""
)

with st.expander("So funktioniert Mehrere Grenzen", expanded=True):
    st.markdown(
        """
1. **Aufgabe:** Ein Fahrzeug startet am Depot, besucht Kunden und kehrt zurück. Jeder Kunde hat ein **Zeitfenster**; jeder Besuch **verbraucht** etwas (Last, Fahrerzeit, eine dritte Größe), und jede dieser Größen hat eine **Obergrenze**.
   Gesucht ist der Weg mit den kleinsten **reduzierten Kosten**: Weglänge minus die **Dualpreise** (Preise, die der Master je Kunde vorgibt) der besuchten Kunden.
2. **Label:** Ein Teilweg bis zu einem Kunden, gemerkt als Zeit, Kosten und Verbrauch je Größe. Das Label-Setting verlängert Labels nach wachsender Zeit um je einen Kunden. **r** ist die Zahl der Größen:
   r = 1 nur Zeit (mit Zeitfenstern), r = 2 plus Last, r = 3 plus Fahrerzeit, r = 4 plus eine dritte Größe.
3. **Dominanz:** Ein Label O dominiert ein Label N am selben Kunden, wenn Kosten, Zeit und **jeder** Verbrauch von O höchstens so groß sind wie bei N. Dann kann N nie zu einem besseren Weg führen als O und wird gestrichen.
4. **Was jede Größe kostet:** Jede zusätzliche Größe ist ein weiterer Vergleich in der Dominanzregel. Für dieselben zwei Labels gilt Dominanz damit seltener oder gleich oft. Wie stark das die Zahl der Labels und der Vergleiche verändert, zeigen die Experimente.
5. **Wiederholungen:** Die Wege dürfen Kunden wiederholen (**nichtelementar**); das **ng-Gedächtnis** verbietet nur Wiederholungen, die es noch kennt: Bei k = 1 merkt sich das Label nur den zuletzt besuchten Kunden selbst (die Wiederkehr nach einem anderen Kunden ist erlaubt), bei k = 5 bis zu fünf nahe Kunden (den Kunden selbst eingerechnet).
   Bei **elementarer** Rechnung (jeder Kunde höchstens einmal) stünde die besuchte Menge im Label; ist sie in der des anderen Labels enthalten, ist jeder aufsummierte Verbrauch (nicht negative Verbräuche vorausgesetzt) schon höchstens so groß. Bei nie bindenden Grenzen würden die zusätzlichen Größen die Dominanz dort nicht verändern, deshalb rechnet die Demo nichtelementar.
        """
    )

st.caption("🔗 Die Adresszeile oben spiegelt Ihre aktuelle Konfiguration wider – einfach kopieren, um ein Szenario zu teilen.")

load_permalink_settings()
init_session_state_defaults()

# --- Seitenleiste ------------------------------------------------------------------------------------------------------------------------

with st.sidebar:
    sidebar_presets()  # Schnellstart oben, das aktive Preset ist hervorgehoben
    st.header("🧮 Handbeispiel")
    st.caption("Für die Experimente 1, 2 und 5 (sechs Kunden, zum Nachrechnen mit dem Stift).")
    h_r = st.radio("Zahl der Größen r", choices("h_r"), key="h_r", horizontal=True, format_func=lambda x: f"r = {x}",
                   help="r = 1: nur Zeit mit Zeitfenstern; r = 2: plus Last; r = 3: plus Fahrerzeit.")
    h_grenzen = st.radio("Grenzen für Last und Fahrerzeit", choices("h_grenzen"), key="h_grenzen",
                         help="„nie bindend“: die Grenzen sind so groß, dass sie nie greifen (reiner Effekt der zusätzlichen Vergleiche). „bindend“: Last höchstens 12, Fahrerzeit höchstens 9, das schneidet Wege ab.")
    h_modell = st.radio("Verbrauch der Fahrerzeit", choices("h_modell"), key="h_modell",
                        help="„unabhängig“: die Zahlen der Tabelle. „gleich der Last“: Fahrerzeit = Last je Kunde. „gegenläufig“: Fahrerzeit = 8 minus Last (kleinste plus größte Last minus Last).")
    st.header("🔧 Live-Rechnung")
    st.caption("Für Experiment 3: ein Pricing-Aufruf auf einer zufälligen Instanz (Dualpreise der ersten Runde).")
    l_n = st.slider("Kunden n", *bounds("l_n"), key="l_n", help="Zahl der Kunden der zufälligen Instanz (Quadrat 100 × 100, Depot in der Mitte).")
    l_breite = st.slider("Breite der Zeitfenster", *bounds("l_breite"), step=10, key="l_breite",
                         help="Je breiter die Fenster, desto mehr Wege sind zulässig; in den gemessenen Reihen entstehen dabei mehr Labels.")
    l_k = st.radio("ng-Gedächtnis k", choices("l_k"), key="l_k", horizontal=True,
                   help="k = 1: das Label merkt sich nur den zuletzt besuchten Kunden selbst; die Wiederkehr nach einem anderen Kunden ist erlaubt. k = 5: das Label merkt sich bis zu fünf nahe Kunden (den Kunden selbst eingerechnet).")
    l_r = st.radio("Zahl der Größen r (bis zu)", choices("l_r"), key="l_r", horizontal=True, format_func=lambda x: f"r = {x}",
                   help="Gerechnet wird für r = 1 bis zu dieser Zahl. r = 4: Zeit, Last, Fahrerzeit und eine dritte Größe.")
    l_grenze = st.radio("Grenze je zusätzlicher Größe", choices("l_grenze"), key="l_grenze",
                        help="„bindend (70)“: höchstens 70 je zusätzlicher Größe. „locker (140)“: höchstens 140. „nie bindend“: keine wirksame Grenze.")
    l_modell = st.radio("Verbrauchsmodell", choices("l_modell"), key="l_modell", help="Wie Fahrerzeit und dritte Größe mit der Last zusammenhängen (Erklärung in Experiment 2).")
    l_seed = st.number_input("Zufalls-Seed der Instanz", *bounds("l_seed"), key="l_seed", step=1)
    st.button("🎲 Neue Instanz generieren", width="stretch", on_click=randomize_seed)

sync_query_params({k_: st.session_state[k_] for k_ in ("h_r", "h_grenzen", "h_modell", "l_n", "l_breite", "l_k", "l_r", "l_grenze", "l_modell", "l_seed")})

# ======================================================================================================================================
# Experiment 1: Handbeispiel
# ======================================================================================================================================

st.subheader("🔬 Experiment 1: Eine Grenze mehr – Schritt für Schritt am Handbeispiel")
st.markdown(
    """
Ein Depot und sechs Kunden auf einem Gitter, Entfernung = Manhattan-Abstand = Fahrzeit, Bedienzeit 2, spätester Rückkehrzeitpunkt 36. Gesucht ist der Weg mit den kleinsten reduzierten Kosten;
Wiederholungen sind erlaubt, solange das Gedächtnis den Kunden nicht mehr kennt (nichtelementar, ng-Gedächtnis 1: nur der zuletzt besuchte Kunde selbst). Mit **r** (Seitenleiste) zählen erst nur die Zeit, dann auch die Last, dann auch die Fahrerzeit.
"""
)
hand_verb = S.hand_verbrauch(h_modell)
hand_inst = S.handbeispiel()
st.dataframe(
    [{"Kunde": i, "Punkt": f"({hand_inst.punkte[i][0]}, {hand_inst.punkte[i][1]})", "Entfernung zum Depot": hand_inst.dist[0][i], "Last": hand_verb[0][i],
      "Fahrerzeit": hand_verb[1][i], "Zeitfenster": f"[{hand_inst.frueh[i]}, {hand_inst.spaet[i]}]", "Dualpreis": S.HAND_DUAL[i]} for i in range(1, 7)],
    hide_index=True, width="stretch",
)
st.caption("Depot bei (5, 5). Fahrerzeit nach der Wahl „Verbrauch der Fahrerzeit“ in der Seitenleiste.")

hand = _hand_zeilen(h_grenzen, h_modell)
if any(z["fehler"] for z in hand):
    st.error("Gegenprobe fehlgeschlagen: " + "; ".join(f"r = {z['r']}: {z['fehler']}" for z in hand if z["fehler"]))
sel, basis = hand[h_r - 1], hand[0]

m1, m2, m3, m4 = st.columns(4)
if h_r == 1:
    m1.metric("Erzeugte Labels", E.fmt_int(sel["erzeugt"]), delta="Referenz: nur Zeit", delta_color="off")
    m2.metric("Anteil dominierter Labels", E.fmt_pct(sel["anteil"]), delta="Referenz: nur Zeit", delta_color="off")
    m3.metric("Vergleiche je Label", E.fmt_dec(sel["je_label"]), delta="Referenz: nur Zeit", delta_color="off")
else:
    # Delta immer als „mein Wert minus Referenz“ (Referenz: nur Zeit); die Farbe regelt delta_color (Vorzeichen-Falle, DEMO-PLAYBOOK §2).
    m1.metric("Erzeugte Labels", E.fmt_int(sel["erzeugt"]), delta=f"{sel['erzeugt'] - basis['erzeugt']:+d} gegen r = 1", delta_color="inverse")
    m2.metric("Anteil dominierter Labels", E.fmt_pct(sel["anteil"]), delta=f"{E.fmt_dec(100 * (sel['anteil'] - basis['anteil']))} Prozentpunkte gegen r = 1", delta_color="normal")
    m3.metric("Vergleiche je Label", E.fmt_dec(sel["je_label"]), delta=f"{E.fmt_dec(sel['je_label'] - basis['je_label'])} gegen r = 1", delta_color="inverse")
m4.metric("Bester Wert", E.fmt_int(sel["bester_wert"]), delta=f"Weg {E.weg_text(sel['weg'])}", delta_color="off")
st.caption(
    f"Gegenprobe durch Aufzählung aller zulässigen Wege (ohne Dominanz): bester Wert {E.fmt_int(sel['aufzaehlung_wert'])}, {E.fmt_int(sel['aufzaehlung_teilwege'])} Teilwege aufgezählt "
    "(der leere Weg am Depot eingerechnet). „Bester Wert“ sind die kleinsten reduzierten Kosten eines Weges; „Anteil dominiert“ ist dominierte geteilt durch erzeugte Labels (das Startlabel am Depot eingerechnet)."
)

c1, c2 = st.columns(2)
with c1:
    st.plotly_chart(V.build_labels(hand), width="stretch", key="hand_labels")
with c2:
    st.plotly_chart(V.build_vergleiche_je_label(hand), width="stretch", key="hand_vergleiche")
st.dataframe(_zeilen_tabelle(hand), hide_index=True, width="stretch", column_config=TABELLE_SPALTEN)
st.caption("Die Tabelle zeigt r = 1, 2, 3 bei den gewählten Grenzen und dem gewählten Verbrauchsmodell; die Diagramme darüber ebenso.")

label_tab, entsch = _hand_protokoll(h_r, h_grenzen, h_modell)
with st.expander(f"📋 Protokoll: jedes der {len(label_tab)} erzeugten Labels (r = {h_r})"):
    st.caption("Nummern in der Reihenfolge der Erzeugung (L0 ist das Startlabel). „Tests“ zählt die Dominanzvergleiche, die dieses Label beim Einfügen ausgelöst hat; ihre Summe ist die Zahl der Vergleiche oben.")
    zeilen = []
    for z in label_tab:
        d = {"Label": f"L{z['id']}", "Weg": E.weg_text(z["weg"]) if z["weg"] else "(Depot)", "Kunde": z["kunde"], "Zeit": z["zeit"], "Kosten": z["kosten"]}
        for m, q in enumerate(z["verbrauch"]):
            d[C.GROESSEN[m + 1]] = q
        d["Tests"] = z["tests"]
        d["Entscheidung"] = E.entscheidung_text(z)
        zeilen.append(d)
    st.dataframe(zeilen, hide_index=True, width="stretch")

if entsch:
    st.markdown("**Eine Dominanzentscheidung ansehen**")
    by_id = {z["id"]: z for z in label_tab}
    wahl = st.selectbox(
        "Entscheidung", list(range(len(entsch))), key="h_entscheidung", label_visibility="collapsed",
        format_func=lambda i: f"{entsch[i][2]}: L{entsch[i][0]} ({E.weg_text(by_id[entsch[i][0]]['weg'])}) dominiert L{entsch[i][1]} ({E.weg_text(by_id[entsch[i][1]]['weg'])})",
    )
    gew, ver, art = entsch[min(wahl, len(entsch) - 1)]
    vergleiche = E.vier_vergleiche(by_id[gew], by_id[ver], h_r)
    st.dataframe([{"Größe": v["größe"], f"L{gew} (dominiert)": v["gewinner"], f"L{ver} (fällt weg)": v["verlierer"], "höchstens so groß?": "✓" if v["höchstens"] else "✗"} for v in vergleiche],
                 hide_index=True, width="stretch")
    st.caption(f"{len(vergleiche)} Einzelvergleiche, alle ✓: L{gew} dominiert L{ver}. Das Label mit den kleineren oder gleichen Werten in jeder Größe gewinnt; die Entscheidung gilt am selben Kunden.")

if h_r >= 2:
    paare = _gebrochene_paare(h_grenzen, h_modell, h_r)
    nicht = [p for p in paare if not p["haelt"]]
    st.markdown(f"**Paare, die erst durch die zusätzlichen Größen unterscheidbar werden.** Von {len(paare)} Dominanzentscheidungen bei r = 1 (nur Kosten und Zeit) gelten bei r = {h_r} nicht mehr: **{len(nicht)}**.")
    if nicht:
        st.dataframe(
            [{"Kunde": p["kunde"], "Dominierender Weg bei r = 1": E.weg_text(p["gewinner"]), "Zeit / Kosten (dominierend)": f"{p['gewinner_zeit']} / {p['gewinner_kosten']}",
              "dominierter Weg": E.weg_text(p["verlierer"]), "Zeit / Kosten (dominiert)": f"{p['verlierer_zeit']} / {p['verlierer_kosten']}", f"bei r = {h_r} nicht, weil": p["grund"]} for p in nicht],
            hide_index=True, width="stretch",
        )
else:
    st.caption("Mit r = 2 oder r = 3 (Seitenleiste) zeigt eine Tabelle, welche Dominanzentscheidungen von r = 1 durch die zusätzlichen Größen hinfällig werden.")

kind, text = E.verdict_dominanz(hand[:h_r], "im Handbeispiel")
getattr(st, kind)(text)
st.markdown("---")

# ======================================================================================================================================
# Experiment 2: Korrelation
# ======================================================================================================================================

st.subheader("🔬 Experiment 2: Hängen die Größen zusammen? Korrelierte Verbräuche")
st.markdown(
    """
Eine zusätzliche Größe, die nur die Last wiederholt, unterscheidet nichts Neues. Hier der Test am Handbeispiel (live) und an einer festen Messreihe mit 30 Kunden.
Die Modelle: **unabhängig** (die Fahrerzeit hat mit der Last nichts zu tun), **gleich der Last** (Fahrerzeit = Last, vollständig korreliert), **gegenläufig** (viel Last, wenig Fahrerzeit);
in der Messreihe außerdem **Last plus Rauschen** (teilweise korreliert).
"""
)
hand_mod = _hand_modelle(h_grenzen)
st.markdown(f"**Handbeispiel, live** (Grenzen: {h_grenzen})")
c1, c2 = st.columns([3, 2])
with c1:
    st.dataframe(
        [{"Fahrerzeit": z["modell"], "r": z["r"], "erzeugte Labels": z["erzeugt"], "dominiert": z["dominiert"], "Vergleiche": z["vergleiche"], "bester Wert": z["bester_wert"]} for z in hand_mod],
        hide_index=True, width="stretch", column_config={"erzeugte Labels": GANZ, "dominiert": GANZ, "Vergleiche": GANZ, "bester Wert": EIN},
    )
with c2:
    st.plotly_chart(V.build_hand_modelle(hand_mod), width="stretch", key="hand_modelle")
kind, text = E.verdict_korrelation_hand(hand_mod)
getattr(st, kind)(text)

st.markdown("**Feste Messreihe** (n = 30 Kunden, zufällig, Zeitfenster der Breite 100, ng-Gedächtnis 5, nie bindende Grenzen, ein Pricing-Aufruf mit den Dualpreisen der ersten Runde, Median über 12 Instanzen)")
p04 = B.p04_tabelle()
c1, c2 = st.columns([3, 2])
with c1:
    st.dataframe(
        [{"Verbrauchsmodell": z["modell"], "r": z["r"], "Labels (Median)": z["labels_median"], "Labels (Mittel)": z["labels_mittel"], "Labels (Maximum)": z["labels_max"],
          "Anteil dominiert (Median)": _prozent(z["anteil_median"]), "Vergleiche (Median)": z["vergleiche_median"], "Vergleiche je Label (Median)": z["vergleiche_je_label"]} for z in p04],
        hide_index=True, width="stretch",
        column_config={"Labels (Median)": GANZ, "Labels (Mittel)": GANZ, "Labels (Maximum)": GANZ, "Anteil dominiert (Median)": PROZENT, "Vergleiche (Median)": GANZ, "Vergleiche je Label (Median)": EIN},
    )
with c2:
    st.plotly_chart(V.build_modelle(p04, "labels_median", "erzeugte Labels (Median)"), width="stretch", key="p04_labels")
st.plotly_chart(V.build_modelle(p04, "anteil_median", "Anteil dominierter Labels (Median, %)", prozent=True), width="stretch", key="p04_anteil")
gleich = min(B.p04_gleich_wie_vorstufe("gleich der Last", 3), B.p04_gleich_wie_vorstufe("gleich der Last", 4))
kind, text = E.verdict_p04(
    gleich, len(C.BAENDER_SEEDS), [B.p04_kennzahlen("gleich der Last", r)["labels_median"] for r in (2, 3, 4)],
    {m: B.p04_kennzahlen(m, 4)["labels_median"] for m in C.MODELLE if m != "gleich der Last"},
)
getattr(st, kind)(text)
st.caption(
    "Eine Zelle, 12 Instanzen, vier Verbrauchsmodelle: andere Korrelationsstärken, k = 1, gruppierte Instanzen, Breite 40 und bindende Grenzen sind in dieser Reihe nicht gemessen. "
    "Die Einzelwerte sind mit dem Kern dieser Demo neu gerechnet und stimmen in Median, Anteil und Vergleichen mit der vor dem Bau gerechneten Messung überein."
)
st.markdown("---")

# ======================================================================================================================================
# Experiment 3: Größenregler (live)
# ======================================================================================================================================

st.subheader("🔬 Experiment 3: Größenregler – ein Pricing-Aufruf auf einer Instanz, live")
st.markdown(
    f"""
Eine zufällige Instanz mit **{l_n} Kunden** (Zufalls-Seed {l_seed}), Zeitfenster der Breite {l_breite}, ng-Gedächtnis {l_k}, Verbrauchsmodell „{l_modell}“, Grenze „{l_grenze}“.
Der Pricing-Aufruf nutzt die Dualpreise der ersten Spaltenerzeugungsrunde (Preis je Kunde = Hin- und Rückweg vom Depot) und wird für r = 1 bis {l_r} gerechnet.
Bei sehr großen Einstellungen bricht die Rechnung an einer festen Obergrenze ab ({E.fmt_int(C.LIVE_MAX_LABELS)} erzeugte Labels oder {E.fmt_int(C.LIVE_MAX_VERGLEICHE)} Vergleiche); die Obergrenze zählt Labels und Vergleiche, keine Sekunden.
"""
)
with st.spinner("Pricing wird gerechnet (die größten Einstellungen brauchen einige Sekunden) …"):
    live = [_live(int(l_n), int(l_breite), int(l_k), r, l_grenze, l_modell, int(l_seed)) for r in range(1, int(l_r) + 1)]
fehler = [z for z in live if z["fehler"]]
if fehler:
    st.error("Prüfung des besten Weges fehlgeschlagen: " + "; ".join(f"r = {z['r']}: {z['fehler']}" for z in fehler))
c1, c2 = st.columns(2)
fertig = [z for z in live if not z["abgebrochen"]]
with c1:
    if fertig:
        st.plotly_chart(V.build_labels(fertig), width="stretch", key="live_labels")
with c2:
    if fertig:
        st.plotly_chart(V.build_vergleiche_je_label(fertig), width="stretch", key="live_vergleiche")
st.dataframe(_zeilen_tabelle(live), hide_index=True, width="stretch", column_config=TABELLE_SPALTEN)
st.caption(
    f"Rechenzeit dieser Läufe zusammen: {E.fmt_dec(sum(z['sekunden'] for z in live))} s (nur zur Information; sie hängt vom Rechner ab, die Zahl der Labels nicht). "
    "„Bester Wert“ ist die kleinste reduzierte Kosten eines Weges, der alle Grenzen, Fenster und das Gedächtnis einhält; er wird vor der Anzeige unabhängig nachgeprüft."
)
kind, text = E.verdict_dominanz(live, "in dieser Instanz")
getattr(st, kind)(text)
st.caption("Eine Instanz ist ein Einzelfall. Das Verdikt gilt für diese Instanz; wie stabil die Richtung über viele Instanzen ist, zeigt Experiment 4.")
st.markdown("---")

# ======================================================================================================================================
# Experiment 4: Bänder
# ======================================================================================================================================

st.subheader("🔬 Experiment 4: Messreihen mit 12 Instanzen je Zelle (Bänder)")
st.markdown(
    """
Feste Messreihe mit 30 Kunden, je Zelle 12 Instanzen (Zufalls-Seeds 0 bis 11). Verbrauch der Last = Nachfrage, Fahrerzeit und dritte Größe unabhängig zufällig (ganze Zahlen von 5 bis 25).
Gezeigt werden Median, Mittel und Maximum der Labels über die fertigen Läufe; die Mediane des Anteils dominierter Labels und der Vergleiche je Label sind je Instanz gebildet.
"""
)
b1, b2, b3, b4 = st.columns(4)
b_typ = b1.radio("Instanzen", list(B.TYPEN), key="b_typ", format_func=lambda x: B.TYPEN[x])
b_breite = b2.radio("Breite der Zeitfenster", (40, 100), key="b_breite")
b_k = b3.radio("ng-Gedächtnis k", (1, 5), key="b_k")
b_art = b4.radio("Was gezählt wird", list(B.ARTEN), key="b_art", format_func=lambda x: B.ARTEN[x])
tabelle = B.v11_tabelle(b_typ, b_breite, b_k, b_art)
ist_colgen = b_art == "colgen"
zeilen = []
for z in tabelle:
    d = {"Grenze": z["grenze"], "r": z["r"], "fertige Läufe": z["fertig"], "abgebrochen": z["abgebrochen"], "Labels (Median)": z["labels_median"],
         "Labels (Mittel)": z["labels_mittel"], "Labels (Maximum)": z["labels_max"], "Anteil dominiert (Median)": _prozent(z["anteil_median"]), "Vergleiche je Label (Median)": z["vergleiche_je_label"]}
    if ist_colgen:
        d["Pricing-Aufrufe (Median)"] = z["aufrufe_median"]
        d["untere Schranke (Median)"] = z["schranke_median"]
    zeilen.append(d)
st.dataframe(
    zeilen, hide_index=True, width="stretch",
    column_config={"Labels (Median)": GANZ, "Labels (Mittel)": GANZ, "Labels (Maximum)": GANZ, "Anteil dominiert (Median)": PROZENT, "Vergleiche je Label (Median)": EIN,
                   "Pricing-Aufrufe (Median)": GANZ, "untere Schranke (Median)": EIN},
)
d1, d2, d3 = st.columns(3)
with d1:
    st.plotly_chart(V.build_baender(tabelle, "labels_median", "Labels (Median)"), width="stretch", key="band_labels")
with d2:
    st.plotly_chart(V.build_baender(tabelle, "anteil_median", "Anteil dominiert (Median, %)", prozent=True), width="stretch", key="band_anteil")
with d3:
    st.plotly_chart(V.build_baender(tabelle, "vergleiche_je_label", "Vergleiche je Label (Median)"), width="stretch", key="band_vergleiche")
instanzen = {}
for g in B.V11_GRENZEN:
    je = B.anteile_je_instanz(b_typ, b_breite, b_k, b_art, g)
    instanzen[g] = {"gesamt": len(je), "1→2": B.zahl_sinkend(je, 1, 2), "2→3": B.zahl_sinkend(je, 2, 3), "3→4": B.zahl_sinkend(je, 3, 4)}
kind, text = E.verdict_baender(tabelle, instanzen, b_art)
getattr(st, kind)(text)
abbr = sum(z["abgebrochen"] for z in tabelle)
if abbr:
    st.warning(
        f"In dieser Zelle brachen {abbr} Läufe ab (Grenze der Messung: 60 s je Pricing-Aufruf, 300 s gesamt); "
        "die betroffenen Zeilen stützen sich auf weniger Instanzen und auf die schnelleren davon (Spalte „fertige Läufe“). Die Zeitgrenzen hängen von der Auslastung des Rechners ab, die Zahlen der Labels nicht."
    )
st.caption("Vergleiche = Zahl der ausgewerteten Dominanztests, nicht ihr Aufwand. Median, Mittel und Maximum können weit auseinanderliegen; darum stehen alle drei da. Kein Konfidenzmaß bei 12 Instanzen.")
st.markdown("---")

# ======================================================================================================================================
# Experiment 5: bindende Grenze
# ======================================================================================================================================

st.subheader("🔬 Experiment 5: Bindende Grenze – weniger Labels als ohne wirksame Grenze, aber ein anderes Problem")
st.markdown(
    """
Eine Grenze, die greift, schneidet Wege ab, die ohne sie zulässig wären. Dann gibt es **weniger** Labels als bei derselben Rechnung ohne wirksame Grenze – aber nicht, weil die Dominanz besser arbeitet, sondern weil die Aufgabe eine andere ist. Gegenüber nur der Zeit können es mehr oder weniger Labels sein.
Zuerst das Handbeispiel (Fahrerzeit „unabhängig“, live), dann die feste Messreihe.
"""
)
nie = _hand_zeilen(C.HAND_GRENZEN[0], "unabhängig")
bind = _hand_zeilen(C.HAND_GRENZEN[1], "unabhängig")
rows = []
for name, zs in ((C.HAND_GRENZEN[0], nie), (C.HAND_GRENZEN[1], bind)):
    for z in zs:
        rows.append({"Grenzen": name, "r": z["r"], "erzeugte Labels": z["erzeugt"], "Erweiterungen an einer Grenze gescheitert": z["grenze_geschnitten"], "bester Wert": z["bester_wert"], "bester Weg": E.weg_text(z["weg"])})
st.dataframe(rows, hide_index=True, width="stretch", column_config={"erzeugte Labels": GANZ, "Erweiterungen an einer Grenze gescheitert": GANZ, "bester Wert": EIN})
kind, text = E.verdict_bindend_hand(nie, bind)
getattr(st, kind)(text)

st.markdown("**Feste Messreihe** (gruppierte Instanzen, n = 30, Breite 100, ng-Gedächtnis 5, ganze Spaltenerzeugung, 12 Instanzen)")
v_basis = B.v11_kennzahlen("cluster", 100, 5, "colgen", "nur Zeit", 1)
v_zeilen = [{"Grenze": "nur Zeit", "r": 1, **v_basis}] + [{"Grenze": "bindend (70)", "r": r, **B.v11_kennzahlen("cluster", 100, 5, "colgen", "bindend (70)", r)} for r in (2, 3, 4)]
st.dataframe(
    [{"Grenze": z["Grenze"], "r": z["r"], "Labels (Median)": z["labels_median"], "Pricing-Aufrufe (Median)": z["aufrufe_median"], "untere Schranke (Median)": z["schranke_median"], "fertige Läufe": z["fertig"]} for z in v_zeilen],
    hide_index=True, width="stretch", column_config={"Labels (Median)": GANZ, "Pricing-Aufrufe (Median)": GANZ, "untere Schranke (Median)": EIN},
)
kind, text = E.verdict_bindend_v11(v_zeilen[0], v_zeilen[-1])
getattr(st, kind)(text)
st.caption(
    f"Die untere Schranke (der Wert der linearen Relaxation am Ende der Spaltenerzeugung) steigt von {E.fmt_dec(v_basis['schranke_median'])} auf {E.fmt_dec(v_zeilen[-1]['schranke_median'])}: "
    "mit der Grenze ist die Aufgabe teurer, also eine andere. Dass die bindende Grenze Wege abschneidet, ist die naheliegende Erklärung für die kleinere Label-Zahl (Deutung, nicht einzeln gemessen)."
)
st.markdown("---")

# ======================================================================================================================================
# Grenzen, Annahmen, Mathematik
# ======================================================================================================================================

st.subheader("🚧 Wo die Annahmen enden")
st.markdown(
    """
| Annahme | Wenn sie nicht gilt | Stand |
|---|---|---|
| **Nichtelementare Rechnung** (ng-Gedächtnis 1 oder 5) | Bei elementarer Rechnung ist jeder aufsummierte Verbrauch durch die Teilmengen-Bedingung der besuchten Kunden schon abgedeckt: die zusätzlichen Größen ändern bei nie bindenden Grenzen weder Labels noch Vergleiche. | bewiesen (Teilmengen-Argument), in den Tests an kleinen Instanzen geprüft |
| **Unabhängige Verbräuche** in den Messreihen | Bei korrelierten Verbräuchen kommen weniger Labels hinzu (Last plus Rauschen) oder keine (gleich der Last); gegenläufige Verbräuche erzeugen mehr (Experiment 2). | in einer Zelle gemessen, 12 Instanzen |
| **Grenzen, die nicht binden** | Bindende Grenzen schneiden Wege ab: weniger Labels als bei derselben Rechnung ohne wirksame Grenze, aber eine andere Aufgabe; gegenüber nur der Zeit können es mehr oder weniger sein (Experiment 5). | am Handbeispiel und in der Messreihe gemessen |
| **30 Kunden, Dualpreise der ersten Runde, Python** | Andere Größen der Instanz, andere Dualpreise und andere Sprachen sind nicht gemessen; bei Dualpreisen am Ende der Spaltenerzeugung stehen die Zellen der dritten Messart in Experiment 4. | teilweise gemessen |
| **Bis zu vier Größen, nur Vorwärtsrechnung** | Mehr als vier Größen, bidirektionales Labeling und Eimer-Verfahren mit mehreren Größen sind nicht gemessen. | nicht gemessen |
"""
)

with st.expander("⚠️ Annahmen, Grenzen und bekannte Probleme"):
    st.markdown(T.assumptions_markdown())

st.markdown("---")

with st.expander("📐 Mathematische Formulierung"):
    st.markdown(T.MATH_LESEHILFE)
    st.markdown(T.MATH_FORMELN)

st.markdown("---")
st.caption(
    "Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net) – "
    "Operations Research und Machine Learning ([Über mich](https://sebastianhanisch.net/ueber-mich.html)). "
    "Mehr zur Reihe: [Ressourcenwege: von der Grenze zur Verfahrenswahl](https://sebastianhanisch.net/konzepte-ressourcenwege.html)."
)
