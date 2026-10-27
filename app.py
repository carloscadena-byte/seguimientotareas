import streamlit as st
import pandas as pd
from datetime import date
from streamlit_gsheets import GSheetsConnection

RESPONSABLES = [
    "",
    "Carlos Cadena",
    "Carlos Muñoz",
    "Sivia Hernandez",
    "Veronica Vasquez"
]

st.set_page_config(page_title="Seguimiento de Tareas", page_icon="📋", layout="wide")

# Conexión directa a Google Sheets
conn = st.connection("gsheets", type=GSheetsConnection)

def cargar_datos():
    try:
        # ttl=0 fuerza a leer los datos más frescos de Google Sheets sin esperar caché
        df = conn.read(ttl=0)
        if df is None or df.empty:
            return pd.DataFrame(columns=["Cumplida", "Tarea", "Responsable", "Prioridad", "Fecha"])
        df["Responsable"] = df["Responsable"].fillna("")
        df["Cumplida"] = df["Cumplida"].astype(bool)
        return df
    except Exception:
        return pd.DataFrame(columns=["Cumplida", "Tarea", "Responsable", "Prioridad", "Fecha"])

def guardar_datos(df):
    conn.update(data=df)

# Cabecera y botón de refresco
col_titulo, col_sync = st.columns([4, 1])
with col_titulo:
    st.title("📋 Tablero de Seguimiento de Tareas")
with col_sync:
    st.write("")
    if st.button("🔄 Sincronizar Ahora", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

df_actual = cargar_datos()

# Formulario para registrar tareas
with st.expander("➕ Registrar Nueva Tarea", expanded=False):
    with st.form("nuevo_registro", clear_on_submit=True):
        col_t, col_r = st.columns([2, 1])
        tarea = col_t.text_input("Descripción de la Tarea")
        responsable = col_r.selectbox("Persona a Cargo", RESPONSABLES, index=0)

        col_p, col_f = st.columns([1, 1])
        prioridad = col_p.selectbox("Prioridad", ["Baja", "Media", "Alta"], index=1)
        fecha_limite = col_f.date_input("Fecha Límite", value=date.today())

        if st.form_submit_button("Agregar Tarea"):
            if tarea.strip():
                nueva_tarea = pd.DataFrame([{
                    "Cumplida": False,
                    "Tarea": tarea.strip(),
                    "Responsable": responsable,
                    "Prioridad": prioridad,
                    "Fecha": str(fecha_limite)
                }])
                df_fresco = cargar_datos()
                df_total = pd.concat([df_fresco, nueva_tarea], ignore_index=True)
                guardar_datos(df_total)
                st.success("¡Tarea guardada directamente en Google Sheets!")
                st.rerun()
            else:
                st.warning("Por favor especifica una descripción para la tarea.")

st.markdown("---")

# Filtros
st.subheader("🔍 Filtros de Búsqueda")
col_f_resp, col_f_estado, col_f_prio = st.columns([2, 1, 1])

with col_f_resp:
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

df_filtrado = df_actual.copy()

if filtro_responsable:
    df_filtrado = df_filtrado[df_filtrado["Responsable"].isin(filtro_responsable)]

if filtro_estado == "Solo Pendientes":
    df_filtrado = df_filtrado[df_filtrado["Cumplida"] == False]
elif filtro_estado == "Solo Cumplidas":
    df_filtrado = df_filtrado[df_filtrado["Cumplida"] == True]

if filtro_prioridad:
    df_filtrado = df_filtrado[df_filtrado["Prioridad"].isin(filtro_prioridad)]

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

col_save, col_metric = st.columns([1, 3])
with col_save:
    if st.button("💾 Guardar Cambios", use_container_width=True):
        df_base = cargar_datos()
        df_base.update(editor_df)
        guardar_datos(df_base)
        st.success("¡Base de datos actualizada en Google Sheets!")
        st.rerun()

with col_metric:
    if not df_filtrado.empty:
        total = len(df_filtrado)
        completadas = int(df_filtrado["Cumplida"].sum())
        avance = int((completadas / total) * 100) if total > 0 else 0
        st.progress(avance / 100, text=f"Progreso en vista actual: {avance}% ({completadas}/{total} tareas)")
