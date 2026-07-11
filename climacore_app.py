import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from datetime import datetime, date

# 1. SAYFA AYARLARI
st.set_page_config(
    page_title="ClimaCore | Türkiye Hidro-Meteorolojik Veri Platformu",
    page_icon="🌤️",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("🌐 ClimaCore: Türkiye İstasyon Analiz ve WRF Platformu")
st.markdown("Türkiye genelindeki **250 meteoroloji istasyonunun** saatlik basınç, sıcaklık, güneşlenme, rüzgar ve yağış verileri.")

# 2. ÖRNEK VERİ SİMÜLASYONU
@st.cache_data
def get_station_metadata():
    data = {
        "station_id": [17060, 17064, 17070, 17084, 17600],
        "name": ["İstanbul (Göztepe)", "Bursa", "Ankara (Bölge)", "Çanakkale", "Samsun (Bölge)"],
        "lat": [40.97, 40.18, 39.97, 40.15, 41.34],
        "lon": [29.08, 29.07, 32.86, 26.40, 36.25],
        "start_year": [1970, 1975, 1965, 1980, 1972],
        "end_date": ["2025-12-31"] * 5
    }
    return pd.DataFrame(data)

@st.cache_data
def load_hourly_station_data(station_id, start_dt, end_dt):
    date_rng = pd.date_range(start=start_dt, end=end_dt, freq="h")
    n = len(date_rng)

    temp = 15 + 10 * np.sin(np.linspace(0, 3.14 * 2 * (n/24), n)) + np.random.normal(0, 1.5, n)
    pressure = 1013 + np.random.normal(0, 5, n)
    solar_rad = np.where(date_rng.hour.isin(range(6, 19)), np.random.uniform(200, 850, n), 0)
    wind_spd = np.abs(np.random.normal(4, 2, n))
    precip = np.where(np.random.random(n) > 0.90, np.random.exponential(2.0, n), 0.0)

    return pd.DataFrame({
        "timestamp": date_rng,
        "temperature": temp.round(1),
        "pressure": pressure.round(1),
        "solar_radiation": solar_rad.round(0),
        "wind_speed": wind_spd.round(1),
        "precipitation": precip.round(2)
    })

stations_df = get_station_metadata()

# 3. YAN MENÜ (SIDEBAR)
st.sidebar.header("📍 İstasyon ve Tarih Seçimi")
selected_station_name = st.sidebar.selectbox("İstasyon seçin:", options=stations_df["name"].tolist(), index=0)
selected_station = stations_df[stations_df["name"] == selected_station_name].iloc[0]

st.sidebar.info(f"**İstasyon:** {selected_station['name']}\n\n**Başlangıç:** {selected_station['start_year']}\n\n**Bitiş:** 2025-12-31")

start_date, end_date = st.sidebar.date_input(
    "Tarih Aralığı:",
    value=[date(2025, 12, 1), date(2025, 12, 31)],
    min_value=date(selected_station["start_year"], 1, 1),
    max_value=date(2025, 12, 31)
)

# 4. TÜRKİYE HARİTASI
col1, col2 = st.columns([1, 2])

with col1:
    st.subheader("🗺️ İstasyon Konumları")
    stations_df["color"] = np.where(stations_df["name"] == selected_station_name, "Seçili İstasyon", "Diğer İstasyonlar")

    fig_map = px.scatter_map(
        stations_df,
        lat="lat", lon="lon",
        hover_name="name",
        color="color",
        color_discrete_map={"Seçili İstasyon": "#FF4B4B", "Diğer İstasyonlar": "#0083B8"},
        zoom=4.5,
        center={"lat": 39.0, "lon": 35.5},
        height=450
    )
    fig_map.update_layout(map_style="carto-positron", margin={"r":0,"t":0,"l":0,"b":0}, showlegend=False)
    st.plotly_chart(fig_map, width="stretch")

# 5. GRAFİKLER VE VERİ ANALİZİ
with col2:
    st.subheader(f"📊 {selected_station['name']} - Saatlik Analiz")
    df_data = load_hourly_station_data(selected_station["station_id"], start_date, end_date)

    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    kpi1.metric("Ort. Sıcaklık", f"{df_data['temperature'].mean():.1f} °C")
    kpi2.metric("Ort. Basınç", f"{df_data['pressure'].mean():.1f} hPa")
    kpi3.metric("Maks. Rüzgar", f"{df_data['wind_speed'].max():.1f} m/s")
    kpi4.metric("Top. Yağış", f"{df_data['precipitation'].sum():.1f} mm")

    tab1, tab2, tab3, tab4 = st.tabs(["🌡️ Sıcaklık & Yağış", "💨 Rüzgar Hızı", "☀️ Güneşlenme", "⏱️ Basınç"])

    with tab1:
        fig_temp = px.line(df_data, x="timestamp", y="temperature", title="Saatlik Sıcaklık (°C)")
        fig_temp.update_traces(line_color="#FF6C6C")
        st.plotly_chart(fig_temp, width="stretch")

        if df_data['precipitation'].sum() > 0:
            fig_precip = px.bar(df_data, x="timestamp", y="precipitation", title="Saatlik Yağış (mm)")
            fig_precip.update_traces(marker_color="#3399FF")
            st.plotly_chart(fig_precip, width="stretch")

    with tab2:
        fig_wind = px.line(df_data, x="timestamp", y="wind_speed", title="Saatlik Rüzgar Hızı (m/s)")
        fig_wind.update_traces(line_color="#00CC96")
        st.plotly_chart(fig_wind, width="stretch")

    with tab3:
        fig_solar = px.area(df_data, x="timestamp", y="solar_radiation", title="Saatlik Güneşlenme (W/m²)")
        fig_solar.update_traces(line_color="#FFAA00", fillcolor="rgba(255, 170, 0, 0.3)")
        st.plotly_chart(fig_solar, width="stretch")

    with tab4:
        fig_pres = px.line(df_data, x="timestamp", y="pressure", title="Saatlik Basınç (hPa)")
        fig_pres.update_traces(line_color="#AB63FA")
        st.plotly_chart(fig_pres, width="stretch")

with st.expander("📁 Ham Veriyi İncele ve İndir"):
    st.dataframe(df_data, width="stretch")
    csv = df_data.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 CSV Olarak İndir",
        data=csv,
        file_name=f"ClimaCore_{selected_station['station_id']}.csv",
        mime="text/csv",
    )
