import io
import urllib.parse
from datetime import datetime, timedelta
from github import Github
import pandas as pd
import streamlit as st
from streamlit_calendar import calendar

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(
    page_title="Planificador de Contenido Instagram",
    layout="wide",
    page_icon="📅",
)

# --- SISTEMA DE AUTENTICACIÓN / LOGIN ---
APP_PASSWORD = "ComunicacionUPEU2026"


def verificar_password():
  if "autenticado" not in st.session_state:
    st.session_state.autenticado = False

  if not st.session_state.autenticado:
    st.title("🔒 Acceso Restringido")
    st.markdown(
        "Esta herramienta contiene información confidencial de planificación de"
        " contenidos."
    )
    password_input = st.text_input("Contraseña de equipo:", type="password")
    if st.button("Ingresar"):
      if password_input == APP_PASSWORD:
        st.session_state.autenticado = True
        st.success("Acceso concedido.")
        st.rerun()
      else:
        st.error("Contraseña incorrecta. Por favor, verificá con tu equipo.")
    return False
  return True


# Detener ejecución si no está autenticado
if not verificar_password():
  st.stop()

# --- SI PASA EL LOGIN, SE EJECUTA LA HERRAMIENTA ---
st.title("📅 Planificador Estratégico de Contenido Instagram & Prensa")
st.markdown(
    "Herramienta confidencial para la carga, gestión y visualización del"
    " calendario editorial."
)

# --- PARÁMETROS Y CONEXIÓN A GITHUB ---
GITHUB_TOKEN = st.secrets.get("GITHUB_TOKEN", "")
REPO_NAME = st.secrets.get("REPO_NAME", "")
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
  columnas = [
      "ID",
      "Fecha",
      "Hora",
      "Pilar",
      "Formato",
      "Gancho",
      "Copy",
      "Link_Visual",
      "Estado",
      "Prioridad",
      "Objetivo",
      "Requiere_Gacetilla",
      "Link_Gacetilla",
  ]
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
      return pd.DataFrame(columns=columnas)
  else:
    try:
      return pd.read_excel(FILE_PATH).fillna("")
    except FileNotFoundError:
      return pd.DataFrame(columns=columnas)


def guardar_datos_en_github(
    df, mensaje_commit="Actualización de contenidos"
):
  output = io.BytesIO()
  with pd.ExcelWriter(output, engine="openpyxl") as writer:
    df.to_excel(writer, index=False)
  excel_data = output.getvalue()
  repo = obtener_repo()
  if repo:
    try:
      try:
        contents = repo.get_contents(FILE_PATH)
        repo.update_file(
            contents.path, mensaje_commit, excel_data, contents.sha
        )
      except Exception:
        repo.create_file(FILE_PATH, mensaje_commit, excel_data)
      return True
    except Exception as e:
      st.error(f"Error al guardar commit en GitHub: {e}")
      return False
  df.to_excel(FILE_PATH, index=False)
  return True


# Carga inicial de datos
df_contenido = cargar_datos_desde_github()

# --- BARRA LATERAL: FORMULARIO DE CARGA Y LOGOUT ---
st.sidebar.header("📝 Cargar Nuevo Contenido")
if st.sidebar.button("🚪 Cerrar Sesión"):
  st.session_state.autenticado = False
  st.rerun()

# Formulario interactivo
fecha = st.sidebar.date_input("Fecha de Publicación", datetime.now())
hora = st.sidebar.time_input("Hora de Publicación", datetime.now().time())
pilar = st.sidebar.selectbox("Eje / Pilar Temático", [
    "Gestión e Institucional",
    "Programas y Convocatorias",
    "Casos de Éxito / Territorio",
    "Educativo / Tips",
    "Comunidad",
])
formato = st.sidebar.selectbox(
    "Formato", ["Reel", "Carrusel", "Imagen Fija", "Historia", "Live"]
)
objetivo = st.sidebar.selectbox("Objetivo", [
    "Alcance / Posicionamiento",
    "Informativo",
    "Tráfico / Clics",
    "Convocatoria / Registro",
])
gancho = st.sidebar.text_input("Idea / Gancho (Hook inicial)")
copy = st.sidebar.text_area("Copy / Texto del posteo")
link_visual = st.sidebar.text_input("Link a Google Drive / Canva")

