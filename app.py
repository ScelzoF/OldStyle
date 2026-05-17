import streamlit as st

st.set_page_config(page_title="OldStyle - Diagnostica", page_icon="🌋")
st.title("🌋 OldStyle — Diagnostica Avvio")
st.info("Se vedi questa pagina, Streamlit funziona. Controllo moduli...")

errori = []

moduli = [
    ("pandas", "pandas"),
    ("numpy", "numpy"),
    ("requests", "requests"),
    ("plotly", "plotly"),
    ("folium", "folium"),
    ("streamlit_folium", "streamlit-folium"),
    ("sklearn", "scikit-learn"),
    ("scipy", "scipy"),
    ("feedparser", "feedparser"),
    ("bs4", "beautifulsoup4"),
    ("openai", "openai"),
    ("supabase", "supabase"),
]

for mod, pkg in moduli:
    try:
        __import__(mod)
        st.success(f"✅ {pkg}")
    except ImportError as e:
        st.error(f"❌ {pkg}: {e}")
        errori.append(pkg)

st.divider()
st.subheader("Moduli locali")
locali = ["data_service", "visualization", "emergency_info", "forum", "utils"]
for mod in locali:
    try:
        __import__(mod)
        st.success(f"✅ {mod}")
    except Exception as e:
        st.error(f"❌ {mod}: {e}")
        errori.append(mod)

if not errori:
    st.balloons()
    st.success("Tutto OK! L'app può partire normalmente.")
else:
    st.warning(f"Moduli mancanti: {errori}")
