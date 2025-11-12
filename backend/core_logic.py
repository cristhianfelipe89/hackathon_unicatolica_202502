# =========================================================
# MÓDULO: core_logic.py (BACKEND)
# Propósito: Ingesta, Predicción y Generación de Alertas.
# =========================================================

import pandas as pd
import numpy as np
import os # Necesario para la manipulación de rutas
import sys # Necesario para determinar la ruta del script de Streamlit

# Importa las constantes y configuraciones del otro módulo
from configuracion.config import UMBRALES, RECOMENDACIONES, WINDOWS_SIZE_MINUTES, PISOS_MONITOREADOS 

# ------------------- FUNCIONES DE INGESTA Y PRE-PROCESAMIENTO -------------------

def load_and_prepare_data(filepath='smartfloors_data.csv'):
    """
    Función de Ingesta. Carga el CSV y prepara el DataFrame, usando una ruta robusta.
    """
    
    # Método robusto para encontrar el archivo en la raíz del proyecto (hacklathon/),
    # sin importar el directorio de trabajo.
    try:
        # sys.argv[0] contiene la ruta del script de Streamlit ('Frontend/app/dashboard.py')
        dashboard_path = os.path.dirname(os.path.abspath(sys.argv[0]))
        # Retrocede dos niveles: /app -> /Frontend -> /hacklathon
        root_dir = os.path.abspath(os.path.join(dashboard_path, '..', '..'))
        # Combina la raíz con el nombre del archivo
        full_path = os.path.join(root_dir, filepath)
    except IndexError:
        # Caso de debug, si el script no fue ejecutado por Streamlit
        full_path = filepath
    
    try:
        # Usar la ruta absoluta corregida
        df = pd.read_csv(full_path) 
        
        # Estas dos líneas son muy sensibles a datos incorrectos
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df = df.set_index('timestamp')
        
        # Asegurarse de que el DataFrame no esté vacío antes de continuar
        if df.empty:
             print("Advertencia: DataFrame cargado está vacío.")
             return pd.DataFrame() 

        return df
    except FileNotFoundError:
        # Notificar al usuario dónde se buscó el archivo
        print(f"ERROR: Archivo de datos no encontrado. Se buscó en: {full_path}")
        return pd.DataFrame()
    except Exception as e:
        print(f"ERROR: Fallo al procesar los datos en core_logic: {e}")
        return pd.DataFrame()

# ------------------- FUNCIONES DE PREDICCIÓN (MVP SIMPLE) -------------------

def predict_60_min_ma(df, piso, variable):
    """
    Calcula la predicción a +60 minutos usando Promedio Móvil simple (MVP).
    """
    df_floor = df[df['piso'] == piso]
    
    # Se usa la media de la última hora (60 registros) como predicción
    # Si la data no tiene al menos 60 puntos, usamos todos los disponibles
    latest_data = df_floor[variable].tail(WINDOWS_SIZE_MINUTES)
    if latest_data.empty:
        return None
        
    prediction = latest_data.mean()
    return round(prediction, 2)


# ------------------- FUNCIONES DE REGLAS DE NEGOCIO Y ALERTAS -------------------

def _check_umbral(value, umbral_config):
    """Función auxiliar para verificar si un valor cruza un umbral."""
    for level, limits in umbral_config.items():
        if level in ['Media', 'Critica', 'Informativa']:
            # Caso de Temperatura (solo 'min')
            if 'min' in limits and value >= limits['min']:
                return level
            # Caso de Humedad (rango 'low' y 'high')
            if 'low' in limits and 'high' in limits:
                if value < limits['low'] or value > limits['high']:
                    return level
        # Caso de Energía (umbral simple, no un diccionario)
        elif isinstance(limits, float) and value >= limits:
            return level
    return None

def generate_alerts(df):
    """
    Función principal de Backend: genera todas las alertas del sistema.
    """
    if df.empty:
        return pd.DataFrame(columns=['timestamp', 'piso', 'variable', 'nivel', 'recomendacion', 'tipo'])

    alerts = []
    current_time = df.index.max()
    
    for piso in PISOS_MONITOREADOS:
        latest_data = df[df['piso'] == piso].tail(1)
        if latest_data.empty: continue
        latest_data = latest_data.iloc[0]

        # 1. Alertas por Condiciones Actuales (T, H, Energía)
        # Temperatura y Humedad
        for var in ['temp_C', 'humedad_pct']:
            level = _check_umbral(latest_data[var], UMBRALES[var])
            if level:
                # Determinar la clave de la recomendación (especial para humedad)
                rec_key = f'{var}_{level}'
                if var == 'humedad_pct':
                    if latest_data[var] < UMBRALES['humedad_pct'][level]['low']:
                        rec_key = f'humedad_pct_Critica_low' # Usamos Critica_low/high para los mensajes
                    elif latest_data[var] > UMBRALES['humedad_pct'][level]['high']:
                        rec_key = f'humedad_pct_Critica_high'
                        
                alerts.append({
                    'timestamp': current_time,
                    'piso': piso,
                    'variable': var,
                    'nivel': level,
                    'recomendacion': RECOMENDACIONES.get(rec_key, f'Revisar {var} en Piso {piso}.').replace('Piso X', f'Piso {piso}'),
                    'tipo': 'Actual'
                })
        
        # 2. Alerta Preventiva (Predicción de Temperatura)
        temp_pred = predict_60_min_ma(df, piso, 'temp_C')
        if temp_pred and temp_pred >= UMBRALES['temp_C']['Media']['min']:
            alerts.append({
                'timestamp': current_time,
                'piso': piso,
                'variable': 'Temperatura (Predicción)',
                'nivel': 'Preventiva Media',
                'recomendacion': RECOMENDACIONES['preventiva_temp_C'].replace('Piso X', f'Piso {piso}'),
                'tipo': 'Preventiva'
            })

        # 3. Alerta de Riesgo Combinado (Temp Media/Crítica + Energía Media/Crítica)
        is_thermal_risk = latest_data['temp_C'] >= UMBRALES['temp_C']['Media']['min']
        is_high_energy = latest_data['energia_kW'] >= UMBRALES['energia_kW']['Media']
        
        if is_thermal_risk and is_high_energy:
             alerts.append({
                'timestamp': current_time,
                'piso': piso,
                'variable': 'riesgo combinado',
                'nivel': 'Crítica',
                'recomendacion': RECOMENDACIONES['riesgo_combinado_Critica'].replace('Piso X', f'Piso {piso}'),
                'tipo': 'Actual'
            })

    return pd.DataFrame(alerts)

# ------------------- FUNCIONES DE INTERFAZ DE BACKEND -------------------

def get_floor_status(df_alerts, piso):
    """
    Retorna el estado más crítico y un resumen para el Frontend.
    """
    level_order = {'Crítica': 4, 'Preventiva Crítica': 3.5, 'Media': 3, 'Preventiva Media': 2.5, 'Informativa': 2, 'OK': 1}
    
    alerts_piso = df_alerts[df_alerts['piso'] == piso]
    
    if alerts_piso.empty:
        return 'OK', 'Sin problemas de eficiencia o confort.'
        
    max_level = 'OK'
    max_score = 1
    
    for level in alerts_piso['nivel'].unique():
        if level in level_order and level_order[level] > max_score:
            max_score = level_order[level]
            max_level = level
            
    summary = ', '.join(alerts_piso['variable'].unique()) + ' fuera de rango.'
    
    # Limpiar el nombre del nivel para la tarjeta (ej: quitar 'Preventiva')
    display_level = max_level.replace('Preventiva ', '') 
    
    return display_level, summary