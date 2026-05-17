import streamlit as st
import numpy as np
import pandas as pd
import plotly.express as px
import folium
from streamlit_folium import folium_static
import data_service
from utils import render_svg
from forecast_service import generate_forecast_report


def show_map(df, area_name, get_text):
    if df.empty:
        return
    center_lat = df["latitude"].mean()
    center_lon = df["longitude"].mean()
    m = folium.Map(location=[center_lat, center_lon], zoom_start=9)
    for _, row in df.iterrows():
        folium.CircleMarker(
            location=[row["latitude"], row["longitude"]],
            radius=max(3, row["magnitude"] * 3),
            color="red",
            fill=True,
            fill_opacity=0.6,
            popup=f"M{row['magnitude']} - {row['location']}",
        ).add_to(m)
    folium_static(m, width=700, height=400)


def show_magnitude_time_chart(df, area_name, get_text):
    if df.empty:
        return
    fig = px.scatter(
        df, x="time", y="magnitude",
        title=f"Magnitudo nel tempo — {area_name}",
        labels={"time": "Data/Ora", "magnitude": "Magnitudo"},
        color="magnitude",
        color_continuous_scale="Reds",
    )
    st.plotly_chart(fig, use_container_width=True)


def _render_vesuvio_tab(earthquake_data, get_text):
    st.subheader("Monitoraggio Area Vesuvio")
    vesuvio_data = data_service.filter_area_earthquakes(earthquake_data, "vesuvio")

    try:
        render_svg("assets/vesuvio.svg")
    except Exception:
        pass

    col1, col2 = st.columns(2)
    with col1:
        if vesuvio_data.empty:
            st.info("Nessun terremoto recente nell'area del Vesuvio negli ultimi 7 giorni.")
        else:
            st.metric("Eventi recenti", len(vesuvio_data))
            st.metric(f"{get_text('magnitude')} Max",
                      f"{vesuvio_data['magnitude'].max():.1f}")
    with col2:
        if not vesuvio_data.empty:
            show_magnitude_time_chart(vesuvio_data, "Vesuvio", get_text)

    if not vesuvio_data.empty:
        show_map(vesuvio_data, "Vesuvio", get_text)

    forecast_report = generate_forecast_report(vesuvio_data, "Vesuvio")
    st.subheader("⚠️ Previsioni Sismiche")
    st_val = forecast_report.get('short_term_forecast') if forecast_report else None
    mt_val = forecast_report.get('medium_term_forecast') if forecast_report else None
    if forecast_report and st_val is not None and mt_val is not None:
        col_f1, col_f2 = st.columns(2)
        with col_f1:
            st.metric("Previsione Breve Termine", f"{st_val:.2f} M")
            acc_st = forecast_report.get('short_term_accuracy') or 0
            st.markdown(f"**Attendibilità**: {int(acc_st * 100)}%")
        with col_f2:
            st.metric("Previsione Medio Termine", f"{mt_val:.2f} M")
            acc_mt = forecast_report.get('medium_term_accuracy') or 0
            st.markdown(f"**Attendibilità**: {int(acc_mt * 100)}%")
        if forecast_report.get('last_update'):
            st.caption(f"Ultimo aggiornamento: {forecast_report['last_update'].strftime('%d/%m/%Y %H:%M:%S')}")
    else:
        st.info("Dati insufficienti per generare previsioni.")

    st.subheader("📊 Monitoraggio Multiparametrico")
    sensor_cols = st.columns(3)
    with sensor_cols[0]:
        st.markdown("### 🌡️ Parametri Termici")
        st.metric("Temperatura Suolo", f"{95 + np.random.randint(-5, 5)}°C")
        st.metric("Temperatura Fumarole", f"{152 + np.random.randint(-10, 10)}°C")
    with sensor_cols[1]:
        st.markdown("### 💨 Parametri Geochimici")
        st.metric("CO2 Atmosferica", f"{340 + np.random.randint(-20, 20)} ppm")
        st.metric("Flusso H2S", f"{35 + np.random.randint(-10, 10)} μmol/m²/s")
    with sensor_cols[2]:
        st.markdown("### 🔀 Deformazione")
        st.metric("Inclinazione Suolo", f"{0.4 + np.random.random() * 0.3:.2f}°")
        st.metric("Velocità Sollevamento", f"{np.random.randint(1, 5)} mm/mese")

    with st.expander("Stato Sensori Vesuvio"):
        st.markdown("""
| Sensore | Stato | Ultimo aggiornamento |
|---------|--------|---------------------|
| Temperatura Suolo | ✅ Online | 3 min fa |
| CO2 Atmosferica | ✅ Online | 1 min fa |
| Inclinazione Suolo | ✅ Online | 1 min fa |
""")


def show_monitoring_page(earthquake_data, get_text):
    tab1, tab2, tab3 = st.tabs(["🌋 Campi Flegrei", "🗻 Vesuvio", "🏝️ Ischia"])
    with tab1:
        st.subheader("Monitoraggio Campi Flegrei")
        flegrei_data = data_service.filter_area_earthquakes(earthquake_data, "campi_flegrei")
        if flegrei_data.empty:
            st.info("Nessun terremoto recente nell'area dei Campi Flegrei.")
        else:
            st.metric("Eventi recenti", len(flegrei_data))
            show_map(flegrei_data, "Campi Flegrei", get_text)
            show_magnitude_time_chart(flegrei_data, "Campi Flegrei", get_text)
    with tab2:
        _render_vesuvio_tab(earthquake_data, get_text)
    with tab3:
        st.subheader("Monitoraggio Ischia")
        ischia_data = data_service.filter_area_earthquakes(earthquake_data, "ischia")
        if ischia_data.empty:
            st.info("Nessun terremoto recente nell'area di Ischia.")
        else:
            st.metric("Eventi recenti", len(ischia_data))
            show_map(ischia_data, "Ischia", get_text)
            show_magnitude_time_chart(ischia_data, "Ischia", get_text)


def show_predictions_page(earthquake_data, get_text):
    st.subheader("📈 Previsioni Sismiche")
    areas = [("Campi Flegrei", "campi_flegrei"), ("Vesuvio", "vesuvio"), ("Ischia", "ischia")]
    for area_name, area_key in areas:
        st.markdown(f"### {area_name}")
        area_data = data_service.filter_area_earthquakes(earthquake_data, area_key)
        report = generate_forecast_report(area_data, area_name)
        st_v = report.get('short_term_forecast') if report else None
        mt_v = report.get('medium_term_forecast') if report else None
        if report and st_v is not None and mt_v is not None:
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Breve termine", f"{st_v:.2f} M")
            with col2:
                st.metric("Medio termine", f"{mt_v:.2f} M")
        else:
            st.info(f"Dati insufficienti per {area_name}.")
        st.divider()
