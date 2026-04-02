"""
Boston Airbnb Market Analytics Dashboard
Inside Airbnb data — Data Scientist Portfolio Project
"""

import pandas as pd
import numpy as np
import gzip
from dash import Dash, dcc, html, Input, Output, callback
import plotly.graph_objects as go
import plotly.express as px

# ─────────────────────────────────────────────
# PALETTE & STYLE
# ─────────────────────────────────────────────
COLORS = {
    "bg":        "#F0F4F8",
    "card":      "#FFFFFF",
    "primary":   "#264653",   # dark teal — main bars/lines
    "secondary": "#2A9D8F",   # teal
    "accent":    "#E9C46A",   # gold highlight
    "alert":     "#E76F51",   # orange-red for key callouts
    "muted":     "#A8DADC",   # light teal for secondary
    "text":      "#264653",
    "subtext":   "#6C757D",
}

ROOM_COLORS = {
    "Entire home/apt": COLORS["primary"],
    "Private room":    COLORS["secondary"],
    "Hotel room":      COLORS["accent"],
    "Shared room":     COLORS["muted"],
}

CARD_STYLE = {
    "backgroundColor": COLORS["card"],
    "borderRadius": "10px",
    "padding": "20px",
    "boxShadow": "0 2px 8px rgba(0,0,0,0.07)",
}

# ─────────────────────────────────────────────
# DATA LOADING & PREPROCESSING
# ─────────────────────────────────────────────
DATA_DIR = "/Users/mengyao/Documents/Bootcamp_project/insideAirbnb"

print("Loading data…")
listings_raw = pd.read_csv(f"{DATA_DIR}/listings.csv")
calendar_raw = pd.read_csv(f"{DATA_DIR}/calendar.csv.gz", compression="gzip")
reviews_raw  = pd.read_csv(f"{DATA_DIR}/reviews.csv.gz",  compression="gzip")
print("Data loaded.")

# ── Listings ──────────────────────────────────
listings = listings_raw.copy()
# cap extreme prices for visualisation (keep ≤ $2000/night)
listings = listings[listings["price"].notna() & (listings["price"] <= 2000)]
listings["price"] = listings["price"].astype(float)

ALL_NEIGHBOURHOODS = sorted(listings["neighbourhood"].dropna().unique())
ALL_ROOM_TYPES     = sorted(listings["room_type"].dropna().unique())

# ── Calendar ──────────────────────────────────
calendar = calendar_raw.copy()
calendar["date"]  = pd.to_datetime(calendar["date"])
calendar["month"] = calendar["date"].dt.month
calendar["month_name"] = calendar["date"].dt.strftime("%b")
calendar["year"]  = calendar["date"].dt.year
MONTH_ORDER = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]

# ── Reviews ───────────────────────────────────
reviews = reviews_raw.copy()
reviews["date"] = pd.to_datetime(reviews["date"])
reviews["year_month"] = reviews["date"].dt.to_period("M").dt.to_timestamp()


# ─────────────────────────────────────────────
# HELPER — reusable chart theme
# ─────────────────────────────────────────────
def base_layout(title="", xaxis_title="", yaxis_title="", showlegend=False):
    return dict(
        title=dict(text=title, font=dict(size=14, color=COLORS["text"], family="Inter, Arial, sans-serif"), x=0, xanchor="left"),
        paper_bgcolor=COLORS["card"],
        plot_bgcolor=COLORS["card"],
        font=dict(family="Inter, Arial, sans-serif", color=COLORS["text"], size=12),
        xaxis=dict(title=xaxis_title, showgrid=False, zeroline=False,
                   tickfont=dict(size=11)),
        yaxis=dict(title=yaxis_title, showgrid=True,
                   gridcolor="#EDEDED", zeroline=False,
                   tickfont=dict(size=11)),
        showlegend=showlegend,
        margin=dict(l=10, r=10, t=40, b=10),
    )


