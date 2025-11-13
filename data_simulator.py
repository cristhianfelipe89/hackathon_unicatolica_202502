# =========================================================
# MÓDULO: data_simulator.py (MODO TIEMPO REAL CON PODA Y CORRECCIÓN)
# Propósito: Generar datos continuamente (cada 5s), podando el historial a 4 horas.
# =========================================================

import pandas as pd
import numpy as np
import time
from datetime import datetime
import os
import random
# Importar configuración para parámetros
try:
    from configuracion.config import PISOS_MONITOREADOS, UMBRALES 
except ImportError:
    PISOS_MONITOREADOS = [1, 2, 3] 

# Parámetros de simulación
INTERVAL_SECONDS = 5  # Frecuencia de escritura: 5 segundos.
MAX_RECORDS = 240 * len(PISOS_MONITOREADOS) # 4 horas * 60 min/h * 3 pisos = 720 registros
FILE_NAME = 'smartfloors_data.csv'

# VARIABLES DE ESTADO GLOBALES - ¡CRÍTICAS PARA LA SIMULACIÓN DE CORRECCIÓN!
# Estas variables son importadas por core_logic.py
system_correction_active = {p: False for p in PISOS_MONITOREADOS} 
correction_timer = {p: 0 for p in PISOS_MONITOREADOS}

def get_daily_base(piso, cycle_factor):
    """Devuelve las bases para un piso."""
    
    # Bases de Consumo y Confort
    if piso == 1:
        base_temp = 22.0 + 3.0 * cycle_factor
        base_hum = 65.0 + 10.0 * cycle_factor
        base_energia = 5.0 + 4.0 * cycle_factor
    elif piso == 2:
        base_temp = 23.5 + 4.0 * cycle_factor
        base_hum = 60.0 + 11.0 * cycle_factor
        base_energia = 7.5 + 5.0 * cycle_factor
    else: # Piso 3: Más propenso a problemas
        base_temp = 24.5 + 5.0 * cycle_factor
        base_hum = 55.0 + 12.0 * cycle_factor
        base_energia = 10.0 + 6.0 * cycle_factor
        
    return base_temp, base_hum, base_energia


def generate_live_data():
    """Genera un nuevo set de datos, aplicando anomalías y correcciones."""
    global system_correction_active, correction_timer
    
    timestamp = datetime.now()
    data = []
    
    minute_of_day = (timestamp.hour * 60 + timestamp.minute) / (24 * 60)
    daily_cycle = np.sin(minute_of_day * 2 * np.pi) 

    for piso in PISOS_MONITOREADOS:
        base_temp, base_hum, base_energia = get_daily_base(piso, daily_cycle)
        
        temp_C = round(base_temp + np.random.normal(0, 0.4), 2)
        humedad_pct = round(base_hum + np.random.normal(0, 0.8), 2)
        energia_kW = round(base_energia + np.random.normal(0, 0.3), 2)
        
        # --- LÓGICA DE CORRECCIÓN (Simula que el setpoint fue ajustado) ---
        if system_correction_active[piso]:
            correction_timer[piso] += 1
            # Reducir la temperatura y energía por la acción
            temp_C = round(temp_C - 2.0 - 0.5 * daily_cycle, 2)
            energia_kW = round(energia_kW - 3.0, 2)
            
            # Desactivar la corrección después de 120 segundos (24 ciclos de 5s)
            if correction_timer[piso] > 24: 
                system_correction_active[piso] = False
                correction_timer[piso] = 0
                print(f"✅ Piso {piso}: Corrección de sistema completada y desactivada.")
                
        # --- LÓGICA DE ANOMALÍAS (Simula fallas más frecuentes) ---
        else:
            # 1. Pico de Energía (15% de probabilidad)
            if random.random() < 0.15: 
                pico_energia = 8.0 + random.normalvariate(0, 1.0)
                energia_kW = round(energia_kW + pico_energia, 2)
                # El pico de energía puede llevar a un aumento de temperatura
                if pico_energia > 9.0:
                    temp_C = round(temp_C + 1.5 + random.normalvariate(0, 0.3), 2)
                    
            # 2. Desviación de Humedad (8% de probabilidad)
            if random.random() < 0.08: 
                humedad_pct = round(humedad_pct + random.choice([-15.0, 15.0]) + random.normalvariate(0, 2.0), 2)

        data.append({
            'timestamp': timestamp,
            'edificio': 'A',
            'piso': piso,
            'temp_C': temp_C,
            'humedad_pct': humedad_pct,
            'energia_kW': energia_kW
        })

    return pd.DataFrame(data)


def run_live_simulator():
    """Función principal para el modo continuo, con limpieza de historial."""
    print("--- INICIANDO SIMULADOR DINÁMICO (Modo Bucle Cerrado) ---")
    
    # Limpiar el CSV al inicio
    if os.path.exists(FILE_NAME):
        os.remove(FILE_NAME)

    while True:
        try:
            new_df = generate_live_data()
            
            # Cargar historial y podar a MAX_RECORDS
            if os.path.exists(FILE_NAME):
                df_history = pd.read_csv(FILE_NAME)
                df_history['timestamp'] = pd.to_datetime(df_history['timestamp'])
                df_history = df_history.tail(MAX_RECORDS - len(new_df))
                df_combined = pd.concat([df_history, new_df])
            else:
                df_combined = new_df

            # Guardar el archivo podado y actualizado (sobreescribir)
            df_combined.to_csv(FILE_NAME, index=False)
            
            print(f"✅ Nuevo registro añadido/podado a {FILE_NAME} - Último registro: {df_combined['timestamp'].max().strftime('%H:%M:%S')}")
            
        except Exception as e:
            print(f"ERROR en simulador: {e}. ¿Está 'smartfloors_data.csv' libre?")
            
        time.sleep(INTERVAL_SECONDS)


if __name__ == '__main__':
    run_live_simulator()