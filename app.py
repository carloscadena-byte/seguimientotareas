import streamlit as st
import pandas as pd
import requests
import json
from datetime import date

# 🔗 Tu URL de Google Apps Script
WEBAPP_URL = "https://script.google.com/macros/s/AKfycbxyQQyYK4sCmb0ix4FkzwoGsbHxBpnL7/exec"

RESPONSABLES = [
    "",
    "Carlos Cadena",
    "Carlos Muñoz",
    "Sivia Hernandez",
    "Veronica Vasquez"
]

COLUMNAS = ["Cumplida", "Tarea", "Responsable", "Prioridad", "Fecha"]

st.set_page_config(page_title="Seguimiento de Tareas", page_icon="📋", layout="wide")

# --- 🚀 FUNCIONES DE CONEXIÓN ---
@st.cache_data(show_spinner=False)
def consultar_sheets():
    """Consulta física a Google Sheets (Se guarda en caché para ir rápido)"""
    try:
        res = requests.get(WEBAPP_URL, timeout=10, allow_redirects=True)
        valores = res.json()
        if isinstance(valores, list) and len(valores) > 1:
            df = pd.DataFrame(valores[1:], columns=valores[0])
            for col in COLUMNAS:
                if col not in df.columns:
                    df[col] = ""
            df["Cumplida"] = df["Cumplida"].apply(lambda x: str(x).lower() in ["true", "1", "yes", "si"])
            df["Responsable"] = df["Responsable"].fillna("")
            return df[COLUMNAS]
    except Exception:
        pass
    return pd.DataFrame(columns=COLUMNAS)

def enviar_segundo_plano(payload):
    """Envía los datos a Google Sheets de forma silenciosa"""
    try:
        requests.post(
            WEBAPP_URL,
            data=json.dumps(payload),
            headers={"Content-Type": "application/json"},
            timeout=10,
            allow_redirects=True
        )
    except Exception:
        pass

# --- 🧠 GESTIÓN DE MEMORIA AL INSTANTE ---
if "df_memoria" not in st.session_state:
    st.session_state.df_memoria = consultar_sheets()

# Cabecera principal
col_titulo, col_sync = st.columns([4, 1])
with col_titulo:
    st.title("📋 Tablero de Seguimiento de Tareas")
with col_sync:
    st.write("")
    if st.button("🔄 Sincronizar Nube", use_container_width=True, help="Fuerza la descarga de cambios nuevos desde Google Sheets"):
        st.cache_data.clear()
        st.session_state.df_memoria = consultar_sheets()
        st.rerun()

# Formulario para registrar tareas
with st.expander("➕ Registrar Nueva Tarea", expanded=False):
    with st.form("nuevo_registro", clear_on_submit=True):
        col_t, col_r = st.columns(2)
        tarea = col_t.text_input("Descripción de la Tarea")
        responsable = col_r.selectbox("Persona a Cargo", RESPONSABLES, index=0)

        col_p, col_f = st.columns(2)
        prioridad = col_p.selectbox("Prioridad", ["Baja", "Media", "Alta"], index=1)
        fecha_limite = col_f.date_input("Fecha Límite", value=date.today())

        if st.form_submit_button("Agregar Tarea"):
            if tarea.strip():
                # 1. Creamos la fila
                nueva_fila = [False, tarea.strip(), responsable, prioridad, str(fecha_limite)]
                
                # 2. ⚡ ACTUALIZACIÓN INSTANTÁNEA: Lo sumamos a la pantalla de inmediato sin parpadeos
                nuevo_df_fila = pd.DataFrame([nueva_fila], columns=COLUMNAS)
                st.session_state.df_memoria = pd.concat([st.session_state.df_memoria, nuevo_df_fila], ignore_index=True)
                
                # 3. Guardamos en la nube de fondo
                enviar_segundo_plano({"action": "append", "row": nueva_fila})
                st.success("¡Tarea agregada!")
                st.rerun()
            else:
                st.warning("Por favor especifica una descripción para la tarea.")

st.markdown("---")

# Filtros rápidos
st.subheader("🔍 Filtros de Búsqueda")
col_f_resp, col_f_estado, col_f_prio = st.columns(3)

with col_f_resp:
    filtro_responsable = st.multiselect("Filtrar por Responsable:", options=[r for r in RESPONSABLES if r != ""], default=[])

with col_f_estado:
    filtro_estado = st.selectbox("Estado de Cumplimiento:", options=["Todas", "Solo Pendientes", "Solo Cumplidas"])

with col_f_prio:
    filtro_prioridad = st.multiselect("Prioridad:", options=["Alta", "Media", "Baja"], default=[])

# Filtrado sobre la memoria rápida
df_filtrado = st.session_state.df_memoria.copy()

if filtro_responsable:
    df_filtrado = df_filtrado[df_filtrado["Responsable"].isin(filtro_responsable)]

if filtro_estado == "Solo Pendientes":
    df_filtrado = df_filtrado[df_filtrado["Cumplida"] == False]
elif filtro_estado == "Solo Cumplidas":
    df_filtrado = df_filtrado[df_filtrado["Cumplida"] == True]

if filtro_prioridad:
    df_filtrado = df_filtrado[df_filtrado["Prioridad"].isin(filtro_prioridad)]

st.subheader(f"Lista de Tareas ({len(df_filtrado)} encontradas)")

# Render interactivo
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

# Guardar cambios manuales (Ediciones masivas)
col_save, col_metric = st.columns(2)
with col_save:
    if st.button("💾 Guardar Cambios", use_container_width=True):
        # 1. Sincronizamos cambios visuales a la memoria local de inmediato
        st.session_state.df_memoria.update(editor_df)
        
        # 2. Enviamos a la nube en paralelo
        data_matrix = [COLUMNAS] + st.session_state.df_memoria.values.tolist()
        enviar_segundo_plano({"action": "update_all", "data": data_matrix})
        st.success("¡Base de datos sincronizada!")
        st.rerun()

with col_metric:
    if not df_filtrado.empty:
        total = len(df_filtrado)
        completadas = int(df_filtrado["Cumplida"].sum())
        avance = int((completadas / total) * 100) if total > 0 else 0
        st.progress(avance / 100, text=f"Progreso actual: {avance}% ({completadas}/{total} tareas)")
