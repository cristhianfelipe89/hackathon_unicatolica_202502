# 💡 SmartFloors: Monitoreo Predictivo MVP

[cite_start]**Reto Hackathon:** "Innovación y Tecnología para el Futuro" - ZONAMERICA[cite: 4, 8].

---

## 1. Descripción del Proyecto

[cite_start]Este proyecto es un Producto Mínimo Viable (MVP) que implementa un sistema de monitoreo predictivo para el **Edificio A, Pisos 1-3**[cite: 28, 31].

**Funcionalidad principal:**
1.  [cite_start]Realizar la ingesta de datos simulados (Temperatura, Humedad, Energía) a $\text{1 registro/minuto}$[cite: 37].
2.  [cite_start]Estimar a **$+60$ minutos** la Temperatura y Humedad[cite: 49].
3.  [cite_start]Detectar anomalías (umbrales térmicos/eléctricos) y **riesgos de sobrecarga térmica**[cite: 51, 124].
4.  [cite_start]Generar **alertas preventivas** con recomendaciones claras y accionables[cite: 52, 130].
5.  [cite_start]Mostrar todo en un panel de control simple y claro con **Streamlit**[cite: 57].

---

## 2. Arquitectura de la Solución (Código)

[cite_start]La solución está desarrollada en Python y utiliza una arquitectura modular de **Backend** (Lógica) y **Frontend** (Presentación), lo que asegura un código mantenible y bien estructurado[cite: 169].

| Módulo | Directorio | Responsabilidad Principal |
| :--- | :--- | :--- |
| **Configuración** | `configuracion/config.py` | Definición de constantes, umbrales y mensajes de recomendación. |
| **Backend** | `backend/core_logic.py` | Carga de datos, Promedio Móvil para predicción, lógica de umbrales y generación del DataFrame de alertas. |
| **Simulador** | `data_simulator.py` | Script para generar los datos de entrada (`smartfloors_data.csv`). |
| **Frontend** | `Frontend/app/dashboard.py` | Aplicación web (Streamlit) que consume los resultados del Backend para la visualización. |

---

## 3. Guía de Ejecución (¡En menos de 5 minutos!)

### A. Requisitos

Asegúrese de tener Python (3.7+) instalado y las siguientes librerías:

```bash
pip install pandas numpy streamlit plotly

## 4. Para crear y activar el entorno virtual
cd hacklathon
python -m venv venv
# Windows
venv\Scripts\activate

pip install -r requirements.txt

##para saber las librerias installadas
pip list

##para exportar a un archivos requirements.txt
pip freeze > requirements.txt