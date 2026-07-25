import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
from streamlit_calendar import calendar
from github import Github
import io

# Configuración de la página
st.set_page_config(page_title="Planificador de Contenido Instagram", layout="wide", page_icon="📱")

st.title("📱 Planificador Estratégico de Contenido - Instagram")
st.markdown("Herramienta interactiva para la carga, gestión y visualización del calendario de contenidos con persistencia en GitHub.")

# --- PARÁMETROS Y CONEXIÓN A GITHUB ---
GITHUB_TOKEN = st.secrets.get("GITHUB_TOKEN", "")
REPO_NAME = st.secrets.get("REPO_NAME", "")  # Ejemplo: "usuario/planificador-instagram"
FILE_PATH = "planificacion_instagram.xlsx"

def obtener_repo():
    if not GITHUB_TOKEN or not REPO_NAME:
        return None
    try:
        g = Github(GITHUB_TOKEN)
        return g.get_repo(REPO_NAME)
    except Exception as e:
        st.error(f"Error al conectar con la API de GitHub: {e}")
        return None

def cargar_datos_desde_github():
    repo = obtener_repo()
    columnas = ["ID", "Fecha", "Hora", "Pilar", "Formato", "Gancho", "Copy", "Link_Visual", "Estado", "Prioridad", "Objetivo"]
    
    if repo:
        try:
            contents = repo.get_contents(FILE_PATH)
            excel_bytes = contents.decoded_content
            df = pd.read_excel(io.BytesIO(excel_bytes))
            for col in columnas:
                if col not in df.columns:
                    df[col] = ""
            return df.fillna("")
        except Exception:
            # Si el archivo no existe aún en el repo
            return pd.DataFrame(columns=columnas)
    else:
        # Fallback local si no están configurados los secrets
        try:
            return pd.read_excel(FILE_PATH).fillna("")
        except FileNotFoundError:
            return pd.DataFrame(columns=columnas)

def guardar_datos_en_github(df, mensaje_commit="Actualización de contenidos"):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False)
    excel_data = output.getvalue()
    
    repo = obtener_repo()
    if repo:
        try:
            try:
                contents = repo.get_contents(FILE_PATH)
                repo.update_file(contents.path, mensaje_commit, excel_data, contents.sha)
            except Exception:
                repo.create_file(FILE_PATH, mensaje_commit, excel_data)
            return True
        except Exception as e:
            st.error(f"Error al guardar commit en GitHub: {e}")
            return False
    else:
        # Guardado local de respaldo
        df.to_excel(FILE_PATH, index=False)
        return True

# Carga inicial de datos
df_contenido = cargar_datos_desde_github()

# --- BARRA LATERAL: FORMULARIO DE CARGA ---
st.sidebar.header("➕ Cargar Nuevo Contenido")

with st.sidebar.form("form_carga", clear_on_submit=True):
    fecha = st.date_input("Fecha de Publicación", datetime.now())
    hora = st.time_input("Hora de Publicación", datetime.now().time())
    pilar = st.selectbox("Eje / Pilar Temático", [
        "Gestión e Institucional", 
        "Programas y Convocatorias", 
        "Casos de Éxito / Territorio", 
        "Educativo / Tips", 
        "Comunidad"
    ])
    formato = st.selectbox("Formato", ["Reel", "Carrusel", "Imagen Fija", "Historia", "Live"])
    objetivo = st.selectbox("Objetivo", ["Alcance / Posicionamiento", "Informativo", "Engagement / Conversación", "Tráfico / Clics"])
    gancho = st.text_input("Idea / Gancho (Hook inicial)")
    copy = st.text_area("Copy / Texto del posteo")
    link_visual = st.text_input("Link a Google Drive / Canva")
    estado = st.selectbox("Estado", ["Idea / Borrador", "Para Diseñar / Grabar", "En Revisión", "Programado", "Publicado"])
    prioridad = st.select_slider("Prioridad", options=["Baja", "Media", "Alta"])
    
    submitted = st.form_submit_button("📥 Cargar al Calendario")

    if submitted:
        nuevo_id = int(datetime.now().timestamp())
        nuevo_registro = {
            "ID": nuevo_id,
            "Fecha": str(fecha),
            "Hora": str(hora),
            "Pilar": pilar,
            "Formato": formato,
            "Gancho": gancho,
            "Copy": copy,
            "Link_Visual": link_visual,
            "Estado": estado,
            "Prioridad": prioridad,
            "Objetivo": objetivo
        }
        
        df_actualizado = pd.concat([df_contenido, pd.DataFrame([nuevo_registro])], ignore_index=True)
        
        with st.spinner("Guardando y haciendo Commit en GitHub..."):
            if guardar_datos_en_github(df_actualizado, f"Agregado posteo: {gancho[:20]}"):
                st.sidebar.success("¡Contenido guardado permanentemente en el repositorio!")
                st.rerun()

