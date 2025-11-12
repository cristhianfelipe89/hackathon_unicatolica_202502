# =========================================================
# MÓDULO: data_simulator.py
# Propósito: Generar el archivo smartfloors_data.csv para el MVP.
# =========================================================

import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Parámetros de simulación
PISOS = [1, 2, 3]
HOURS_OF_DATA = 48  # Generar 48 horas de historial
FILE_NAME = 'smartfloors_data.csv'


def generate_simulated_data(hours):
    """Genera datos simulados para el Edificio A, Pisos 1, 2 y 3."""

    start_time = datetime.now() - timedelta(hours=hours)
    data = []
    total_minutes = hours * 60

    # Generar un registro por minuto para cada piso
    for i in range(total_minutes):
        timestamp = start_time + timedelta(minutes=i)

        # Factor de variación (simula ciclos diarios/semanales)
        daily_cycle = np.sin(i / (60 * 24) * 2 * np.pi)

        for piso in PISOS:

            # --- BASE DE DATOS REALISTA (Se simulan diferencias entre pisos) ---
            if piso == 1:
                # Piso 1: Más bajo, tiende a ser más fresco y consume menos energía
                base_temp = 22.0 + 3.0 * daily_cycle + \
                    np.sin(i / (60 * 6) * 2 * np.pi) * 0.5
                base_hum = 55.0 + 10.0 * daily_cycle
                base_energia = 5.0 + 4.0 * daily_cycle
            elif piso == 3:
                # Piso 3: Más alto, tiende a ser más caliente y consume más energía
                base_temp = 25.0 + 4.5 * daily_cycle + \
                    np.sin(i / (60 * 4) * 2 * np.pi) * 0.7
                base_hum = 65.0 + 12.0 * daily_cycle
                base_energia = 10.0 + 6.0 * daily_cycle
            else:
                # Piso 2: Intermedio
                base_temp = 23.5 + 4.0 * daily_cycle
                base_hum = 60.0 + 11.0 * daily_cycle
                base_energia = 7.5 + 5.0 * daily_cycle

            # --- AÑADIR RUIDO Y CONVERSIÓN ---
            temp_C = round(base_temp + np.random.normal(0, 0.4), 2)
            humedad_pct = round(base_hum + np.random.normal(0, 0.8), 2)
            energia_kW = round(base_energia + np.random.normal(0, 0.3), 2)

            # **SIMULAR UNA ANOMALÍA RECIENTE EN EL PISO 3**
            # Si estamos en la última hora, sube la temperatura y energía del Piso 3
            if piso == 3 and i > total_minutes - 60:
                temp_C = round(temp_C + 4.0 + np.random.normal(0, 0.5), 2)
                energia_kW = round(energia_kW + 7.0 +
                                   np.random.normal(0, 0.8), 2)

            data.append({
                'timestamp': timestamp,
                'edificio': 'A',
                'piso': piso,
                'temp_C': temp_C,
                'humedad_pct': humedad_pct,
                'energia_kW': energia_kW
            })

    df = pd.DataFrame(data)
    return df


# --- FUNCIÓN PRINCIPAL DE EJECUCIÓN ---
if __name__ == "__main__":
    print(
        f"Generando {HOURS_OF_DATA} horas de datos simulados para los Pisos {PISOS}...")
    df_data = generate_simulated_data(hours=HOURS_OF_DATA)
    df_data.to_csv(FILE_NAME, index=False)
    print(
        f"✅ Datos generados exitosamente en '{FILE_NAME}'. Filas: {len(df_data)}")
