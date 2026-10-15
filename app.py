%%writefile app.py
import streamlit as st
import feedparser
import pandas as pd
from datetime import datetime
import time
import urllib.parse

# ==========================================
# 1. CONFIGURATION & DESIGN (Charte Enedis)
# ==========================================
st.set_page_config(page_title="Veille Territoriale Enedis", page_icon="⚡", layout="wide")

# CSS pour les cartes d'actualités
st.markdown("""
    <style>
    .news-card {
        background-color: #ffffff; padding: 20px; border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1); margin-bottom: 15px;
        border-left: 5px solid #004F9F;
    }
    .source-badge { background-color: #e6f0ff; color: #004F9F; padding: 4px 10px; border-radius: 12px; font-weight: bold; font-size: 0.8em; }
    </style>
""", unsafe_allow_html=True)

# En-tête personnalisé
st.markdown("""
    <div style="text-align: center; margin-bottom: 20px;">
        <h1 style="color: #004F9F; font-size: 2.8em; font-weight: 900; margin-bottom: 0px; text-transform: uppercase;">
            ENEDIS | LÉLIO CORNUAULT
        </h1>
        <h3 style="color: #555555; font-size: 1.5em; font-weight: 300; margin-top: 5px;">
            Direction Territoriale - Veille Stratégique & Intelligence Économique
        </h3>
        <hr style="border: 2px solid #004F9F; width: 100%; margin-top: 20px;">
    </div>
""", unsafe_allow_html=True)

# ==========================================
# 2. MOTEUR DE RECHERCHE ULTRA-LOCAL (79 & 86)
# ==========================================
def make_google_rss(query):
    return f"https://news.google.com/rss/search?q={urllib.parse.quote(query)}&hl=fr&gl=FR&ceid=FR:fr"

TERRITOIRE = '("Vienne" OR "Deux-Sèvres" OR "Poitiers" OR "Niort" OR "Châtellerault" OR "Bressuire" OR "Parthenay")'

CATEGORIES = {
    "🚨 Pannes & Incidents": {
        "Coupures Locales": make_google_rss(f'("coupure" OR "panne" OR "incident" OR "rétablissement") AND "électricité" AND {TERRITOIRE}'),
    },
    "🏢 Enedis & Acteurs Locaux": {
        "Actualité Enedis Locale": make_google_rss(f'"Enedis" AND {TERRITOIRE}'),
        "Régies & Acteurs": make_google_rss(f'("Sorégies" OR "Alter Energies" OR "Syndicat d\'énergie" OR "SIVED") AND {TERRITOIRE}'),
    },
    "⚖️ Politique, Social & Juridique": {
        "Élus & Décisions": make_google_rss(f'("maire" OR "préfecture" OR "conseil départemental" OR "arrêté" OR "tribunal") AND "énergie" AND {TERRITOIRE}'),
        "Climat Social": make_google_rss(f'("grève" OR "syndicat" OR "recrutement" OR "CSE") AND "énergie" AND {TERRITOIRE}'),
    },
    "🌱 Projets EnR & Environnement": {
        "Développement EnR": make_google_rss(f'("solaire" OR "photovoltaïque" OR "éolien" OR "méthanisation" OR "biogaz") AND {TERRITOIRE}'),
        "EnR Spécialisé": "https://www.revolution-energetique.com/feed/"
    }
}

@st.cache_data(ttl=1800)
def fetch_news(cat_name):
    articles = []
    for source_name, url in CATEGORIES[cat_name].items():
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:10]:
                date_parsed = entry.get('published_parsed')
                clean_date = time.strftime('%d/%m/%Y à %H:%M', date_parsed) if date_parsed else 'Récent'
                articles.append({
                    "Source": source_name, "Titre": entry.title, 
                    "Lien": entry.link, "Date": clean_date
                })
        except: continue
    return pd.DataFrame(articles)

# ==========================================
# 3. INTERFACE DU RADAR
# ==========================================
col1, col2, col3 = st.columns(3)
col1.metric("Dernier balayage web", datetime.now().strftime('%H:%M'))
nb_sources = sum(len(sources) for sources in CATEGORIES.values())
col2.metric("Sources surveillées", f"{nb_sources} flux actifs")
col3.metric("Statut du radar", "🟢 Opérationnel")
st.divider()

search_query = st.text_input("🔍 Filtrer les résultats par mot-clé (ex: nom d'une commune, tempête, maire) :", "")

tab1, tab2, tab3, tab4 = st.tabs([
    "🚨 Pannes & Incidents", 
    "🏢 Enedis & Acteurs Locaux", 
    "⚖️ Politique, Social & Juridique", 
    "🌱 Projets EnR & Environnement"
])

def display_news_tab(category_name):
    df_cat = fetch_news(category_name)
    if not df_cat.empty:
        if search_query:
            df_cat = df_cat[df_cat["Titre"].str.contains(search_query, case=False, na=False)]
            
        for idx, row in df_cat.iterrows():
            st.markdown(f"""
                <div class="news-card">
                    <span class="source-badge">{row['Source']}</span>
                    <span style="float: right; color: gray; font-size: 0.85em;">📅 {row['Date']}</span>
                    <h4 style="margin-top: 10px;"><a href="{row['Lien']}" target="_blank" style="text-decoration: none; color: black;">{row['Titre']}</a></h4>
                </div>
            """, unsafe_allow_html=True)
    else:
        st.info("Aucune actualité détectée sur ce radar pour le moment.")

with tab1: display_news_tab("🚨 Pannes & Incidents")
with tab2: display_news_tab("🏢 Enedis & Acteurs Locaux")
with tab3: display_news_tab("⚖️ Politique, Social & Juridique")
with tab4: display_news_tab("🌱 Projets EnR & Environnement")
