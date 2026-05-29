import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import pydeck as pdk
import math
import re
import os
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()
st.set_page_config(page_title="RentRadar", layout="wide", initial_sidebar_state="expanded")

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

/* ═══════════════════════════════════════════════
   BASE RESET & TYPOGRAPHY
═══════════════════════════════════════════════ */
*, *::before, *::after { box-sizing: border-box; }
html, body, [class*="css"], [class*="st-"] {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
    font-size: 14px;
    color: #374151;
}
h1, h2, h3, h4, h5    { color: #111827 !important; font-weight: 700 !important; }
p, .stMarkdown p       { color: #6B7280 !important; font-size: 14px !important; line-height: 1.6 !important; }
[data-testid="stHorizontalBlock"] { gap: 0.75rem !important; align-items: stretch !important; }

/* ═══════════════════════════════════════════════
   APP SHELL
═══════════════════════════════════════════════ */
.stApp, [data-testid="stApp"], .main,
[data-testid="stMain"], [data-testid="stAppViewContainer"] {
    background-color: #F8F9FB !important;
}
.block-container {
    padding-top: 1.5rem !important;
    padding-bottom: 2rem !important;
    padding-left: 2rem !important;
    padding-right: 2rem !important;
    max-width: 100% !important;
    box-sizing: border-box !important;
    overflow-x: hidden !important;
}

/* ── Hide Streamlit chrome ── */
[data-testid="stMainMenuButton"],
[data-testid="stDeployButton"],
[data-testid="stToolbar"],
[data-testid="stDecoration"],
[data-testid="stStatusWidget"],
[data-testid="stElementToolbar"],
[data-testid="stHeader"],
[data-testid="stSidebarCollapseButton"],
[data-testid="stSidebarNavSeparator"],
[data-testid="stSidebarNav"],
#MainMenu, footer { display: none !important; }

/* ── App view container: reserve 220px left gutter for fixed sidebar ── */
[data-testid="stAppViewContainer"] {
    padding-top: 0 !important;
    padding-left: 220px !important;
    box-sizing: border-box !important;
    width: 100% !important;
    overflow-x: hidden !important;
}

/* ── Main content: no extra offsets (handled by container padding above) ── */
[data-testid="stMain"],
section[data-testid="stMain"],
.main {
    padding-top: 0 !important;
    margin-top: 0 !important;
    margin-left: 0 !important;
    width: 100% !important;
    min-width: 0 !important;
    overflow-x: hidden !important;
}

/* ── Sidebar: fixed position, out of flex flow ── */
section[data-testid="stSidebar"],
[data-testid="stSidebar"] {
    position: fixed !important;
    left: 0 !important;
    top: 0 !important;
    height: 100vh !important;
    width: 220px !important;
    min-width: 220px !important;
    max-width: 220px !important;
    background-color: #FFFFFF !important;
    border-right: 1px solid #E5E7EB !important;
    z-index: 999 !important;
    transform: none !important;
    visibility: visible !important;
    display: flex !important;
    flex-direction: column !important;
    overflow-y: auto !important;
    overflow-x: hidden !important;
}
[data-testid="stSidebar"] > div:first-child {
    width: 220px !important;
    min-width: 220px !important;
    padding: 1.25rem 0.75rem 1.5rem !important;
}

/* ── Sidebar nav buttons ── */
[data-testid="stSidebar"] .stButton { margin-bottom: 0 !important; }
[data-testid="stSidebar"] .stButton button {
    background: transparent !important;
    border-top: none !important;
    border-right: none !important;
    border-radius: 0 !important;
    border-left: 3px solid transparent !important;
    border-bottom: 1px solid #E5E7EB !important;
    color: #6B7280 !important;
    font-size: 13px !important;
    font-weight: 500 !important;
    text-align: left !important;
    display: flex !important;
    align-items: center !important;
    justify-content: flex-start !important;
    gap: 10px !important;
    padding: 10px 14px 10px 10px !important;
    width: 100% !important;
    min-height: 42px !important;
    height: auto !important;
    box-shadow: none !important;
    transition: background-color 0.12s, color 0.12s, border-left-color 0.12s !important;
}
[data-testid="stSidebar"] .stButton button:hover {
    background: #EFF6FF !important;
    color: #1D4ED8 !important;
    border-left-color: #93C5FD !important;
}
/* Button text alignment */
[data-testid="stSidebar"] .stButton button p,
[data-testid="stSidebar"] .stButton button div {
    text-align: left !important;
    color: inherit !important;
    line-height: 1 !important;
    margin: 0 !important;
    padding: 0 !important;
}

/* ── Sidebar nav SVG icons via ::before ── */
[data-testid="stSidebar"] .stButton button::before {
    content: '' !important;
    flex: 0 0 16px !important;
    width: 16px !important;
    height: 16px !important;
    background-size: contain !important;
    background-repeat: no-repeat !important;
    background-position: center !important;
    opacity: 0.65 !important;
}
/* Overview — bar chart */
[data-testid="stSidebar"] button[aria-label="Overview"]::before {
    background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='16' height='16' viewBox='0 0 24 24' fill='none' stroke='%236B7280' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cline x1='18' y1='20' x2='18' y2='10'/%3E%3Cline x1='12' y1='20' x2='12' y2='4'/%3E%3Cline x1='6' y1='20' x2='6' y2='14'/%3E%3C/svg%3E") !important;
}
/* Pricing Intelligence — dollar sign */
[data-testid="stSidebar"] button[aria-label="Pricing Intelligence"]::before {
    background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='16' height='16' viewBox='0 0 24 24' fill='none' stroke='%236B7280' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cline x1='12' y1='1' x2='12' y2='23'/%3E%3Cpath d='M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6'/%3E%3C/svg%3E") !important;
}
/* Map — map pin */
[data-testid="stSidebar"] button[aria-label="Map"]::before {
    background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='16' height='16' viewBox='0 0 24 24' fill='none' stroke='%236B7280' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z'/%3E%3Ccircle cx='12' cy='10' r='3'/%3E%3C/svg%3E") !important;
}
/* Forecast — trending up */
[data-testid="stSidebar"] button[aria-label="Forecast"]::before {
    background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='16' height='16' viewBox='0 0 24 24' fill='none' stroke='%236B7280' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpolyline points='23 6 13.5 15.5 8.5 10.5 1 18'/%3E%3Cpolyline points='17 6 23 6 23 12'/%3E%3C/svg%3E") !important;
}
/* Companies — building */
[data-testid="stSidebar"] button[aria-label="Companies"]::before {
    background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='16' height='16' viewBox='0 0 24 24' fill='none' stroke='%236B7280' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M6 22V4a2 2 0 0 1 2-2h8a2 2 0 0 1 2 2v18Z'/%3E%3Cpath d='M6 12H4a2 2 0 0 0-2 2v6a2 2 0 0 0 2 2h2'/%3E%3Cpath d='M18 9h2a2 2 0 0 1 2 2v9a2 2 0 0 1-2 2h-2'/%3E%3Cpath d='M10 6h4'/%3E%3Cpath d='M10 10h4'/%3E%3Cpath d='M10 14h4'/%3E%3Cpath d='M10 18h4'/%3E%3C/svg%3E") !important;
}

/* ═══════════════════════════════════════════════
   SCROLLBAR
═══════════════════════════════════════════════ */
::-webkit-scrollbar       { width: 5px; height: 5px; }
::-webkit-scrollbar-track { background: #F8F9FB; }
::-webkit-scrollbar-thumb { background: #D1D5DB; border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: #9CA3AF; }

/* ═══════════════════════════════════════════════
   TABS
═══════════════════════════════════════════════ */
[data-testid="stTabs"] > div:first-child {
    border-bottom: 1px solid #E5E7EB !important;
    gap: 0 !important;
    background: transparent !important;
}
button[data-baseweb="tab"] {
    background: transparent !important;
    color: #6B7280 !important;
    font-size: 14px !important;
    font-weight: 500 !important;
    border: none !important;
    border-bottom: 2px solid transparent !important;
    border-radius: 0 !important;
    padding: 8px 20px 8px 0 !important;
    margin-right: 8px !important;
    transition: color 0.12s ease !important;
}
button[data-baseweb="tab"]:hover { color: #111827 !important; background: transparent !important; }
button[data-baseweb="tab"][aria-selected="true"] {
    color: #111827 !important;
    border-bottom: 2px solid #2563EB !important;
    background: transparent !important;
    font-weight: 600 !important;
}
[data-testid="stTabContent"] { padding-top: 1rem !important; }

/* ═══════════════════════════════════════════════
   PAGE HEADER HELPERS
═══════════════════════════════════════════════ */
.page-header   { margin-bottom: 0.6rem; }
.page-title    { color: #111827; font-size: 20px; font-weight: 700; letter-spacing: -0.3px; margin: 0 0 3px 0; }
.page-subtitle { color: #6B7280; font-size: 12px; margin: 0; }
.section-divider { height: 1px; background: #E5E7EB; margin: 1.2rem 0 1.4rem; }

/* ═══════════════════════════════════════════════
   KPI CARDS
═══════════════════════════════════════════════ */
.kpi-card {
    background: #FFFFFF;
    border: 1px solid #E5E7EB;
    border-radius: 12px;
    padding: 1.1rem 1.3rem 0.9rem;
    height: 100%;
    box-shadow: 0 1px 3px rgba(0,0,0,0.08);
}
.kpi-label {
    color: #6B7280;
    font-size: 11px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    margin-bottom: 0.4rem;
}
.kpi-value {
    color: #111827;
    font-size: 32px;
    font-weight: 700;
    line-height: 1.1;
    letter-spacing: -0.5px;
    margin-bottom: 0.6rem;
}
.kpi-delta {
    display: flex;
    align-items: center;
    gap: 4px;
    font-size: 12px;
    font-weight: 500;
    padding-top: 0.5rem;
    border-top: 1px solid #F3F4F6;
}
.kpi-delta.positive { color: #16A34A; }
.kpi-delta.negative { color: #DC2626; }
.kpi-delta.neutral  { color: #9CA3AF; }

/* ═══════════════════════════════════════════════
   CHART CARDS
═══════════════════════════════════════════════ */
[data-testid="stPlotlyChart"] {
    background: #FFFFFF !important;
    border: 1px solid #E5E7EB !important;
    border-radius: 12px !important;
    overflow: hidden !important;
    padding: 0 !important;
    box-shadow: 0 1px 3px rgba(0,0,0,0.06) !important;
}

/* ═══════════════════════════════════════════════
   DATAFRAMES / TABLES
═══════════════════════════════════════════════ */
[data-testid="stDataFrame"] {
    border-radius: 12px !important;
    overflow: hidden !important;
    border: 1px solid #E5E7EB !important;
    box-shadow: 0 1px 3px rgba(0,0,0,0.06) !important;
}
/* Column header row */
[data-testid="stDataFrame"] [role="columnheader"] {
    background-color: #F3F4F6 !important;
    color: #6B7280 !important;
    font-size: 11px !important;
    font-weight: 600 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.05em !important;
    border-bottom: 1px solid #E5E7EB !important;
    border-right: none !important;
}
/* Data cells */
[data-testid="stDataFrame"] [role="gridcell"] {
    font-size: 13px !important;
    color: #374151 !important;
    border-bottom: 1px solid #F9FAFB !important;
    border-right: none !important;
}
/* Alternating rows */
[data-testid="stDataFrame"] [role="row"]:nth-child(even) [role="gridcell"] {
    background-color: #F9FAFB !important;
}
[data-testid="stDataFrame"] [role="row"]:hover [role="gridcell"] {
    background-color: #EFF6FF !important;
}

/* ═══════════════════════════════════════════════
   INPUTS — TEXT, NUMBER, SELECT, SLIDER
═══════════════════════════════════════════════ */
[data-testid="stTextInput"] input,
[data-testid="stNumberInput"] input {
    border: 1px solid #D1D5DB !important;
    border-radius: 8px !important;
    color: #111827 !important;
    font-size: 13px !important;
    background: #FFFFFF !important;
    font-family: 'Inter', sans-serif !important;
    transition: border-color 0.12s, box-shadow 0.12s !important;
}
[data-testid="stTextInput"] input:focus,
[data-testid="stNumberInput"] input:focus {
    border-color: #2563EB !important;
    box-shadow: 0 0 0 3px rgba(37,99,235,0.1) !important;
    outline: none !important;
}
[data-testid="stSelectbox"] > div > div {
    border: 1px solid #D1D5DB !important;
    border-radius: 8px !important;
    background: #FFFFFF !important;
    font-size: 13px !important;
    color: #111827 !important;
}
[data-testid="stSlider"] [role="slider"] {
    background-color: #2563EB !important;
    border-color: #2563EB !important;
}
[data-testid="stSlider"] [data-testid="stSliderThumb"] {
    background-color: #2563EB !important;
}

/* ═══════════════════════════════════════════════
   FILTER PANEL & HELPERS
═══════════════════════════════════════════════ */
[data-testid="stVerticalBlockBorderWrapper"] {
    background-color: #FFFFFF !important;
    border: 1px solid #E5E7EB !important;
    border-radius: 12px !important;
    padding: 20px !important;
    box-shadow: 0 1px 3px rgba(0,0,0,0.06) !important;
}
.flbl {
    color: #9CA3AF;
    font-size: 11px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    margin: 0 0 8px 0;
    line-height: 1;
}
.fsep { height: 1px; background: #E5E7EB; margin: 14px 0 12px; }
.fval { color: #6B7280; font-size: 12px; margin: -2px 0 4px 0; }

/* ── Filter toggle button ── */
button[aria-label^="▼ Filter"],
button[aria-label^="▲ Filter"] {
    background-color: #FFFFFF !important;
    border: 1px solid #E5E7EB !important;
    border-radius: 8px !important;
    color: #374151 !important;
    font-size: 13px !important;
    font-weight: 500 !important;
    padding: 4px 14px !important;
    min-height: 0 !important;
    height: 34px !important;
    box-shadow: 0 1px 2px rgba(0,0,0,0.05) !important;
    transition: border-color 0.12s !important;
}
button[aria-label^="▼ Filter"]:hover,
button[aria-label^="▲ Filter"]:hover { border-color: #2563EB !important; color: #2563EB !important; }
button[aria-label^="▲ Filter"] {
    border-color: #2563EB !important;
    color: #2563EB !important;
    background-color: #EFF6FF !important;
}

/* ── Reset button ── */
button[aria-label="Reset"] {
    background: transparent !important;
    border: none !important;
    color: #9CA3AF !important;
    font-size: 11px !important;
    padding: 0 6px !important;
    min-height: 0 !important;
    height: 34px !important;
    box-shadow: none !important;
    text-decoration: underline;
}
button[aria-label="Reset"]:hover { color: #6B7280 !important; }

/* ── Multiselect inside filter bar ── */
[data-testid="stMultiSelect"] [data-baseweb="select"] {
    border-color: #E5E7EB !important;
    border-radius: 8px !important;
    font-size: 13px !important;
}
[data-testid="stMultiSelect"] [data-baseweb="tag"] {
    background-color: #EFF6FF !important;
    color: #2563EB !important;
    border-radius: 6px !important;
    font-size: 12px !important;
}

/* ── Select All / Clear (kept for compat) ── */
button[aria-label="Select All"], button[aria-label="Clear"] {
    background: transparent !important;
    border: none !important;
    color: #2563EB !important;
    font-size: 11px !important;
    padding: 0 4px !important;
    min-height: 0 !important;
    height: 20px !important;
    font-weight: 500 !important;
    box-shadow: none !important;
}
button[aria-label="Select All"]:hover, button[aria-label="Clear"]:hover {
    color: #1D4ED8 !important;
}

/* ── Checkboxes ── */
[data-testid="stVerticalBlockBorderWrapper"] .stCheckbox { margin-bottom: 2px !important; }
[data-testid="stVerticalBlockBorderWrapper"] .stCheckbox label {
    color: #111827 !important; font-size: 12px !important; gap: 6px !important;
}
[data-testid="stVerticalBlockBorderWrapper"] .stCheckbox [data-testid="stMarkdownContainer"] p {
    color: #111827 !important; font-size: 12px !important;
    margin: 0 !important; white-space: normal !important;
}
[data-testid="stVerticalBlockBorderWrapper"] input[type="checkbox"] { accent-color: #2563EB; }

/* ═══════════════════════════════════════════════
   PILLS — BEDROOMS, MAP LAYERS, ACTIVITY
═══════════════════════════════════════════════ */
button[aria-label="1bd"],  button[aria-label="2bd"],
button[aria-label="3bd"],  button[aria-label="4bd"],
button[aria-label="5+bd"],
button[aria-label="Scatter"],
button[aria-label="Heatmap"],
button[aria-label="Hexagon"] {
    background-color: #F3F4F6 !important;
    border: 1px solid #E5E7EB !important;
    border-radius: 20px !important;
    color: #6B7280 !important;
    font-size: 12px !important;
    font-weight: 500 !important;
    padding: 0 4px !important;
    width: 100% !important;
    min-height: 28px !important;
    height: 28px !important;
    line-height: 1 !important;
    box-shadow: none !important;
    transition: background-color 0.12s, border-color 0.12s, color 0.12s !important;
}
button[aria-label="1bd"]:hover,   button[aria-label="2bd"]:hover,
button[aria-label="3bd"]:hover,   button[aria-label="4bd"]:hover,
button[aria-label="5+bd"]:hover,
button[aria-label="Scatter"]:hover,
button[aria-label="Heatmap"]:hover,
button[aria-label="Hexagon"]:hover {
    background-color: #EFF6FF !important;
    border-color: #93C5FD !important;
    color: #2563EB !important;
}

/* ── Weekly activity pills ── */
button[aria-label^="New this week"],
button[aria-label^="Leased this week"] {
    background-color: #FFFFFF !important;
    border: 1px solid #D1D5DB !important;
    border-radius: 20px !important;
    color: #374151 !important;
    font-size: 12px !important;
    font-weight: 500 !important;
    min-height: 28px !important;
    height: 28px !important;
    line-height: 1 !important;
    box-shadow: none !important;
    padding: 0 10px !important;
}
button[aria-label^="New this week"]:hover    { border-color: #2563EB !important; color: #2563EB !important; }
button[aria-label^="Leased this week"]:hover { border-color: #16A34A !important; color: #16A34A !important; }

/* ═══════════════════════════════════════════════
   MAP
═══════════════════════════════════════════════ */
[data-testid="stDeckGlJsonChart"] {
    border-radius: 12px !important;
    overflow: hidden !important;
    border: 1px solid #E5E7EB !important;
    box-shadow: 0 1px 3px rgba(0,0,0,0.06) !important;
}
.map-legend {
    display: flex; gap: 14px; flex-wrap: wrap;
    align-items: center; margin-top: 4px;
}
.leg-item {
    display: inline-flex; align-items: center;
    gap: 5px; font-size: 12px; color: #374151; white-space: nowrap;
}
.leg-dot {
    display: inline-block; width: 10px; height: 10px;
    border-radius: 2px; flex-shrink: 0;
}
.map-count {
    color: #9CA3AF; font-size: 12px; font-weight: 500;
    text-align: right; padding-top: 20px;
}

/* ═══════════════════════════════════════════════
   RENT CALCULATOR BUTTON
═══════════════════════════════════════════════ */
button[aria-label="Calculate Rent Range"] {
    background-color: #2563EB !important;
    color: #FFFFFF !important;
    font-weight: 700 !important;
    border-radius: 8px !important;
    border: none !important;
    width: 100% !important;
    box-shadow: 0 1px 3px rgba(37,99,235,0.25) !important;
    transition: background-color 0.12s, box-shadow 0.12s !important;
}
button[aria-label="Calculate Rent Range"]:hover {
    background-color: #1D4ED8 !important;
    box-shadow: 0 2px 6px rgba(37,99,235,0.35) !important;
}

/* ═══════════════════════════════════════════════
   ALERTS, EXPANDERS
═══════════════════════════════════════════════ */
[data-testid="stAlert"] {
    border-radius: 10px !important;
    font-size: 13px !important;
    font-family: 'Inter', sans-serif !important;
}
[data-testid="stExpander"] {
    border: 1px solid #E5E7EB !important;
    border-radius: 12px !important;
    background: #FFFFFF !important;
    box-shadow: 0 1px 3px rgba(0,0,0,0.06) !important;
    overflow: hidden !important;
}
</style>
""", unsafe_allow_html=True)


# ── Plotly light theme ────────────────────────────────────────────────────────
def _chart_layout(title: str = "", **overrides) -> dict:
    layout = dict(
        plot_bgcolor="white",
        paper_bgcolor="white",
        font=dict(family="Inter, sans-serif", color="#111827", size=12),
        title=dict(
            text=title.upper(),
            font=dict(size=11, color="#9ca3af", family="Inter, sans-serif"),
            x=0.015, xanchor="left", pad=dict(l=4, t=6),
        ),
        xaxis=dict(
            gridcolor="#f3f4f6", linecolor="#e5e7eb", zeroline=False,
            tickfont=dict(color="#6b7280", size=11),
            title_font=dict(color="#6b7280", size=11),
        ),
        yaxis=dict(
            gridcolor="#f3f4f6", linecolor="#e5e7eb", zeroline=False,
            tickfont=dict(color="#6b7280", size=11),
            title_font=dict(color="#6b7280", size=11),
        ),
        margin=dict(l=8, r=8, t=44, b=8),
        legend=dict(font=dict(color="#6b7280", size=11), bgcolor="rgba(0,0,0,0)", bordercolor="#e5e7eb"),
        hoverlabel=dict(bgcolor="#ffffff", bordercolor="#e1e4e8", font=dict(color="#111827", size=12)),
    )
    layout.update(overrides)
    return layout


# ── KPI card HTML ─────────────────────────────────────────────────────────────
def kpi_card(label: str, value: str, delta: str = "—", delta_class: str = "neutral") -> str:
    icon = "▲ " if delta_class == "positive" else ("▼ " if delta_class == "negative" else "")
    return f"""<div class="kpi-card">
    <div class="kpi-label">{label}</div>
    <div class="kpi-value">{value}</div>
    <div class="kpi-delta {delta_class}">{icon}{delta}</div>
</div>"""


# ── Data loading ──────────────────────────────────────────────────────────────
_CSV_COLUMNS = [
    "scraped_date", "scraped_time", "event",
    "company", "address", "property_type",
    "rent", "bedrooms", "bathrooms", "sqft",
    "pets", "parking", "laundry", "utilities_included",
    "available", "url", "lat", "lng",
]


def _get_secret(key):
    """Read from st.secrets (Streamlit Cloud) with fallback to env vars (local)."""
    try:
        return st.secrets[key]
    except (KeyError, FileNotFoundError):
        pass
    try:
        return st.secrets["secrets"][key]
    except (KeyError, FileNotFoundError):
        pass
    return os.environ.get(key)


@st.cache_data(ttl=3600)
def load_data():
    _url = _get_secret("SUPABASE_URL")
    _key = _get_secret("SUPABASE_KEY")
    if not _url or not _key:
        try:
            _available = list(st.secrets.keys())
        except Exception:
            _available = []
        st.error(
            "Missing Supabase credentials. "
            "Add **SUPABASE_URL** and **SUPABASE_KEY** to your Streamlit secrets. "
            f"(URL found: {bool(_url)}, Key found: {bool(_key)}, "
            f"Keys in st.secrets: {_available})"
        )
        st.stop()
    _supabase = create_client(_url, _key)
    result = _supabase.table("listings").select("*").execute()
    if not result.data:
        st.warning("The Supabase listings table is empty. Run the scraper or upload your CSV data to populate it.")
        st.stop()
    df = pd.DataFrame(result.data)
    df["rent"]         = pd.to_numeric(df["rent"],         errors="coerce")
    df["bedrooms"]     = pd.to_numeric(df["bedrooms"],     errors="coerce")
    df["scraped_date"] = pd.to_datetime(df["scraped_date"], errors="coerce").dt.normalize()
    df["lat"]          = pd.to_numeric(df["lat"],          errors="coerce")
    df["lng"]          = pd.to_numeric(df["lng"],          errors="coerce")
    df = df[df["rent"] > 0]
    df = df[df["bedrooms"] <= 7]
    return df


@st.cache_data
def load_city_addresses():
    try:
        cdf = pd.read_csv("data/city_addresses.csv")
    except FileNotFoundError:
        return pd.DataFrame(columns=["Full Street Address", "Latitude", "Longitude", "_norm"])
    cdf["Latitude"]  = pd.to_numeric(cdf["Latitude"],  errors="coerce")
    cdf["Longitude"] = pd.to_numeric(cdf["Longitude"], errors="coerce")
    cdf = cdf.dropna(subset=["Latitude", "Longitude"])
    cdf["_norm"] = cdf["Full Street Address"].str.upper().str.strip()
    return cdf


_ABBREV = {
    "STREET": "ST", "AVENUE": "AVE", "COURT": "CT", "DRIVE": "DR",
    "BOULEVARD": "BLVD", "LANE": "LN", "PLACE": "PL", "ROAD": "RD",
    "CIRCLE": "CIR", "TERRACE": "TER", "TRAIL": "TRL", "HIGHWAY": "HWY",
}

def _norm_addr(addr: str) -> str:
    addr = addr.upper().strip()
    addr = re.sub(r"\s+(APT|UNIT|SUITE|STE|#)\s*\S*", "", addr)
    for full, abbr in _ABBREV.items():
        addr = re.sub(rf"\b{full}\b", abbr, addr)
    return addr.strip()

def _geocode_addr(addr: str, cdf: pd.DataFrame):
    norm = _norm_addr(addr)
    m = cdf[cdf["_norm"].str.startswith(norm)]
    if m.empty:
        m = cdf[cdf["_norm"].str.contains(re.escape(norm), regex=True, na=False)]
    if m.empty:
        return None, None
    row = m.iloc[0]
    return float(row["Latitude"]), float(row["Longitude"])


df = load_data()
latest_date    = df["scraped_date"].max()
_city_addr_df  = load_city_addresses()

# ── Dataset metadata ──────────────────────────────────────────────────────────
_all_companies  = sorted(df["company"].dropna().unique())
_all_prop_types = sorted(df["property_type"].dropna().unique())
_rent_lo        = int(df["rent"].min())
_rent_hi        = int(df["rent"].max())
_avail_series   = pd.to_datetime(df["available"], errors="coerce").dropna()
_avail_lo       = _avail_series.min().date()
_avail_hi       = _avail_series.max().date()
_PILLS          = [("1", 1), ("2", 2), ("3", 3), ("4", 4), ("5+", 5)]
_ALL_BD_LABELS  = frozenset(lbl for lbl, _ in _PILLS)


# ── Session state init ────────────────────────────────────────────────────────
def _init_state():
    ss = st.session_state
    if "filter_bar_open" not in ss:
        ss.filter_bar_open = False
    if "flt_bedrooms" not in ss:
        ss.flt_bedrooms = set()   # empty = no filter; add labels to restrict
    if "flt_rent_range" not in ss:
        ss.flt_rent_range = (_rent_lo, _rent_hi)
    if "flt_avail_range" not in ss:
        ss.flt_avail_range = (_avail_lo, _avail_hi)
    if "map_layer" not in ss:
        ss.map_layer = "Scatter"
    if "map_show_new_week" not in ss:
        ss.map_show_new_week = False
    if "map_show_leased_week" not in ss:
        ss.map_show_leased_week = False
    if "map_show_rings" not in ss:
        ss.map_show_rings = True
    if "map_show_campus" not in ss:
        ss.map_show_campus = True
    if "act_filter" not in ss:
        ss.act_filter = "all"
    if "calc_result" not in ss:
        ss.calc_result = None
    if "active_page" not in ss:
        ss.active_page = "Overview"
    if "flt_companies" not in ss:
        ss.flt_companies = []          # empty list = no filter = show all companies
    if "overview_expanded_kpi" not in ss:
        ss.overview_expanded_kpi = None
    for pt in _all_prop_types:
        if f"pt_{pt}" not in ss:
            ss[f"pt_{pt}"] = True


_init_state()


# ── Active filter count ───────────────────────────────────────────────────────
def _active_count() -> int:
    ss = st.session_state
    n = 0
    if ss.get("flt_companies", []): n += 1
    if ss.flt_bedrooms:                                                                    n += 1
    lo_r, hi_r = ss.flt_rent_range
    if int(lo_r) != _rent_lo or int(hi_r) != _rent_hi:                                   n += 1
    lo_a, hi_a = ss.flt_avail_range
    if lo_a != _avail_lo or hi_a != _avail_hi:                                            n += 1
    if {pt for pt in _all_prop_types if ss.get(f"pt_{pt}", True)} != set(_all_prop_types): n += 1
    return n


# ── Reset all filters ─────────────────────────────────────────────────────────
def _reset_filters():
    ss = st.session_state
    ss.flt_bedrooms    = set()
    ss.flt_rent_range  = (_rent_lo, _rent_hi)
    ss.flt_avail_range = (_avail_lo, _avail_hi)
    ss.flt_companies = []
    for pt in _all_prop_types:
        ss[f"pt_{pt}"] = True


# ── get_filtered_df ───────────────────────────────────────────────────────────
def get_filtered_df(source: pd.DataFrame, skip_company: bool = False) -> pd.DataFrame:
    ss = st.session_state
    r = source.copy()

    if not skip_company:
        sel_cos = set(ss.get("flt_companies") or [])
        if sel_cos:
            r = r[r["company"].isin(sel_cos)]

    active_bds = set(ss.flt_bedrooms)
    if active_bds:   # non-empty = restrict to selected bedroom counts
        allowed: set = set()
        for lbl, min_val in _PILLS:
            if lbl in active_bds:
                allowed.update(range(5, 12) if lbl == "5+" else [min_val])
        r = r[r["bedrooms"].isin(allowed)]

    lo_r, hi_r = int(ss.flt_rent_range[0]), int(ss.flt_rent_range[1])
    if lo_r != _rent_lo or hi_r != _rent_hi:
        r = r[r["rent"].between(lo_r, hi_r)]

    lo_a, hi_a = ss.flt_avail_range[0], ss.flt_avail_range[1]
    if lo_a != _avail_lo or hi_a != _avail_hi:
        avail = pd.to_datetime(r["available"], errors="coerce")
        r = r[avail.isna() | avail.between(pd.Timestamp(lo_a), pd.Timestamp(hi_a))]

    sel_pts = {pt for pt in _all_prop_types if ss.get(f"pt_{pt}", True)}
    if 0 < len(sel_pts) < len(_all_prop_types):
        r = r[r["property_type"].isin(sel_pts)]

    return r


# ── Callbacks ─────────────────────────────────────────────────────────────────
def _toggle_bd(val: str):
    bds = st.session_state.flt_bedrooms
    bds.discard(val) if val in bds else bds.add(val)


def _co_select_all():
    for co in _all_companies:
        st.session_state[f"co_{co}"] = True


def _co_clear_all():
    for co in _all_companies:
        st.session_state[f"co_{co}"] = False


def _set_map_layer(val: str):
    st.session_state.map_layer = val


def _toggle_map_new_week():
    st.session_state.map_show_new_week = not st.session_state.get("map_show_new_week", False)


def _toggle_map_leased_week():
    st.session_state.map_show_leased_week = not st.session_state.get("map_show_leased_week", False)


def _set_act_filter(val: str):
    st.session_state.act_filter = val


def _set_co(co: str):
    st.session_state.selected_company = co


def _set_page(page: str):
    st.session_state.active_page = page


def _fd(d) -> str:
    """Format a date as 'Aug 1, 2026' without zero-padded day (cross-platform)."""
    import datetime
    if isinstance(d, datetime.datetime):
        d = d.date()
    return d.strftime(f"%b {d.day}, %Y")


# ── Filter bar ────────────────────────────────────────────────────────────────
def render_filter_bar():
    ss = st.session_state
    n = _active_count()
    badge = f" ({n})" if n > 0 else ""

    btn_col, rst_col, _ = st.columns([1, 1, 10])
    with btn_col:
        open_label = f"▲ Filter{badge}" if ss.filter_bar_open else f"▼ Filter{badge}"
        if st.button(open_label, key="filter_toggle"):
            ss.filter_bar_open = not ss.filter_bar_open
    with rst_col:
        if n > 0:
            st.button("Reset", key="btn_reset", on_click=_reset_filters)

    if not ss.filter_bar_open:
        return

    with st.container(border=True):
        col1, col2, col3 = st.columns([5, 3, 4])

        # ── Col 1: Company + Property Type ───────────────────────────────────
        with col1:
            st.markdown('<div class="flbl">Company</div>', unsafe_allow_html=True)
            st.multiselect(
                "flt_companies",
                options=_all_companies,
                key="flt_companies",
                label_visibility="collapsed",
                placeholder="All companies — select to filter…",
            )
            st.markdown('<div class="fsep"></div>', unsafe_allow_html=True)
            st.markdown('<div class="flbl">Property Type</div>', unsafe_allow_html=True)
            pt_cols = st.columns(len(_all_prop_types))
            for c, pt in zip(pt_cols, _all_prop_types):
                with c:
                    st.checkbox(pt, key=f"pt_{pt}")

        # ── Col 2: Bedrooms + Availability ───────────────────────────────────
        with col2:
            st.markdown('<div class="flbl">Bedrooms</div>', unsafe_allow_html=True)

            # Selected pills — inject blue override before buttons render
            sel_css = "".join(
                f'button[aria-label="{lbl}bd"]{{background-color:#2563eb!important;'
                f'border-color:#2563eb!important;color:#ffffff!important;font-weight:600!important;}}'
                for lbl, _ in _PILLS if lbl in ss.flt_bedrooms
            )
            if sel_css:
                st.markdown(f"<style>{sel_css}</style>", unsafe_allow_html=True)

            pcols = st.columns(len(_PILLS))
            for pc, (lbl, _val) in zip(pcols, _PILLS):
                with pc:
                    st.button(f"{lbl}bd", key=f"pill_{lbl}", on_click=_toggle_bd, args=(lbl,))

            st.markdown('<div class="fsep"></div>', unsafe_allow_html=True)
            st.markdown('<div class="flbl">Availability</div>', unsafe_allow_html=True)
            # No format= param: avoids the "%b %2026" rendering bug in Streamlit 1.57
            st.slider(
                "avail_range",
                min_value=_avail_lo,
                max_value=_avail_hi,
                key="flt_avail_range",
                label_visibility="collapsed",
            )
            lo_a, hi_a = ss.flt_avail_range
            st.markdown(f'<div class="fval">{_fd(lo_a)} → {_fd(hi_a)}</div>', unsafe_allow_html=True)

        # ── Col 3: Rent ───────────────────────────────────────────────────────
        with col3:
            st.markdown('<div class="flbl">Rent Range</div>', unsafe_allow_html=True)
            st.slider(
                "rent_range",
                min_value=_rent_lo,
                max_value=_rent_hi,
                key="flt_rent_range",
                label_visibility="collapsed",
            )
            lo_r, hi_r = int(ss.flt_rent_range[0]), int(ss.flt_rent_range[1])
            st.markdown(f'<div class="fval">${lo_r:,} → ${hi_r:,}</div>', unsafe_allow_html=True)




# ── KPI row ───────────────────────────────────────────────────────────────────
def _kpi_delta(diff: float, unit: str, invert: bool = False):
    """Return (delta_str, delta_class) for a numeric change."""
    if diff == 0:
        return "No change", "neutral"
    cls = ("negative" if invert else "positive") if diff > 0 else ("positive" if invert else "negative")
    return f"{abs(diff):,.0f} {unit}", cls


def render_kpi_row(latest_df: pd.DataFrame, prev_df: pd.DataFrame,
                   active_df: pd.DataFrame = None, prev_active_df: pd.DataFrame = None):
    _active  = active_df      if active_df      is not None else latest_df
    _pactive = prev_active_df if prev_active_df is not None else prev_df

    cur_listings = len(_active)
    prv_listings  = len(_pactive)
    cur_cos = _active["company"].nunique() if cur_listings else 0
    prv_cos  = _pactive["company"].nunique() if prv_listings else 0

    listings_delta, listings_dc = _kpi_delta(cur_listings - prv_listings, "listings")
    cos_delta, cos_dc           = _kpi_delta(cur_cos - prv_cos, "companies")

    def _avg_rpb(frame):
        rpb = frame["rent"] / frame["bedrooms"].replace(0, float("nan"))
        return rpb.mean()

    cur_rpb = _avg_rpb(_active)  if cur_listings else float("nan")
    prv_rpb = _avg_rpb(_pactive) if prv_listings  else float("nan")

    import math as _math
    if cur_listings and prv_listings and not _math.isnan(cur_rpb) and not _math.isnan(prv_rpb):
        rpb_diff = cur_rpb - prv_rpb
        if rpb_diff == 0:
            rpb_delta, rpb_dc = "No change", "neutral"
        else:
            rpb_delta = f"${abs(rpb_diff):,.0f}/bed"
            rpb_dc    = "negative" if rpb_diff > 0 else "positive"
    else:
        rpb_delta, rpb_dc = "—", "neutral"

    col1, col2, col3, col4 = st.columns(4)
    metrics = [
        ("Active listings",    f"{cur_listings:,}",                                                      listings_delta, listings_dc),
        ("Avg rent / bed",     f"${cur_rpb:,.0f}" if cur_listings and not _math.isnan(cur_rpb) else "—", rpb_delta,      rpb_dc),
        ("Avg days listed",    "—",                                                                       "—",            "neutral"),
        ("Companies tracked",  f"{cur_cos:,}",                                                            cos_delta,      cos_dc),
    ]
    for col, (label, value, delta, dc) in zip([col1, col2, col3, col4], metrics):
        with col:
            st.markdown(kpi_card(label, value, delta, dc), unsafe_allow_html=True)


# ── KPI history ───────────────────────────────────────────────────────────────
@st.cache_data
def compute_kpi_history(_df):
    """For each scrape date, compute active listings, avg rent/bed, avg days listed, companies."""
    dates = sorted(_df["scraped_date"].dropna().unique())
    rows = []
    for d in dates:
        sub = _df[_df["scraped_date"] <= d]
        url_last = sub.sort_values("scraped_date").groupby("url").last().reset_index()
        active = url_last[url_last["event"] != "removed"]
        n = len(active)
        rpb = (active["rent"] / active["bedrooms"].replace(0, float("nan"))).mean() if n else float("nan")
        first_seen = sub.groupby("url")["scraped_date"].min().rename("first_seen")
        dom_series = active.join(first_seen, on="url", how="left")["first_seen"]
        avg_dom = ((pd.Timestamp(d) - dom_series).dt.days).mean() if n else float("nan")
        rows.append({
            "date":      pd.Timestamp(d),
            "active":    n,
            "rpb":       rpb,
            "dom":       avg_dom,
            "companies": active["company"].nunique() if n else 0,
        })
    return pd.DataFrame(rows)


# ── Campus constants (shared by Map and Companies tabs) ───────────────────────
CAMPUS_LAT = 39.179416
CAMPUS_LNG = -86.513358
IU_CAMPUS_POLYGON = [[
    [-86.514628, 39.193551], [-86.514611, 39.195748],
    [-86.509885, 39.195710], [-86.509893, 39.196456],
    [-86.509731, 39.196478], [-86.508206, 39.196456],
    [-86.507896, 39.196556], [-86.505168, 39.193499],
    [-86.500477, 39.193438], [-86.495907, 39.193414],
    [-86.495797, 39.192684], [-86.495750, 39.189119],
    [-86.491075, 39.189112], [-86.491036, 39.186322],
    [-86.490999, 39.183775], [-86.490979, 39.182364],
    [-86.490585, 39.182238], [-86.490260, 39.176393],
    [-86.495486, 39.175992], [-86.495368, 39.171468],
    [-86.500121, 39.171545], [-86.503995, 39.171554],
    [-86.506417, 39.171731], [-86.507215, 39.171413],
    [-86.507213, 39.170511], [-86.507187, 39.168894],
    [-86.509459, 39.167573], [-86.509444, 39.165757],
    [-86.509412, 39.164271], [-86.510910, 39.164270],
    [-86.514209, 39.164266], [-86.517429, 39.164284],
    [-86.521062, 39.164262], [-86.525215, 39.164284],
    [-86.526910, 39.164314], [-86.526919, 39.165558],
    [-86.526944, 39.167524], [-86.526959, 39.168509],
    [-86.523494, 39.169483], [-86.523519, 39.171465],
    [-86.523520, 39.172537], [-86.523538, 39.174140],
    [-86.523560, 39.175201], [-86.525861, 39.175235],
    [-86.525978, 39.177210], [-86.525982, 39.178005],
    [-86.527059, 39.179027], [-86.528309, 39.179316],
    [-86.528343, 39.184138], [-86.528343, 39.185236],
    [-86.525042, 39.186287], [-86.523339, 39.186276],
    [-86.521465, 39.186194], [-86.518713, 39.185811],
    [-86.517154, 39.185458], [-86.515740, 39.185035],
    [-86.514858, 39.184726], [-86.514518, 39.186273],
    [-86.513747, 39.187045], [-86.513795, 39.188620],
    [-86.513813, 39.189223], [-86.514515, 39.189227],
    [-86.514545, 39.189821], [-86.514573, 39.190623],
    [-86.514578, 39.192256], [-86.514628, 39.193551],
]]

# ── Sidebar navigation ────────────────────────────────────────────────────────
_NAV_PAGES = [
    "Overview",
    "Pricing",
    "Map",
    "Forecast",
    "Companies",
]

_active_page = st.session_state.active_page

# Inject active highlight — aria-label is exactly the page name (no emoji prefix)
_nav_label_esc = _active_page.replace('"', '\\"')
st.sidebar.markdown(
    f'<style>[data-testid="stSidebar"] button[aria-label="{_nav_label_esc}"]'
    f'{{background:#EFF6FF!important;color:#2563EB!important;'
    f'border-left-color:#2563EB!important;font-weight:600!important;}}</style>',
    unsafe_allow_html=True,
)

with st.sidebar:
    st.image("images/RentRadarLogo1.png", width=155)
    st.markdown(
        '<div style="height:1px;background:#E5E7EB;margin:14px -1rem 6px;"></div>',
        unsafe_allow_html=True,
    )
    for _pg in _NAV_PAGES:
        st.button(
            _pg, key=f"nav_{_pg}",
            on_click=_set_page, args=(_pg,),
            use_container_width=True,
        )
    st.markdown(
        '<div style="height:1px;background:#E5E7EB;margin:10px -1rem 12px;"></div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        f'<div style="color:#9CA3AF;font-size:11px;line-height:1.8;padding:0 4px;">'
        f'<span style="color:#6B7280;font-weight:600;">Bloomington, IN</span><br>'
        f'Last scrape: {latest_date.strftime("%b")} {latest_date.day}, {latest_date.strftime("%Y")}'
        f'</div>',
        unsafe_allow_html=True,
    )

# ── Data prep (filter values already in session state from last interaction) ──
filtered  = get_filtered_df(df)
latest_df = filtered[filtered["scraped_date"] == latest_date]

_sorted_dates = sorted(filtered["scraped_date"].dropna().unique())
_prev_date    = _sorted_dates[-2] if len(_sorted_dates) >= 2 else None
prev_df       = filtered[filtered["scraped_date"] == _prev_date] if _prev_date is not None else pd.DataFrame(columns=df.columns)

# All currently active listings: most recent row per URL, excluding removed
_url_last  = filtered.sort_values("scraped_date").groupby("url").last().reset_index()
active_df  = _url_last[_url_last["event"] != "removed"]

# Previous active count (same logic but excluding the latest scrape date)
_url_last_prev = (
    filtered[filtered["scraped_date"] < latest_date]
    .sort_values("scraped_date").groupby("url").last().reset_index()
)
prev_active_df = _url_last_prev[_url_last_prev["event"] != "removed"]


if _active_page == "Overview":
    render_filter_bar()
    render_kpi_row(latest_df, prev_df, active_df, prev_active_df)

    # ── KPI history toggle buttons ────────────────────────────────────────────
    _KPI_DEFS = [
        ("active",    "Active listings"),
        ("rpb",       "Avg rent / bed"),
        ("dom",       "Avg days listed"),
        ("companies", "Companies tracked"),
    ]
    st.markdown("""<style>
    button[aria-label^="▾ Active listings"], button[aria-label^="▴ Active listings"],
    button[aria-label^="▾ Avg rent / bed"], button[aria-label^="▴ Avg rent / bed"],
    button[aria-label^="▾ Avg days listed"], button[aria-label^="▴ Avg days listed"],
    button[aria-label^="▾ Companies tracked"], button[aria-label^="▴ Companies tracked"] {
        background: transparent !important; border: none !important;
        color: #9CA3AF !important; font-size: 11px !important;
        padding: 1px 0 !important; min-height: 0 !important; height: 22px !important;
        box-shadow: none !important; width: 100% !important;
        text-align: center !important; text-decoration: underline !important;
    }
    button[aria-label^="▴ "] { color: #2563EB !important; }
    </style>""", unsafe_allow_html=True)

    _hc1, _hc2, _hc3, _hc4 = st.columns(4)
    for _hcol, (_hkey, _hlabel) in zip([_hc1, _hc2, _hc3, _hc4], _KPI_DEFS):
        with _hcol:
            _is_open = st.session_state.overview_expanded_kpi == _hkey
            _btn_lbl = f"▴ {_hlabel}" if _is_open else f"▾ {_hlabel}"
            if st.button(_btn_lbl, key=f"kpi_hist_{_hkey}"):
                st.session_state.overview_expanded_kpi = None if _is_open else _hkey

    _expanded_kpi = st.session_state.overview_expanded_kpi
    if _expanded_kpi:
        _hist_df = compute_kpi_history(filtered)
        _kpi_chart_meta = {
            "active":    ("Active Listings Over Time",   "active",    "Active Listings"),
            "rpb":       ("Avg Rent / Bed Over Time",    "rpb",       "Avg $/bed"),
            "dom":       ("Avg Days Listed Over Time",   "dom",       "Days"),
            "companies": ("Companies Tracked Over Time", "companies", "Companies"),
        }
        _cht_title, _cht_col, _cht_ylabel = _kpi_chart_meta[_expanded_kpi]
        _hist_plot = _hist_df.dropna(subset=[_cht_col])
        if not _hist_plot.empty:
            _fig_hist = px.line(
                _hist_plot, x="date", y=_cht_col,
                labels={"date": "", _cht_col: _cht_ylabel},
                color_discrete_sequence=["#2563eb"],
            )
            _fig_hist.update_traces(mode="lines+markers", marker=dict(size=4))
            _fig_hist.update_layout(
                **_chart_layout(_cht_title, height=240),
            )
            if _cht_col == "rpb":
                _fig_hist.update_layout(yaxis=dict(tickprefix="$"))
            st.plotly_chart(_fig_hist, use_container_width=True)

    st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)

    # Clean data for rent chart — same three filters as Pricing Intelligence
    _ov = latest_df[latest_df["rent"].between(400, 12_000)].copy()
    _ov_avail   = pd.to_datetime(_ov["available"], errors="coerce")
    _ov_med     = _ov.groupby("bedrooms")["rent"].median()
    _ov_thresh  = _ov["bedrooms"].map(_ov_med) * 0.6
    _ov_soon    = _ov_avail < (pd.Timestamp.now().normalize() + pd.Timedelta(days=60))
    _ov         = _ov[~(_ov_soon & (_ov["rent"] < _ov_thresh))]
    _ov_counts  = _ov["bedrooms"].value_counts()
    _ov_clean   = _ov[_ov["bedrooms"].isin(_ov_counts[_ov_counts >= 5].index)]

    avg_rent = _ov_clean.groupby("bedrooms")["rent"].mean().reset_index()
    fig1 = px.bar(
        avg_rent, x="bedrooms", y="rent",
        labels={"bedrooms": "Bedrooms", "rent": "Avg rent ($)"},
        color_discrete_sequence=["#2563eb"],
        text=avg_rent["rent"].apply(lambda v: f"${v:,.0f}"),
    )
    fig1.update_traces(textposition="outside", textfont=dict(size=11, color="#374151"))
    fig1.update_layout(**_chart_layout("Average Rent by Bedroom Count"), showlegend=False)

    company_counts = (
        active_df.groupby("company").size()
        .reset_index(name="listings").sort_values("listings")
    )
    fig2 = px.bar(
        company_counts, x="listings", y="company", orientation="h",
        labels={"listings": "Listings", "company": ""},
        color_discrete_sequence=["#2563eb"],
        text="listings",
    )
    fig2.update_traces(textposition="outside", textfont=dict(size=11, color="#374151"))
    fig2.update_layout(**_chart_layout("Active Listings by Company"))

    chart_col1, chart_col2 = st.columns(2)
    with chart_col1:
        st.plotly_chart(fig1)
    with chart_col2:
        st.plotly_chart(fig2)

    # ── Recent Activity ───────────────────────────────────────────────────────
    st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)

    _act_filter = st.session_state.act_filter
    _APILLS = [("All", "all", "#2563eb"), ("New", "new", "#1d4ed8"),
               ("Removed", "removed", "#b91c1c"), ("Price", "price_change", "#b45309")]
    _apill_base = (
        "background-color:#f3f4f6!important;border:1px solid #e5e7eb!important;"
        "border-radius:20px!important;color:#6b7280!important;font-size:11px!important;"
        "font-weight:600!important;padding:0 12px!important;min-height:26px!important;"
        "height:26px!important;line-height:1!important;box-shadow:none!important;"
    )
    _apill_css = "".join(
        f'button[aria-label="{lbl}"]{{' + _apill_base + "}"
        for lbl, _, _ in _APILLS
    )
    for lbl, key, clr in _APILLS:
        if key == _act_filter:
            _apill_css += (
                f'button[aria-label="{lbl}"]{{background-color:{clr}!important;'
                f'border-color:{clr}!important;color:#ffffff!important;}}'
            )
    st.markdown(f"<style>{_apill_css}</style>", unsafe_allow_html=True)

    _ap1, _ap2, _ap3, _ap4, _, _act_win_col = st.columns([0.6, 0.6, 0.9, 0.7, 6, 1.2])
    for _col, (lbl, key, _clr) in zip([_ap1, _ap2, _ap3, _ap4], _APILLS):
        with _col:
            st.button(lbl, key=f"act_f_{key}", on_click=_set_act_filter, args=(key,))
    with _act_win_col:
        act_days = st.selectbox(
            "act_window", [1, 7],
            format_func=lambda d: "Last 1d" if d == 1 else "Last 7d",
            label_visibility="collapsed", key="act_days",
        )

    _act_cutoff = (pd.Timestamp.now() - pd.Timedelta(days=act_days)).normalize()
    _act_cols   = ["scraped_date", "address", "company", "bedrooms", "rent", "available"]

    _new_act = filtered[
        (filtered["event"] == "new") & (filtered["scraped_date"] >= _act_cutoff)
    ][_act_cols].copy()
    _new_act["_type"] = "new"
    _new_act["_old_rent"] = pd.NA

    _rem_raw = filtered[
        (filtered["event"] == "removed") & (filtered["scraped_date"] >= _act_cutoff)
    ].copy()
    # Keep only the most recent removal per URL — the scraper bug could write
    # duplicate "removed" rows for the same listing across consecutive runs.
    _rem_raw = _rem_raw.sort_values("scraped_date").groupby("url", as_index=False).last()
    _rem_act = _rem_raw[_act_cols].copy()
    _rem_act["_type"] = "removed"
    _rem_act["_old_rent"] = pd.NA

    _fsorted = filtered.sort_values(["url", "scraped_date"]).copy()
    _fsorted["_prev_rent"] = _fsorted.groupby("url")["rent"].shift(1)
    _pc_act = _fsorted[
        (_fsorted["scraped_date"] >= _act_cutoff) &
        (_fsorted["rent"] != _fsorted["_prev_rent"]) &
        _fsorted["_prev_rent"].notna()
    ][_act_cols + ["_prev_rent"]].copy()
    _pc_act.rename(columns={"_prev_rent": "_old_rent"}, inplace=True)
    _pc_act["_type"] = "price_change"

    activity = (
        pd.concat([_new_act, _rem_act, _pc_act], ignore_index=True)
        .sort_values("scraped_date", ascending=False)
    )

    if _act_filter != "all":
        activity = activity[activity["_type"] == _act_filter]

    activity = activity.head(150)

    if activity.empty:
        st.markdown(
            '<p style="color:#9ca3af;font-size:13px;">No activity recorded in this period.</p>',
            unsafe_allow_html=True,
        )
    else:
        _BADGE = {
            "new":          ("NEW",     "#dbeafe", "#1d4ed8"),
            "removed":      ("REMOVED", "#fee2e2", "#b91c1c"),
            "price_change": ("PRICE",   "#fef3c7", "#b45309"),
        }

        rows_html = []
        for _, row in activity.iterrows():
            typ        = row["_type"]
            lbl, bg, fg = _BADGE.get(typ, ("—", "#f3f4f6", "#6b7280"))
            addr       = str(row["address"]) if pd.notna(row["address"]) else "—"
            addr_short = addr[:48] + "…" if len(addr) > 48 else addr
            company    = str(row["company"]) if pd.notna(row["company"]) else "—"
            beds       = f"{int(row['bedrooms'])} bd" if pd.notna(row["bedrooms"]) else "—"
            d          = row["scraped_date"]
            date_s     = f"{d.strftime('%b')} {d.day}" if pd.notna(d) else "—"
            _av_raw    = row.get("available")
            _av_dt     = pd.to_datetime(_av_raw, errors="coerce") if pd.notna(_av_raw) else pd.NaT
            avail_s    = f"{_av_dt.strftime('%b')} {_av_dt.day}, {_av_dt.strftime('%Y')}" if not pd.isna(_av_dt) else "—"

            old_r = row.get("_old_rent")
            if typ == "price_change" and pd.notna(old_r):
                new_r  = int(row["rent"])
                old_r  = int(old_r)
                diff   = new_r - old_r
                arrow  = "▲" if diff > 0 else "▼"
                clr    = "#dc2626" if diff > 0 else "#16a34a"
                rent_s = (
                    f'<span style="color:#9ca3af;font-size:11px;text-decoration:line-through;">'
                    f'${old_r:,}</span>&nbsp;'
                    f'<span style="color:{clr};font-size:13px;font-weight:600;">'
                    f'{arrow}&nbsp;${new_r:,}/mo</span>'
                )
            elif pd.notna(row["rent"]):
                rent_s = f'<span style="color:#111827;font-size:13px;font-weight:500;">${int(row["rent"]):,}/mo</span>'
            else:
                rent_s = '<span style="color:#9ca3af;">—</span>'

            rows_html.append(
                f'<div style="display:flex;align-items:center;gap:12px;padding:9px 16px;'
                f'border-bottom:1px solid #f9fafb;">'
                f'<span style="background:{bg};color:{fg};font-size:10px;font-weight:700;'
                f'padding:3px 8px;border-radius:10px;min-width:64px;text-align:center;'
                f'letter-spacing:0.05em;flex-shrink:0;">{lbl}</span>'
                f'<span style="flex:2;color:#111827;font-size:13px;overflow:hidden;'
                f'text-overflow:ellipsis;white-space:nowrap;" title="{addr}">{addr_short}</span>'
                f'<span style="flex:1;color:#6b7280;font-size:12px;overflow:hidden;'
                f'text-overflow:ellipsis;white-space:nowrap;">{company}</span>'
                f'<span style="color:#9ca3af;font-size:12px;white-space:nowrap;'
                f'min-width:32px;">{beds}</span>'
                f'<div style="white-space:nowrap;min-width:130px;text-align:right;">{rent_s}</div>'
                f'<span style="color:#6b7280;font-size:12px;white-space:nowrap;'
                f'min-width:90px;text-align:right;">📅 {avail_s}</span>'
                f'<span style="color:#9ca3af;font-size:11px;white-space:nowrap;'
                f'min-width:38px;text-align:right;">{date_s}</span>'
                f'</div>'
            )

        n_new_s = (activity["_type"] == "new").sum()
        n_rem_s = (activity["_type"] == "removed").sum()
        n_pc_s  = (activity["_type"] == "price_change").sum()

        summary_parts = []
        if n_new_s:    summary_parts.append(f'<span style="color:#1d4ed8;font-size:12px;font-weight:600;">{n_new_s} new</span>')
        if n_rem_s:    summary_parts.append(f'<span style="color:#b91c1c;font-size:12px;font-weight:600;">{n_rem_s} removed</span>')
        if n_pc_s:     summary_parts.append(f'<span style="color:#b45309;font-size:12px;font-weight:600;">{n_pc_s} price changes</span>')
        summary_html = '<span style="color:#d1d5db;font-size:12px;margin:0 4px;">·</span>'.join(summary_parts)

        st.markdown(
            f'<div style="background:#ffffff;border:1px solid #e1e4e8;border-radius:10px;'
            f'overflow:hidden;box-shadow:0 1px 3px rgba(0,0,0,0.06);">'
            f'<div style="display:flex;align-items:center;justify-content:space-between;'
            f'padding:11px 16px;border-bottom:1px solid #f3f4f6;background:#fafafa;">'
            f'<div style="display:flex;gap:12px;align-items:center;">{summary_html}</div>'
            f'<span style="color:#9ca3af;font-size:11px;">Showing {len(activity)} events</span>'
            f'</div>'
            f'<div style="max-height:380px;overflow-y:auto;">{"".join(rows_html)}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

if _active_page == "Pricing Intelligence":
    render_filter_bar()
    # ── Filter 1: outlier rents ───────────────────────────────────────────────
    _pi = latest_df[latest_df["rent"].between(400, 12_000)].copy()

    # ── Filter 2: short-term / partial-semester listings ──────────────────────
    _today     = pd.Timestamp.now().normalize()
    _cutoff    = _today + pd.Timedelta(days=60)
    _avail_dt  = pd.to_datetime(_pi["available"], errors="coerce")
    _med_by_bd = _pi.groupby("bedrooms")["rent"].median()
    _threshold = _pi["bedrooms"].map(_med_by_bd) * 0.6
    _soon      = _avail_dt < _cutoff          # NaT → False (safe)
    _cheap     = _pi["rent"] < _threshold     # NaN threshold → False (safe)
    _pi        = _pi[~(_soon & _cheap)]

    # ── Filter 3: minimum 5 listings per bedroom count ────────────────────────
    _bed_counts  = _pi["bedrooms"].value_counts()
    _valid_beds  = _bed_counts[_bed_counts >= 5].index
    pricing_df   = _pi[_pi["bedrooms"].isin(_valid_beds)]

    _n_excluded  = len(latest_df) - len(pricing_df)

    render_kpi_row(latest_df, prev_df, active_df, prev_active_df)
    st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)

    if _n_excluded > 0:
        st.markdown(
            f'<p style="color:#9ca3af;font-size:12px;margin:-4px 0 10px;">'
            f'{_n_excluded} listing{"s" if _n_excluded != 1 else ""} excluded as outliers or short-term rentals</p>',
            unsafe_allow_html=True,
        )

    if pricing_df.empty:
        st.warning("No listings match the current filters.")
    else:
        fig = px.box(
            pricing_df, x="bedrooms", y="rent",
            labels={"bedrooms": "Bedrooms", "rent": "Monthly rent ($)"},
            color_discrete_sequence=["#2563eb"],
        )
        fig.update_layout(**_chart_layout("Rent Distribution by Bedroom Count"), showlegend=False)
        fig.update_layout(xaxis=dict(dtick=1))
        st.plotly_chart(fig)

    # ── Rent Calculator ───────────────────────────────────────────────────────
    st.markdown(
        '<hr style="border:none;border-top:1px solid #e1e4e8;margin:1.8rem 0 1.2rem;">',
        unsafe_allow_html=True,
    )
    st.markdown('<div class="page-title" style="font-size:18px;margin-bottom:4px;">Rent Calculator</div>', unsafe_allow_html=True)
    st.markdown(
        '<p style="color:#9ca3af;font-size:12px;margin:0 0 1rem;">Enter your property details '
        'to see a recommended rent range based on live competitor listings.</p>',
        unsafe_allow_html=True,
    )

    _COND_MULT = {"Basic": 0.85, "Standard": 1.00, "Updated": 1.10, "Premium": 1.20}
    _RAD_TIERS = ["0.25 mi", "0.5 mi", "1 mi", "1.5 mi", "2 mi", "City-wide"]
    _RAD_MILES = {"0.25 mi": 0.25, "0.5 mi": 0.5, "1 mi": 1.0,
                  "1.5 mi": 1.5, "2 mi": 2.0, "City-wide": None}

    def _hav_calc(lat1, lng1, lat2, lng2):
        la1, lo1, la2, lo2 = map(math.radians, [lat1, lng1, lat2, lng2])
        dlat, dlng = la2 - la1, lo2 - lo1
        a = math.sin(dlat/2)**2 + math.cos(la1)*math.cos(la2)*math.sin(dlng/2)**2
        return 3958.8 * 2 * math.asin(math.sqrt(a))

    calc_left, calc_right = st.columns(2)

    with calc_left:
        r1a, r1b, r1c = st.columns(3)
        with r1a:
            calc_beds = st.number_input("Bedrooms", min_value=0, max_value=7, step=1, value=2, key="calc_beds")
        with r1b:
            calc_baths = st.selectbox("Bathrooms", [1, 1.5, 2, 2.5, 3, 3.5, 4, 4.5, 5], key="calc_baths")
        with r1c:
            calc_ptype = st.selectbox("Property Type", ["Apartment", "House", "Duplex/Triplex", "Any"], key="calc_ptype")

        calc_addr_raw = st.text_input("Address (optional)", key="calc_addr", placeholder="e.g. 123 N College Ave")
        st.markdown(
            '<p style="color:#9ca3af;font-size:11px;margin:-8px 0 10px;">Enter a Bloomington address '
            'to find comps by distance. Leave blank to search city-wide.</p>',
            unsafe_allow_html=True,
        )

        if calc_addr_raw.strip():
            calc_radius = st.select_slider("Search radius", options=_RAD_TIERS, value="0.5 mi", key="calc_radius")
        else:
            calc_radius = "City-wide"

        st.markdown('<p class="flbl" style="margin:10px 0 4px;">Unit condition</p>', unsafe_allow_html=True)
        calc_cond = st.select_slider(
            "unit_condition", options=list(_COND_MULT.keys()), value="Standard",
            key="calc_condition", label_visibility="collapsed",
        )
        st.markdown(
            '<p style="color:#9ca3af;font-size:11px;margin:-4px 0 14px;">'
            'Basic: −15%&nbsp;&nbsp;&nbsp;Standard: 0%&nbsp;&nbsp;&nbsp;'
            'Updated: +10%&nbsp;&nbsp;&nbsp;Premium: +20%</p>',
            unsafe_allow_html=True,
        )

        calc_clicked = st.button("Calculate Rent Range", key="calc_btn", use_container_width=True)

    # ── Calculation (runs between column contexts) ─────────────────────────────
    if calc_clicked:
        _notes = []
        _pool  = active_df.copy()
        _pool["rent"]      = pd.to_numeric(_pool["rent"],      errors="coerce")
        _pool["bedrooms"]  = pd.to_numeric(_pool["bedrooms"],  errors="coerce")
        _pool["bathrooms"] = pd.to_numeric(_pool["bathrooms"], errors="coerce")
        _pool = _pool.dropna(subset=["rent", "bedrooms"])

        # Step 1a — bedroom match
        _exact = _pool[_pool["bedrooms"] == calc_beds]
        if len(_exact) >= 5:
            _pool = _exact
        else:
            _pool = _pool[_pool["bedrooms"].between(calc_beds - 1, calc_beds + 1)]
            _notes.append(f"bedroom count expanded to ±1 — only {len(_exact)} exact match{'es' if len(_exact)!=1 else ''} found")

        # Step 1b — property type
        if calc_ptype != "Any":
            _typed = _pool[_pool["property_type"].str.lower() == calc_ptype.lower()]
            if len(_typed) >= 5:
                _pool = _typed
            else:
                _notes.append(f"property type filter dropped — only {len(_typed)} {calc_ptype} listing{'s' if len(_typed)!=1 else ''} found")

        # Step 1c/d — address / radius
        _input_lat = _input_lng = None
        if calc_addr_raw.strip():
            _input_lat, _input_lng = _geocode_addr(calc_addr_raw, _city_addr_df)
            if _input_lat is None:
                _notes.append("address not found in city database — searching city-wide")

        if _input_lat is not None:
            _pool["lat"] = pd.to_numeric(_pool["lat"], errors="coerce")
            _pool["lng"] = pd.to_numeric(_pool["lng"], errors="coerce")
            _pool = _pool.dropna(subset=["lat","lng"])
            _pool = _pool[(_pool["lat"] != 0) & (_pool["lng"] != 0)]
            _pool["_dist"] = _pool.apply(
                lambda r: _hav_calc(r["lat"], r["lng"], _input_lat, _input_lng), axis=1
            )
            _sel_rad  = calc_radius
            _rad_mi   = _RAD_MILES[_sel_rad]
            _within   = _pool[_pool["_dist"] <= _rad_mi] if _rad_mi else _pool
            if len(_within) < 5 and _rad_mi:
                for _nt in _RAD_TIERS[_RAD_TIERS.index(_sel_rad) + 1:]:
                    _nm = _RAD_MILES[_nt]
                    _within = _pool[_pool["_dist"] <= _nm] if _nm else _pool
                    if len(_within) >= 5 or _nt == "City-wide":
                        _notes.append(f"radius expanded to {_nt} — fewer than 5 comps within {_sel_rad}")
                        break
            _pool = _within.sort_values("_dist")
        else:
            _pool["_dist"] = None

        # Step 2 — similarity scoring
        def _score_comp(r):
            s = 0
            if pd.notna(r.get("bathrooms")):
                diff = abs(float(r["bathrooms"]) - float(calc_baths))
                s += 30 if diff == 0 else (15 if diff <= 0.5 else 0)
            if calc_ptype != "Any" and pd.notna(r.get("property_type")):
                if str(r["property_type"]).lower() == calc_ptype.lower():
                    s += 20
            if pd.notna(r.get("_dist")):
                d = float(r["_dist"])
                s += 30 if d <= 0.25 else (20 if d <= 0.5 else (10 if d <= 1.0 else 0))
            return s

        _pool["_score"] = _pool.apply(_score_comp, axis=1)
        _top = _pool.sort_values("_score", ascending=False).head(20)

        if len(_top) < 3:
            st.session_state.calc_result = {
                "error": True, "beds": calc_beds,
                "n_total": len(active_df[active_df["bedrooms"] == calc_beds]),
            }
        else:
            _mult = _COND_MULT[calc_cond]
            def _r25(v): return round(v / 25) * 25
            _rents = _top["rent"]
            _fs = (
                df[df["event"] == "new"]
                .groupby("url")["scraped_date"].min()
                .rename("first_seen").reset_index()
            )
            _top = _top.merge(_fs, on="url", how="left")
            _top["_dom"] = (pd.Timestamp.now() - _top["first_seen"]).dt.days.astype("Int64")
            st.session_state.calc_result = {
                "error":    False,
                "low":      _r25(_rents.quantile(0.25) * _mult),
                "mid":      _r25(_rents.quantile(0.50) * _mult),
                "high":     _r25(_rents.quantile(0.75) * _mult),
                "condition": calc_cond,
                "mult":     _mult,
                "n_comps":  len(_top),
                "notes":    _notes,
                "comps":    _top,
                "has_dist": _input_lat is not None,
                "beds":     calc_beds,
            }

    # ── Results ────────────────────────────────────────────────────────────────
    with calc_right:
        _res = st.session_state.get("calc_result")
        if _res is None:
            st.markdown(
                '<div style="padding-top:60px;text-align:center;color:#9ca3af;font-size:13px;">'
                'Fill in the details and click Calculate to see your rent range.</div>',
                unsafe_allow_html=True,
            )
        elif _res.get("error"):
            _n_bd = int(_res["n_total"])
            st.warning(
                f"Not enough comparable listings found. Try expanding your search radius or "
                f"selecting 'Any' for property type. Currently tracking {len(active_df):,} total "
                f"listings with {_n_bd} listing{'s' if _n_bd != 1 else ''} at "
                f"{int(_res['beds'])} bedrooms in Bloomington."
            )
        else:
            _adj_pct = int(round((_res["mult"] - 1) * 100))
            _adj_str = ("No adjustment (Standard)" if _adj_pct == 0
                        else f"{'+'if _adj_pct>0 else ''}{_adj_pct}% condition adjustment ({_res['condition']})")
            _notes_html = "".join(
                f'<div style="color:#d97706;font-size:11px;margin-top:3px;">⚠ {n}</div>'
                for n in _res.get("notes", [])
            )
            st.markdown(f"""
<div style="background:#ffffff;border:1px solid #e1e4e8;border-radius:12px;padding:20px 20px 16px;">
  <div style="color:#9ca3af;font-size:11px;font-weight:600;text-transform:uppercase;
              letter-spacing:0.08em;margin-bottom:2px;">
    Based on {_res['n_comps']} comparable listing{'s' if _res['n_comps']!=1 else ''}
  </div>
  {_notes_html}
  <div style="display:flex;margin:16px 0 12px;text-align:center;">
    <div style="flex:1;padding:0 8px;border-right:1px solid #f3f4f6;">
      <div style="color:#9ca3af;font-size:10px;font-weight:700;text-transform:uppercase;
                  letter-spacing:0.07em;margin-bottom:6px;">Conservative</div>
      <div style="color:#6b7280;font-size:22px;font-weight:700;">${_res['low']:,}</div>
      <div style="color:#9ca3af;font-size:11px;">/mo</div>
    </div>
    <div style="flex:1;padding:0 8px;border-right:1px solid #f3f4f6;">
      <div style="color:#9ca3af;font-size:10px;font-weight:700;text-transform:uppercase;
                  letter-spacing:0.07em;margin-bottom:6px;">Recommended</div>
      <div style="background:#eff6ff;border-radius:8px;padding:8px 4px 6px;">
        <div style="color:#2563eb;font-size:28px;font-weight:800;">${_res['mid']:,}</div>
        <div style="color:#93c5fd;font-size:11px;">/mo</div>
      </div>
    </div>
    <div style="flex:1;padding:0 8px;">
      <div style="color:#9ca3af;font-size:10px;font-weight:700;text-transform:uppercase;
                  letter-spacing:0.07em;margin-bottom:6px;">Premium</div>
      <div style="color:#6b7280;font-size:22px;font-weight:700;">${_res['high']:,}</div>
      <div style="color:#9ca3af;font-size:11px;">/mo</div>
    </div>
  </div>
  <div style="color:#9ca3af;font-size:11px;padding-top:10px;border-top:1px solid #f3f4f6;">
    {_adj_str}
  </div>
</div>""", unsafe_allow_html=True)

            st.markdown('<p class="flbl" style="margin:14px 0 6px;">Comparable listings used</p>', unsafe_allow_html=True)
            _comps = _res["comps"].copy()
            _disp_cols = ["address", "rent", "bedrooms", "bathrooms", "property_type", "company", "_dom"]
            if _res["has_dist"]:
                _disp_cols.insert(5, "_dist")
            _comps = _comps[[c for c in _disp_cols if c in _comps.columns]].copy()
            _comps = _comps.rename(columns={
                "address": "Address", "rent": "Rent", "bedrooms": "Beds",
                "bathrooms": "Baths", "property_type": "Type",
                "company": "Company", "_dom": "Days Listed", "_dist": "Distance",
            })
            _comps["Rent"] = _comps["Rent"].apply(lambda x: f"${int(x):,}" if pd.notna(x) else "—")
            _comps["Beds"] = _comps["Beds"].apply(lambda x: int(x) if pd.notna(x) else "—")
            if "Distance" in _comps.columns:
                _comps["Distance"] = _comps["Distance"].apply(lambda x: f"{x:.1f} mi" if pd.notna(x) else "—")
            _col_cfg = {}
            if "Days Listed" in _comps.columns:
                _col_cfg["Days Listed"] = st.column_config.NumberColumn("Days Listed", format="%d days")
            st.dataframe(_comps, hide_index=True, height=300, column_config=_col_cfg)

    st.markdown(
        '<p style="color:#9ca3af;font-size:11px;font-style:italic;margin-top:14px;">'
        'Estimates are based on currently listed competitor properties and do not account for '
        'lease terms, included utilities, amenities, or unit-specific condition. '
        'Use as a market reference only.</p>',
        unsafe_allow_html=True,
    )

if _active_page == "Map":
    render_filter_bar()
    ss = st.session_state

    # ── Constants ─────────────────────────────────────────────────────────────
    # CAMPUS_LAT, CAMPUS_LNG, IU_CAMPUS_POLYGON defined at module level above
    _LAYER_OPTIONS = ["Scatter", "Heatmap", "Hexagon"]
    _RING_SPECS    = [(0.25, "1/4 mi"), (0.5, "1/2 mi"), (1.0, "1 mi"), (2.0, "2 mi")]
    _MAP_STYLE     = "https://basemaps.cartocdn.com/gl/positron-gl-style/style.json"
    _HEX_COLOR_RANGE = [
        [59,  130, 246, 200], [16, 185, 129, 200],
        [245, 158,  11, 200], [239,  68,  68, 200],
    ]

    # ── Helper functions ───────────────────────────────────────────────────────
    def haversine_miles(lat1, lng1, lat2, lng2):
        R = 3958.8
        lat1, lng1, lat2, lng2 = map(math.radians, [lat1, lng1, lat2, lng2])
        dlat, dlng = lat2 - lat1, lng2 - lng1
        a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlng / 2) ** 2
        return R * 2 * math.asin(math.sqrt(a))

    def make_circle(center_lat, center_lng, radius_miles, n_points=64):
        lat_deg = radius_miles * 0.01449
        lng_deg = radius_miles * 0.01449 / math.cos(math.radians(center_lat))
        return [
            [center_lng + lng_deg * math.sin(2 * math.pi * i / n_points),
             center_lat + lat_deg * math.cos(2 * math.pi * i / n_points)]
            for i in range(n_points + 1)
        ]

    def vacancy_color(days):
        if pd.isna(days):  return [150, 150, 150, 180]
        elif days <= 7:    return [37,  99,  235, 220]
        elif days <= 30:   return [34,  197,  94, 220]
        elif days <= 60:   return [234, 179,   8, 220]
        else:              return [239,  68,  68, 220]

    # ── Main listing data prep ────────────────────────────────────────────────
    map_df = active_df.copy()
    map_df["lat"] = pd.to_numeric(map_df["lat"], errors="coerce")
    map_df["lng"] = pd.to_numeric(map_df["lng"], errors="coerce")
    map_df = map_df.dropna(subset=["lat", "lng"])
    map_df = map_df[(map_df["lat"] != 0) & (map_df["lng"] != 0)]
    map_df["rent_int"] = pd.to_numeric(map_df["rent"], errors="coerce")

    if map_df.empty:
        st.warning("No listings with location data match the current filters.")
    else:
        # ── Days on market (earliest "new" event per URL across all history) ──
        _first_seen = (
            df[df["event"] == "new"]
            .groupby("url")["scraped_date"].min()
            .rename("first_seen").reset_index()
        )
        map_df = map_df.merge(_first_seen, on="url", how="left")
        map_df["days_on_market"] = (pd.Timestamp.now() - map_df["first_seen"]).dt.days
        map_df["dom_label"]    = map_df["days_on_market"].apply(
            lambda d: f"{int(d)} days" if pd.notna(d) else "Unknown"
        )
        map_df["status_label"] = "Active"
        map_df["color"]        = map_df["days_on_market"].apply(vacancy_color)

        # Heatmap weight (rent-based)
        r_min, r_max = map_df["rent_int"].min(), map_df["rent_int"].max()
        map_df["rent_weight"] = (
            (map_df["rent_int"] - r_min) / (r_max - r_min)
            if r_max > r_min else 1.0
        )

        # Distance from campus
        map_df["dist_miles"] = map_df.apply(
            lambda r: haversine_miles(r["lat"], r["lng"], CAMPUS_LAT, CAMPUS_LNG),
            axis=1,
        )

        # ── Weekly activity (full unfiltered dataset) ─────────────────────────
        _cutoff = (pd.Timestamp.now() - pd.Timedelta(days=7)).normalize()

        def _prep_week_df(event_type, status_lbl, dom_lbl_fn):
            w = filtered[(filtered["event"] == event_type) & (filtered["scraped_date"] >= _cutoff)].copy()
            w["lat"] = pd.to_numeric(w["lat"], errors="coerce")
            w["lng"] = pd.to_numeric(w["lng"], errors="coerce")
            w = w.dropna(subset=["lat", "lng"])
            w = w[(w["lat"] != 0) & (w["lng"] != 0)]
            w["status_label"] = status_lbl
            w["dom_label"]    = w.apply(dom_lbl_fn, axis=1)
            return w

        new_week_df = _prep_week_df(
            "new", "New this week",
            lambda r: "New listing",
        )
        leased_week_df = _prep_week_df(
            "removed", "Leased / Removed",
            lambda r: f"Last seen {_fd(r['scraped_date'])}" if pd.notna(r["scraped_date"]) else "Unknown",
        )
        n_new    = len(new_week_df)
        n_leased = len(leased_week_df)

        # ── Ring geometry ─────────────────────────────────────────────────────
        _band_bounds = {0.25: (0, 0.25), 0.5: (0.25, 0.5), 1.0: (0.5, 1.0), 2.0: (1.0, 2.0)}

        def _band_avg_per_bed(lo, hi):
            sub = map_df[(map_df["dist_miles"] >= lo) & (map_df["dist_miles"] < hi)].copy()
            sub = sub.dropna(subset=["rent_int", "bedrooms"])
            sub = sub[sub["bedrooms"] > 0]
            if sub.empty:
                return None
            m = (sub["rent_int"] / sub["bedrooms"]).mean()
            return m if pd.notna(m) else None

        rings_data = [
            {"path": make_circle(CAMPUS_LAT, CAMPUS_LNG, r), "label": lbl}
            for r, lbl in _RING_SPECS
        ]
        ring_labels_data = []
        for r, lbl in _RING_SPECS:
            lo, hi = _band_bounds[r]
            avg    = _band_avg_per_bed(lo, hi)
            lat_deg = r * 0.01449
            label_str = f"{lbl}  |  ${avg:,.0f}/bd" if avg is not None else lbl
            ring_labels_data.append({
                "position": [CAMPUS_LNG, CAMPUS_LAT + lat_deg],
                "label":    label_str,
            })

        # ── Static PyDeck layer objects ───────────────────────────────────────
        campus_layer = pdk.Layer(
            "PolygonLayer",
            data=[{"polygon": IU_CAMPUS_POLYGON[0]}],
            get_polygon="polygon",
            get_fill_color=[165, 30, 55, 40],
            get_line_color=[165, 30, 55, 200],
            line_width_min_pixels=2,
            pickable=False,
        )
        text_layer = pdk.Layer(
            "TextLayer",
            data=[{"position": [-86.5134, 39.1794], "text": "IU Campus"}],
            get_position="position",
            get_text="text",
            get_size=14,
            get_color=[165, 30, 55, 220],
            get_alignment_baseline="'center'",
        )
        rings_layer = pdk.Layer(
            "PathLayer",
            data=rings_data,
            get_path="path",
            get_color=[165, 30, 55, 100],
            get_width=2,
            width_min_pixels=1,
            pickable=False,
            dash_array=[6, 4],
        )
        ring_labels_layer = pdk.Layer(
            "TextLayer",
            data=ring_labels_data,
            get_position="position",
            get_text="label",
            get_size=12,
            get_color=[120, 20, 40, 220],
            get_text_anchor="'middle'",
            get_alignment_baseline="'bottom'",
        )

        # ── CSS: base styles for weekly pills + selected overrides ────────────
        new_btn_label    = f"New this week ({n_new})"
        leased_btn_label = f"Leased this week ({n_leased})"

        st.markdown("""<style>
button[aria-label^="New this week"],
button[aria-label^="Leased this week"] {
    background-color: #ffffff !important; border: 1px solid #d1d5db !important;
    border-radius: 20px !important; color: #374151 !important;
    font-size: 12px !important; font-weight: 500 !important;
    min-height: 28px !important; height: 28px !important;
    line-height: 1 !important; box-shadow: none !important; padding: 0 10px !important;
}
button[aria-label^="New this week"]:hover    { border-color:#2563eb!important; color:#2563eb!important; }
button[aria-label^="Leased this week"]:hover { border-color:#16a34a!important; color:#16a34a!important; }
</style>""", unsafe_allow_html=True)

        _css = []
        for lyr in _LAYER_OPTIONS:
            if lyr == ss.map_layer:
                _css.append(f'button[aria-label="{lyr}"]{{background-color:#2563eb!important;'
                            f'border-color:#2563eb!important;color:#ffffff!important;font-weight:600!important;}}')
        if ss.map_show_new_week:
            _css.append(f'button[aria-label="{new_btn_label}"]{{background-color:#2563eb!important;'
                        f'border-color:#2563eb!important;color:#ffffff!important;font-weight:600!important;}}')
        if ss.map_show_leased_week:
            _css.append(f'button[aria-label="{leased_btn_label}"]{{background-color:#22c55e!important;'
                        f'border-color:#22c55e!important;color:#ffffff!important;font-weight:600!important;}}')
        if _css:
            st.markdown(f"<style>{''.join(_css)}</style>", unsafe_allow_html=True)

        # ── Control panel ─────────────────────────────────────────────────────
        with st.container(border=True):

            # ── Section 1: Layer ──────────────────────────────────────────────
            s1a, s1b = st.columns([9, 1])
            with s1a:
                st.markdown('<div class="flbl">Layer</div>', unsafe_allow_html=True)
                lc1, lc2, lc3, _ = st.columns([1, 1, 1, 6])
                for lc, lyr in zip([lc1, lc2, lc3], _LAYER_OPTIONS):
                    with lc:
                        st.button(lyr, key=f"map_layer_{lyr}", on_click=_set_map_layer, args=(lyr,))
            with s1b:
                st.markdown(
                    f'<div class="map-count">Showing {len(map_df):,} listings</div>',
                    unsafe_allow_html=True,
                )

            st.markdown('<div class="fsep"></div>', unsafe_allow_html=True)

            # ── Section 2: Weekly Activity ────────────────────────────────────
            st.markdown('<div class="flbl">Weekly Activity</div>', unsafe_allow_html=True)
            wa1, wa2, _ = st.columns([2, 2, 6])
            with wa1:
                st.button(new_btn_label,    key="btn_map_new_week",    on_click=_toggle_map_new_week)
            with wa2:
                st.button(leased_btn_label, key="btn_map_leased_week", on_click=_toggle_map_leased_week)

            net     = n_new - n_leased
            net_clr = "#2563eb" if net >= 0 else "#dc2626"
            net_str = f"+{net}" if net >= 0 else str(net)
            st.markdown(
                f'<div style="color:#6b7280;font-size:12px;margin-top:4px;">'
                f'This week: {n_new} new listings, {n_leased} leased — net change: '
                f'<span style="color:{net_clr};font-weight:600;">{net_str} units</span>'
                f'</div>',
                unsafe_allow_html=True,
            )

            st.markdown('<div class="fsep"></div>', unsafe_allow_html=True)

            # ── Section 3: Display Options ────────────────────────────────────
            st.markdown('<div class="flbl">Display Options</div>', unsafe_allow_html=True)
            disp_leg, disp_chk = st.columns([7, 3])
            with disp_leg:
                st.markdown("""
<div class="map-legend">
  <span class="leg-item"><span class="leg-dot" style="background:rgb(37,99,235);"></span>New (0-7 days)</span>
  <span class="leg-item"><span class="leg-dot" style="background:rgb(34,197,94);"></span>Fresh (8-30 days)</span>
  <span class="leg-item"><span class="leg-dot" style="background:rgb(234,179,8);"></span>Aging (31-60 days)</span>
  <span class="leg-item"><span class="leg-dot" style="background:rgb(239,68,68);"></span>Stale (60+ days)</span>
  <span class="leg-item"><span class="leg-dot" style="background:rgb(150,150,150);"></span>Unknown</span>
</div>""", unsafe_allow_html=True)
            with disp_chk:
                st.checkbox("Show campus distance rings", key="map_show_rings")
                st.checkbox("Show IU campus boundary",   key="map_show_campus")

        # ── Build PyDeck deck ─────────────────────────────────────────────────
        view    = pdk.ViewState(latitude=39.165, longitude=-86.526, zoom=12, pitch=45)
        tooltip = {
            "html": (
                "<div style='font-family:Inter,sans-serif;font-size:12px;line-height:1.7;'>"
                "<b style='font-size:13px;'>{address}</b><br/>"
                "<span style='color:#9ca3af;'>Rent</span>&nbsp;<b>${rent}/mo</b><br/>"
                "<span style='color:#9ca3af;'>Beds/Baths</span>&nbsp;{bedrooms} bd / {bathrooms} ba<br/>"
                "<span style='color:#9ca3af;'>Company</span>&nbsp;{company}<br/>"
                "<span style='color:#9ca3af;'>Available</span>&nbsp;{available}<br/>"
                "<span style='color:#9ca3af;'>Days listed</span>&nbsp;{dom_label}<br/>"
                "<span style='color:#9ca3af;'>Status</span>&nbsp;{status_label}"
                "</div>"
            ),
            "style": {
                "backgroundColor": "#1f2937", "color": "#ffffff",
                "border": "1px solid #374151", "borderRadius": "8px",
                "padding": "10px 14px", "maxWidth": "280px",
            },
        }

        # Assemble layer stack
        active_layers = []
        if ss.map_show_campus:
            active_layers.append(campus_layer)
        if ss.map_show_rings:
            active_layers.append(rings_layer)

        if ss.map_layer == "Scatter":
            active_layers.append(pdk.Layer(
                "ScatterplotLayer", data=map_df,
                get_position=["lng", "lat"], get_radius=40,
                get_fill_color="color", pickable=True, opacity=0.8,
            ))
        elif ss.map_layer == "Heatmap":
            active_layers.append(pdk.Layer(
                "HeatmapLayer", data=map_df,
                get_position=["lng", "lat"], get_weight="rent_weight",
                radius_pixels=60, pickable=False,
            ))
        else:
            active_layers.append(pdk.Layer(
                "HexagonLayer", data=map_df,
                get_position=["lng", "lat"], radius=100,
                elevation_scale=4, elevation_range=[0, 500],
                extruded=True, coverage=0.8,
                color_range=_HEX_COLOR_RANGE, pickable=False,
            ))

        if ss.map_show_new_week and not new_week_df.empty:
            active_layers.append(pdk.Layer(
                "ScatterplotLayer", data=new_week_df,
                get_position=["lng", "lat"], get_radius=70,
                get_fill_color=[37, 99, 235, 255],
                get_line_color=[255, 255, 255, 255],
                stroked=True, line_width_min_pixels=2,
                pickable=True, opacity=1.0,
            ))
        if ss.map_show_leased_week and not leased_week_df.empty:
            active_layers.append(pdk.Layer(
                "ScatterplotLayer", data=leased_week_df,
                get_position=["lng", "lat"], get_radius=70,
                get_fill_color=[34, 197, 94, 255],
                get_line_color=[255, 255, 255, 255],
                stroked=True, line_width_min_pixels=2,
                pickable=True, opacity=1.0,
            ))

        # Text labels on top
        if ss.map_show_rings:
            active_layers.append(ring_labels_layer)
        if ss.map_show_campus:
            active_layers.append(text_layer)

        deck = pdk.Deck(
            layers=active_layers,
            initial_view_state=view,
            map_style=_MAP_STYLE,
            tooltip=tooltip,
        )
        _map_event = st.pydeck_chart(
            deck, height=600, use_container_width=True,
            on_select="rerun", selection_mode="single-object",
            key="main_map",
        )

        # ── Selected listing detail strip ─────────────────────────────────────
        _sel_objects = getattr(getattr(_map_event, "selection", None), "objects", {}) or {}
        _sel_rows = next(iter(_sel_objects.values()), []) if _sel_objects else []
        if _sel_rows:
            _s = _sel_rows[0]
            _s_rent  = _s.get("rent")
            _s_beds  = _s.get("bedrooms")
            _s_baths = _s.get("bathrooms")
            _s_co    = _s.get("company", "—")
            _s_avail = _s.get("available", "—")
            _s_addr  = _s.get("address", "—")
            _s_url   = _s.get("url")
            _s_dom   = _s.get("dom_label", "—")
            st.markdown(
                f'<div style="background:#EFF6FF;border:1px solid #BFDBFE;border-radius:10px;'
                f'padding:12px 18px;margin:10px 0;display:flex;gap:32px;align-items:center;flex-wrap:wrap;">'
                f'<span style="font-weight:600;color:#1D4ED8;font-size:14px;">📍 {_s_addr}</span>'
                f'<span style="color:#374151;font-size:13px;">'
                f'<b>${int(_s_rent):,}/mo</b> · {int(_s_beds) if _s_beds else "?"} bd / {_s_baths} ba</span>'
                f'<span style="color:#6B7280;font-size:12px;">{_s_co}</span>'
                f'<span style="color:#6B7280;font-size:12px;">Avail: {_s_avail}</span>'
                f'<span style="color:#6B7280;font-size:12px;">Listed {_s_dom}</span>'
                + (f'<a href="{_s_url}" target="_blank" style="color:#2563EB;font-size:12px;margin-left:auto;">View listing →</a>'
                   if _s_url else '')
                + f'</div>',
                unsafe_allow_html=True,
            )

        # ── Distance from campus chart ─────────────────────────────────────────
        st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)

        _DIST_BINS   = [0, 0.25, 0.5, 1.0, 1.5, 2.0, 3.0, 99]
        _DIST_LABELS = ["0-¼ mi", "¼-½ mi", "½-1 mi", "1-1.5 mi", "1.5-2 mi", "2-3 mi", "3+ mi"]

        dist_df = map_df.dropna(subset=["dist_miles", "rent_int", "bedrooms"]).copy()
        dist_df["bedrooms"] = dist_df["bedrooms"].astype(int).astype(str)
        dist_df["distance_band"] = pd.cut(
            dist_df["dist_miles"], bins=_DIST_BINS, labels=_DIST_LABELS,
        )

        grouped = (
            dist_df.groupby(["distance_band", "bedrooms"], observed=True)["rent_int"]
            .mean().reset_index()
            .rename(columns={"rent_int": "rent"})
        )

        if not grouped.empty:
            dist_chart = px.bar(
                grouped,
                x="distance_band", y="rent", color="bedrooms",
                barmode="group",
                category_orders={"distance_band": _DIST_LABELS},
                labels={
                    "distance_band": "Distance from Campus",
                    "rent": "Avg Rent ($)",
                    "bedrooms": "Bedrooms",
                },
                color_discrete_sequence=[
                    "#2563eb", "#3b82f6", "#60a5fa",
                    "#93c5fd", "#bfdbfe", "#dbeafe", "#eff6ff",
                ],
            )
            dist_chart.update_layout(
                **_chart_layout("Average Rent by Distance from IU Campus"),
                showlegend=True,
            )
            dist_chart.add_shape(
                type="line", x0=0.5, x1=0.5, y0=0, y1=1,
                xref="x", yref="paper",
                line=dict(color="#a51e37", width=1.5, dash="dot"),
            )
            dist_chart.add_annotation(
                x=0.5, y=0.96, xref="x", yref="paper",
                text="¼ mi boundary", showarrow=False,
                font=dict(color="#a51e37", size=10, family="Inter, sans-serif"),
                bgcolor="rgba(255,255,255,0.88)",
                bordercolor="#a51e37", borderwidth=1, borderpad=3,
            )
            st.plotly_chart(dist_chart)

            near_avg = dist_df[dist_df["dist_miles"] <= 0.5]["rent_int"].mean()
            far_avg  = dist_df[dist_df["dist_miles"] >  1.0]["rent_int"].mean()
            if pd.notna(near_avg) and pd.notna(far_avg) and abs(near_avg - far_avg) >= 1:
                diff      = near_avg - far_avg
                direction = "more" if diff > 0 else "less"
                insight   = (
                    f"Units within ½ mile of campus average "
                    f"<b>${abs(diff):,.0f} {direction}</b> per month "
                    f"than units beyond 1 mile."
                )
                st.markdown(
                    f'<p style="color:#6b7280;font-size:13px;margin-top:2px;">{insight}</p>',
                    unsafe_allow_html=True,
                )

if _active_page == "Forecast":
    render_filter_bar()

    # ── IU academic calendar (hardcoded) ──────────────────────────────────────
    IU_DATES = {
        "2026-08-24": "Fall Move-In",
        "2026-08-26": "Fall Classes Start",
        "2026-12-19": "Fall Finals End",
        "2027-01-11": "Spring Classes Start",
        "2027-05-07": "Spring Finals End",
        "2027-05-09": "Commencement",
    }

    # ── Data prep ─────────────────────────────────────────────────────────────
    _today_fc = pd.Timestamp.now().normalize()
    _fc_end   = _today_fc + pd.DateOffset(months=18)
    _90d_end  = _today_fc + pd.Timedelta(days=90)
    _12w_end  = _today_fc + pd.Timedelta(weeks=12)

    _fc_src = active_df.copy()
    _fc_src["_avail"] = pd.to_datetime(_fc_src["available"], errors="coerce")
    _fc_src = _fc_src.dropna(subset=["_avail"])
    _fc_src = _fc_src[(_fc_src["_avail"] >= _today_fc) & (_fc_src["_avail"] <= _fc_end)]

    _BED_ORDER     = ["1 BR", "2 BR", "3 BR", "4 BR", "5+ BR"]
    _BED_COLORS_FC = ["#1e40af", "#2563eb", "#3b82f6", "#60a5fa", "#93c5fd"]
    _BED_CLR_MAP   = dict(zip(_BED_ORDER, _BED_COLORS_FC))

    def _fc_bed_lbl(b):
        try:
            return "5+ BR" if int(b) >= 5 else f"{int(b)} BR"
        except Exception:
            return "Other"

    def _wk_str(p):
        d = p.start_time
        return f"{d.strftime('%b')} {d.day}"

    if not _fc_src.empty:
        _fc_src["_bed_lbl"] = _fc_src["bedrooms"].apply(_fc_bed_lbl)
        _fc_src["_month"]   = _fc_src["_avail"].dt.to_period("M")
        _fc_src["_week"]    = _fc_src["_avail"].dt.to_period("W")

        # Monthly
        _month_periods = sorted(_fc_src["_month"].unique())
        _month_strs    = [p.strftime("%b %Y") for p in _month_periods]
        _monthly_long  = (
            _fc_src.groupby(["_month", "_bed_lbl"])
            .size().reset_index(name="count")
        )
        _monthly_long["month_str"] = _monthly_long["_month"].apply(lambda p: p.strftime("%b %Y"))
        _monthly_total = _fc_src.groupby("_month").size()
        _avg_pm        = float(_monthly_total.mean())

        # Weekly (12 weeks)
        _fc_12w      = _fc_src[_fc_src["_avail"] <= _12w_end]
        _week_periods = sorted(_fc_12w["_week"].unique()) if not _fc_12w.empty else []
        _week_strs    = [_wk_str(p) for p in _week_periods]
        _weekly_long  = (
            _fc_12w.groupby(["_week", "_bed_lbl"])
            .size().reset_index(name="count")
        ) if not _fc_12w.empty else pd.DataFrame()
        if not _weekly_long.empty:
            _weekly_long["week_str"] = _weekly_long["_week"].apply(_wk_str)

        # 90-day slices
        _fc_90  = _fc_src[_fc_src["_avail"] <= _90d_end]
        _co_90  = (
            _fc_90.groupby("company").size()
            .reset_index(name="count")
            .sort_values("count", ascending=False)
        ) if not _fc_90.empty else pd.DataFrame()
        _bed_90 = (
            _fc_90.groupby("_bed_lbl").size()
            .reset_index(name="count")
            .sort_values("count", ascending=False)
        ) if not _fc_90.empty else pd.DataFrame()

        # KPIs
        _this_mo_count = int((_fc_src["_month"] == _today_fc.to_period("M")).sum())
        _next30_count  = int((_fc_src["_avail"] <= _today_fc + pd.Timedelta(days=30)).sum())
        _peak_period   = _monthly_total.idxmax()
        _peak_count    = int(_monthly_total.max())
        _tight_period  = _monthly_total.idxmin()
        _tight_count   = int(_monthly_total.min())
    else:
        _month_strs = _week_strs = []
        _monthly_long = _weekly_long = _fc_12w = _fc_90 = _co_90 = _bed_90 = pd.DataFrame()
        _this_mo_count = _next30_count = _peak_count = _tight_count = 0
        _avg_pm = 0.0
        _peak_period = _tight_period = None

    # ── Page header ───────────────────────────────────────────────────────────
    _fh_l, _fh_r = st.columns([4, 1])
    with _fh_l:
        st.markdown(
            '<div class="page-title" style="font-size:20px;margin-bottom:4px;">Lease Expiration Forecast</div>',
            unsafe_allow_html=True,
        )
        st.markdown(
            '<p style="color:#6b7280;font-size:13px;margin:0 0 0.8rem;">Units coming available across all '
            'tracked competitors over the next 18 months. Use this to anticipate market competition and '
            'time your own lease renewals and rent increases.</p>',
            unsafe_allow_html=True,
        )
    with _fh_r:
        st.markdown(
            f'<div style="text-align:right;padding-top:10px;color:#9ca3af;font-size:12px;">'
            f'Data as of: {latest_date.strftime("%b")} {latest_date.day}, {latest_date.strftime("%Y")}'
            f'</div>',
            unsafe_allow_html=True,
        )

    # ── KPI row ───────────────────────────────────────────────────────────────
    _fk1, _fk2, _fk3, _fk4 = st.columns(4)
    _peak_val   = _peak_period.strftime("%B %Y") if _peak_period is not None else "—"
    _peak_delta = f"{_peak_count:,} units — peak month" if _peak_count else "—"
    _fc_metrics = [
        ("Available This Month",   f"{_this_mo_count:,}", "active listings", "neutral"),
        ("Available Next 30 Days", f"{_next30_count:,}",  "active listings", "neutral"),
        ("Peak Month",             _peak_val,              _peak_delta,       "neutral"),
        ("Avg Units / Month",      f"{_avg_pm:.0f}",       "18-month window", "neutral"),
    ]
    for _col, (_lbl, _val, _dlt, _dc) in zip([_fk1, _fk2, _fk3, _fk4], _fc_metrics):
        with _col:
            st.markdown(kpi_card(_lbl, _val, _dlt, _dc), unsafe_allow_html=True)

    st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)

    if _fc_src.empty:
        st.info("No listings with parseable availability dates found in the next 18 months.")
    else:
        # ── Chart 1: 18-month stacked bar ─────────────────────────────────────
        _fig_fc = px.bar(
            _monthly_long,
            x="month_str", y="count", color="_bed_lbl",
            barmode="stack",
            labels={"month_str": "", "count": "Units", "_bed_lbl": "Bedrooms"},
            category_orders={"month_str": _month_strs, "_bed_lbl": _BED_ORDER},
            color_discrete_map=_BED_CLR_MAP,
        )
        _fig_fc.update_layout(
            **_chart_layout(
                "",
                legend=dict(
                    orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0,
                    font=dict(color="#6b7280", size=11), bgcolor="rgba(0,0,0,0)",
                ),
                margin=dict(l=8, r=8, t=40, b=8),
            )
        )
        # August highlight + annotation
        for _fi, _ms in enumerate(_month_strs):
            if "Aug" in _ms:
                _fig_fc.add_vrect(
                    x0=_fi - 0.5, x1=_fi + 0.5,
                    fillcolor="rgba(254,243,199,0.45)", line_width=0, layer="below",
                )
                _fig_fc.add_annotation(
                    x=_fi, y=1.06, yref="paper", text="IU Move-In",
                    showarrow=False, xanchor="center",
                    font=dict(color="#92400e", size=10, family="Inter, sans-serif"),
                    bgcolor="rgba(254,243,199,0.9)",
                    bordercolor="#d97706", borderwidth=1, borderpad=3,
                )
        # Today line
        _fig_fc.add_shape(
            type="line", x0=-0.5, x1=-0.5, y0=0, y1=1, yref="paper",
            line=dict(dash="dash", color="#9ca3af", width=1.5),
        )
        _fig_fc.add_annotation(
            x=-0.5, y=1.02, yref="paper", text="Today",
            showarrow=False, xanchor="right",
            font=dict(color="#9ca3af", size=10, family="Inter, sans-serif"),
        )
        # Average line
        _fig_fc.add_hline(
            y=_avg_pm, line_dash="dash", line_color="#d1d5db", line_width=1,
            annotation_text=f"Monthly avg  ({_avg_pm:.0f})",
            annotation_position="top right",
            annotation_font=dict(color="#9ca3af", size=10),
        )
        st.markdown('<p style="font-size:11px;color:#9ca3af;font-family:Inter,sans-serif;text-transform:uppercase;letter-spacing:.05em;margin:0 0 4px 4px;">Units Coming Available by Month</p>', unsafe_allow_html=True)
        st.plotly_chart(_fig_fc)

        # ── Chart 2: 12-week stacked bar ──────────────────────────────────────
        if not _weekly_long.empty and _week_strs:
            _fig_wk = px.bar(
                _weekly_long,
                x="week_str", y="count", color="_bed_lbl",
                barmode="stack",
                labels={"week_str": "", "count": "Units", "_bed_lbl": "Bedrooms"},
                category_orders={"week_str": _week_strs, "_bed_lbl": _BED_ORDER},
                color_discrete_map=_BED_CLR_MAP,
            )
            _fig_wk.update_layout(
                **_chart_layout(
                    "",
                    legend=dict(
                        orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0,
                        font=dict(color="#6b7280", size=11), bgcolor="rgba(0,0,0,0)",
                    ),
                    margin=dict(l=8, r=8, t=40, b=8),
                )
            )
            for _iu_dt_str, _iu_lbl in IU_DATES.items():
                _iu_ts = pd.Timestamp(_iu_dt_str)
                if _today_fc <= _iu_ts <= _12w_end:
                    _iu_wstr = _wk_str(_iu_ts.to_period("W"))
                    if _iu_wstr in _week_strs:
                        _iu_idx = _week_strs.index(_iu_wstr)
                        _fig_wk.add_shape(
                            type="line", x0=_iu_idx, x1=_iu_idx, y0=0, y1=1, yref="paper",
                            line=dict(dash="dash", color="#dc2626", width=1.5),
                        )
                        _fig_wk.add_annotation(
                            x=_iu_idx, y=0.97, yref="paper", text=_iu_lbl,
                            showarrow=False, textangle=-90, xanchor="right",
                            font=dict(color="#dc2626", size=9, family="Inter, sans-serif"),
                        )
            st.markdown('<p style="font-size:11px;color:#9ca3af;font-family:Inter,sans-serif;text-transform:uppercase;letter-spacing:.05em;margin:0 0 4px 4px;">Units Coming Available — Next 12 Weeks</p>', unsafe_allow_html=True)
            st.plotly_chart(_fig_wk)

        # ── Chart 3: company breakdown + bedroom mix ───────────────────────────
        _c3l, _c3r = st.columns(2)
        with _c3l:
            if not _co_90.empty:
                _fig_co = px.bar(
                    _co_90.sort_values("count", ascending=True),
                    x="count", y="company", orientation="h",
                    labels={"count": "Units", "company": ""},
                    color_discrete_sequence=["#2563eb"],
                )
                _fig_co.update_layout(
                    **_chart_layout("UNITS AVAILABLE IN NEXT 90 DAYS BY COMPANY"),
                    showlegend=False,
                )
                st.plotly_chart(_fig_co)
            else:
                st.info("No data in next 90 days.")

        with _c3r:
            if not _bed_90.empty:
                _bed_90_chart = _bed_90[_bed_90["_bed_lbl"].isin(_BED_ORDER)]
                _fig_bd = px.pie(
                    _bed_90_chart, names="_bed_lbl", values="count", hole=0.45,
                    color="_bed_lbl", color_discrete_map=_BED_CLR_MAP,
                    category_orders={"_bed_lbl": _BED_ORDER},
                )
                _fig_bd.update_layout(**_chart_layout("BEDROOM MIX — NEXT 90 DAYS"))
                _fig_bd.update_traces(textposition="inside", textinfo="percent+label",
                                      textfont=dict(size=11))
                st.plotly_chart(_fig_bd)
            else:
                st.info("No data in next 90 days.")

        # ── Insight callout ────────────────────────────────────────────────────
        _insights_fc = []
        if _peak_period is not None:
            _above_pct = ((_peak_count - _avg_pm) / _avg_pm * 100) if _avg_pm > 0 else 0
            _insights_fc.append(
                f"Peak availability month: {_peak_period.strftime('%B %Y')} with {_peak_count:,} units "
                f"— {_above_pct:.0f}% more than the monthly average."
            )
        if _tight_period is not None:
            _insights_fc.append(
                f"Tightest month: {_tight_period.strftime('%B %Y')} with only {_tight_count:,} units "
                f"coming available — potential opportunity to hold rents firm."
            )
        if not _co_90.empty:
            _top_co = _co_90.iloc[0]
            _insights_fc.append(
                f"{_top_co['company']} has the most units coming available in the next 90 days "
                f"({int(_top_co['count']):,} units)."
            )
        if not _bed_90.empty:
            _top_bed    = _bed_90.iloc[0]
            _bd_tot_90  = int(_bed_90["count"].sum())
            _bd_pct_90  = (_top_bed["count"] / _bd_tot_90 * 100) if _bd_tot_90 > 0 else 0
            _insights_fc.append(
                f"{_top_bed['_bed_lbl'].replace(' BR', '-bedroom')} units make up the largest share of "
                f"upcoming availability ({_bd_pct_90:.0f}% of next 90 days)."
            )

        if _insights_fc:
            _bullets_fc = "".join(
                f'<div style="margin-bottom:5px;">· {ins}</div>'
                for ins in _insights_fc
            )
            st.markdown(
                f'<div style="background:#eff6ff;border:1px solid #bfdbfe;border-radius:10px;'
                f'padding:16px 18px;margin-top:4px;">'
                f'<div style="color:#1e40af;font-size:13px;line-height:1.7;">{_bullets_fc}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )

        # ── Forecast data table ────────────────────────────────────────────────
        with st.expander("View full forecast data", expanded=False):
            _piv = (
                _fc_src.groupby(["_month", "_bed_lbl"])
                .size().unstack(fill_value=0).reset_index()
            )
            for _bc in _BED_ORDER:
                if _bc not in _piv.columns:
                    _piv[_bc] = 0
            _piv_beds = [c for c in _BED_ORDER if c in _piv.columns]
            _piv["Total Units"] = _piv[_piv_beds].sum(axis=1)
            _piv["Month"]       = _piv["_month"].apply(lambda p: p.strftime("%B %Y"))
            _piv["vs. Avg"]     = (_piv["Total Units"] - _avg_pm).round(0).astype(int)
            _piv_disp = _piv[["Month", "Total Units"] + _piv_beds + ["vs. Avg"]].copy()

            def _style_va(val):
                if val > 0:   return "color:#dc2626;font-weight:600"
                if val < 0:   return "color:#16a34a;font-weight:600"
                return "color:#6b7280"

            _styled_piv = _piv_disp.style.map(_style_va, subset=["vs. Avg"])
            st.dataframe(
                _styled_piv,
                hide_index=True,
                column_config={
                    "vs. Avg": st.column_config.NumberColumn("vs. Avg", format="%+d"),
                },
            )

if _active_page == "Companies":
    render_filter_bar()

    # Market baseline: all filters applied except company, so "vs Market" charts
    # compare selected companies against the full (non-company-filtered) dataset.
    _co_df = get_filtered_df(df, skip_company=True)

    _co_url_last = (
        _co_df.sort_values("scraped_date").groupby("url").last().reset_index()
    )
    _co_active = _co_url_last[_co_url_last["event"] != "removed"].copy()

    _co_names = sorted(_co_df["company"].dropna().unique().tolist())

    # Selected companies come from the filter bar's company filter.
    # If no company filter is set, default to showing all companies.
    _sel_cos = list(st.session_state.flt_companies) if st.session_state.flt_companies else list(_co_names)

    # Palette — one distinct color per selected company
    _COMPANY_PALETTE = ["#2563EB", "#7C3AED", "#D97706", "#059669",
                        "#DC2626", "#0891B2", "#BE185D", "#92400E"]
    _co_color_map = {
        co: _COMPANY_PALETTE[i % len(_COMPANY_PALETTE)]
        for i, co in enumerate(_sel_cos)
    }
    _co_color_map["Market"] = "#E5E7EB"

    # 4-week prior active
    _co_4w_date = latest_date - pd.Timedelta(weeks=4)
    _co_4w_last = (
        _co_df[_co_df["scraped_date"] <= _co_4w_date]
        .sort_values("scraped_date").groupby("url").last().reset_index()
    )
    _co_4w_active = _co_4w_last[_co_4w_last["event"] != "removed"].copy()

    # Days on market via first-seen date per URL
    _url_first_seen = _co_df.groupby("url")["scraped_date"].min().rename("first_seen")

    def _add_dom(frame: pd.DataFrame) -> pd.DataFrame:
        f = frame.join(_url_first_seen, on="url", how="left")
        f["days_listed"] = (f["scraped_date"] - f["first_seen"]).dt.days.fillna(0).astype(int)
        return f

    _co_active    = _add_dom(_co_active)
    _co_4w_active = _add_dom(_co_4w_active)

    _co_sel    = _co_active[_co_active["company"].isin(_sel_cos)]    if _sel_cos else pd.DataFrame()
    _co_sel_4w = _co_4w_active[_co_4w_active["company"].isin(_sel_cos)] if _sel_cos else pd.DataFrame()
    _co_total_act = len(_co_active)

    # ── Page header ───────────────────────────────────────────────────────────
    st.markdown(
        '<div style="font-size:20px;font-weight:700;color:#111827;margin-bottom:2px;">Companies</div>'
        '<div style="color:#9ca3af;font-size:12px;margin-bottom:10px;">'
        'Use the filter bar above to focus on specific companies, bedrooms, or rent ranges.</div>',
        unsafe_allow_html=True,
    )

    st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)

    if not _co_names:
        st.warning("No listings match the current filters.")
        st.stop()

    # ── 5 KPI cards ───────────────────────────────────────────────────────────
    _co_cur_n   = len(_co_sel)
    _co_4w_n    = len(_co_sel_4w)
    _co_cur_md  = float(_co_sel["rent"].median())    if _co_cur_n else 0.0
    _co_4w_md   = float(_co_sel_4w["rent"].median()) if _co_4w_n  else 0.0
    _co_cur_dom = float(_co_sel["days_listed"].mean())    if _co_cur_n else 0.0
    _co_4w_dom  = float(_co_sel_4w["days_listed"].mean()) if _co_4w_n  else 0.0
    _co_rpb     = float((_co_sel["rent"] / _co_sel["bedrooms"]).replace([float("inf"), float("-inf")], float("nan")).mean()) if _co_cur_n else 0.0
    _co_share   = (_co_cur_n / _co_total_act * 100) if _co_total_act else 0.0

    def _co_delta(cur, prev, unit, fmt=",.0f", invert=False):
        diff = cur - prev
        if diff == 0 or prev == 0:
            return "No change", "neutral"
        cls = ("negative" if invert else "positive") if diff > 0 else ("positive" if invert else "negative")
        return f"{abs(diff):{fmt}} {unit}", cls

    _kd1, _kd1c = _co_delta(_co_cur_n,   _co_4w_n,   "listings")
    _kd2, _kd2c = ("—", "neutral") if not _co_4w_n else _co_delta(_co_cur_md, _co_4w_md, "/mo")
    _kd3, _kd3c = _co_delta(_co_cur_dom, _co_4w_dom, "days", fmt=".1f", invert=True)

    _k1c, _k2c, _k3c, _k4c, _k5c = st.columns(5)
    with _k1c:
        st.markdown(kpi_card("Active Listings",    f"{_co_cur_n:,}",             _kd1, _kd1c), unsafe_allow_html=True)
    with _k2c:
        st.markdown(kpi_card("Median Rent",        f"${_co_cur_md:,.0f}" if _co_cur_n else "—", _kd2, _kd2c), unsafe_allow_html=True)
    with _k3c:
        st.markdown(kpi_card("Avg Days Listed",    f"{_co_cur_dom:.0f}" if _co_cur_n else "—",  _kd3, _kd3c), unsafe_allow_html=True)
    with _k4c:
        st.markdown(kpi_card("Avg Rent / Bedroom", f"${_co_rpb:,.0f}" if _co_cur_n else "—",   "—", "neutral"), unsafe_allow_html=True)
    with _k5c:
        st.markdown(kpi_card("Market Share",       f"{_co_share:.1f}%" if _co_total_act else "—", "—", "neutral"), unsafe_allow_html=True)

    st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)

    # ── Two-column: charts (60%) + mini map (40%) ─────────────────────────────
    _CO_BED_ORDER  = ["1 BR", "2 BR", "3 BR", "4 BR", "5+ BR"]
    _CO_BED_COLORS = ["#1e40af", "#2563eb", "#3b82f6", "#60a5fa", "#93c5fd"]
    _CO_BED_MAP    = dict(zip(_CO_BED_ORDER, _CO_BED_COLORS))

    def _co_bed_lbl(b):
        try:
            bi = int(b)
            return f"{bi} BR" if bi <= 4 else "5+ BR"
        except Exception:
            return "Other"

    _cl5, _cr5 = st.columns([3, 2])

    with _cl5:
        # Chart 1: Median rent by bedroom count — selected companies vs market
        if _co_cur_n > 0:
            _bar_src = _co_active[["company", "rent", "bedrooms"]].copy()
            _bar_src["_bed_lbl"] = _bar_src["bedrooms"].apply(_co_bed_lbl)
            _bar_src["_group"]   = _bar_src["company"].apply(
                lambda c: c if c in _sel_cos else "Market"
            )
            _bar_src = _bar_src[
                (_bar_src["_bed_lbl"] != "Other") &
                _bar_src["rent"].notna()
            ]
            # Only show bedroom counts present in at least one selected company
            _co_bed_set = set(_bar_src.loc[_bar_src["_group"] != "Market", "_bed_lbl"])
            _bar_src = _bar_src[_bar_src["_bed_lbl"].isin(_co_bed_set)]

            _med_by_bed = (
                _bar_src.groupby(["_bed_lbl", "_group"])["rent"]
                .median().reset_index()
                .rename(columns={"rent": "Median Rent", "_bed_lbl": "Bedrooms", "_group": "Source"})
            )

            _fig_cobox = px.bar(
                _med_by_bed,
                x="Bedrooms", y="Median Rent",
                color="Source",
                barmode="group",
                color_discrete_map=_co_color_map,
                labels={"Bedrooms": "Bedrooms", "Median Rent": "Median Rent ($)", "Source": ""},
                category_orders={
                    "Bedrooms": [b for b in _CO_BED_ORDER if b in _co_bed_set],
                },
            )
            _fig_cobox.update_traces(
                selector={"name": "Market"},
                marker_line_color="#9ca3af", marker_line_width=1,
            )
            _fig_cobox.update_layout(
                **_chart_layout(
                    "",
                    legend=dict(
                        orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0,
                        font=dict(color="#6b7280", size=11), bgcolor="rgba(0,0,0,0)",
                    ),
                    margin=dict(l=8, r=8, t=40, b=8),
                )
            )
            st.markdown('<p style="font-size:11px;color:#9ca3af;font-family:Inter,sans-serif;text-transform:uppercase;letter-spacing:.05em;margin:0 0 4px 4px;">Median Rent by Bedroom vs. Market</p>', unsafe_allow_html=True)
            st.plotly_chart(_fig_cobox)

        # Chart 2: Listing volume over time — one line per selected company
        _co_df["_vol_week"] = _co_df["scraped_date"].dt.to_period("W").apply(lambda p: p.start_time)
        _vol_ts = (
            _co_df.groupby(["company", "_vol_week"])["url"]
            .nunique().reset_index()
        )
        _vol_ts.columns = ["company", "week", "count"]
        _vol_mkt = _vol_ts.groupby("week")["count"].mean().reset_index().sort_values("week")

        _fig_vol = go.Figure()
        for _co_i, _co_name in enumerate(_sel_cos):
            _vol_co = _vol_ts[_vol_ts["company"] == _co_name].sort_values("week")
            if not _vol_co.empty:
                _fig_vol.add_trace(go.Scatter(
                    x=_vol_co["week"], y=_vol_co["count"],
                    name=_co_name, mode="lines+markers",
                    line=dict(color=_COMPANY_PALETTE[_co_i % len(_COMPANY_PALETTE)], width=2),
                    marker=dict(size=5),
                ))
        _fig_vol.add_trace(go.Scatter(
            x=_vol_mkt["week"], y=_vol_mkt["count"],
            name="Market Avg", mode="lines",
            line=dict(color="#d1d5db", width=1.5, dash="dash"),
        ))
        if _fig_vol.data:
            _fig_vol.update_layout(
                **_chart_layout(
                    "",
                    legend=dict(
                        orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0,
                        font=dict(color="#6b7280", size=11), bgcolor="rgba(0,0,0,0)",
                    ),
                    margin=dict(l=8, r=8, t=40, b=8),
                )
            )
            st.markdown('<p style="font-size:11px;color:#9ca3af;font-family:Inter,sans-serif;text-transform:uppercase;letter-spacing:.05em;margin:0 0 4px 4px;">Listings Activity Over Time</p>', unsafe_allow_html=True)
            st.plotly_chart(_fig_vol)

        # Chart 3: Bedroom mix vs. market — one row per selected company + market
        if _co_cur_n > 0:
            _bdmix_rows = []
            for _co_name in _sel_cos:
                _bdf = _co_active[_co_active["company"] == _co_name]["bedrooms"].dropna().apply(_co_bed_lbl).value_counts().reset_index()
                _bdf.columns = ["_bed_lbl", "count"]
                _tot = _bdf["count"].sum()
                _bdf["pct"]  = _bdf["count"] / _tot * 100 if _tot else 0
                _bdf["_src"] = _co_name
                _bdmix_rows.append(_bdf)
            _mkt_bd = _co_active["bedrooms"].dropna().apply(_co_bed_lbl).value_counts().reset_index()
            _mkt_bd.columns = ["_bed_lbl", "count"]
            _mkt_tot = _mkt_bd["count"].sum()
            _mkt_bd["pct"]  = _mkt_bd["count"] / _mkt_tot * 100 if _mkt_tot else 0
            _mkt_bd["_src"] = "Market"
            _bdmix_rows.append(_mkt_bd)
            _bdmix = pd.concat(_bdmix_rows, ignore_index=True)

            _fig_bdmix = px.bar(
                _bdmix, x="pct", y="_src", color="_bed_lbl",
                orientation="h", barmode="stack",
                labels={"pct": "% of Listings", "_src": "", "_bed_lbl": "Bedrooms"},
                color_discrete_map=_CO_BED_MAP,
                category_orders={"_bed_lbl": _CO_BED_ORDER},
            )
            _fig_bdmix.update_layout(
                **_chart_layout(
                    "",
                    legend=dict(
                        orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0,
                        font=dict(color="#6b7280", size=11), bgcolor="rgba(0,0,0,0)",
                    ),
                    margin=dict(l=8, r=8, t=40, b=8),
                )
            )
            st.markdown('<p style="font-size:11px;color:#9ca3af;font-family:Inter,sans-serif;text-transform:uppercase;letter-spacing:.05em;margin:0 0 4px 4px;">Bedroom Mix vs. Market</p>', unsafe_allow_html=True)
            st.plotly_chart(_fig_bdmix)

    with _cr5:
        # Mini map — availability colors (1 company) or company colors (2+)
        _map5 = _co_sel.copy()
        _map5["lat"] = pd.to_numeric(_map5.get("lat", pd.Series(dtype=float)), errors="coerce")
        _map5["lng"] = pd.to_numeric(_map5.get("lng", pd.Series(dtype=float)), errors="coerce")
        _map5 = _map5.dropna(subset=["lat", "lng"])
        _map5 = _map5[(_map5["lat"] != 0) & (_map5["lng"] != 0)]

        if not _map5.empty:
            _m5_lat_c = (_map5["lat"].min() + _map5["lat"].max()) / 2
            _m5_lng_c = (_map5["lng"].min() + _map5["lng"].max()) / 2
            _m5_lat_span = max(_map5["lat"].max() - _map5["lat"].min(), 0.008)
            _m5_lng_span = max(_map5["lng"].max() - _map5["lng"].min(), 0.008)
            _m5_zoom = max(10, min(14, 11 - math.log2(max(_m5_lat_span, _m5_lng_span) / 0.05)))

            _today5 = pd.Timestamp.now().normalize()

            def _hex_to_rgb(h):
                h = h.lstrip("#")
                return [int(h[i:i+2], 16) for i in (0, 2, 4)] + [200]

            if len(_sel_cos) == 1:
                # Single company: color by availability window
                _map5["_avail_dt"] = pd.to_datetime(_map5["available"], errors="coerce")
                def _avail5_color(dt):
                    if pd.isna(dt):  return [100, 100, 100, 160]
                    d = (dt - _today5).days
                    if d < 0:    return [234, 88, 12, 200]
                    if d <= 30:  return [22, 163, 74, 200]
                    if d <= 90:  return [37, 99, 235, 200]
                    return [147, 197, 253, 200]
                _map5["_color"] = _map5["_avail_dt"].apply(_avail5_color)
                _map5["_tip"]   = _map5["address"].fillna("") + " — $" + _map5["rent"].apply(lambda r: f"{r:,.0f}")
                _map_legend = (
                    '<div style="font-size:11px;color:#6b7280;margin-top:4px;line-height:1.9;">'
                    '<span style="color:#16a34a;">●</span> Available ≤30 days &nbsp;&nbsp;'
                    '<span style="color:#2563eb;">●</span> 31–90 days &nbsp;&nbsp;'
                    '<span style="color:#93c5fd;">●</span> 90+ days &nbsp;&nbsp;'
                    '<span style="color:#ea580c;">●</span> Past due</div>'
                )
            else:
                # Multiple companies: color by company
                _map5["_color"] = _map5["company"].apply(
                    lambda c: _hex_to_rgb(_co_color_map.get(c, "#9CA3AF"))
                )
                _map5["_tip"] = (
                    _map5["company"].fillna("") + " · " +
                    _map5["address"].fillna("") + " — $" +
                    _map5["rent"].apply(lambda r: f"{r:,.0f}")
                )
                _legend_dots = " &nbsp; ".join(
                    f'<span style="color:{_co_color_map[c]};">●</span> {c}'
                    for c in _sel_cos if c in _co_color_map
                )
                _map_legend = f'<div style="font-size:11px;color:#6b7280;margin-top:4px;line-height:1.9;">{_legend_dots}</div>'

            _m5_campus_layer = pdk.Layer(
                "PolygonLayer",
                data=[{"polygon": IU_CAMPUS_POLYGON[0]}],
                get_polygon="polygon",
                get_fill_color=[165, 30, 55, 35],
                get_line_color=[165, 30, 55, 180],
                line_width_min_pixels=2,
                pickable=False,
            )
            _m5_scatter_layer = pdk.Layer(
                "ScatterplotLayer",
                data=_map5[["lat", "lng", "_color", "_tip"]].to_dict("records"),
                get_position="[lng, lat]",
                get_fill_color="_color",
                get_radius=50,
                pickable=True,
            )
            st.pydeck_chart(
                pdk.Deck(
                    layers=[_m5_campus_layer, _m5_scatter_layer],
                    initial_view_state=pdk.ViewState(
                        latitude=_m5_lat_c, longitude=_m5_lng_c,
                        zoom=_m5_zoom, pitch=0,
                    ),
                    map_style="https://basemaps.cartocdn.com/gl/positron-gl-style/style.json",
                    tooltip={"text": "{_tip}"},
                )
            )
            st.markdown(_map_legend, unsafe_allow_html=True)
        else:
            st.info("No geocoded listings for the selected companies.")

    st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)

    # ── Pricing history: 20 most recent rent changes ───────────────────────────
    st.markdown(
        '<div style="font-size:14px;font-weight:600;color:#374151;margin-bottom:8px;">'
        'Recent Price Changes</div>',
        unsafe_allow_html=True,
    )
    if _sel_cos:
        _ph_src = (
            _co_df[_co_df["company"].isin(_sel_cos)]
            .sort_values(["url", "scraped_date"])
            .copy()
        )
        _ph_src["_prev_rent"] = _ph_src.groupby("url")["rent"].shift(1)
        _ph_changes = _ph_src[
            _ph_src["_prev_rent"].notna() & (_ph_src["rent"] != _ph_src["_prev_rent"])
        ][["scraped_date", "company", "address", "_prev_rent", "rent"]].copy()
        _ph_changes.columns = ["Date", "Company", "Address", "Old Rent", "New Rent"]
        _ph_changes["Change"] = _ph_changes["New Rent"] - _ph_changes["Old Rent"]
        _ph_changes = _ph_changes.sort_values("Date", ascending=False).head(20).reset_index(drop=True)
        if len(_sel_cos) == 1:
            _ph_changes = _ph_changes.drop(columns=["Company"])
    else:
        _ph_changes = pd.DataFrame()

    if not _ph_changes.empty:
        def _ph_style(val):
            return "color:#16a34a;font-weight:600" if val < 0 else "color:#dc2626;font-weight:600"
        _ph_col_cfg = {
            "Old Rent": st.column_config.NumberColumn("Old Rent", format="$%.0f"),
            "New Rent": st.column_config.NumberColumn("New Rent", format="$%.0f"),
            "Change":   st.column_config.NumberColumn("Change",   format="$%+.0f"),
            "Date":     st.column_config.DateColumn("Date"),
        }
        st.dataframe(
            _ph_changes.style.map(_ph_style, subset=["Change"]),
            hide_index=True,
            column_config=_ph_col_cfg,
            use_container_width=True,
        )
    else:
        st.info("No price changes recorded for the selected companies.")

    st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)

    # ── All active listings for selected company ──────────────────────────────
    st.markdown(
        '<div style="font-size:14px;font-weight:600;color:#374151;margin-bottom:4px;">'
        'All Active Listings</div>'
        '<div style="color:#9ca3af;font-size:12px;margin-bottom:10px;">'
        'Every current listing from this company with availability and unit details.</div>',
        unsafe_allow_html=True,
    )

    if _sel_cos and not _co_sel.empty:
        _listings_base_cols = [
            "address", "available", "rent", "bedrooms", "bathrooms",
            "property_type", "days_listed", "pets", "parking", "laundry",
            "utilities_included", "url",
        ]
        # Prepend company column when comparing multiple
        _listings_cols = (["company"] + _listings_base_cols) if len(_sel_cos) > 1 else _listings_base_cols
        _listings_disp = _co_sel[
            [c for c in _listings_cols if c in _co_sel.columns]
        ].copy()

        # Parse and sort by availability date
        _listings_disp["available"] = pd.to_datetime(
            _listings_disp["available"], errors="coerce"
        )
        _listings_disp = _listings_disp.sort_values("available", na_position="last")

        # Clean up bedrooms / bathrooms to ints/floats where possible
        if "bedrooms" in _listings_disp.columns:
            _listings_disp["bedrooms"] = pd.to_numeric(
                _listings_disp["bedrooms"], errors="coerce"
            ).apply(lambda x: int(x) if pd.notna(x) else None)
        if "bathrooms" in _listings_disp.columns:
            _listings_disp["bathrooms"] = pd.to_numeric(
                _listings_disp["bathrooms"], errors="coerce"
            )

        _listings_disp = _listings_disp.rename(columns={
            "company":            "Company",
            "address":            "Address",
            "available":          "Available",
            "rent":               "Rent",
            "bedrooms":           "Beds",
            "bathrooms":          "Baths",
            "property_type":      "Type",
            "days_listed":        "Days Listed",
            "pets":               "Pets",
            "parking":            "Parking",
            "laundry":            "Laundry",
            "utilities_included": "Utilities",
            "url":                "URL",
        })

        _listing_col_cfg = {
            "Rent":        st.column_config.NumberColumn("Rent",        format="$%.0f"),
            "Days Listed": st.column_config.NumberColumn("Days Listed", format="%d days"),
            "Available":   st.column_config.DateColumn("Available",     format="MMM D, YYYY"),
        }
        if "URL" in _listings_disp.columns:
            _listing_col_cfg["URL"] = st.column_config.LinkColumn("URL")

        st.dataframe(
            _listings_disp,
            hide_index=True,
            use_container_width=True,
            column_config=_listing_col_cfg,
        )
        _co_label = _sel_cos[0] if len(_sel_cos) == 1 else f"{len(_sel_cos)} companies"
        st.markdown(
            f'<div style="color:#9ca3af;font-size:11px;margin-top:4px;">'
            f'{len(_listings_disp):,} active listing{"s" if len(_listings_disp) != 1 else ""} '
            f'for {_co_label}</div>',
            unsafe_allow_html=True,
        )
    else:
        st.info("No active listings found for the selected companies.")

    st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)

    # ── Company comparison table ──────────────────────────────────────────────
    st.markdown(
        '<div style="font-size:14px;font-weight:600;color:#374151;margin-bottom:8px;">'
        'Company Comparison</div>',
        unsafe_allow_html=True,
    )
    _cmp_rows = []
    for _cmp_co in _co_names:
        _cmp_a  = _co_active[_co_active["company"] == _cmp_co]
        _cmp_4w = _co_4w_active[_co_4w_active["company"] == _cmp_co]
        _n = len(_cmp_a)
        _cmp_rows.append({
            "Company":     _cmp_co,
            "Active":      _n,
            "Median Rent": float(_cmp_a["rent"].median()) if _n else 0.0,
            "Mkt Share":   (_n / _co_total_act * 100) if _co_total_act else 0.0,
            "4W Trend":    _n - len(_cmp_4w),
        })
    _cmp_df = pd.DataFrame(_cmp_rows).sort_values("Active", ascending=False).reset_index(drop=True)

    def _cmp_row_bg(row):
        bg = "background-color:#eff6ff" if row["Company"] in _sel_cos else ""
        return [bg] * len(row)

    def _cmp_trend_clr(val):
        if val > 0: return "color:#16a34a;font-weight:600"
        if val < 0: return "color:#dc2626;font-weight:600"
        return "color:#6b7280"

    st.dataframe(
        _cmp_df.style.apply(_cmp_row_bg, axis=1).map(_cmp_trend_clr, subset=["4W Trend"]),
        hide_index=True,
        column_config={
            "Median Rent": st.column_config.NumberColumn("Median Rent", format="$%.0f"),
            "Mkt Share":   st.column_config.NumberColumn("Mkt Share",   format="%.1f%%"),
            "4W Trend":    st.column_config.NumberColumn("4W Trend",    format="%+.0f"),
        },
    )
