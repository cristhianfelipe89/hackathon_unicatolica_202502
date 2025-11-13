# =========================================================
# MÓDULO: core_logic.py (BACKEND - BUCLE CERRADO SIMULADO)
# Propósito: Ingesta, Predicción, Generación de Alertas y Activación de Corrección.
# =========================================================

import pandas as pd
import numpy as np
import os 
import sys 
import random

# Importa las constantes y configuraciones
from configuracion.config import UMBRALES, RECOMENDACIONES, WINDOWS_SIZE_MINUTES, PISOS_MONITOREADOS 

# --- IMPOTACIÓN CRÍTICA DEL SIMULADOR PARA EL BUCLE CERRADO ---
try:
    # Ajusta el path para importar data_simulator.py (que está en la carpeta raíz)
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
    from data_simulator import system_correction_active 
except ImportError:
    # Modo seguro en caso de fallo de importación (la simulación de corrección no funcionará)
    system_correction_active = {p: False for p in PISOS_MONITOREADOS} 
    print("Advertencia: No se pudo enlazar la lógica de corrección con el simulador.")

# ------------------- FUNCIONES DE INGESTA Y PRE-PROCESAMIENTO -------------------

def load_and_prepare_data(filepath='smartfloors_data.csv'):
    """
    Función de Ingesta. Carga el CSV y prepara el DataFrame, usando una ruta robusta.
    """
    
    try:
        # Intenta determinar la ruta absoluta del archivo CSV.
        dashboard_path = os.path.dirname(os.path.abspath(sys.argv[0]))
        root_dir = os.path.abspath(os.path.join(dashboard_path, '..', '..'))
        full_path = os.path.join(root_dir, filepath)
    except IndexError:
        full_path = filepath
    
    try:
        df = pd.read_csv(full_path) 
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df = df.set_index('timestamp')
        
        if df.empty:
             return pd.DataFrame() 

        return df
    except FileNotFoundError:
        return pd.DataFrame()
    except Exception as e:
        return pd.DataFrame()

# ------------------- FUNCIONES DE PREDICCIÓN (MVP SIMPLE) -------------------

def predict_60_min_ma(df, piso, variable):
    """
    Calcula la predicción a +60 minutos usando Promedio Móvil simple (MVP).
    """
    df_floor = df[df['piso'] == piso]
    latest_data = df_floor[variable].tail(WINDOWS_SIZE_MINUTES)
    if latest_data.empty:
        return None
        
    prediction = latest_data.mean()
    return round(prediction, 2)


# ------------------- FUNCIONES DE REGLAS DE NEGOCIO Y ALERTAS -------------------

def _check_umbral(value, umbral_config, var_name): 
    """Función auxiliar para verificar si un valor cruza un umbral."""
    for level, limits in umbral_config.items():
        
        # 1. Variables con rangos (Temperatura, Humedad)
        if isinstance(limits, dict): 
            if var_name == 'temp_C' and 'min' in limits and value >= limits['min']:
                return level
            
            elif var_name == 'humedad_pct' and 'low' in limits and 'high' in limits:
                if value < limits['low'] or value > limits['high']:
                    return level
        
        # 2. Variables con umbral simple flotante (Energía)
        elif isinstance(limits, (float, int)) and value >= limits:
            return level
            
    return None

def generate_alerts(df):
    """
    Función principal de Backend: genera todas las alertas del sistema y 
    activa la simulación de corrección si se detecta una CRÍTICA.
    """
    global system_correction_active 
    
    if df.empty:
        # Si el input está vacío, retorna un DF vacío con columnas definidas
        return pd.DataFrame(columns=['timestamp', 'piso', 'variable', 'nivel', 'recomendacion', 'tipo'])

    alerts = []
    current_time = df.index.max()
    
    for piso in PISOS_MONITOREADOS:
        latest_data = df[df['piso'] == piso].tail(1)
        if latest_data.empty: continue
        latest_data = latest_data.iloc[0]
        
        is_critical_alert = False

        # 1. Alertas por Condiciones Actuales (T, H, Energía)
        for var in ['temp_C', 'humedad_pct', 'energia_kW']:
            level = _check_umbral(latest_data[var], UMBRALES[var], var)
            
            if level:
                if level == 'Critica':
                    is_critical_alert = True
                
                # Determinar la clave de la recomendación
                rec_key = f'{var}_{level}'
                if var == 'humedad_pct' and level == 'Critica':
                    if latest_data[var] < UMBRALES['humedad_pct'][level]['low']:
                        rec_key = f'humedad_pct_Critica_low'
                    elif latest_data[var] > UMBRALES['humedad_pct'][level]['high']:
                        rec_key = f'humedad_pct_Critica_high'
                elif var == 'energia_kW':
                    rec_key = f'energia_kW_Critica' 

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
             is_critical_alert = True 
             
        # --- FUNCIÓN DE NOTIFICACIÓN Y CORRECCIÓN (Simulación) ---
        if is_critical_alert and not system_correction_active[piso]:
             system_correction_active[piso] = True
             print(f"*** ALERTA CRÍTICA DETECTADA en Piso {piso}. INICIANDO CORRECCIÓN SIMULADA ***")
    
    # --- CORRECCIÓN FINAL DEL ERROR ---
    # Garantiza que el DataFrame de alertas siempre tenga las columnas necesarias, incluso si está vacío.
    df_alerts = pd.DataFrame(alerts, columns=['timestamp', 'piso', 'variable', 'nivel', 'recomendacion', 'tipo'])
    return df_alerts

# ------------------- FUNCIONES DE INTERFAZ DE BACKEND -------------------

def get_floor_status(df_alerts, piso):
    """
    Retorna el estado más crítico y un resumen para el Frontend.
    """
    level_order = {'Crítica': 4, 'Preventiva Crítica': 3.5, 'Media': 3, 'Preventiva Media': 2.5, 'Informativa': 2, 'OK': 1}
    
    # La columna 'piso' ahora está garantizada por la corrección en generate_alerts
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
    
    display_level = max_level.replace('Preventiva ', '') 
    
    return display_level, summary