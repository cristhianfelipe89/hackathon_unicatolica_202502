# =========================================================
# MÓDULO: config.py
# Propósito: Definir umbrales y recomendaciones del negocio.
# =========================================================

# -------------------- UMBRALES DEL RETO (T, H, Energía) --------------------
UMBRALES = {
    'temp_C': {
        'Informativa': {'min': 26.0},
        'Media': {'min': 28.0},
        'Critica': {'min': 29.5}
    },
    'humedad_pct': {
        'Informativa': {'low': 25, 'high': 70},
        'Media': {'low': 22, 'high': 75},
        'Critica': {'low': 20, 'high': 80}
    },
    'energia_kW': {
        'Media': 15.0,  # Umbral de kW que indica carga alta
        'Critica': 18.0 # Umbral de kW que indica sobrecarga
    }
}

# -------------------- MENSAJES Y RECOMENDACIONES --------------------
RECOMENDACIONES = {
    'temp_C_Media': "Ajustar setpoint del Piso X a 24°C en los próximos 15 min.",
    'temp_C_Critica': "Revisión urgente de HVAC y carga en Piso X. Ajustar setpoint inmediatamente.",
    'humedad_pct_Critica_low': "Programar revisión de sellos térmicos en Piso X para evitar pérdida de humedad.",
    'humedad_pct_Critica_high': "Incrementar ventilación del Piso X; revisar puertas/celosías por humedad excesiva.",
    'energia_kW_Critica': "Redistribuir carga eléctrica del Piso X al Piso Y en la próxima hora.",
    'riesgo_combinado_Critica': "RIESGO CRÍTICO: Sobrecarga térmica inminente. Redistribuir carga eléctrica en Piso X para prevenir fallas.",
    'preventiva_temp_C': "Predicción: Posiblemente supere el umbral de Temp Media en +60 min. Ajustar setpoint preventivamente."
}

# -------------------- PARÁMETROS GENERALES --------------------
WINDOWS_SIZE_MINUTES = 60 # Ventana de tiempo para el promedio móvil (1 hora)
PISOS_MONITOREADOS = [1, 2, 3]