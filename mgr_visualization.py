"""Plotly-Abbildungen. Alle Achsen sind gesperrt (fixedrange), damit Touch-Geräte beim Scrollen nicht am Diagramm hängen bleiben.

Beschriftungen stehen als Text auf Kategorienachsen („r = 1“, „r = 2“ …), damit Plotly keine lineare Achse mit Zwischenwerten anlegt."""

import plotly.graph_objects as go

import mgr_constants as C
from mgr_evaluation import fmt_dec, fmt_int, fmt_pct


def lock_axes(fig):
    fig.update_xaxes(fixedrange=True)
    fig.update_yaxes(fixedrange=True)
    return fig


def _base(fig, height=330, legende=True):
    fig.update_layout(height=height, margin=dict(l=10, r=10, t=10, b=10), plot_bgcolor="rgba(0,0,0,0)",
                      legend=dict(orientation="h", y=-0.25) if legende else None, showlegend=legende)
    return lock_axes(fig)


def _r_text(r) -> str:
    return f"r = {r}"


def build_labels(zeilen: list):
    """Erzeugte Labels je r, gestapelt in lebende (bleiben) und dominierte (fallen weg); darüber der Anteil dominierter Labels."""
    xs = [_r_text(z["r"]) for z in zeilen]
    bleiben = [z["erzeugt"] - z["dominiert"] for z in zeilen]
    fig = go.Figure()
    fig.add_trace(go.Bar(x=xs, y=bleiben, name="bleiben", marker_color=C.COLOR_KEPT, hovertemplate="%{x}: %{y} Labels bleiben<extra></extra>"))
    fig.add_trace(go.Bar(x=xs, y=[z["dominiert"] for z in zeilen], name="dominiert (fallen weg)", marker_color=C.COLOR_DOMINATED,
                         hovertemplate="%{x}: %{y} Labels dominiert<extra></extra>"))
    hoehe = max(z["erzeugt"] for z in zeilen)
    for z, x in zip(zeilen, xs):
        fig.add_annotation(x=x, y=z["erzeugt"], text=f"{fmt_pct(z['anteil'])} dominiert", showarrow=False, yshift=12, font=dict(size=11))
    fig.update_layout(barmode="stack")
    fig.update_yaxes(title_text="erzeugte Labels", range=[0, hoehe * 1.15])
    return _base(fig)


def build_vergleiche_je_label(zeilen: list):
    """Dominanzvergleiche je erzeugtem Label und r."""
    xs = [_r_text(z["r"]) for z in zeilen]
    fig = go.Figure(go.Bar(x=xs, y=[z["je_label"] for z in zeilen], marker_color=C.COLOR_LINE3, name="Vergleiche je Label",
                           text=[fmt_dec(z["je_label"]) for z in zeilen], textposition="outside", hovertemplate="%{x}: %{y:.1f} Vergleiche je Label<extra></extra>"))
    hoehe = max(z["je_label"] for z in zeilen)
    fig.update_yaxes(title_text="Vergleiche je Label", range=[0, hoehe * 1.2 if hoehe else 1])
    return _base(fig, legende=False)


def build_hand_modelle(zeilen: list):
    """Erzeugte Labels des Handbeispiels je r, für jedes Verbrauchsmodell eine Balkengruppe."""
    fig = go.Figure()
    modelle = []
    for z in zeilen:
        if z["modell"] not in modelle:
            modelle.append(z["modell"])
    farben = {1: C.COLORS_BY_R[1], 2: C.COLORS_BY_R[2], 3: C.COLORS_BY_R[3]}
    for r in (1, 2, 3):
        werte = [next(z for z in zeilen if z["modell"] == m and z["r"] == r)["erzeugt"] for m in modelle]
        fig.add_trace(go.Bar(x=[f"Fahrerzeit {m}" for m in modelle], y=werte, name=_r_text(r), marker_color=farben[r],
                             text=[fmt_int(w) for w in werte], textposition="outside", hovertemplate="%{x}, " + _r_text(r) + ": %{y} Labels<extra></extra>"))
    fig.update_layout(barmode="group")
    fig.update_yaxes(title_text="erzeugte Labels", range=[0, max(z["erzeugt"] for z in zeilen) * 1.2])
    return _base(fig)


def _linien(serien: dict, ytitel: str, prozent: bool = False, farben: dict | None = None):
    """Eine Linie je Serie über r = 1 bis 4; `serien[name]` ist die Liste der Werte (None = fehlt)."""
    fig = go.Figure()
    palette = [C.COLOR_LINE, C.COLOR_LINE3, C.COLOR_LINE2, C.COLOR_LINE4]
    for i, (name, werte) in enumerate(serien.items()):
        farbe = (farben or {}).get(name, palette[i % len(palette)])
        xs = [_r_text(r) for r in range(1, len(werte) + 1)]
        y = [None if v is None else (100 * v if prozent else v) for v in werte]
        fig.add_trace(go.Scatter(x=xs, y=y, mode="lines+markers", name=name, line=dict(color=farbe, width=3), connectgaps=False,
                                 hovertemplate="%{x}: %{y:,.1f}" + (" %" if prozent else "") + "<extra>" + name + "</extra>"))
    fig.update_yaxes(title_text=ytitel)
    return _base(fig)


def build_baender(tabelle: list, kennzahl: str, ytitel: str, prozent: bool = False):
    """Median einer Kennzahl über r = 1 bis 4, eine Linie je Grenze (r = 1 ist für alle gleich: nur Zeit)."""
    basis = next(z for z in tabelle if z["r"] == 1)
    serien = {}
    for g in ("bindend (70)", "locker (140)", "nie bindend"):
        zeilen = [z for z in tabelle if z["grenze"] == g]
        serien[g] = [basis[kennzahl]] + [z[kennzahl] for z in zeilen]
    farben = {"bindend (70)": C.COLOR_LINE, "locker (140)": C.COLOR_LINE3, "nie bindend": C.COLOR_LINE2}
    return _linien(serien, ytitel, prozent, farben)


def build_modelle(tabelle: list, kennzahl: str, ytitel: str, prozent: bool = False):
    """Median einer Kennzahl der Verbrauchsmodell-Reihe über r = 1 bis 4, eine Linie je Modell."""
    serien = {m: [z[kennzahl] for z in tabelle if z["modell"] == m] for m in C.MODELLE}
    return _linien(serien, ytitel, prozent)
