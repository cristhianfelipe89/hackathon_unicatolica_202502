# =========================================================
# MÓDULO: dashboard.py (FRONTEND)
# Propósito: Interfaz de usuario (Streamlit) y visualización.
# =========================================================
import streamlit as st
import pandas as pd
import plotly.express as px
import sys
import os

# --- 1. CONFIGURACIÓN DE RUTAS Y PATH DE MÓDULOS ---
# AGREGAR EL DIRECTORIO RAIZ DEL PROYECTO AL PYTHON PATH
# Esto permite que Python encuentre los módulos en 'backend/' y 'configuracion/'
# sin importar el directorio de trabajo.
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

# --- 2. IMPORTACIONES DE LÓGICA ---
# Importa las funciones necesarias del backend y las constantes de configuración
from backend.core_logic import load_and_prepare_data, generate_alerts, get_floor_status, predict_60_min_ma
from configuracion.config import PISOS_MONITOREADOS

# --- 3. CONFIGURACIÓN INICIAL DE STREAMLIT ---
st.set_page_config(layout="wide", page_title="SmartFloors MVP")

# --- 4. CARGA Y PROCESAMIENTO DE DATOS ---
@st.cache_data
def get_data_and_alerts():
    """Carga los datos y genera las alertas (función principal de Streamlit)."""
    # La función load_and_prepare_data ahora maneja la búsqueda de 'smartfloors_data.csv'
    df = load_and_prepare_data()
    if df.empty:
        # Esto previene el fallo si el simulador no se ejecutó o si el path falló.
        st.error("No se pudieron cargar los datos. Asegúrese de que 'smartfloors_data.csv' exista.")
        return pd.DataFrame(), pd.DataFrame()

    df_alerts = generate_alerts(df)
    return df, df_alerts

df_data, df_alerts = get_data_and_alerts()

# Si los datos no se cargaron, detener la ejecución de la UI.
if df_data.empty:
    st.stop()

# Pre-procesamiento para gráficos (derretir el DataFrame)
df_melted = df_data.reset_index().melt(
    id_vars=['timestamp', 'edificio', 'piso'],
    value_vars=['temp_C', 'humedad_pct', 'energia_kW'],
    var_name='variable',
    value_name='valor'
)
# Solo las últimas 4 horas
latest_timestamp = df_data.index.max()
df_4_hours = df_melted[df_melted['timestamp'] > latest_timestamp - pd.Timedelta(hours=4)]


# --- 5. TÍTULO Y FILTROS ---
st.title("💡 SmartFloors: Monitoreo Predictivo MVP")
st.markdown("Dashboard de estado en tiempo real del Edificio A (Pisos 1-3).")

# --- 6. TARJETAS POR PISO (STATUS CARDS) ---
st.subheader("Estado General por Piso")
col_cards = st.columns(len(PISOS_MONITOREADOS))

for i, piso in enumerate(PISOS_MONITOREADOS):
    level, summary = get_floor_status(df_alerts, piso)

    # Mapeo de estado a color para la tarjeta
    color_map = {
        'OK': 'green',
        'Informativa': 'blue',
        'Media': 'orange',
        'Critica': 'red'
    }

    # Mostrar la tarjeta (Métrica)
    col_cards[i].metric(
        label=f"Piso {piso}",
        value=level,
        delta=summary,
        delta_color="off" 
    )
    
    # Personalizar el color del valor de la métrica usando HTML/CSS
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

# Gráfico de Temperatura
fig_temp = px.line(
    df_4_hours[df_4_hours['variable'] == 'temp_C'],
    x='timestamp',
    y='valor',
    color='piso',
    title='Temperatura (°C) - Predicción a +60 min',
    line_dash='piso'
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
            font=dict(color="red" if pred >= 28.0 else "blue")
        )
# Ajustar el eje X para que incluya la predicción (+60 min)
fig_temp.update_xaxes(range=[df_4_hours['timestamp'].min(), latest_timestamp + pd.Timedelta(minutes=65)])
col1.plotly_chart(fig_temp, use_container_width=True)

# Gráfico de Humedad
fig_hum = px.line(
    df_4_hours[df_4_hours['variable'] == 'humedad_pct'],
    x='timestamp',
    y='valor',
    color='piso',
    title='Humedad Relativa (%)',
    line_dash='piso'
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
st.plotly_chart(fig_energia, use_container_width=True)


# --- 8. TABLA DE ALERTAS Y FILTROS ---
st.subheader("Tabla de Alertas Activas")

# Filtros
cols_filter = st.columns(2)
# Filtro por Piso
selected_piso = cols_filter[0].multiselect(
    "Filtrar por Piso:",
    options=PISOS_MONITOREADOS,
    default=PISOS_MONITOREADOS,
    format_func=lambda x: f"Piso {x}"
)

# Filtro por Nivel de Alerta
selected_nivel = cols_filter[1].multiselect(
    "Filtrar por Nivel de Alerta:",
    options=['Crítica', 'Media', 'Informativa', 'Preventiva Media', 'Preventiva Crítica'],
    default=['Crítica', 'Media', 'Preventiva Media']
)

# Aplicar filtros
df_filtered_alerts = df_alerts[
    df_alerts['piso'].isin(selected_piso) & 
    df_alerts['nivel'].isin(selected_nivel)
]

if df_filtered_alerts.empty:
    st.info("No hay alertas activas que coincidan con los filtros seleccionados.")
else:
    # Mostrar la tabla de alertas
    df_display = df_filtered_alerts[[
        'timestamp', 'piso', 'variable', 'nivel', 'recomendacion', 'tipo'
    ]].sort_values(by='nivel', key=lambda x: x.map({'Crítica': 4, 'Media': 3, 'Informativa': 2, 'Preventiva Media': 2.5, 'Preventiva Crítica': 3.5}), ascending=False)
    
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