# --- PANEL CENTRAL: MÉTRICAS Y RESUMEN ---
col1, col2, col3, col4 = st.columns(4)
total_posts = len(df_contenido)
programados = len(df_contenido[df_contenido["Estado"] == "Programado"])
reels = len(df_contenido[df_contenido["Formato"] == "Reel"])
pendientes = len(df_contenido[df_contenido["Estado"].isin(["Idea / Borrador", "Para Diseñar / Grabar"])])

col1.metric("Total Publicaciones", total_posts)
col2.metric("Programados", programados)
col3.metric("Reels Planificados", reels)
col4.metric("Pendientes de Producción", pendientes)

st.divider()

# --- PESTAÑAS DE VISUALIZACIÓN ---
tab1, tab2, tab3 = st.tabs(["🗓️ Calendario Visual", "📋 Tabla y Edición", "📊 Análisis y Balance"])

with tab1:
    st.subheader("Calendario de Contenidos")
    if not df_contenido.empty:
        events = []
        for index, row in df_contenido.iterrows():
            if str(row['Fecha']).strip():
                events.append({
                    "title": f"[{row['Formato']}] {row['Gancho'] if row['Gancho'] else row['Pilar']}",
                    "start": f"{row['Fecha']}T{row['Hora'] if row['Hora'] else '12:00:00'}",
                    "backgroundColor": "#FF4B4B" if row['Prioridad'] == "Alta" else "#3D82F6",
                })
        
        calendar_options = {
            "initialView": "dayGridMonth",
            "headerToolbar": {
                "left": "prev,next today",
                "center": "title",
                "right": "dayGridMonth,timeGridWeek"
            },
        }
        calendar(events=events, options=calendar_options)
    else:
        st.info("No hay contenidos cargados aún. Usá el formulario de la izquierda para empezar.")

with tab2:
    st.subheader("Listado Detallado de Publicaciones")
    st.dataframe(df_contenido, use_container_width=True)
    
    # Sección para eliminar un registro si fuera necesario
    if not df_contenido.empty and "ID" in df_contenido.columns:
        st.divider()
        st.subheader("🗑️ Eliminar o Editar Registro")
        opcion_eliminar = st.selectbox("Seleccioná la publicación por ID / Gancho:", 
                                       options=df_contenido["ID"].tolist(),
                                       format_func=lambda x: f"ID: {x} - {df_contenido[df_contenido['ID']==x]['Gancho'].values[0]}")
        if st.button("Eliminar Publicación"):
            df_filtrado = df_contenido[df_contenido["ID"] != opcion_eliminar]
            with st.spinner("Actualizando repositorio..."):
                guardar_datos_en_github(df_filtrado, f"Eliminado posteo ID: {opcion_eliminar}")
                st.success("Registro eliminado correctamente.")
                st.rerun()

with tab3:
    st.subheader("Distribución de Contenido")
    if not df_contenido.empty:
        col_g1, col_g2 = st.columns(2)
        with col_g1:
            st.write("**Porcentaje por Pilar Temático**")
            st.bar_chart(df_contenido["Pilar"].value_counts())
        with col_g2:
            st.write("**Formatos Utilizados**")
            st.bar_chart(df_contenido["Formato"].value_counts())