# --- NUEVOS CAMPOS: GACETILLA DE PRENSA ---
st.sidebar.markdown("---")
requiere_gacetilla = st.sidebar.radio(
    "¿Requiere Gacetilla de Prensa?", ["No", "Sí"]
)
link_gacetilla = ""
if requiere_gacetilla == "Sí":
  link_gacetilla = st.sidebar.text_input(
      "Link al borrador de Gacetilla (Drive):"
  )

st.sidebar.markdown("---")
estado = st.sidebar.selectbox("Estado", [
    "Idea / Borrador",
    "Para Diseñar / Grabar",
    "En Revisión",
    "Programado",
    "Publicado",
])
prioridad = st.sidebar.select_slider(
    "Prioridad", options=["Baja", "Media", "Alta"]
)

if st.sidebar.button("🚀 Cargar al Calendario"):
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
      "Objetivo": objetivo,
      "Requiere_Gacetilla": requiere_gacetilla,
      "Link_Gacetilla": link_gacetilla,
  }
  df_actualizado = pd.concat(
      [df_contenido, pd.DataFrame([nuevo_registro])], ignore_index=True
  )
  with st.spinner("Guardando de forma segura..."):
    if guardar_datos_en_github(
        df_actualizado, f"Agregado posteo: {gancho[:20]}"
    ):
      st.sidebar.success("¡Contenido guardado con éxito!")
      st.rerun()

# --- PANEL CENTRAL: MÉTRICAS Y RESUMEN ---
col1, col2, col3, col4 = st.columns(4)
total_posts = len(df_contenido)
programados = (
    len(df_contenido[df_contenido["Estado"] == "Programado"])
    if not df_contenido.empty
    else 0
)
reels = (
    len(df_contenido[df_contenido["Formato"] == "Reel"])
    if not df_contenido.empty
    else 0
)
gacetillas_pendientes = (
    len(df_contenido[df_contenido["Requiere_Gacetilla"] == "Sí"])
    if not df_contenido.empty and "Requiere_Gacetilla" in df_contenido.columns
    else 0
)

col1.metric("Total Publicaciones", total_posts)
col2.metric("Programados", programados)
col3.metric("Reels Planificados", reels)
col4.metric("Con Gacetilla de Prensa", gacetillas_pendientes)
st.divider()

# --- PESTAÑAS DE VISUALIZACIÓN ---
tab1, tab2, tab3, tab4 = st.tabs([
    "📅 Calendario Visual",
    "📋 Tabla y Edición",
    "📊 Análisis",
    "📱 Reporte para WhatsApp",
])

with tab1:
  st.subheader("Calendario de Contenidos")
  if not df_contenido.empty:
    events = []
    for index, row in df_contenido.iterrows():
      if str(row["Fecha"]).strip():
        titulo = (
            f"[{row['Formato']}] {row['Gancho'] if row['Gancho'] else row['Pilar']}"
        )
        if row.get("Requiere_Gacetilla") == "Sí":
          titulo = "📰 " + titulo
        events.append({
            "title": titulo,
            "start": f"{row['Fecha']}T{row['Hora'] if row['Hora'] else '12:00:00'}",
            "backgroundColor": (
                "#FF4B4B" if row["Prioridad"] == "Alta" else "#3D82F6"
            ),
        })
    calendar_options = {
        "initialView": "dayGridMonth",
        "headerToolbar": {
            "left": "prev,next today",
            "center": "title",
            "right": "dayGridMonth,timeGridWeek",
        },
    }
    calendar(events=events, options=calendar_options)
  else:
    st.info(
        "No hay contenidos cargados aún. Usá el formulario de la izquierda para"
        " agregar."
    )

