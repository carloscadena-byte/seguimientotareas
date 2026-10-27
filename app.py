import streamlit as st
import pandas as pd
import os
from datetime import date

ARCHIVO_DATOS = "tareas.csv"

# Configuración de página
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

# Inicializar estado en memoria
if "tareas_df" not in st.session_state:
    st.session_state.tareas_df = cargar_datos()

# Formulario para registrar tareas
with st.expander("➕ Registrar Nueva Tarea", expanded=False):
    with st.form("nuevo_registro", clear_on_submit=True):
        col_t, col_r = st.columns([2, 1])
        tarea = col_t.text_input("Descripción de la Tarea")
        responsable = col_r.text_input("Persona a Cargo")

        col_p, col_f = st.columns([1, 1])
        prioridad = col_p.selectbox("Prioridad", ["Baja", "Media", "Alta"], index=1)
        fecha_limite = col_f.date_input("Fecha Límite", value=date.today())

        if st.form_submit_button("Agregar Tarea"):
            if tarea.strip():
                nueva_tarea = {
                    "Cumplida": False,
                    "Tarea": tarea.strip(),
                    "Responsable": responsable.strip() if responsable.strip() else "Sin asignar",
                    "Prioridad": prioridad,
                    "Fecha": str(fecha_limite)
                }
                st.session_state.tareas_df = pd.concat(
                    [st.session_state.tareas_df, pd.DataFrame([nueva_tarea])],
                    ignore_index=True
                )
                guardar_datos(st.session_state.tareas_df)
                st.success("¡Tarea agregada con éxito!")
                st.rerun()
            else:
                st.warning("Por favor especifica una descripción para la tarea.")

# Tabla interactiva con checkboxes de cumplimiento
st.subheader("Lista de Tareas")
st.caption("Marca las casillas de cumplimiento y haz clic en 'Guardar Cambios' para actualizar el archivo.")

editor_df = st.data_editor(
    st.session_state.tareas_df,
    num_rows="dynamic",
    use_container_width=True,
    column_config={
        "Cumplida": st.column_config.CheckboxColumn("¿Cumplida?", default=False),
        "Prioridad": st.column_config.SelectboxColumn("Prioridad", options=["Baja", "Media", "Alta"])
    }
)

col_save, col_metric = st.columns([1, 3])
with col_save:
    if st.button("💾 Guardar Cambios"):
        st.session_state.tareas_df = editor_df
        guardar_datos(editor_df)
        st.success("Cambios actualizados.")

with col_metric:
    if not editor_df.empty:
        total = len(editor_df)
        completadas = int(editor_df["Cumplida"].sum())
        avance = int((completadas / total) * 100) if total > 0 else 0
        st.progress(avance / 100, text=f"Progreso global: {avance}% ({completadas}/{total} tareas)")
