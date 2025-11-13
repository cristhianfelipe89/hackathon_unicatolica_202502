# =========================================================
# MÓDULO: dashboard.py (FRONTEND - VERSIÓN DINÁMICA)
# Propósito: Interfaz de usuario (Streamlit) y visualización dinámica.
# =========================================================
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go 
import sys
import os

# --- 1. CONFIGURACIÓN DE RUTAS Y PATH DE MÓDULOS ---
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

# --- 2. IMPORTACIONES DE LÓGICA ---
from backend.core_logic import load_and_prepare_data, generate_alerts, get_floor_status, predict_60_min_ma
from configuracion.config import PISOS_MONITOREADOS, UMBRALES 

# --- 3. CONFIGURACIÓN INICIAL DE STREAMLIT ---
st.set_page_config(layout="wide", page_title="SmartFloors MVP")

# --- 4. CARGA Y PROCESAMIENTO DE DATOS ---
# ttl=5 fuerza a Streamlit a volver a ejecutar esta función y recargar el archivo CSV
# cada 5 segundos, simulando un flujo de datos en tiempo real.
@st.cache_data(ttl=5) 
def get_data_and_alerts():
    """Carga los datos y genera las alertas (función principal de Streamlit)."""
    df = load_and_prepare_data()
    if df.empty:
        st.error("No se pudieron cargar los datos. **[Importante]** Ejecute el simulador de datos en la Terminal 1.")
        return pd.DataFrame(), pd.DataFrame()
        
    df_alerts = generate_alerts(df)
    return df, df_alerts

df_data, df_alerts = get_data_and_alerts()

if df_data.empty:
    st.stop()

# Pre-procesamiento para gráficos (derretir el DataFrame)
df_melted = df_data.reset_index().melt(
    id_vars=['timestamp', 'edificio', 'piso'],
    value_vars=['temp_C', 'humedad_pct', 'energia_kW'],
    var_name='variable',
    value_name='valor'
)
# Solo las últimas 4 horas (la poda del simulador asegura que esto siempre sea 4h)
latest_timestamp = df_data.index.max()
df_4_hours = df_melted[df_melted['timestamp'] > latest_timestamp - pd.Timedelta(hours=4)]


# --- 5. TÍTULO Y FILTROS ---
st.title("💡 SmartFloors: Monitoreo Predictivo MVP")
st.markdown("Dashboard de estado en tiempo real del Edificio A (Pisos 1-3). **¡Sistema de Auto-Corrección Simulado Activo!**")

# --- 6. TARJETAS POR PISO (STATUS CARDS) ---
st.subheader("Estado General por Piso")
col_cards = st.columns(len(PISOS_MONITOREADOS))

for i, piso in enumerate(PISOS_MONITOREADOS):
    level, summary = get_floor_status(df_alerts, piso)

    color_map = {
        'OK': 'green',
        'Informativa': 'blue',
        'Media': 'orange',
        'Critica': 'red'
    }

    col_cards[i].metric(
        label=f"Piso {piso}",
        value=level,
        delta=summary,
        delta_color="off" 
    )
    
    st.markdown(
        f"""
        <style>
            [data-testid="stMetricValue"]:has(div:contains("{level}")) {{
                color: {color_map.get(level, 'gray')} !important;
            }}
        </style>
        """,
        unsafe_allow_html=True
    )

st.divider()

# --- 7. GRÁFICOS DE TENDENCIA (ÚLTIMAS 4 HORAS) ---
st.subheader("Tendencias Recientes (Últimas 4 Horas)")

col1, col2 = st.columns(2)

# Gráfico de Temperatura (CON LÍNEAS DE UMBRAL)
fig_temp = px.line(
    df_4_hours[df_4_hours['variable'] == 'temp_C'],
    x='timestamp',
    y='valor',
    color='piso',
    title='Temperatura (°C) - Predicción y Umbrales',
    line_dash='piso'
)

# --- AÑADIR LÍNEAS DE UMBRAL DE TEMPERATURA ---
fig_temp.add_hline(
    y=UMBRALES['temp_C']['Critica']['min'], 
    line_dash="dash", 
    line_color="red",
    annotation_text=f"Crítica ({UMBRALES['temp_C']['Critica']['min']}°C)",
    annotation_position="top left"
)
fig_temp.add_hline(
    y=UMBRALES['temp_C']['Media']['min'], 
    line_dash="dot", 
    line_color="orange",
    annotation_text=f"Media ({UMBRALES['temp_C']['Media']['min']}°C)",
    annotation_position="bottom right"
)

