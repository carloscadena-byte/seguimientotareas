import streamlit as st
import pandas as pd
import requests
import json
from datetime import date

WEBAPP_URL = "https://script.google.com/macros/s/AKfycbxyQQyYK4sCmb0ix4FkzwoGsbHxBpnL7MjCRGrfg9UrnA4Gf7zK2AJWNFDSpJbuJlEB/exec"

RESPONSABLES = [
    "",
    "Carlos Cadena",
    "Carlos Muñoz",
    "Sivia Hernandez",
    "Veronica Vasquez"
]

COLUMNAS = ["Cumplida", "Tarea", "Responsable", "Prioridad", "Fecha"]

st.set_page_config(page_title="Seguimiento de Tareas", page_icon="📋", layout="wide")

# 1. Consulta con caché para evitar llamadas lentas repetidas
@st.cache_data(show_spinner=False)
def obtener_datos_remotos():
    try:
        res = requests.get(WEBAPP_URL, timeout=12, allow_redirects=True)
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

def enviar_datos(payload):
    try:
        res = requests.post(
            WEBAPP_URL,
            data=json.dumps(payload),
            headers={"Content-Type": "text/plain"},
            timeout=15,
            allow_redirects=True
        )
        if res.status_code in [200, 302]:
            return True, "OK"
        return False, f"HTTP {res.status_code}"
    except Exception as e:
        return False, str(e)

# Inicialización del estado de memoria local
if "df_tareas" not in st.session_state:
    st.session_state.df_tareas = obtener_datos_remotos()

# 🛠️ CORRECCIÓN AQUÍ: Se añade el argumento '2' (st.columns(2)) para evitar el TypeError
col_titulo, col_sync = st.columns(2)
with col_titulo:
    st.title("📋 Tablero de Seguimiento de Tareas")
with col_sync:
    st.write("")
    if st.button("🔄 Sincronizar con Google Sheets", use_container_width=True):
        st.cache_data.clear()
        st.session_state.df_tareas = obtener_datos_remotos()
        st.toast("Datos Sincronizados", icon="✅")

# 2. ⚡ FRAGMENTO AISLADO: El formulario corre de forma independiente del resto de la página
@st.fragment
def formulario_registro():
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
                    nueva_fila = [False, tarea.strip(), responsable, prioridad, str(fecha_limite)]
                    
                    # Guardamos de fondo en Google Sheets
                    exito, mensaje = enviar_datos({"action": "append", "row": nueva_fila})
                    
                    if exito:
                        # Actualizamos la memoria del navegador de inmediato
                        nueva_fila_df = pd.DataFrame([nueva_fila], columns=COLUMNAS)
                        st.session_state.df_tareas = pd.concat([st.session_state.df_tareas, nueva_fila_df], ignore_index=True)
                        st.toast("¡Tarea guardada exitosamente!", icon="🚀")
                        # Forzamos una actualización limpia de la pantalla sin reconstrucción completa
                        st.rerun(scope="app")
                    else:
                        st.error(f"Error al enviar a Google: {mensaje}")
                else:
                    st.warning("Por favor especifica una descripción para la tarea.")

# Renderizar el formulario aislado
formulario_registro()

st.markdown("---")

# Filtros rápidos (viven en la UI principal)
st.subheader("🔍 Filtros de Búsqueda")
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

# Filtrado sobre la memoria viva
df_filtrado = st.session_state.df_tareas.copy()

if filtro_responsable:
    df_filtrado = df_filtrado[df_filtrado["Responsable"].isin(filtro_responsable)]

if filtro_estado == "Solo Pendientes":
    df_filtrado = df_filtrado[df_filtrado["Cumplida"] == False]
elif filtro_estado == "Solo Cumplidas":
    df_filtrado = df_filtrado[df_filtrado["Cumplida"] == True]

if filtro_prioridad:
    df_filtrado = df_filtrado[df_filtrado["Prioridad"].isin(filtro_prioridad)]

st.subheader(f"Lista de Tareas ({len(df_filtrado)} encontradas)")

# Tabla interactiva
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
    if st.button("💾 Guardar Cambios en Google Sheets", use_container_width=True):
        st.session_state.df_tareas.update(editor_df)
        data_matrix = [COLUMNAS] + st.session_state.df_tareas.values.tolist()
        exito, mensaje = enviar_datos({"action": "update_all", "data": data_matrix})
        
        if exito:
            st.toast("¡Cambios actualizados!", icon="💾")
            st.rerun()
        else:
            st.error(f"Error al sincronizar: {mensaje}")

with col_metric:
    if not df_filtrado.empty:
        total = len(df_filtrado)
        completadas = int(df_filtrado["Cumplida"].sum())
        avance = int((completadas / total) * 100) if total > 0 else 0
        st.progress(avance / 100, text=f"Progreso en vista actual: {avance}% ({completadas}/{total} tareas)")