# ─────────────────────────────────────────────
# APP LAYOUT
# ─────────────────────────────────────────────
app = Dash(__name__, title="Boston Airbnb Analytics")
server = app.server   # expose Flask server for gunicorn (Render / Railway deploy)

app.layout = html.Div(
    style={"backgroundColor": COLORS["bg"], "minHeight": "100vh",
           "fontFamily": "Inter, Arial, sans-serif", "padding": "24px 32px"},
    children=[

        # ── HEADER ───────────────────────────
        html.Div([
            html.H1("Boston Airbnb Market Analytics",
                    style={"margin": "0 0 4px 0", "color": COLORS["primary"],
                           "fontSize": "26px", "fontWeight": "700"}),
            html.P("Exploring listing supply, pricing, and seasonal demand across Boston's 25 neighbourhoods  |  "
                   "Data: Inside Airbnb  •  Sept 2025",
                   style={"margin": 0, "color": COLORS["subtext"], "fontSize": "13px"}),
        ], style={"marginBottom": "20px"}),

        # ── GLOBAL FILTERS ───────────────────
        html.Div([
            html.Div([
                html.Label("Neighbourhood", style={"fontSize": "12px", "fontWeight": "600",
                                                   "color": COLORS["subtext"], "marginBottom": "4px"}),
                dcc.Dropdown(
                    id="filter-neighbourhood",
                    options=[{"label": n, "value": n} for n in ALL_NEIGHBOURHOODS],
                    value=None,
                    placeholder="All neighbourhoods",
                    multi=True,
                    clearable=True,
                    style={"fontSize": "13px"},
                ),
            ], style={"flex": "1", "minWidth": "220px"}),

            html.Div([
                html.Label("Room Type", style={"fontSize": "12px", "fontWeight": "600",
                                               "color": COLORS["subtext"], "marginBottom": "4px"}),
                dcc.Dropdown(
                    id="filter-room-type",
                    options=[{"label": r, "value": r} for r in ALL_ROOM_TYPES],
                    value=None,
                    placeholder="All room types",
                    multi=True,
                    clearable=True,
                    style={"fontSize": "13px"},
                ),
            ], style={"flex": "1", "minWidth": "200px"}),

            html.Div([
                html.P("↑ Filters apply to all charts below",
                       style={"margin": 0, "fontSize": "12px", "color": COLORS["subtext"],
                              "fontStyle": "italic", "marginTop": "22px"}),
            ]),
        ], style={"display": "flex", "gap": "16px", "alignItems": "flex-start",
                  "backgroundColor": COLORS["card"], "padding": "16px 20px",
                  "borderRadius": "10px", "boxShadow": "0 2px 8px rgba(0,0,0,0.07)",
                  "marginBottom": "20px"}),

        # ── KPI CARDS ────────────────────────
        html.Div(id="kpi-row",
                 style={"display": "grid", "gridTemplateColumns": "repeat(4, 1fr)",
                        "gap": "16px", "marginBottom": "20px"}),

        # ── ROW 2: Neighbourhood + Price dist ─
        html.Div([
            html.Div([
                dcc.Graph(id="chart-neighbourhood", config={"displayModeBar": False},
                          style={"height": "360px"}),
                html.P("Bar height = number of listings. Color intensity = median nightly price. "
                       "Neighbourhoods with fewer but pricier listings (e.g. Bay Village) differ from "
                       "high-volume areas like Dorchester.",
                       style={"fontSize": "11px", "color": COLORS["subtext"],
                              "margin": "8px 4px 0 4px"}),
            ], style={**CARD_STYLE, "flex": "3"}),

            html.Div([
                dcc.Graph(id="chart-price-dist", config={"displayModeBar": False},
                          style={"height": "360px"}),
                html.P("Entire homes command the highest prices; private rooms offer budget-friendly options. "
                       "Outliers above $500 are mostly luxury properties.",
                       style={"fontSize": "11px", "color": COLORS["subtext"],
                              "margin": "8px 4px 0 4px"}),
            ], style={**CARD_STYLE, "flex": "2"}),
        ], style={"display": "flex", "gap": "16px", "marginBottom": "20px"}),

        # ── ROW 3: Seasonal demand + Availability ─
        html.Div([
            html.Div([
                dcc.Graph(id="chart-reviews-trend", config={"displayModeBar": False},
                          style={"height": "320px"}),
                html.P("Review count is a strong proxy for booking activity. "
                       "Boston peaks in May–Oct and dips in winter — plan pricing strategy accordingly.",
                       style={"fontSize": "11px", "color": COLORS["subtext"],
                              "margin": "8px 4px 0 4px"}),
            ], style={**CARD_STYLE, "flex": "3"}),

            html.Div([
                dcc.Graph(id="chart-availability", config={"displayModeBar": False},
                          style={"height": "320px"}),
                html.P("Average % of nights available per calendar month (forward-looking). "
                       "Higher availability = more nights unbooked.",
                       style={"fontSize": "11px", "color": COLORS["subtext"],
                              "margin": "8px 4px 0 4px"}),
            ], style={**CARD_STYLE, "flex": "2"}),
        ], style={"display": "flex", "gap": "16px", "marginBottom": "20px"}),

        # ── ROW 4: Price vs Reviews scatter ───
        html.Div([
            html.Div([
                dcc.Graph(id="chart-scatter", config={"displayModeBar": False},
                          style={"height": "350px"}),
                html.P("Each point is a listing. Size = availability_365. "
                       "Most reviewed (and therefore most booked) listings cluster under $400/night — "
                       "there's a clear sweet spot for demand.",
                       style={"fontSize": "11px", "color": COLORS["subtext"],
                              "margin": "8px 4px 0 4px"}),
            ], style={**CARD_STYLE, "flex": "1"}),
        ], style={"display": "flex", "gap": "16px", "marginBottom": "24px"}),

        # ── FOOTER ───────────────────────────
        html.P("Built with Plotly Dash  •  Data: insideairbnb.com  •  Mengyao — Data Scientist Portfolio",
               style={"textAlign": "center", "color": COLORS["subtext"],
                      "fontSize": "12px", "paddingTop": "8px"}),
    ]
)