# Agregar línea de predicción como anotación
for piso in PISOS_MONITOREADOS:
    pred = predict_60_min_ma(df_data, piso, 'temp_C')
    if pred is not None:
        fig_temp.add_annotation(
            x=latest_timestamp + pd.Timedelta(minutes=60),
            y=pred,
            text=f"P{piso}: {pred}°C (Pred)",
            showarrow=True,
            arrowhead=2,
            arrowsize=1,
            arrowwidth=2,
            font=dict(color="red" if pred >= UMBRALES['temp_C']['Media']['min'] else "blue")
        )

fig_temp.update_xaxes(range=[df_4_hours['timestamp'].min(), latest_timestamp + pd.Timedelta(minutes=65)])
col1.plotly_chart(fig_temp, use_container_width=True)

# Gráfico de Humedad (CON LÍNEAS DE UMBRAL)
fig_hum = px.line(
    df_4_hours[df_4_hours['variable'] == 'humedad_pct'],
    x='timestamp',
    y='valor',
    color='piso',
    title='Humedad Relativa (%) - Umbrales de Confort',
    line_dash='piso'
)

# --- AÑADIR LÍNEAS DE UMBRAL DE HUMEDAD ---
fig_hum.add_hline(
    y=UMBRALES['humedad_pct']['Critica']['high'], 
    line_dash="dash", 
    line_color="red",
    annotation_text=f"Crítica Alta ({UMBRALES['humedad_pct']['Critica']['high']}%)",
    annotation_position="top left"
)
fig_hum.add_hline(
    y=UMBRALES['humedad_pct']['Critica']['low'], 
    line_dash="dash", 
    line_color="red",
    annotation_text=f"Crítica Baja ({UMBRALES['humedad_pct']['Critica']['low']}%)",
    annotation_position="bottom right"
)

col2.plotly_chart(fig_hum, use_container_width=True)


# Gráfico de Energía (columna completa)
st.subheader("Consumo Eléctrico (kW)")
fig_energia = px.line(
    df_4_hours[df_4_hours['variable'] == 'energia_kW'],
    x='timestamp',
    y='valor',
    color='piso',
    title='Consumo de Energía (kW)',
    line_dash='piso'
)

# --- AÑADIR LÍNEA DE UMBRAL DE ENERGÍA ---
fig_energia.add_hline(
    y=UMBRALES['energia_kW']['Critica'],
    line_dash="dash",
    line_color="red",
    annotation_text=f"Sobrecarga Crítica ({UMBRALES['energia_kW']['Critica']}kW)"
)

st.plotly_chart(fig_energia, use_container_width=True)


# --- 8. TABLA DE ALERTAS Y FILTROS ---
st.subheader("Tabla de Alertas Activas")

cols_filter = st.columns(2)
selected_piso = cols_filter[0].multiselect(
    "Filtrar por Piso:",
    options=PISOS_MONITOREADOS,
    default=PISOS_MONITOREADOS,
    format_func=lambda x: f"Piso {x}"
)

selected_nivel = cols_filter[1].multiselect(
    "Filtrar por Nivel de Alerta:",
    options=['Crítica', 'Media', 'Informativa', 'Preventiva Media', 'Preventiva Crítica'],
    default=['Crítica', 'Media', 'Preventiva Media']
)

df_filtered_alerts = df_alerts[
    df_alerts['piso'].isin(selected_piso) & 
    df_alerts['nivel'].isin(selected_nivel)
]

if df_filtered_alerts.empty:
    st.info("No hay alertas activas que coincidan con los filtros seleccionados.")
else:
    level_map = {'Crítica': 4, 'Preventiva Crítica': 3.5, 'Media': 3, 'Preventiva Media': 2.5, 'Informativa': 2, 'OK': 1}
    df_display = df_filtered_alerts[[
        'timestamp', 'piso', 'variable', 'nivel', 'recomendacion', 'tipo'
    ]].sort_values(by='nivel', key=lambda x: x.map(level_map), ascending=False)
    
    st.dataframe(
        df_display,
        use_container_width=True,
        column_config={
            "timestamp": st.column_config.DatetimeColumn("Hora de Alerta", format="YYYY-MM-DD HH:mm"),
            "piso": st.column_config.NumberColumn("Piso", format="%d"),
            "variable": "Variable",
            "nivel": st.column_config.TextColumn("Nivel de Riesgo"),
            "recomendacion": "Recomendación/Acción",
            "tipo": "Tipo de Alerta"
        }
    )