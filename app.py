import streamlit as st
import pandas as pd
import os
from datetime import date

ARCHIVO_DATOS = "tareas.csv"

# 👥 Lista de responsables incluyendo un campo en blanco al inicio
RESPONSABLES = [
    "", # Opción vacía por defecto
    "Carlos Cadena",
    "Carlos Muñoz",
    "Sivia Hernandez",
    "Veronica Vasquez"
]

st.set_page_config(page_title="Seguimiento de Tareas", page_icon="📋", layout="wide")

# Cabecera principal con Título y Botón de Sincronización recuperado
col_titulo, col_sync = st.columns([4, 1])
with col_titulo:
    st.title("📋 Tablero de Seguimiento de Tareas")
with col_sync:
    st.write("") # Espaciador visual para alinear el botón
    if st.button("🔄 Sincronizar Ahora", use_container_width=True):
        # Al presionar limpia el estado de la sesión y lee directamente del disco
        if "tareas_df" in st.session_state:
            del st.session_state.tareas_df
        st.rerun()

# Función para cargar registros
def cargar_datos():
    if os.path.exists(ARCHIVO_DATOS):
        df = pd.read_csv(ARCHIVO_DATOS)
        # Aseguramos que los valores vacíos se interpreten como texto vacío en lugar de NaN
        df["Responsable"] = df["Responsable"].fillna("")
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
        # El desplegable ahora inicia por defecto con la opción en blanco
        responsable = col_r.selectbox("Persona a Cargo", RESPONSABLES, index=0)

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
                # Recargar archivo del disco para no pisar cambios ajenos
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
    # Mostramos los nombres sin incluir la opción vacía para filtrar limpiamente
    filtro_responsable = st.multiselect(
        "Filtrar por Responsable:",
        options=[r for r in RESPONSABLES if r != ""],
        default=[]
    )

with col_f_estado:
    filtro_estado = st.selectbox(
        "Estado de Cumplimiento:",
        options=["Todas", "Solo Pendientes", "Solo Cumplidas"]
    )

with col_f_prio:
    filtro_prioridad = st.multiselect(
        "Prioridad:",
        options=["Alta", "Media", "Baja"],
        default=[]
    )

# Aplicar lógica de filtrado sobre el DataFrame
df_filtrado = st.session_state.tareas_df.copy()

if filtro_responsable:
    df_filtrado = df_filtrado[df_filtrado["Responsable"].isin(filtro_responsable)]

if filtro_estado == "Solo Pendientes":
    df_filtrado = df_filtrado[df_filtrado["Cumplida"] == False]
elif filtro_estado == "Solo Cumplidas":
    df_filtrado = df_filtrado[df_filtrado["Cumplida"] == True]

if filtro_prioridad:
    df_filtrado = df_filtrado[df_filtrado["Prioridad"].isin(filtro_prioridad)]

# Mostrar resumen y tabla filtrada
st.subheader(f"Lista de Tareas ({len(df_filtrado)} encontradas)")

editor_df = st.data_editor(
    df_filtrado,
    num_rows="dynamic",
    use_container_width=True,
    key="tabla_editor",
    column_config={
        "Cumplida": st.column_config.CheckboxColumn("¿Cumplida?", default=False),
        "Responsable": st.column_config.SelectboxColumn("Responsable", options=RESPONSABLES),
        "Prioridad": st.column_config.SelectboxColumn("Prioridad", options=["Baja", "Media", "Alta"])
    }
)

# Botones de acción y métricas
col_save, col_metric = st.columns([1, 3])
with col_save:
    if st.button("💾 Guardar Cambios", use_container_width=True):
        # Actualizar los registros modificados en la base principal usando el índice
        st.session_state.tareas_df.update(editor_df)
        guardar_datos(st.session_state.tareas_df)
        st.success("¡Cambios guardados con éxito!")
        st.rerun()

with col_metric:
    if not df_filtrado.empty:
        total = len(df_filtrado)
        completadas = int(df_filtrado["Cumplida"].sum())
        avance = int((completadas / total) * 100) if total > 0 else 0
        st.progress(avance / 100, text=f"Progreso en vista actual: {avance}% ({completadas}/{total} tareas)")