# ─────────────────────────────────────────────
# FILTER HELPER
# ─────────────────────────────────────────────
def filter_listings(neighbourhoods, room_types):
    df = listings.copy()
    if neighbourhoods:
        df = df[df["neighbourhood"].isin(neighbourhoods)]
    if room_types:
        df = df[df["room_type"].isin(room_types)]
    return df


# ─────────────────────────────────────────────
# CALLBACKS
# ─────────────────────────────────────────────

@callback(
    Output("kpi-row", "children"),
    Input("filter-neighbourhood", "value"),
    Input("filter-room-type",     "value"),
)
def update_kpis(neighbourhoods, room_types):
    df = filter_listings(neighbourhoods, room_types)

    total_listings  = len(df)
    median_price    = df["price"].median()
    avg_avail       = df["availability_365"].mean()
    total_reviews   = df["number_of_reviews"].sum()

    def kpi_card(label, value, sub, highlight=False):
        return html.Div([
            html.P(label, style={"margin": "0 0 4px 0", "fontSize": "11px",
                                 "fontWeight": "600", "color": COLORS["subtext"],
                                 "textTransform": "uppercase", "letterSpacing": "0.05em"}),
            html.P(value, style={"margin": "0 0 2px 0", "fontSize": "28px",
                                 "fontWeight": "700",
                                 "color": COLORS["alert"] if highlight else COLORS["primary"]}),
            html.P(sub,   style={"margin": 0, "fontSize": "11px", "color": COLORS["subtext"]}),
        ], style={**CARD_STYLE, "textAlign": "center"})

    return [
        kpi_card("Total Listings",    f"{total_listings:,}",
                 "after removing extreme prices (>$2K)", highlight=True),
        kpi_card("Median Nightly Price", f"${median_price:,.0f}",
                 "per night (USD)"),
        kpi_card("Avg Availability",  f"{avg_avail:.0f} days/yr",
                 "out of 365 (higher = less booked)"),
        kpi_card("Total Reviews",     f"{total_reviews:,}",
                 "proxy for cumulative bookings"),
    ]


