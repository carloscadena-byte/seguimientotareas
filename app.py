import streamlit as st
import pandas as pd
import os
from datetime import date

ARCHIVO_DATOS = "tareas.csv"

RESPONSABLES = [
    "",
    "Carlos Cadena",
    "Carlos Muñoz",
    "Sivia Hernandez",
    "Veronica Vasquez"
]

# Configuración de página
st.set_page_config(page_title="Seguimiento de Tareas", page_icon="📋", layout="wide")

# 🔄 AUTO-REFRESCO: Actualiza la app automáticamente cada 10 segundos para ver cambios de otros usuarios
st.logo("https://cdn-icons-png.flaticon.com/512/2618/2618245.png", icon_image="https://cdn-icons-png.flaticon.com/512/2618/2618245.png")
st.fragment(run_every="10s")

st.title("📋 Tablero de Seguimiento de Tareas")

# Función para cargar registros (forzamos lectura fresca del disco)
def cargar_datos():
    if os.path.exists(ARCHIVO_DATOS):
        # Evitamos caché de pandas leyendo directamente
        df = pd.read_csv(ARCHIVO_DATOS)
        if "Cumplida" in df.columns:
            df["Cumplida"] = df["Cumplida"].astype(bool)
        return df
    return pd.DataFrame(columns=["Cumplida", "Tarea", "Responsable", "Prioridad", "Fecha"])

# Función para persistir registros
def guardar_datos(df):
    df.to_csv(ARCHIVO_DATOS, index=False)

# Carga fresca en cada ejecución del script
tareas_actuales = cargar_datos()

# Cabecera con botón de sincronización manual rápida
col_titulo, col_sync = st.columns([4, 1])
with col_sync:
    if st.button("🔄 Sincronizar Ahora", use_container_width=True):
        st.rerun()

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
                # Cargar el estado más reciente del archivo antes de guardar para no pisar cambios de otros
                df_reciente = cargar_datos()
                df_actualizado = pd.concat([df_reciente, pd.DataFrame([nueva_tarea])], ignore_index=True)
                guardar_datos(df_actualizado)
                st.success("¡Tarea agregada con éxito!")
                st.rerun()
            else:
                st.warning("Por favor especifica una descripción para la tarea.")

# Tabla interactiva
st.subheader("Lista de Tareas")
st.caption("La tabla se sincroniza sola cada 10 segundos. Si haces cambios manuales, presiona 'Guardar Cambios'.")

editor_df = st.data_editor(
    tareas_actuales,
    num_rows="dynamic",
    use_container_width=True,
    key="editor_tareas",
    column_config={
        "Cumplida": st.column_config.CheckboxColumn("¿Cumplida?", default=False),
        "Responsable": st.column_config.SelectboxColumn("Responsable", options=RESPONSABLES),
        "Prioridad": st.column_config.SelectboxColumn("Prioridad", options=["Baja", "Media", "Alta"])
    }
)

col_save, col_metric = st.columns([1, 3])
with col_save:
    if st.button("💾 Guardar Cambios", use_container_width=True):
        guardar_datos(editor_df)
        st.success("¡Cambios guardados en el servidor!")
        st.rerun()

with col_metric:
    if not editor_df.empty:
        total = len(editor_df)
        completadas = int(editor_df["Cumplida"].sum())
        avance = int((completadas / total) * 100) if total > 0 else 0
        st.progress(avance / 100, text=f"Progreso global: {avance}% ({completadas}/{total} tareas)")
