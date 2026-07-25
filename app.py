import streamlit as st
import pandas as pd
from datetime import datetime
from streamlit_calendar import calendar

# Configuración de la página
st.set_page_config(page_title="Planificador de Contenido Instagram", layout="wide", page_icon="📱")

st.title("📱 Planificador Estratégico de Contenido - Instagram")
st.markdown("Herramienta interactiva para la carga, gestión y visualización del calendario de contenidos.")

# Inicializar estado para guardar los datos si no existe
if "df_contenido" not in st.session_state:
    st.session_state.df_contenido = pd.DataFrame(columns=[
        "Fecha", "Hora", "Pilar", "Formato", "Gancho", "Copy", 
        "Link_Visual", "Estado", "Prioridad", "Objetivo"
    ])

# --- BARRA LATERAL: FORMULARIO DE CARGA ---
st.sidebar.header("➕ Cargar Nuevo Contenido")

with st.sidebar.form("form_carga", clear_on_submit=True):
    fecha = st.date_input("Fecha de Publicación", datetime.now())
    hora = st.time_input("Hora de Publicación", datetime.now().time())
    pilar = st.selectbox("Eje / Pilar Temático", ["Gestión e Institucional", "Programas y Convocatorias", "Casos de Éxito / Territorio", "Educativo / Tips", "Comunidad"])
    formato = st.selectbox("Formato", ["Reel", "Carrusel", "Imagen Fija", "Historia", "Live"])
    objetivo = st.selectbox("Objetivo", ["Alcance / Posicionamiento", "Informativo", "Engagement / Conversación", "Tráfico / Clics"])
    gancho = st.text_input("Idea / Gancho (Hook inicial)")
    copy = st.text_area("Copy / Texto del posteo")
    link_visual = st.text_input("Link a Google Drive / Canva")
    estado = st.selectbox("Estado", ["Idea / Borrador", "Para Diseñar / Grabar", "En Revisión", "Programado", "Publicado"])
    prioridad = st.select_slider("Prioridad", options=["Baja", "Media", "Alta"])
    
    submitted = st.form_submit_dict = st.form_submit_button("📥 Cargar al Calendario")

    if submitted:
        nuevo_registro = {
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
        st.session_state.df_contenido = pd.concat(
            [st.session_state.df_contenido, pd.DataFrame([nuevo_registro])], 
            ignore_index=True
        )
        st.sidebar.success("¡Contenido agregado con éxito!")

# --- PANEL CENTRAL: MÉTRICAS Y RESUMEN ---
col1, col2, col3, col4 = st.columns(4)
total_posts = len(st.session_state.df_contenido)
programados = len(st.session_state.df_contenido[st.session_state.df_contenido["Estado"] == "Programado"])
reels = len(st.session_state.df_contenido[st.session_state.df_contenido["Formato"] == "Reel"])
pendientes = len(st.session_state.df_contenido[st.session_state.df_contenido["Estado"].isin(["Idea / Borrador", "Para Diseñar / Grabar"])])

col1.metric("Total Publicaciones", total_posts)
col2.metric("Programados", programados)
col3.metric("Reels Planificados", reels)
col4.metric("Pendientes de Producción", pendientes)

st.divider()

# --- PESTAÑAS DE VISUALIZACIÓN ---
tab1, tab2, tab3 = st.tabs(["🗓️ Calendario Visual", "📋 Tabla de Gestión", "📊 Análisis y Balance"])

with tab1:
    st.subheader("Calendario de Contenidos")
    if not st.session_state.df_contenido.empty:
        events = []
        for index, row in st.session_state.df_contenido.iterrows():
            events.append({
                "title": f"[{row['Formato']}] {row['Gancho'] if row['Gancho'] else row['Pilar']}",
                "start": f"{row['Fecha']}T{row['Hora']}",
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
    st.dataframe(st.session_state.df_contenido, use_container_width=True)
    
    # Opción para exportar datos
    if not st.session_state.df_contenido.empty:
        csv = st.session_state.df_contenido.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Descargar Planificación en CSV", data=csv, file_name="planificacion_instagram.csv", mime="text/csv")

with tab3:
    st.subheader("Distribución de Contenido")
    if not st.session_state.df_contenido.empty:
        col_g1, col_g2 = st.columns(2)
        with col_g1:
            st.write("**Porcentaje por Pilar Temático**")
            st.bar_chart(st.session_state.df_contenido["Pilar"].value_counts())
        with col_g2:
            st.write("**Formatos Utilizados**")
            st.bar_chart(st.session_state.df_contenido["Formato"].value_counts())
