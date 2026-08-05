import streamlit as st
import pandas as pd
from streamlit_calendar import calendar
from datetime import datetime, date
import re
import os
import io
import requests
import base64

# ==========================================
# 1. CONFIGURACIÓN DE PÁGINA Y ESTILOS
# ==========================================
st.set_page_config(
    layout="wide", 
    page_title="Planificador de Contenidos UPEU", 
    page_icon="📲"
)

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Figtree:ital,wght@0,300..900;1,300..900&display=swap');
    html, body, [class*="css"], .stMarkdown, p, div { font-family: 'Figtree', sans-serif !important; }
    .stApp, .main, [data-testid="stAppViewContainer"], [data-testid="stHeader"] { 
        background-color: #E8E8E8 !important; 
    }
    div[data-testid="stForm"] { 
        background-color: #FFFFFF !important; border-radius: 8px !important; padding: 25px !important; 
        box-shadow: 0px 4px 6px rgba(0, 0, 0, 0.05) !important; border: 1px solid #D1D5DB !important;
    }
    h1 { color: #000000 !important; font-weight: 800 !important; font-size: 2.2rem !important; }
    h2, h3 { color: #007BE0 !important; font-weight: 700 !important; }
    button[kind="primary"] { background-color: #6AC64F !important; color: #FFFFFF !important; font-weight: 700 !important; border-radius: 6px !important; border: none !important; }
    button[kind="primary"]:hover { background-color: #59b040 !important; }
    .hashtag-gestion { color: #6AC64F !important; font-weight: 800; font-size: 1.1rem; }
    div[data-baseweb="tab-list"] button[aria-selected="true"] { color: #007BE0 !important; border-bottom-color: #007BE0 !important; }
    </style>
""", unsafe_allow_html=True)

LOGO_FILE = "isologo_RN.svg"

# ==========================================
# 2. CONTROL DE ACCESO
# ==========================================
st.sidebar.header("🔑 Control de Acceso")
password = st.sidebar.text_input("Contraseña de Editor", type="password")
CONTRASEÑA_CORRECTA = "UPEU2026" 
es_editor = (password == CONTRASEÑA_CORRECTA)

if es_editor: st.sidebar.success("🔑 Modo Editor Activado")
else: st.sidebar.info("👁️ Modo Visualización (Solo Lectura)")

# ==========================================
# 3. CONEXIÓN A GITHUB
# ==========================================
def github_request(method, payload=None):
    token = st.secrets.get("GITHUB_TOKEN")
    repo = st.secrets.get("GITHUB_REPO")
    path = st.secrets.get("GITHUB_FILE_PATH", "planificador_contenido_upeu.xlsx")
    
    if not token or not repo:
        return None, "Faltan configurar las credenciales de GitHub en los Secrets de Streamlit."
        
    url = f"https://api.github.com/repos/{repo}/contents/{path}"
    headers = {"Authorization": f"token {token}", "Accept": "application/vnd.github.v3+json"}
    
    if method == "GET":
        response = requests.get(url, headers=headers)
        if response.status_code == 200: return response.json(), None
        return None, f"Error al descargar archivo de GitHub (Status: {response.status_code})"
    elif method == "PUT" and payload:
        response = requests.put(url, headers=headers, json=payload)
        if response.status_code in [200, 201]: return response.json(), None
        return None, f"Error al guardar cambios en GitHub: {response.text}"
    return None, "Método inválido"

def load_data():
    file_info, error = github_request("GET")
    columnas_requeridas = ["Fecha Publicación", "Red / Canal", "Pilar de Contenido", "Título / Tema", "Copy / Texto", "Formato", "Estado", "Responsable", "Link a Materiales (Drive/Canva)", "Link a Publicación", "Notas / Observaciones"]
    
    if error or not file_info:
        path_local = st.secrets.get("GITHUB_FILE_PATH", "planificador_contenido_upeu.xlsx")
        if os.path.exists(path_local): df = pd.read_excel(path_local)
        else: return pd.DataFrame(columns=columnas_requeridas)
    else:
        conte_bytes = base64.b64decode(file_info["content"])
        df = pd.read_excel(io.BytesIO(conte_bytes))
        
    df.columns = df.columns.str.strip()
    for col in columnas_requeridas:
        if col not in df.columns: df[col] = ""
    return df.reset_index(drop=True)

def push_data_to_github(df, commit_message="Actualización del planificador de contenidos"):
    file_info, error = github_request("GET")
    if error or not file_info:
        st.error(f"No se pudo sincronizar en GitHub: {error}")
        return False
        
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer: df.to_excel(writer, index=False)
    content_b64 = base64.b64encode(output.getvalue()).decode("utf-8")
    
    payload = {"message": commit_message, "content": content_b64, "sha": file_info["sha"]}
    _, put_error = github_request("PUT", payload=payload)
    if put_error:
        st.error(put_error)
        return False
    return True

if 'plan_contenido' not in st.session_state:
    st.session_state.plan_contenido = load_data()

# ==========================================
# 4. INTERFAZ PRINCIPAL
# ==========================================
if os.path.exists(LOGO_FILE): st.image(LOGO_FILE, width=180)

st.title("Planificador de Contenidos y Comunicación")
st.markdown("**Unidad Provincial de Enlace con Universidades (UPEU)** | Gobierno de Río Negro")
st.markdown("<span class='hashtag-gestion'>#gobiernodelosrionegrinos</span>", unsafe_allow_html=True) 

if es_editor:
    tab1, tab2, tab3, tab4 = st.tabs(["🗓️ Calendario de Publicaciones", "✍️ Registrar Nuevo Contenido", "✏️ Editar / Eliminar Publicación", "📊 Grilla Completa y Filtros"])
else:
    tab1, tab4 = st.tabs(["🗓️ Calendario de Publicaciones", "📊 Grilla Completa y Filtros"])
    tab2, tab3 = None, None

# TAB 1: CALENDARIO
with tab1:
    st.header("Cronograma de Publicaciones")
    events = []
    colores_redes = {"Instagram": "#E1306C", "Facebook": "#1877F2", "X (Twitter)": "#000000", "Gacetilla de Prensa": "#007BE0", "Web Oficial": "#6AC64F", "WhatsApp": "#25D366"}
    
    for idx, row in st.session_state.plan_contenido.iterrows():
        fecha_val = str(row.get('Fecha Publicación', '')).strip().split(" ")[0]
        if fecha_val and fecha_val != "nan":
            red = str(row.get('Red / Canal', 'Red'))
            titulo = f"[{red}] {str(row.get('Título / Tema', 'Sin Título'))}"
            color = colores_redes.get(red, "#333333")
            events.append({
                "title": titulo, "start": fecha_val, "end": fecha_val, "color": color,
                "extendedProps": {
                    "red": red, "pilar": str(row.get('Pilar de Contenido', '')),
                    "copy": str(row.get('Copy / Texto', '')), "formato": str(row.get('Formato', '')),
                    "estado": str(row.get('Estado', '')), "link_mat": str(row.get('Link a Materiales (Drive/Canva)', '')),
                    "link_pub": str(row.get('Link a Publicación', '')), "notas": str(row.get('Notas / Observaciones', ''))
                }
            })
            
    if len(events) > 0:
        state = calendar(events=events, options={"headerToolbar": {"left": "prev,next today", "center": "title", "right": "dayGridMonth,listMonth"}, "initialView": "dayGridMonth", "locale": "es"}, key="cal_contenido")
        if state.get("eventClick"):
            props = state["eventClick"]["event"].get("extendedProps", {})
            st.markdown("---")
            st.subheader("🔍 Detalle del Contenido Seleccionado")
            col_d1, col_d2 = st.columns(2)
            with col_d1:
                st.markdown(f"**📌 Título:** {state['eventClick']['event']['title']}")
                st.markdown(f"**📲 Red / Canal:** `{props.get('red')}`")
                st.markdown(f"**🎨 Formato:** `{props.get('formato')}`")
                st.markdown(f"**⚙️ Estado:** `{props.get('estado')}`")
                if props.get('link_mat'):
                    st.markdown(f"**📁 Materiales:** [Abrir en Drive/Canva]({props.get('link_mat')})")
            with col_d2:
                st.markdown(f"**📝 Copy / Texto:**")
                st.info(props.get('copy'))
                if props.get('link_pub'):
                    st.markdown(f"**🔗 Ver Publicación:** [Ir al post]({props.get('link_pub')})")
    else: st.warning("No hay publicaciones agendadas para mostrar.")

# TAB 2: REGISTRO DE NUEVO CONTENIDO
if es_editor and tab2 is not None:
    with tab2:
        st.header("Cargar Nueva Pieza de Contenido")
        with st.form("form_nuevo_contenido", clear_on_submit=True):
            c1, c2 = st.columns(2)
            with c1:
                f_fecha = st.date_input("Fecha estimada de publicación", datetime.today())
                f_red = st.selectbox("Red / Canal", ["Instagram", "Facebook", "X (Twitter)", "Gacetilla de Prensa", "Web Oficial", "WhatsApp", "Otro"])
                f_pilar = st.selectbox("Pilar de Contenido", ["Institucional", "Educación / Universidades", "Gestión Territorial", "Anuncios / Becas", "Protocolo"])
                f_titulo = st.text_input("Título / Tema principal")
                f_formato = st.selectbox("Formato de la pieza", ["Reel / Video corto", "Carrusel", "Placa fija", "Historia", "Gacetilla de texto", "Comunicado Oficial"])
                f_estado = st.selectbox("Estado inicial", ["Idea / Pendiente", "En producción", "En revisión", "Aprobado", "Publicado"])
            with c2:
                f_copy = st.text_area("Copy / Texto para el post", height=120)
                f_link_mat = st.text_input("Link a Materiales (Carpeta Drive, Canva, etc.)")
                f_link_pub = st.text_input("Link a la publicación final (si ya fue publicada)")
                f_responsable = st.text_input("Responsable de edición", value="Equipo UPEU")
                f_notas = st.text_area("Notas / Indicaciones de diseño")
                
            sub = st.form_submit_button("💾 Guardar Contenido")
            if sub:
                if not f_titulo: st.error("Por favor completa el título o tema.")
                else:
                    nuevo_reg = {
                        "Fecha Publicación": str(f_fecha), "Red / Canal": f_red, "Pilar de Contenido": f_pilar,
                        "Título / Tema": f_titulo, "Copy / Texto": f_copy, "Formato": f_formato, "Estado": f_estado,
                        "Responsable": f_responsable, "Link a Materiales (Drive/Canva)": f_link_mat,
                        "Link a Publicación": f_link_pub, "Notas / Observaciones": f_notas
                    }
                    df_new = pd.concat([st.session_state.plan_contenido, pd.DataFrame([nuevo_reg])], ignore_index=True)
                    if push_data_to_github(df_new, f"Añadir contenido: {f_titulo}"):
                        st.session_state.plan_contenido = df_new
                        st.success("¡Pieza de contenido agendada e impactada en GitHub!")
                        st.rerun()

# TAB 4: GRILLA COMPLETA Y DESCARGA
with tab4:
    st.header("Grilla de Contenidos")
    st.dataframe(st.session_state.plan_contenido, use_container_width=True)
    
    out_e = io.BytesIO()
    with pd.ExcelWriter(out_e, engine='openpyxl') as writer: st.session_state.plan_contenido.to_excel(writer, index=False)
    st.download_button("📥 Descargar Grilla en Excel", data=out_e.getvalue(), file_name="grilla_contenidos_upeu.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
