"""
Interface Streamlit de validation humaine.
Affiche les propositions de l'IA, permet de valider / rejeter / modifier,
propose des fournisseurs, et génère des PDF.
"""

import sys
import os
import requests
import pandas as pd
import streamlit as st
from pathlib import Path
from datetime import datetime
import json
import sqlite3

# ── Résolution des imports relatifs ──────────────────────────────────────────
ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from agent.groq_agent import GroqAgent
from utils.pdf_generator import generer_pdf_commande, generer_pdf_recommandations

# ─── Configuration ────────────────────────────────────────────────────────────
SUPPLIER_API_URL = "http://localhost:5001"
DB_PATH = ROOT / "data" / "warehouse.db"

URGENCE_COLORS = {"critique": "#ff4757", "élevée": "#ff6b35", "moyenne": "#ffa502", "faible": "#2ed573"}
URGENCE_ICONS  = {"critique": "🔴", "élevée": "🟠", "moyenne": "🟡", "faible": "🟢"}
URGENCE_BG     = {"critique": "rgba(255,71,87,0.08)", "élevée": "rgba(255,107,53,0.08)",
                  "moyenne": "rgba(255,165,2,0.08)", "faible": "rgba(46,213,115,0.08)"}

# ─── Initialisation ───────────────────────────────────────────────────────────

@st.cache_resource
def get_agent():
    api_key = os.getenv("GROQ_API_KEY")
    return GroqAgent(api_key=api_key)


def appeler_recommandations(matiere: str, quantite: float, urgence: str) -> list:
    try:
        resp = requests.post(
            f"{SUPPLIER_API_URL}/recommandations",
            json={"matiere": matiere, "quantite": quantite, "urgence": urgence},
            timeout=10
        )
        if resp.status_code == 200:
            return resp.json().get("recommandations", [])
        st.error(f"Erreur API: {resp.status_code}")
        return []
    except Exception as e:
        st.error(f"Erreur connexion API: {e}")
        return []


def passer_commande(matiere, quantite, fournisseur_id, decision_id, delai_type="standard"):
    try:
        resp = requests.post(
            f"{SUPPLIER_API_URL}/passer_commande",
            json={"matiere": matiere, "quantite": quantite,
                  "fournisseur_id": fournisseur_id,
                  "decision_ia_id": decision_id, "delai_type": delai_type},
            timeout=10
        )
        return resp.json()
    except Exception as e:
        return {"statut": "erreur", "message": str(e)}


def charger_historique_local(limit: int = 50) -> pd.DataFrame:
    if not DB_PATH.exists():
        return pd.DataFrame()
    try:
        conn = sqlite3.connect(DB_PATH)
        df = pd.read_sql_query(
            """
            SELECT id, matiere, quantite, fournisseur_nom AS fournisseur, statut,
                 delai_jours, date_livraison_prevue, prix_total, created_at
            FROM commande_fournisseur
            ORDER BY id DESC LIMIT ?
            """,
            conn,
            params=(limit,)
        )
        conn.close()
        return df
    except Exception:
        return pd.DataFrame()


# ─── CSS ──────────────────────────────────────────────────────────────────────