@callback(
    Output("chart-neighbourhood", "figure"),
    Input("filter-neighbourhood", "value"),
    Input("filter-room-type",     "value"),
)
def update_neighbourhood(neighbourhoods, room_types):
    df = filter_listings(neighbourhoods, room_types)

    nb = (df.groupby("neighbourhood")
            .agg(count=("id", "count"), median_price=("price", "median"))
            .reset_index()
            .sort_values("count", ascending=True)
            .tail(20))   # top 20 neighbourhoods by listing count

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=nb["count"], y=nb["neighbourhood"],
        orientation="h",
        marker=dict(
            color=nb["median_price"],
            colorscale=[[0, COLORS["muted"]], [0.5, COLORS["secondary"]], [1, COLORS["primary"]]],
            showscale=True,
            colorbar=dict(title="Median<br>Price ($)", tickfont=dict(size=10), len=0.8),
        ),
        hovertemplate="<b>%{y}</b><br>Listings: %{x}<br>Median price: $%{marker.color:.0f}<extra></extra>",
    ))

    fig.update_layout(**base_layout(
        title="Listings per Neighbourhood  (colour = median nightly price)",
        xaxis_title="Number of Listings",
    ))
    return fig


@callback(
    Output("chart-price-dist", "figure"),
    Input("filter-neighbourhood", "value"),
    Input("filter-room-type",     "value"),
)
def update_price_dist(neighbourhoods, room_types):
    df = filter_listings(neighbourhoods, room_types)
    df = df[df["price"] <= 800]   # zoom into realistic range

    fig = go.Figure()
    for rt in ["Entire home/apt", "Private room", "Hotel room", "Shared room"]:
        subset = df[df["room_type"] == rt]["price"]
        if len(subset) == 0:
            continue
        fig.add_trace(go.Box(
            y=subset, name=rt,
            marker_color=ROOM_COLORS.get(rt, COLORS["muted"]),
            boxmean=True,
            hovertemplate=f"<b>{rt}</b><br>Price: $%{{y:.0f}}<extra></extra>",
        ))

    fig.update_layout(**base_layout(
        title="Price Distribution by Room Type",
        yaxis_title="Nightly Price ($)",
        showlegend=False,
    ))
    fig.update_xaxes(tickangle=-20)
    return fig


@callback(
    Output("chart-reviews-trend", "figure"),
    Input("filter-neighbourhood", "value"),
    Input("filter-room-type",     "value"),
)
def update_reviews(neighbourhoods, room_types):
    df_l = filter_listings(neighbourhoods, room_types)
    listing_ids = set(df_l["id"].tolist())

    # filter reviews by selected listings
    rev = reviews[reviews["listing_id"].isin(listing_ids)].copy()
    monthly = (rev.groupby("year_month").size().reset_index(name="reviews")
                  .sort_values("year_month"))
    # only show last 5 years for clarity
    monthly = monthly[monthly["year_month"] >= "2020-01-01"]

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=monthly["year_month"], y=monthly["reviews"],
        mode="lines",
        line=dict(color=COLORS["primary"], width=2.5),
        fill="tozeroy",
        fillcolor="rgba(38,70,83,0.08)",
        hovertemplate="%{x|%b %Y}: <b>%{y:,}</b> reviews<extra></extra>",
    ))

    # annotate the peak
    if len(monthly):
        peak = monthly.loc[monthly["reviews"].idxmax()]
        fig.add_annotation(
            x=peak["year_month"], y=peak["reviews"],
            text=f"<b>Peak: {peak['reviews']:,}</b>",
            showarrow=True, arrowhead=2,
            arrowcolor=COLORS["alert"], font=dict(color=COLORS["alert"], size=11),
            ax=0, ay=-30,
        )

    fig.update_layout(**base_layout(
        title="Monthly Review Activity  (2020 – Present)",
        xaxis_title="", yaxis_title="Reviews / Month",
    ))
    return fig


