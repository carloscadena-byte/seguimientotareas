import streamlit as st
import pandas as pd
import os
from datetime import date

ARCHIVO_DATOS = "tareas.csv"

RESPONSABLES = [
    "Carlos Cadena",
    "Carlos Muñoz",
    "Sivia Hernandez",
    "Veronica Vasquez"
]

st.set_page_config(page_title="Seguimiento de Tareas", page_icon="📋", layout="wide")
st.title("📋 Tablero de Seguimiento de Tareas")

# Función para cargar registros
def cargar_datos():
    if os.path.exists(ARCHIVO_DATOS):
        df = pd.read_csv(ARCHIVO_DATOS)
        if "Cumplida" in df.columns:
            df["Cumplida"] = df["Cumplida"].astype(bool)
        return df
    return pd.DataFrame(columns=["Cumplida", "Tarea", "Responsable", "Prioridad", "Fecha"])

# Función para persistir registros
def guardar_datos(df):
    df.to_csv(ARCHIVO_DATOS, index=False)

# Cargar datos base
if "tareas_df" not in st.session_state:
    st.session_state.tareas_df = cargar_datos()

# Formulario para registrar tareas
with st.expander("➕ Registrar Nueva Tarea", expanded=False):
    with st.form("nuevo_registro", clear_on_submit=True):
        col_t, col_r = st.columns([2, 1])
        tarea = col_t.text_input("Descripción de la Tarea")
        responsable = col_r.selectbox("Persona a Cargo", RESPONSABLES)

        col_p, col_f = st.columns([1, 1])
        prioridad = col_p.selectbox("Prioridad", ["Baja", "Media", "Alta"], index=1)
        fecha_limite = col_f.date_input("Fecha Límite", value=date.today())

        if st.form_submit_button("Agregar Tarea"):
            if tarea.strip():
                nueva_tarea = {
                    "Cumplida": False,
                    "Tarea": tarea.strip(),
                    "Responsable": responsable,
                    "Prioridad": prioridad,
                    "Fecha": str(fecha_limite)
                }
                # Recargar archivo para evitar sobreescrituras
                df_disco = cargar_datos()
                df_actualizado = pd.concat([df_disco, pd.DataFrame([nueva_tarea])], ignore_index=True)
                guardar_datos(df_actualizado)
                st.session_state.tareas_df = df_actualizado
                st.success("¡Tarea agregada con éxito!")
                st.rerun()
            else:
                st.warning("Por favor especifica una descripción para la tarea.")

st.markdown("---")

# 🔍 Panel de Filtros
st.subheader("🔍 Filtros de Búsqueda")
col_f_resp, col_f_estado, col_f_prio = st.columns([2, 1, 1])

with col_f_resp:
    filtro_responsable =