def inject_css():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=DM+Sans:wght@300;400;500;600&display=swap');

    :root {
      --bg:        #080c14;
      --surface:   #0d1424;
      --surface2:  #111827;
      --border:    rgba(255,255,255,0.07);
      --border2:   rgba(255,255,255,0.12);
      --accent:    #4f8ef7;
      --accent2:   #7c6af7;
      --text:      #e8edf5;
      --muted:     #6b7a99;
      --critique:  #ff4757;
      --elevee:    #ff6b35;
      --moyenne:   #ffa502;
      --faible:    #2ed573;
    }

    html, body, [class*="css"] {
      font-family: 'DM Sans', sans-serif;
      background-color: var(--bg) !important;
      color: var(--text) !important;
    }

    /* ── Sidebar ── */
    [data-testid="stSidebar"] {
      background: var(--surface) !important;
      border-right: 1px solid var(--border) !important;
    }
    [data-testid="stSidebar"] * { color: var(--text) !important; }

    .sidebar-logo {
      display: flex;
      align-items: center;
      gap: 10px;
      padding: 1.2rem 0 1rem;
      border-bottom: 1px solid var(--border);
      margin-bottom: 1.4rem;
    }
    .sidebar-logo .icon {
      width: 38px; height: 38px;
      background: linear-gradient(135deg, var(--accent), var(--accent2));
      border-radius: 10px;
      display: flex; align-items: center; justify-content: center;
      font-size: 1.1rem;
    }
    .sidebar-logo .brand { font-family: 'Syne', sans-serif; font-weight: 800; font-size: 1rem; }
    .sidebar-logo .sub   { font-size: 0.7rem; color: var(--muted); }

    .nav-item {
      display: flex; align-items: center; gap: 10px;
      padding: 0.65rem 0.9rem;
      border-radius: 8px;
      margin-bottom: 4px;
      cursor: pointer;
      font-size: 0.88rem;
      font-weight: 500;
      color: var(--muted) !important;
      transition: all 0.2s;
    }
    .nav-item:hover  { background: rgba(79,142,247,0.08); color: var(--text) !important; }
    .nav-item.active { background: rgba(79,142,247,0.14); color: var(--accent) !important; border-left: 2px solid var(--accent); }
    .nav-icon        { font-size: 1rem; width: 20px; text-align: center; }

    .status-pill {
      display: inline-flex; align-items: center; gap: 6px;
      padding: 5px 10px; border-radius: 20px;
      font-size: 0.75rem; font-weight: 600;
      background: rgba(46,213,115,0.1);
      border: 1px solid rgba(46,213,115,0.3);
      color: var(--faible);
    }
    .status-pill.offline {
      background: rgba(255,71,87,0.1);
      border-color: rgba(255,71,87,0.3);
      color: var(--critique);
    }
    .status-dot { width: 7px; height: 7px; border-radius: 50%; background: currentColor; }

    /* ── Page header ── */
    .page-header {
      padding: 2rem 0 1.5rem;
      border-bottom: 1px solid var(--border);
      margin-bottom: 2rem;
    }
    .page-header .tag {
      display: inline-flex; align-items: center; gap: 6px;
      background: rgba(79,142,247,0.1);
      border: 1px solid rgba(79,142,247,0.25);
      color: var(--accent);
      padding: 3px 10px; border-radius: 20px;
      font-size: 0.72rem; font-weight: 600; letter-spacing: 0.08em;
      text-transform: uppercase; margin-bottom: 0.6rem;
    }
    .page-header h1 {
      font-family: 'Syne', sans-serif;
      font-size: 1.9rem; font-weight: 800;
      color: var(--text); margin: 0 0 0.3rem;
    }
    .page-header p { color: var(--muted); font-size: 0.88rem; margin: 0; }

    /* ── KPI cards ── */
    .kpi-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 14px; margin-bottom: 1.8rem; }
    .kpi-card {
      background: var(--surface2);
      border: 1px solid var(--border);
      border-radius: 12px;
      padding: 1.1rem 1.2rem;
      position: relative; overflow: hidden;
      transition: border-color 0.2s;
    }
    .kpi-card:hover { border-color: var(--border2); }
    .kpi-card .kpi-label  { font-size: 0.73rem; color: var(--muted); font-weight: 500; text-transform: uppercase; letter-spacing: 0.06em; margin-bottom: 0.4rem; }
    .kpi-card .kpi-value  { font-family: 'Syne', sans-serif; font-size: 1.7rem; font-weight: 700; color: var(--text); line-height: 1; }
    .kpi-card .kpi-sub    { font-size: 0.75rem; color: var(--muted); margin-top: 4px; }
    .kpi-card .kpi-accent { position: absolute; top: 0; right: 0; width: 60px; height: 60px; border-radius: 0 12px 0 60px; opacity: 0.12; }

    /* ── Section titles ── */
    .section-title {
      font-family: 'Syne', sans-serif;
      font-size: 1rem; font-weight: 700;
      color: var(--text); margin: 1.6rem 0 1rem;
      display: flex; align-items: center; gap: 8px;
    }
    .section-title::after {
      content: ''; flex: 1; height: 1px;
      background: var(--border); margin-left: 8px;
    }

    /* ── Stock table ── */
    .stock-row {
      display: grid; grid-template-columns: 2fr 1fr 1fr 1fr 100px;
      align-items: center; gap: 12px;
      padding: 0.8rem 1rem;
      border-radius: 8px; margin-bottom: 6px;
      background: var(--surface2);
      border: 1px solid var(--border);
      transition: border-color 0.2s;
    }
    .stock-row:hover { border-color: var(--border2); }
    .stock-row .mat-name { font-weight: 600; font-size: 0.9rem; }
    .stock-row .mat-val  { font-size: 0.85rem; color: var(--muted); }
    .stock-header {
      display: grid; grid-template-columns: 2fr 1fr 1fr 1fr 100px;
      gap: 12px; padding: 0 1rem 0.5rem;
      font-size: 0.72rem; color: var(--muted);
      text-transform: uppercase; letter-spacing: 0.06em; font-weight: 600;
    }

    /* ── Status badges ── */
    .badge {
      display: inline-flex; align-items: center; gap: 5px;
      padding: 3px 10px; border-radius: 20px;
      font-size: 0.73rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em;
    }
    .badge-critique { background: rgba(255,71,87,0.12);  color: var(--critique); border: 1px solid rgba(255,71,87,0.3); }
    .badge-élevée   { background: rgba(255,107,53,0.12); color: var(--elevee);   border: 1px solid rgba(255,107,53,0.3); }
    .badge-moyenne  { background: rgba(255,165,2,0.12);  color: var(--moyenne);  border: 1px solid rgba(255,165,2,0.3); }
    .badge-faible   { background: rgba(46,213,115,0.12); color: var(--faible);   border: 1px solid rgba(46,213,115,0.3); }
    .badge-ok       { background: rgba(46,213,115,0.12); color: var(--faible);   border: 1px solid rgba(46,213,115,0.3); }
    .badge-rupture  { background: rgba(255,71,87,0.12);  color: var(--critique); border: 1px solid rgba(255,71,87,0.3); }
    .badge-seuil    { background: rgba(255,165,2,0.12);  color: var(--moyenne);  border: 1px solid rgba(255,165,2,0.3); }

    /* ── AI card ── */
    .ai-card {
      background: var(--surface2);
      border-radius: 14px; padding: 1.5rem;
      border: 1px solid var(--border);
      margin: 1rem 0 1.4rem;
      position: relative; overflow: hidden;
    }
    .ai-card::before {
      content: ''; position: absolute;
      top: 0; left: 0; right: 0; height: 2px;
      background: linear-gradient(90deg, var(--accent), var(--accent2));
    }
    .ai-card .ai-header {
      display: flex; justify-content: space-between; align-items: flex-start;
      margin-bottom: 1.2rem;
    }
    .ai-card .ai-title {
      font-family: 'Syne', sans-serif; font-size: 1rem; font-weight: 700; margin: 0;
    }
    .ai-card .ai-source { font-size: 0.75rem; color: var(--muted); margin-top: 2px; }
    .ai-metrics {
      display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; margin-bottom: 1.2rem;
    }
    .ai-metric {
      background: rgba(255,255,255,0.03);
      border: 1px solid var(--border); border-radius: 8px; padding: 0.7rem;
    }
    .ai-metric .m-label { font-size: 0.7rem; color: var(--muted); text-transform: uppercase; letter-spacing: 0.06em; margin-bottom: 3px; }
    .ai-metric .m-val   { font-family: 'Syne', sans-serif; font-size: 1.1rem; font-weight: 700; }
    .ai-metric .m-val.negative { color: var(--critique); }
    .ai-metric .m-val.positive { color: var(--faible); }
    .ai-justif {
      background: rgba(79,142,247,0.05);
      border: 1px solid rgba(79,142,247,0.15);
      border-radius: 8px; padding: 0.8rem 1rem;
      font-size: 0.85rem; line-height: 1.6; color: var(--text);
    }
    .ai-justif .jlabel { font-size: 0.7rem; color: var(--accent); font-weight: 600; text-transform: uppercase; letter-spacing: 0.06em; margin-bottom: 4px; }

    /* ── Supplier card ── */
    .sup-card {
      background: var(--surface2);
      border: 1px solid var(--border);
      border-radius: 12px; padding: 1.1rem 1.2rem;
      margin-bottom: 10px; transition: all 0.2s;
    }
    .sup-card:hover { border-color: var(--border2); }
    .sup-card.selected { border-color: rgba(46,213,115,0.5); background: rgba(46,213,115,0.04); }
    .sup-card .sup-name { font-family: 'Syne', sans-serif; font-weight: 700; font-size: 0.95rem; margin-bottom: 4px; }
    .sup-card .sup-loc  { font-size: 0.8rem; color: var(--muted); margin-bottom: 8px; }
    .sup-stats { display: flex; gap: 18px; flex-wrap: wrap; }
    .sup-stat  { font-size: 0.82rem; }
    .sup-stat span { color: var(--muted); }
    .sup-stat strong { color: var(--text); }

    /* ── Order summary ── */
    .order-summary {
      background: var(--surface2);
      border: 1px solid var(--border); border-radius: 12px; padding: 1.3rem 1.5rem;
      margin: 1rem 0;
    }
    .order-summary h4 {
      font-family: 'Syne', sans-serif; font-weight: 700; margin: 0 0 1rem;
      font-size: 0.95rem; color: var(--text);
    }
    .order-row {
      display: flex; justify-content: space-between; align-items: center;
      padding: 0.45rem 0; border-bottom: 1px solid var(--border);
      font-size: 0.85rem;
    }
    .order-row:last-child { border-bottom: none; }
    .order-row .ok  { color: var(--muted); }
    .order-row .ov  { font-weight: 600; color: var(--text); }
    .order-row .price { font-family: 'Syne', sans-serif; font-weight: 700; color: var(--accent); font-size: 1rem; }

    /* ── Info/Warning banners ── */
    .info-banner {
      background: rgba(79,142,247,0.08);
      border: 1px solid rgba(79,142,247,0.2);
      border-radius: 8px; padding: 0.75rem 1rem;
      font-size: 0.85rem; color: var(--text);
      margin: 0.6rem 0;
    }

    /* ── Streamlit overrides ── */
    .stButton > button {
      font-family: 'DM Sans', sans-serif !important;
      font-weight: 600 !important; font-size: 0.85rem !important;
      border-radius: 8px !important;
      transition: all 0.2s !important;
    }
    .stButton > button[kind="primary"] {
      background: linear-gradient(135deg, var(--accent), var(--accent2)) !important;
      border: none !important; color: #fff !important;
    }
    .stButton > button[kind="primary"]:hover {
      opacity: 0.88 !important; transform: translateY(-1px) !important;
    }
    .stButton > button[kind="secondary"] {
      background: transparent !important;
      border: 1px solid var(--border2) !important; color: var(--text) !important;
    }
    .stButton > button[kind="secondary"]:hover {
      background: rgba(255,255,255,0.05) !important; transform: translateY(-1px) !important;
    }
    div[data-testid="stDataFrame"] { border-radius: 10px; overflow: hidden; }
    div[data-testid="stSelectbox"] label,
    div[data-testid="stToggle"] label { font-size: 0.83rem !important; color: var(--muted) !important; }
    .stSelectbox > div > div { background: var(--surface2) !important; border-color: var(--border) !important; }
    .stAlert { border-radius: 8px !important; }
    .stSpinner > div { border-top-color: var(--accent) !important; }
    div[data-testid="stTabs"] button {
      font-family: 'DM Sans', sans-serif !important;
      font-size: 0.85rem !important; font-weight: 500 !important;
    }
    div[data-testid="stDownloadButton"] button {
      background: linear-gradient(135deg, var(--accent), var(--accent2)) !important;
      border: none !important; color: #fff !important;
      font-weight: 600 !important; border-radius: 8px !important;
    }
    hr { border-color: var(--border) !important; margin: 1.2rem 0 !important; }
    #MainMenu { visibility: hidden; }
    footer     { visibility: hidden; }
    </style>
    """, unsafe_allow_html=True)


# ─── Helpers UI ───────────────────────────────────────────────────────────────

def badge(urgence: str) -> str:
    icon = URGENCE_ICONS.get(urgence, "⚪")
    return f'<span class="badge badge-{urgence}">{icon} {urgence.upper()}</span>'


def stock_badge(stock_futur, seuil):
    if stock_futur < 0:
        return '<span class="badge badge-rupture">⛔ RUPTURE</span>'
    if stock_futur < seuil:
        return '<span class="badge badge-seuil">⚠️ SOUS SEUIL</span>'
    return '<span class="badge badge-ok">✅ OK</span>'


# ─── PAGES ────────────────────────────────────────────────────────────────────

def page_analyse(agent: GroqAgent):
    # ── Sidebar controls ──────────────────────────────────────────────────
    with st.sidebar:
        st.markdown("""
        <div class="sidebar-logo">
          <div class="icon">🏭</div>
          <div><div class="brand">StockIA</div>
               <div class="sub">Système de gestion</div></div>
        </div>
        """, unsafe_allow_html=True)

        matieres = agent.get_matieres()
        matiere  = st.selectbox("Matière à analyser", matieres, key="matiere_select")
        use_llm  = st.toggle("Utiliser Groq (LLM)", value=True)
        st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)

        # API status
        try:
            r = requests.get(f"{SUPPLIER_API_URL}/health", timeout=2)
            if r.ok:
                nb = ""
                try:
                    fr = requests.get(f"{SUPPLIER_API_URL}/fournisseurs", timeout=2)
                    nb = f" · {fr.json()['total']} fournisseurs" if fr.ok else ""
                except Exception:
                    pass
                st.markdown(f'<div class="status-pill"><div class="status-dot"></div>API connectée{nb}</div>', unsafe_allow_html=True)
            else:
                raise Exception()
        except Exception:
            st.markdown('<div class="status-pill offline"><div class="status-dot"></div>API hors ligne</div>', unsafe_allow_html=True)

        st.markdown("<hr>", unsafe_allow_html=True)
        if st.button("🔄 Recharger les CSV", use_container_width=True):
            agent.charger_csv()
            # Réinitialiser l'état après rechargement
            for key in ["decision", "decision_id", "etape", "recommandations", "commande_data", "fournisseur_selectionne", "modification_activee", "quantite_modifiee", "last_matiere"]:
                st.session_state.pop(key, None)
            st.success("CSV rechargés !")

    # ── Page header ───────────────────────────────────────────────────────
    st.markdown("""
    <div class="page-header">
      <div class="tag">🤖 IA · Logistique</div>
      <h1>Gestion des Stocks IA</h1>
      <p>Analyse prédictive · Validation humaine · Sélection fournisseur · Génération PDF</p>
    </div>
    """, unsafe_allow_html=True)

    # ── KPI cards ─────────────────────────────────────────────────────────
    all_stocks = []
    for _, row in agent.stocks_df.iterrows():
        info = agent.calculer_stock_futur(row["nom"])
        all_stocks.append(info)

    nb_rupture    = sum(1 for s in all_stocks if s["stock_futur"] < 0)
    nb_sous_seuil = sum(1 for s in all_stocks if 0 <= s["stock_futur"] < s["seuil_reappro"])
    nb_ok         = sum(1 for s in all_stocks if s["stock_futur"] >= s["seuil_reappro"])
    nb_total      = len(all_stocks)

    st.markdown(f"""
    <div class="kpi-grid">
      <div class="kpi-card">
        <div class="kpi-accent" style="background:#4f8ef7"></div>
        <div class="kpi-label">Total matières</div>
        <div class="kpi-value">{nb_total}</div>
        <div class="kpi-sub">en surveillance</div>
      </div>
      <div class="kpi-card">
        <div class="kpi-accent" style="background:#ff4757"></div>
        <div class="kpi-label">Ruptures</div>
        <div class="kpi-value" style="color:#ff4757">{nb_rupture}</div>
        <div class="kpi-sub">stock futur négatif</div>
      </div>
      <div class="kpi-card">
        <div class="kpi-accent" style="background:#ffa502"></div>
        <div class="kpi-label">Sous seuil</div>
        <div class="kpi-value" style="color:#ffa502">{nb_sous_seuil}</div>
        <div class="kpi-sub">réapprovisionnement requis</div>
      </div>
      <div class="kpi-card">
        <div class="kpi-accent" style="background:#2ed573"></div>
        <div class="kpi-label">Statut OK</div>
        <div class="kpi-value" style="color:#2ed573">{nb_ok}</div>
        <div class="kpi-sub">niveaux satisfaisants</div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Stock overview table ───────────────────────────────────────────────
    st.markdown('<div class="section-title">📊 Vue d\'ensemble des stocks</div>', unsafe_allow_html=True)
    st.markdown("""
    <div class="stock-header">
      <div>Matière</div><div>Stock actuel</div><div>Consommation</div><div>Stock futur</div><div>Statut</div>
    </div>
    """, unsafe_allow_html=True)

    for s in all_stocks:
        sb = stock_badge(s["stock_futur"], s["seuil_reappro"])
        st.markdown(f"""
        <div class="stock-row">
          <div class="mat-name">{s['nom']}</div>
          <div class="mat-val">{s['stock_actuel']:,}</div>
          <div class="mat-val">{s['conso_prevue']:,.1f}</div>
          <div class="mat-val" style="color:{'#ff4757' if s['stock_futur']<0 else '#e8edf5'}">
            {s['stock_futur']:,.1f}
          </div>
          <div>{sb}</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<hr>", unsafe_allow_html=True)

    # ── AI analysis ───────────────────────────────────────────────────────
    st.markdown(f'<div class="section-title">🔍 Analyse IA — {matiere}</div>', unsafe_allow_html=True)

    # Réinitialiser l'état quand la matière change
    if "last_matiere" not in st.session_state:
        st.session_state.last_matiere = matiere
    elif st.session_state.last_matiere != matiere:
        # La matière a changé, on réinitialise l'état
        for key in ["decision", "decision_id", "etape", "recommandations", "commande_data", "fournisseur_selectionne", "modification_activee", "quantite_modifiee"]:
            st.session_state.pop(key, None)
        st.session_state.last_matiere = matiere

    if st.button("🚀 Lancer l'analyse IA", type="primary", use_container_width=True):
        with st.spinner("Analyse en cours…"):
            if use_llm and agent.groq_ok:
                decision = agent.proposer_decision_llm(matiere)
            else:
                decision = agent.proposer_decision_regles(matiere)
            st.session_state["decision"] = decision
            st.session_state["decision_id"] = agent.enregistrer_proposition(decision)
            st.session_state["etape"] = "ia_analyse"
            st.session_state["modification_activee"] = False
            if "quantite_modifiee" in st.session_state:
                del st.session_state.quantite_modifiee

    # ── AI proposal ───────────────────────────────────────────────────────
    if "decision" in st.session_state and st.session_state.get("etape") == "ia_analyse":
        decision = st.session_state["decision"]
        urgence = decision.get("urgence", "faible")
        source = "🤖 Groq LLM" if decision.get("source") == "groq_llm" else "⚙️ Règles métier"
        action = decision.get("action", "?").upper()
        futur = decision.get("stock_futur", 0)
        futur_cls = "negative" if futur < 0 else "positive"
        
        # Récupérer la quantité actuelle (priorité à la quantité modifiée)
        quantite_affichee = st.session_state.get("quantite_modifiee", decision.get("quantite", 0))

        st.markdown(f"""
        <div class="ai-card">
          <div class="ai-header">
            <div>
              <div class="ai-title">Proposition IA — {action}</div>
              <div class="ai-source">Source : {source}</div>
            </div>
            {badge(urgence)}
          </div>
          <div class="ai-metrics">
            <div class="ai-metric">
              <div class="m-label">Stock actuel</div>
              <div class="m-val">{decision.get('stock_actuel', 0):,}</div>
            </div>
            <div class="ai-metric">
              <div class="m-label">Consommation prévue</div>
              <div class="m-val">{decision.get('conso_prevue', 0):,.1f}</div>
            </div>
            <div class="ai-metric">
              <div class="m-label">Stock futur</div>
              <div class="m-val {futur_cls}">{futur:,.1f}</div>
            </div>
          </div>
          <div class="ai-metric" style="margin-bottom:12px">
            <div class="m-label">Quantité à commander</div>
            <div class="m-val" style="color:#4f8ef7">{quantite_affichee:,.0f} unités</div>
          </div>
          <div class="ai-justif">
            <div class="jlabel">Justification</div>
            {decision.get('justification', '—')}
          </div>
        </div>
        """, unsafe_allow_html=True)

        # Créer 3 colonnes pour les boutons
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("✅ Accepter la proposition", use_container_width=True, type="primary", key="accept_btn"):
                # Mettre à jour la décision avec la quantité modifiée
                if "quantite_modifiee" in st.session_state:
                    decision["quantite"] = st.session_state.quantite_modifiee
                    decision["source"] = "humain_modifie"
                    st.session_state["decision"] = decision
                st.session_state["etape"] = "selection_fournisseur"
                st.session_state["modification_activee"] = False
                st.rerun()
        
        with col2:
            # Bouton Modifier ou interface de modification
            if not st.session_state.get("modification_activee", False):
                if st.button("✏️ Modifier la quantité", use_container_width=True, key="modify_btn"):
                    st.session_state["modification_activee"] = True
                    st.rerun()
            else:
                # Interface de modification
                current_qty = st.session_state.get("quantite_modifiee", decision.get("quantite", 0))
                nouvelle_qte = st.number_input(
                    "Nouvelle quantité", 
                    min_value=0, 
                    value=int(current_qty),
                    step=100,
                    key="modif_quantite_input"
                )
                col_modif1, col_modif2 = st.columns(2)
                with col_modif1:
                    if st.button("✅ Appliquer", use_container_width=True, key="apply_modif"):
                        st.session_state.quantite_modifiee = nouvelle_qte
                        st.session_state["modification_activee"] = False
                        st.success(f"✅ Quantité modifiée : {nouvelle_qte} unités")
                        st.rerun()
                with col_modif2:
                    if st.button("❌ Annuler", use_container_width=True, key="cancel_modif"):
                        st.session_state["modification_activee"] = False
                        if "quantite_modifiee" in st.session_state:
                            # Ne pas supprimer, juste désactiver le mode modification
                            pass
                        st.rerun()
        
        with col3:
            if st.button("❌ Rejeter", use_container_width=True, key="reject_btn"):
                agent.maj_statut_decision(st.session_state["decision_id"], "rejetee")
                st.warning("Proposition rejetée.")
                # Nettoyer l'état
                for key in ["decision", "etape", "modification_activee", "quantite_modifiee"]:
                    st.session_state.pop(key, None)
                st.rerun()

    # ── Supplier selection ─────────────────────────────────────────────────
    if st.session_state.get("etape") == "selection_fournisseur":
        decision = st.session_state["decision"]
        matiere  = decision.get("matiere")
        # Utiliser la quantité modifiée si disponible
        quantite = st.session_state.get("quantite_modifiee", decision.get("quantite"))
        urgence  = decision.get("urgence", "moyenne")

        st.markdown('<div class="section-title">🏢 Sélection du fournisseur</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="info-banner">🔎 Recherche pour <strong>{matiere}</strong> — quantité : <strong>{quantite:,.0f} unités</strong> — urgence : {badge(urgence)}</div>',
                    unsafe_allow_html=True)

        if st.button("🔍 Rechercher des fournisseurs", type="primary", use_container_width=True):
            with st.spinner("Consultation des fournisseurs…"):
                recommandations = appeler_recommandations(matiere, quantite, urgence)
                st.session_state["recommandations"]      = recommandations
                st.session_state["fournisseur_selectionne"] = None

        if "recommandations" in st.session_state:
            recommandations = st.session_state["recommandations"]

            if recommandations:
                if st.button("📄 Exporter la liste (PDF)", use_container_width=True):
                    pdf_path = generer_pdf_recommandations(recommandations, matiere, quantite)
                    with open(pdf_path, "rb") as f:
                        st.download_button("📥 Télécharger PDF recommandations",
                                           data=f, file_name=Path(pdf_path).name,
                                           mime="application/pdf")

                st.markdown(f"<div style='font-size:0.8rem;color:var(--muted);margin-bottom:10px'>{len(recommandations)} fournisseur(s) trouvé(s)</div>", unsafe_allow_html=True)

                for idx, rec in enumerate(recommandations):
                    fournisseur = rec["fournisseur"]
                    selected    = st.session_state.get("fournisseur_selectionne") == idx
                    sel_cls     = "selected" if selected else ""

                    col1, col2 = st.columns([4, 1])
                    with col1:
                        st.markdown(f"""
                        <div class="sup-card {sel_cls}">
                          <div class="sup-name">{fournisseur['nom']}</div>
                          <div class="sup-loc">📍 {fournisseur['ville']}, {fournisseur['pays']}</div>
                          <div class="sup-stats">
                            <div class="sup-stat"><span>Score </span><strong>{rec['score']}/5</strong></div>
                            <div class="sup-stat"><span>Qualité </span><strong>⭐ {fournisseur['qualite']}/5</strong></div>
                            <div class="sup-stat"><span>Prix total </span><strong>{rec['prix_total']:,.2f} €</strong></div>
                            <div class="sup-stat"><span>Unitaire </span><strong>{rec['prix_unitaire']:.2f} €</strong></div>
                            <div class="sup-stat"><span>Délai </span><strong>🚚 {rec['delai_jours']} j</strong></div>
                            <div class="sup-stat"><span>Livraison </span><strong>{rec['date_livraison_prevue']}</strong></div>
                          </div>
                          <div style="font-size:0.78rem;color:var(--muted);margin-top:8px;font-style:italic">{fournisseur['description']}</div>
                        </div>
                        """, unsafe_allow_html=True)
                    with col2:
                        st.markdown("<div style='height:38px'></div>", unsafe_allow_html=True)
                        if st.button("✅ Choisir", key=f"select_{idx}", use_container_width=True, type="primary"):
                            st.session_state["fournisseur_selectionne"] = idx
                            st.session_state["commande_data"] = {
                                "matiere": matiere, 
                                "quantite": quantite,
                                "fournisseur_id":       fournisseur["id"],
                                "fournisseur_nom":      fournisseur["nom"],
                                "fournisseur_contact":  fournisseur["email"],
                                "fournisseur_telephone": fournisseur["telephone"],
                                "fournisseur_email":    fournisseur["email"],
                                "prix_total":           rec["prix_total"],
                                "prix_unitaire":        rec["prix_unitaire"],
                                "delai_jours":          rec["delai_jours"],
                                "date_livraison_prevue": rec["date_livraison_prevue"],
                                "decision_ia_id":       st.session_state.get("decision_id"),
                                "action_ia":            decision.get("action"),
                                "justification_ia":     decision.get("justification"),
                            }
                            st.rerun()
            else:
                st.warning("Aucun fournisseur trouvé pour cette matière.")

    # ── Order validation ───────────────────────────────────────────────────
    if st.session_state.get("commande_data"):
        commande_data = st.session_state["commande_data"]

        st.markdown('<div class="section-title">✅ Validation de la commande</div>', unsafe_allow_html=True)
        st.markdown(f"""
        <div class="order-summary">
          <h4>Récapitulatif de la commande</h4>
          <div class="order-row"><span class="ok">Fournisseur</span><span class="ov">{commande_data['fournisseur_nom']}</span></div>
          <div class="order-row"><span class="ok">Matière</span><span class="ov">{commande_data['matiere']}</span></div>
          <div class="order-row"><span class="ok">Quantité</span><span class="ov">{commande_data['quantite']:,.0f} unités</span></div>
          <div class="order-row"><span class="ok">Prix unitaire</span><span class="ov">{commande_data['prix_unitaire']:.2f} €</span></div>
          <div class="order-row"><span class="ok">Prix total</span><span class="price">{commande_data['prix_total']:,.2f} €</span></div>
          <div class="order-row"><span class="ok">Délai de livraison</span><span class="ov">{commande_data['delai_jours']} jours</span></div>
          <div class="order-row"><span class="ok">Livraison prévue</span><span class="ov">{commande_data['date_livraison_prevue']}</span></div>
        </div>
        """, unsafe_allow_html=True)

        col1, col2 = st.columns(2)
        with col1:
            if st.button("✅ Confirmer et commander", type="primary", use_container_width=True):
                with st.spinner("Passation de la commande…"):
                    urgence_dec = st.session_state.get("decision", {}).get("urgence", "")
                    resultat = passer_commande(
                        commande_data["matiere"], commande_data["quantite"],
                        commande_data["fournisseur_id"], commande_data.get("decision_ia_id"),
                        "express" if urgence_dec == "critique" else "standard"
                    )
                    if resultat.get("statut") in ["accepté", "retardé"]:
                        st.success(f"✅ Commande {resultat.get('statut')} !")
                        commande_data["statut"] = resultat.get("statut")
                        commande_data["delai_jours"] = resultat.get("delai_jours", commande_data["delai_jours"])
                        commande_data["date_livraison_prevue"] = resultat.get("date_livraison_prevue", commande_data["date_livraison_prevue"])
                        st.session_state["commande_data"] = commande_data
                        st.session_state["etape"]         = "pdf_generation"
                        st.rerun()
                    else:
                        st.error(f"❌ Commande refusée : {resultat.get('message')}")
        with col2:
            if st.button("📄 Générer le PDF", use_container_width=True):
                st.session_state["etape"] = "pdf_generation"
                st.rerun()

    # ── PDF generation ─────────────────────────────────────────────────────
    if st.session_state.get("etape") == "pdf_generation":
        commande_data = st.session_state["commande_data"]
        st.markdown('<div class="section-title">📄 Bon de commande PDF</div>', unsafe_allow_html=True)

        if st.button("📥 Générer et télécharger le PDF", type="primary", use_container_width=True):
            with st.spinner("Génération du PDF…"):
                pdf_path = generer_pdf_commande(commande_data)
                with open(pdf_path, "rb") as f:
                    st.download_button(
                        label="📄 Télécharger le bon de commande",
                        data=f, file_name=Path(pdf_path).name,
                        mime="application/pdf", use_container_width=True
                    )
                st.success("✅ PDF généré avec succès !")
                if "decision_id" in st.session_state:
                    get_agent().maj_statut_decision(st.session_state["decision_id"], "validee_avec_commande")

        if st.button("🏠 Retour à l'accueil", use_container_width=True):
            for key in ["decision", "recommandations", "commande_data", "etape", "fournisseur_selectionne", "modification_activee", "quantite_modifiee"]:
                st.session_state.pop(key, None)
            st.rerun()


def page_historique(agent: GroqAgent):
    with st.sidebar:
        st.markdown("""
        <div class="sidebar-logo">
          <div class="icon">🏭</div>
          <div><div class="brand">StockIA</div>
               <div class="sub">Système de gestion</div></div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("""
    <div class="page-header">
      <div class="tag">📜 Historique</div>
      <h1>Commandes passées</h1>
      <p>Journal de toutes les commandes fournisseurs validées</p>
    </div>
    """, unsafe_allow_html=True)

    try:
      resp = requests.get(f"{SUPPLIER_API_URL}/historique_commandes", timeout=5)
      if resp.status_code == 200:
        commandes = resp.json()
        if commandes:
          df = pd.DataFrame(commandes)
          st.dataframe(df, use_container_width=True, hide_index=True)
          return
        st.markdown('<div class="info-banner">📭 Aucune commande enregistrée pour l\'instant.</div>', unsafe_allow_html=True)
        return
      st.warning("API historique indisponible, lecture locale en cours…")
    except Exception:
      st.warning("API historique indisponible, lecture locale en cours…")

    df_local = charger_historique_local()
    if not df_local.empty:
      st.dataframe(df_local, use_container_width=True, hide_index=True)
    else:
      st.markdown('<div class="info-banner">📭 Aucun historique local disponible.</div>', unsafe_allow_html=True)


def page_donnees(agent: GroqAgent):
    with st.sidebar:
        st.markdown("""
        <div class="sidebar-logo">
          <div class="icon">🏭</div>
          <div><div class="brand">StockIA</div>
               <div class="sub">Système de gestion</div></div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("""
    <div class="page-header">
      <div class="tag">📂 Données</div>
      <h1>Données brutes</h1>
      <p>Consultation des fichiers CSV chargés en mémoire</p>
    </div>
    """, unsafe_allow_html=True)

    t1, t2, t3 = st.tabs(["📦 Stocks", "📉 Consommation", "📋 Commandes"])
    with t1:
        st.dataframe(agent.stocks_df, use_container_width=True, hide_index=True)
    with t2:
        st.dataframe(agent.consommation_df, use_container_width=True, hide_index=True)
    with t3:
        st.dataframe(agent.commandes_df, use_container_width=True, hide_index=True)


# ─── MAIN ─────────────────────────────────────────────────────────────────────

def main():
    st.set_page_config(page_title="StockIA — Gestion des stocks", page_icon="🏭", layout="wide")
    inject_css()

    agent = get_agent()

    with st.sidebar:
        page = st.radio(
            "Navigation",
            ["Analyse & Validation", "Historique", "Données brutes"],
            label_visibility="collapsed"
        )

    if page == "Analyse & Validation":
        page_analyse(agent)
    elif page == "Historique":
        page_historique(agent)
    elif page == "Données brutes":
        page_donnees(agent)


if __name__ == "__main__":
    main()