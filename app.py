import streamlit as st
import pandas as pd
import requests
from datetime import date

# 🔗 Pega aquí la URL que obtuviste al implementar tu Google Apps Script (/exec)
WEBAPP_URL = "https://script.google.com/macros/s/TU_SCRIPT_ID_AQUI/exec"

RESPONSABLES = [
    "",
    "Carlos Cadena",
    "Carlos Muñoz",
    "Sivia Hernandez",
    "Veronica Vasquez"
]

COLUMNAS = ["Cumplida", "Tarea", "Responsable", "Prioridad", "Fecha"]

st.set_page_config(page_title="Seguimiento de Tareas", page_icon="📋", layout="wide")

def cargar_datos():
    try:
        res = requests.get(WEBAPP_URL, timeout=10)
        valores = res.json()
        if len(valores) > 1:
            df = pd.DataFrame(valores[1:], columns=valores[0])
            for col in COLUMNAS:
                if col not in df.columns:
                    df[col] = ""
            df["Cumplida"] = df["Cumplida"].apply(lambda x: str(x).lower() in ["true", "1", "yes", "si"])
            df["Responsable"] = df["Responsable"].fillna("")
            return df[COLUMNAS]
        return pd.DataFrame(columns=COLUMNAS)
    except Exception:
        return pd.DataFrame(columns=COLUMNAS)

def agregar_fila(nueva_fila):
    payload = {"action": "append", "row": nueva_fila}
    requests.post(WEBAPP_URL, json=payload, timeout=10)

def actualizar_todo(df):
    data_matrix = [COLUMNAS] + df.values.tolist()
    payload = {"action": "update_all", "data": data_matrix}
    requests.post(WEBAPP_URL, json=payload, timeout=10)

# 🛠️ CORRECCIÓN AQUÍ: Se especifica st.columns(2) para evitar el TypeError
col_titulo, col_sync = st.columns(2)
with col_titulo:
    st.title("📋 Tablero de Seguimiento de Tareas")
with col_sync:
    st.write("")
    if st.button("🔄 Sincronizar Ahora", use_container_width=True):
        st.rerun()

df_actual = cargar_datos()

# Formulario para registrar tareas
with st.expander("➕ Registrar Nueva Tarea", expanded=False):
    with st.form("nuevo_registro", clear_on_submit=True):
        # 🛠️ CORRECCIÓN AQUÍ: Se especifica st.columns(2)
        col_t, col_r = st.columns(2)
        tarea = col_t.text_input("Descripción de la Tarea")
        responsable = col_r.selectbox("Persona a Cargo", RESPONSABLES, index=0)

        # 🛠️ CORRECCIÓN AQUÍ: Se especifica st.columns(2)
        col_p, col_f = st.columns(2)
        prioridad = col_p.selectbox("Prioridad", ["Baja", "Media", "Alta"], index=1)
        fecha_limite = col_f.date_input("Fecha Límite", value=date.today())

        if st.form_submit_button("Agregar Tarea"):
            if tarea.strip():
                fila = [False, tarea.strip(), responsable, prioridad, str(fecha_limite)]
                agregar_fila(fila)
                st.success("¡Tarea agregada directamente en Google Sheets!")
                st.rerun()
            else:
                st.warning("Por favor especifica una descripción para la tarea.")

st.markdown("---")

# Filtros
st.subheader("🔍 Filtros de Búsqueda")
# 🛠️ CORRECCIÓN AQUÍ: Se especifica st.columns(3) para las tres secciones de filtros
col_f_resp, col_f_estado, col_f_prio = st.columns(3)

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

# 🛠️ CORRECCIÓN AQUÍ: Se especifica st.columns(2)
col_save, col_metric = st.columns(2)
with col_save:
    if st.button("💾 Guardar Cambios", use_container_width=True):
        df_base = df_actual.copy()
        df_base.update(editor_df)
        actualizar_todo(df_base)
        st.success("¡Base de datos actualizada en Google Sheets!")
        st.rerun()

with col_metric:
    if not df_filtrado.empty:
        total = len(df_filtrado)
        completadas = int(df_filtrado["Cumplida"].sum())
        avance = int((completadas / total) * 100) if total > 0 else 0
        st.progress(avance / 100, text=f"Progreso en vista actual: {avance}% ({completadas}/{total} tareas)")