with tab2:
  st.subheader("Listado Detallado de Publicaciones")
  st.dataframe(df_contenido, use_container_width=True)
  if not df_contenido.empty and "ID" in df_contenido.columns:
    st.divider()
    st.subheader("🗑️ Eliminar Registro")
    opcion_eliminar = st.selectbox(
        "Seleccioná la publicación por ID / Gancho:",
        options=df_contenido["ID"].tolist(),
        format_func=(
            lambda x: (
                f"ID: {x} -"
                f" {df_contenido[df_contenido['ID'] == x]['Gancho'].values[0]}"
            )
        ),
    )
    if st.button("Eliminar Publicación"):
      df_filtrado = df_contenido[df_contenido["ID"] != opcion_eliminar]
      with st.spinner("Actualizando repositorio..."):
        guardar_datos_en_github(
            df_filtrado, f"Eliminado posteo ID: {opcion_eliminar}"
        )
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

with tab4:
  st.subheader("📱 Generador de Resumen Semanal para Validación")
  st.markdown(
      "Seleccioná el rango de fechas para armar el mensaje de validación:"
  )
  col_f1, col_f2 = st.columns(2)
  fecha_inicio = col_f1.date_input("Fecha Inicio de Semana", datetime.now())
  fecha_fin = col_f2.date_input(
      "Fecha Fin de Semana", datetime.now() + timedelta(days=6)
  )

  if not df_contenido.empty:
    df_temp = df_contenido.copy()
    df_temp["Fecha_dt"] = pd.to_datetime(df_temp["Fecha"], errors="coerce")
    mask = (df_temp["Fecha_dt"] >= pd.to_datetime(fecha_inicio)) & (
        df_temp["Fecha_dt"] <= pd.to_datetime(fecha_fin)
    )
    df_semana = df_temp.loc[mask].sort_values("Fecha_dt")

    if not df_semana.empty:
      msj = "*PLANIFICACIÓN DE CONTENIDO INSTAGRAM*\n"
      msj += (
          f"*Semana:* {fecha_inicio.strftime('%d/%m')} al"
          f" {fecha_fin.strftime('%d/%m')}\n\n"
      )
      msj += (
          "Hola! Te comparto la propuesta de contenidos para esta semana para"
          " tu revisión y visto bueno:\n\n"
      )

      for index, row in df_semana.iterrows():
        fecha_fmt = (
            pd.to_datetime(row["Fecha"]).strftime("%d/%m")
            if row["Fecha"]
            else ""
        )
        msj += f"*{fecha_fmt} - {row['Formato']}*\n"
        msj += f"• *Eje:* {row['Pilar']}\n"
        msj += f"• *Gancho/Idea:* {row['Gancho']}\n"
        if row["Copy"]:
          copy_resumen = (
              row["Copy"][:100] + "..."
              if len(row["Copy"]) > 100
              else row["Copy"]
          )
          msj += f"• *Texto:* _{copy_resumen}_\n"
        if row["Link_Visual"]:
          msj += f"• *Preview visual:* {row['Link_Visual']}\n"
        if row.get("Requiere_Gacetilla") == "Sí":
          msj += "• *Gacetilla de prensa:* Sí"
          if row.get("Link_Gacetilla"):
            msj += f" ({row['Link_Gacetilla']})"
          msj += "\n"
        msj += f"• *Estado:* {row['Estado']}\n\n"

      msj += "Quedo atenta a tus comentarios o sugerencias. ¡Muchas gracias!"

      st.markdown("### Vista previa del mensaje:")
      st.code(msj, language="markdown")
      texto_encoded = urllib.parse.quote(msj)
      ws_url = f"https://api.whatsapp.com/send?text={texto_encoded}"
      st.markdown(
          f'<a href="{ws_url}" target="_blank"><button style="background-color:'
          " #25D366; color: white; padding: 10px 20px; border: none;"
          ' border-radius: 5px; cursor: pointer; font-weight: bold;">Abrir y'
          " enviar por WhatsApp</button></a>",
          unsafe_allow_html=True,
      )
    else:
      st.warning(
          "No hay publicaciones programadas para el rango de fechas"
          " seleccionado."
      )
  else:
    st.info("No hay publicaciones registradas para generar el reporte.")