@callback(
    Output("chart-availability", "figure"),
    Input("filter-neighbourhood", "value"),
    Input("filter-room-type",     "value"),
)
def update_availability(neighbourhoods, room_types):
    df_l = filter_listings(neighbourhoods, room_types)
    listing_ids = set(df_l["id"].tolist())

    cal = calendar_raw.copy()
    cal = cal[cal["listing_id"].isin(listing_ids)]
    cal["date"]  = pd.to_datetime(cal["date"])
    cal["month"] = cal["date"].dt.month
    cal["month_name"] = cal["date"].dt.strftime("%b")
    cal["is_available"] = (cal["available"] == "t").astype(int)

    avail_by_month = (cal.groupby(["month", "month_name"])["is_available"]
                         .mean().reset_index()
                         .sort_values("month"))
    avail_by_month["pct"] = avail_by_month["is_available"] * 100

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=avail_by_month["month_name"],
        y=avail_by_month["pct"],
        marker_color=[
            COLORS["alert"] if v < avail_by_month["pct"].mean() else COLORS["secondary"]
            for v in avail_by_month["pct"]
        ],
        hovertemplate="%{x}: <b>%{y:.1f}%</b> available<extra></extra>",
    ))

    avg = avail_by_month["pct"].mean()
    fig.add_hline(y=avg, line_dash="dot", line_color=COLORS["subtext"],
                  annotation_text=f"Avg {avg:.1f}%",
                  annotation_font_color=COLORS["subtext"],
                  annotation_font_size=11)

    fig.update_layout(**base_layout(
        title="Avg Nightly Availability by Month",
        xaxis_title="", yaxis_title="% Available Nights",
    ))
    fig.update_yaxes(range=[0, 100], ticksuffix="%")
    return fig


@callback(
    Output("chart-scatter", "figure"),
    Input("filter-neighbourhood", "value"),
    Input("filter-room-type",     "value"),
)
def update_scatter(neighbourhoods, room_types):
    df = filter_listings(neighbourhoods, room_types)
    df = df[df["price"] <= 800]
    # sample for performance
    df = df.sample(min(len(df), 1500), random_state=42)

    fig = go.Figure()
    for rt in ALL_ROOM_TYPES:
        sub = df[df["room_type"] == rt]
        if len(sub) == 0:
            continue
        fig.add_trace(go.Scatter(
            x=sub["price"],
            y=sub["number_of_reviews"],
            mode="markers",
            name=rt,
            marker=dict(
                color=ROOM_COLORS.get(rt, COLORS["muted"]),
                size=6, opacity=0.65,
                line=dict(width=0.5, color="white"),
            ),
            hovertemplate=(
                "<b>%{text}</b><br>"
                "Price: $%{x}<br>"
                "Reviews: %{y}<br>"
                "Room type: " + rt + "<extra></extra>"
            ),
            text=sub["name"].str[:40],
        ))

    # sweet-spot annotation
    fig.add_vrect(x0=80, x1=300,
                  fillcolor=COLORS["accent"], opacity=0.08,
                  annotation_text="Sweet spot", annotation_position="top left",
                  annotation_font_color=COLORS["accent"],
                  annotation_font_size=11,
                  line_width=0)

    fig.update_layout(**base_layout(
        title="Nightly Price vs. Total Reviews  (sampled, ≤$800)",
        xaxis_title="Nightly Price ($)",
        yaxis_title="Number of Reviews",
        showlegend=True,
    ))
    fig.update_layout(legend=dict(
        orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1,
        font=dict(size=11),
    ))
    return fig


# ─────────────────────────────────────────────
if __name__ == "__main__":
    app.run(debug=False, port=8050)
