with tab2:
    st.subheader("Monitoraggio Area Vesuvio")
    vesuvio_data = data_service.filter_area_earthquakes(earthquake_data, 'vesuvio')

    # Render Vesuvius SVG image
    from utils import render_svg
    col1, col2 = st.columns([1, 2])
    with col1:
        render_svg('assets/vesuvio.svg')

    with col2:
        if vesuvio_data.empty:
            st.info("Nessun terremoto recente nell'area del Vesuvio negli ultimi 7 giorni.")
        else:
            st.metric("Eventi recenti", len(vesuvio_data))
            st.metric(f"{get_text('magnitude')} Max", f"{vesuvio_data['magnitude'].max():.1f}" if not vesuvio_data.empty else "N/A")

    # Show map and charts
    if not vesuvio_data.empty:
        show_map(vesuvio_data, "Vesuvio", get_text)
        show_magnitude_time_chart(vesuvio_data, "Vesuvio", get_text)

    # Previsioni sismiche
    from forecast_service import generate_forecast_report
    forecast_report = generate_forecast_report(vesuvio_data, "Vesuvio")

    st.subheader("⚠️ Previsioni Sismiche")
    if forecast_report:
        col_f1, col_f2 = st.columns(2)
        with col_f1:
            st.metric("Previsione Breve Termine", f"{forecast_report['short_term_forecast']:.2f} M")
            st.markdown(f"**Attendibilità**: {int(forecast_report['short_term_accuracy'] * 100)}%")
        with col_f2:
            st.metric("Previsione Medio Termine", f"{forecast_report['medium_term_forecast']:.2f} M")
            st.markdown(f"**Attendibilità**: {int(forecast_report['medium_term_accuracy'] * 100)}%")
        st.caption(f"Ultimo aggiornamento: {forecast_report['last_update'].strftime('%d/%m/%Y %H:%M:%S')}")
    else:
        st.info("Dati insufficienti per generare previsioni.")

    # Estensione: Monitoraggio Multiparametrico Vesuvio
    st.subheader("📊 Monitoraggio Multiparametrico")

    sensor_cols = st.columns(3)

    with sensor_cols[0]:
        st.markdown("### 🌡️ Parametri Termici")
        st.metric("Temperatura Suolo", f"{95 + np.random.randint(-5, 5)}°C", f"{np.random.randint(-2, 2)}°C")
        st.metric("Temperatura Fumarole", f"{152 + np.random.randint(-10, 10)}°C", f"{np.random.randint(-5, 5)}°C")

    with sensor_cols[1]:
        st.markdown("### 💨 Parametri Geochimici")
        st.metric("CO2 Atmosferica", f"{340 + np.random.randint(-20, 20)} ppm", f"{np.random.randint(-5, 5)}%")
        st.metric("Flusso H2S", f"{35 + np.random.randint(-10, 10)} μmol/m²/s", f"{np.random.randint(-8, 8)}%")

    with sensor_cols[2]:
        st.markdown("### 🔀 Deformazione")
        st.metric("Inclinazione Suolo", f"{0.4 + np.random.random() * 0.3:.2f}°", f"{np.random.randint(-1, 2)} µrad")
        st.metric("Velocità Sollevamento", f"{np.random.randint(1, 5)} mm/mese", f"{np.random.randint(-1, 2)} mm")

    # Grafico interattivo
    st.subheader("📈 Andamento Parametri nel Tempo")
    param_option = st.selectbox("Seleziona parametro da visualizzare (Vesuvio)", [
        "Temperatura Suolo", "CO2 Atmosferica", "Inclinazione Suolo", "Velocità Sollevamento"
    ])

    times = pd.date_range(end=pd.Timestamp.now(), periods=24, freq='h')
    if param_option == "Temperatura Suolo":
        values = [95 + np.random.randint(-5, 5) for _ in range(24)]
        unit = "°C"
    elif param_option == "CO2 Atmosferica":
        values = [340 + np.random.randint(-20, 20) for _ in range(24)]
        unit = "ppm"
    elif param_option == "Inclinazione Suolo":
        values = [0.4 + np.random.random() * 0.3 for _ in range(24)]
        unit = "gradi"
    else:
        values = [3 + np.random.randint(-2, 2) for _ in range(24)]
        unit = "mm/mese"

    fig = px.line(
        x=times,
        y=values,
        title=f"Andamento {param_option} ultime 24 ore",
        labels={"x": "Tempo", "y": f"{param_option} ({unit})"}
    )
    st.plotly_chart(fig, use_container_width=True)

    # Stato sensori
    with st.expander("Stato Sensori Vesuvio"):
        st.markdown("""
        | Sensore | Stato | Ultimo aggiornamento | Accuratezza |
        |---------|--------|---------------------|-------------|
        | Temperatura Suolo | ✅ Online | 3 min fa | ±0.5°C |
        | Temperatura Fumarole | ✅ Online | 2 min fa | ±1.0°C |
        | CO2 Atmosferica | ✅ Online | 1 min fa | ±5 ppm |
        | Flusso H2S | ✅ Online | 2 min fa | ±2 μmol/m²/s |
        | Inclinazione Suolo | ✅ Online | 1 min fa | ±0.01° |
        | Velocità Sollevamento | ✅ Online | 5 min fa | ±0.5 mm/mese |
        """)