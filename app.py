import json
import io
import urllib.parse
from datetime import datetime, timedelta
from github import Github
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

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
  columnas = [
      "ID",
      "Fecha",
      "Hora",
      "Tema",
      "Formato",
      "Contenido",
      "Link_Doc_Copys",
      "Link_Visual",
      "Estado",
      "Prioridad",
      "Objetivo",
      "Requiere_Gacetilla",
      "Link_Gacetilla",
  ]
  df_vacio = pd.DataFrame(columns=columnas)
  repo = obtener_repo()

  if repo:
    try:
      contents = repo.get_contents(FILE_PATH)
      excel_bytes = contents.decoded_content
      df_cargado = pd.read_excel(
          io.BytesIO(excel_bytes), dtype={"Hora": str, "Fecha": str}, engine="openpyxl"
      )

      if "Gancho" in df_cargado.columns and "Contenido" not in df_cargado.columns:
        df_cargado["Contenido"] = df_cargado["Gancho"]
      if "Pilar" in df_cargado.columns and "Tema" not in df_cargado.columns:
        df_cargado["Tema"] = df_cargado["Pilar"]

      for col in columnas:
        if col not in df_cargado.columns:
          df_cargado[col] = ""

      return df_cargado[columnas].fillna("")
    except Exception:
      return df_vacio
  else:
    try:
      df_cargado = pd.read_excel(
          FILE_PATH, dtype={"Hora": str, "Fecha": str}, engine="openpyxl"
      ).fillna("")
      if "Gancho" in df_cargado.columns and "Contenido" not in df_cargado.columns:
        df_cargado["Contenido"] = df_cargado["Gancho"]
      if "Pilar" in df_cargado.columns and "Tema" not in df_cargado.columns:
        df_cargado["Tema"] = df_cargado["Pilar"]

      for col in columnas:
        if col not in df_cargado.columns:
          df_cargado[col] = ""

      return df_cargado[columnas].fillna("")
    except Exception:
      return df_vacio


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
  try:
    df.to_excel(FILE_PATH, index=False, engine="openpyxl")
    return True
  except Exception:
    return False


# Carga inicial de datos
df_contenido = cargar_datos_desde_github()

# OPCIONES FIJAS DE LISTAS
OPCIONES_FORMATO = ["Reel", "Carrusel", "Imagen Fija", "Historia", "Live"]
OPCIONES_OBJETIVO = [
    "Alcance / Posicionamiento",
    "Informativo",
    "Tráfico / Clics",
    "Convocatoria / Registro",
]
OPCIONES_ESTADO = [
    "Idea / Borrador",
    "Para Diseñar / Grabar",
    "En Revisión",
    "Programado",
    "Publicado",
]
OPCIONES_PRIORIDAD = ["Baja", "Media", "Alta"]

# --- BARRA LATERAL: FORMULARIO DE CARGA ---
st.sidebar.header("📝 Cargar Nuevo Contenido")
if st.sidebar.button("🚪 Cerrar Sesión"):
  st.session_state.autenticado = False
  st.rerun()

fecha = st.sidebar.date_input("Fecha de Publicación", datetime.now())
hora_texto = st.sidebar.text_input(
    "Hora de Publicación (Formato 24hs HH:MM)", value="18:00"
)

tema = st.sidebar.text_input("Tema")
formato = st.sidebar.selectbox("Formato", OPCIONES_FORMATO)
objetivo = st.sidebar.selectbox("Objetivo", OPCIONES_OBJETIVO)
contenido_post = st.sidebar.text_input("Contenido")

link_doc_copys = st.sidebar.text_input(
    "Link al Documento de Copys Semanal (Google Doc / Drive)"
)
link_visual = st.sidebar.text_input(
    "Link al Recurso Visual / Contenido (Reel / Canva / Drive)"
)

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
estado = st.sidebar.selectbox("Estado", OPCIONES_ESTADO)
prioridad = st.sidebar.select_slider("Prioridad", options=OPCIONES_PRIORIDAD)

if st.sidebar.button("🚀 Cargar al Calendario"):
  fecha_str = str(fecha)[:10]
  nuevo_id = int(datetime.now().timestamp())
  nuevo_registro = {
      "ID": nuevo_id,
      "Fecha": fecha_str,
      "Hora": str(hora_texto).strip(),
      "Tema": tema,
      "Formato": formato,
      "Contenido": contenido_post,
      "Link_Doc_Copys": link_doc_copys,
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
        df_actualizado, f"Agregado posteo: {contenido_post[:20]}"
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
    len(df_contenido[df_contenido["Requiere_Gacetilla"].isin(["Sí", "Si"])])
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
    "📋 Tabla, Edición y Bajas",
    "📊 Análisis",
    "📱 Reporte para WhatsApp",
])

with tab1:
  st.subheader("Calendario de Contenidos")
  events = []

  if not df_contenido.empty:
    for index, row in df_contenido.iterrows():
      try:
        raw_fecha = str(row.get("Fecha", "")).strip()
        if raw_fecha and raw_fecha.lower() != "nan":
          dt_parsed = pd.to_datetime(raw_fecha, errors="coerce")
          if pd.notnull(dt_parsed):
            fecha_clean = dt_parsed.strftime("%Y-%m-%d")

            hora_raw = str(row.get("Hora", "")).strip()
            if not hora_raw or hora_raw.lower() == "nan":
              hora_raw = "18:00"
            if len(hora_raw) == 5:
              hora_raw += ":00"

            cont_txt = str(row.get("Contenido", "")).replace("nan", "").strip()
            tema_txt = str(row.get("Tema", "")).replace("nan", "").strip()
            titulo_base = (
                cont_txt if cont_txt else (tema_txt if tema_txt else "Sin título")
            )

            titulo = f"[{hora_raw[:5]}] [{row.get('Formato', '')}] {titulo_base}"
            if str(row.get("Requiere_Gacetilla", "")).strip() in ["Sí", "Si"]:
              titulo = "📰 " + titulo

            events.append({
                "title": titulo,
                "start": f"{fecha_clean}T{hora_raw}",
                "color": (
                    "#FF4B4B"
                    if str(row.get("Prioridad", "")) == "Alta"
                    else "#3D82F6"
                ),
                # Propiedades extendidas para mostrar abajo al hacer clic
                "extendedProps": {
                    "tema": str(row.get("Tema", "")),
                    "formato": str(row.get("Formato", "")),
                    "contenido": str(row.get("Contenido", "")),
                    "objetivo": str(row.get("Objetivo", "")),
                    "estado": str(row.get("Estado", "")),
                    "prioridad": str(row.get("Prioridad", "")),
                    "link_visual": str(row.get("Link_Visual", "")),
                    "link_copys": str(row.get("Link_Doc_Copys", "")),
                    "gacetilla": str(row.get("Requiere_Gacetilla", "")),
                    "link_gacetilla": str(row.get("Link_Gacetilla", "")),
                    "hora": hora_raw[:5],
                    "fecha": fecha_clean,
                }
            })
      except Exception:
        continue

  if events:
    st.caption(f"✓ {len(events)} publicación(es) cargada(s). Hacé clic en cualquier evento para desplegar su detalle.")
  else:
    st.info(
        "No hay publicaciones visibles todavía. Cargar tu primer contenido"
        " desde el menú lateral."
    )

  events_json = json.dumps(events)
  calendar_html = f"""
  <!DOCTYPE html>
  <html>
  <head>
    <link href='https://cdn.jsdelivr.net/npm/fullcalendar@5.11.3/main.min.css' rel='stylesheet' />
    <script src='https://cdn.jsdelivr.net/npm/fullcalendar@5.11.3/main.min.js'></script>
    <script src='https://cdn.jsdelivr.net/npm/fullcalendar@5.11.3/locales/es.js'></script>
    <style>
      body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; margin: 0; padding: 5px; background-color: #ffffff; color: #31333F; }}
      #calendar {{ max-width: 100%; margin: 0 auto; }}
      .fc-event {{ cursor: pointer; padding: 2px 4px; font-size: 0.85em; border-radius: 4px; }}
      
      /* Tarjeta de detalle que se despliega abajo */
      #detalle-container {{
        display: none;
        margin-top: 20px;
        padding: 16px;
        border-radius: 8px;
        background-color: #f8f9fa;
        border: 1px solid #e9ecef;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
      }}
      #detalle-container h4 {{ margin-top: 0; color: #1f2937; margin-bottom: 12px; font-size: 1.1em; display: flex; justify-content: space-between; align-items: center; }}
      .detalle-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 12px; margin-bottom: 12px; }}
      .detalle-item {{ background: #ffffff; padding: 10px; border-radius: 6px; border: 1px solid #edf2f7; }}
      .detalle-item span {{ font-size: 0.75em; color: #6b7280; text-transform: uppercase; font-weight: bold; display: block; margin-bottom: 4px; }}
      .detalle-item p {{ margin: 0; font-size: 0.9em; font-weight: 500; color: #111827; word-break: break-word; }}
      .badge {{ display: inline-block; padding: 3px 8px; border-radius: 12px; font-size: 0.8em; font-weight: bold; color: white; }}
      a.btn-link {{ color: #2563eb; text-decoration: underline; font-weight: 500; }}
    </style>
  </head>
  <body>
    <div id='calendar'></div>
    
    <div id='detalle-container'>
      <h4 id='det-titulo'>📋 Detalle del Contenido Seleccionado 
        <button onclick="cerrarDetalle()" style="background:none; border:none; cursor:pointer; font-size:1.2em; color:#6b7280;">✕</button>
      </h4>
      <div class='detalle-grid'>
        <div class='detalle-item'><span>Fecha y Hora</span><p id='det-fechahora'>-</p></div>
        <div class='detalle-item'><span>Tema</span><p id='det-tema'>-</p></div>
        <div class='detalle-item'><span>Formato</span><p id='det-formato'>-</p></div>
        <div class='detalle-item'><span>Estado</span><p id='det-estado'>-</p></div>
        <div class='detalle-item'><span>Objetivo</span><p id='det-objetivo'>-</p></div>
        <div class='detalle-item'><span>Prioridad</span><p id='det-prioridad'>-</p></div>
      </div>
      <div class='detalle-item' style='margin-bottom: 12px;'><span>Contenido / Gancho</span><p id='det-contenido'>-</p></div>
      <div class='detalle-grid'>
        <div class='detalle-item'><span>Link al Contenido</span><p id='det-linkvisual'>-</p></div>
        <div class='detalle-item'><span>Doc Copys Semanal</span><p id='det-linkcopys'>-</p></div>
        <div class='detalle-item'><span>Gacetilla de Prensa</span><p id='det-gacetilla'>-</p></div>
      </div>
    </div>

    <script>
      function cerrarDetalle() {{
        document.getElementById('detalle-container').style.display = 'none';
      }}

      document.addEventListener('DOMContentLoaded', function() {{
        var calendarEl = document.getElementById('calendar');
        var calendar = new FullCalendar.Calendar(calendarEl, {{
          initialView: 'dayGridMonth',
          locale: 'es',
          height: 'auto',
          headerToolbar: {{
            left: 'prev,next today',
            center: 'title',
            right: 'dayGridMonth,timeGridWeek'
          }},
          events: {events_json},
          eventClick: function(info) {{
            var props = info.event.extendedProps;
            
            document.getElementById('det-fechahora').innerText = props.fecha + ' a las ' + props.hora + ' hs';
            document.getElementById('det-tema').innerText = props.tema || 'N/A';
            document.getElementById('det-formato').innerText = props.formato || 'N/A';
            document.getElementById('det-estado').innerText = props.estado || 'N/A';
            document.getElementById('det-objetivo').innerText = props.objetivo || 'N/A';
            document.getElementById('det-prioridad').innerText = props.prioridad || 'N/A';
            document.getElementById('det-contenido').innerText = props.contenido || 'Sin descripción';
            
            // Render de Links
            document.getElementById('det-linkvisual').innerHTML = props.link_visual ? '<a class="btn-link" href="' + props.link_visual + '" target="_blank">Abrir Recurso</a>' : 'Sin enlace';
            document.getElementById('det-linkcopys').innerHTML = props.link_copys ? '<a class="btn-link" href="' + props.link_copys + '" target="_blank">Abrir Doc Copys</a>' : 'Sin enlace';
            
            var gacetillaTxt = props.gacetilla === 'Sí' || props.gacetilla === 'Si' ? 'Sí' : 'No';
            if ((props.gacetilla === 'Sí' || props.gacetilla === 'Si') && props.link_gacetilla) {{
              gacetillaTxt += ' - <a class="btn-link" href="' + props.link_gacetilla + '" target="_blank">Ver Borrador</a>';
            }}
            document.getElementById('det-gacetilla').innerHTML = gacetillaTxt;

            var container = document.getElementById('detalle-container');
            container.style.display = 'block';
            container.scrollIntoView({{ behavior: 'smooth' }});
          }}
        }});
        calendar.render();
      }});
    </script>
  </body>
  </html>
  """
  components.html(calendar_html, height=850, scrolling=True)

with tab2:
  st.subheader("Listado Detallado de Publicaciones")
  st.dataframe(df_contenido, use_container_width=True)

  if not df_contenido.empty and "ID" in df_contenido.columns:
    st.divider()
    col_ed1, col_ed2 = st.columns(2)

    with col_ed1:
      st.subheader("✏️ Modificar Publicación Existente")
      id_editar = st.selectbox(
          "Seleccioná para Editar:",
          options=df_contenido["ID"].tolist(),
          format_func=(
              lambda x: (
                  f"ID: {x} -"
                  f" {df_contenido[df_contenido['ID'] == x]['Contenido'].values[0]}"
              )
          ),
          key="select_edit",
      )

      registro_actual = (
          df_contenido[df_contenido["ID"] == id_editar].iloc[0].to_dict()
      )

      with st.form("form_editar"):
        e_fecha = st.date_input(
            "Fecha",
            pd.to_datetime(registro_actual.get("Fecha")).date()
            if registro_actual.get("Fecha")
            and str(registro_actual.get("Fecha")).lower() != "nan"
            else datetime.now(),
        )
        e_hora = st.text_input(
            "Hora (HH:MM)", value=str(registro_actual.get("Hora", "18:00"))
        )
        e_tema = st.text_input(
            "Tema", value=str(registro_actual.get("Tema", ""))
        )

        idx_formato = (
            OPCIONES_FORMATO.index(registro_actual["Formato"])
            if registro_actual.get("Formato") in OPCIONES_FORMATO
            else 0
        )
        idx_objetivo = (
            OPCIONES_OBJETIVO.index(registro_actual["Objetivo"])
            if registro_actual.get("Objetivo") in OPCIONES_OBJETIVO
            else 0
        )
        idx_estado = (
            OPCIONES_ESTADO.index(registro_actual["Estado"])
            if registro_actual.get("Estado") in OPCIONES_ESTADO
            else 0
        )
        idx_prio = (
            OPCIONES_PRIORIDAD.index(registro_actual["Prioridad"])
            if registro_actual.get("Prioridad") in OPCIONES_PRIORIDAD
            else 0
        )

        e_formato = st.selectbox("Formato", OPCIONES_FORMATO, index=idx_formato)
        e_objetivo = st.selectbox(
            "Objetivo", OPCIONES_OBJETIVO, index=idx_objetivo
        )
        e_contenido = st.text_input(
            "Contenido", value=str(registro_actual.get("Contenido", ""))
        )
        e_link_doc_copys = st.text_input(
            "Link Doc Copys Semanal",
            value=str(registro_actual.get("Link_Doc_Copys", "")),
        )
        e_link_visual = st.text_input(
            "Link Recurso Visual / Contenido",
            value=str(registro_actual.get("Link_Visual", "")),
        )
        e_gacetilla = st.radio(
            "¿Requiere Gacetilla?",
            ["No", "Sí"],
            index=0
            if registro_actual.get("Requiere_Gacetilla") not in ["Sí", "Si"]
            else 1,
        )
        e_link_gacetilla = st.text_input(
            "Link Borrador Gacetilla (Drive)",
            value=str(registro_actual.get("Link_Gacetilla", "")),
        )

        e_estado = st.selectbox("Estado", OPCIONES_ESTADO, index=idx_estado)
        e_prioridad = st.select_slider(
            "Prioridad",
            options=OPCIONES_PRIORIDAD,
            value=OPCIONES_PRIORIDAD[idx_prio],
        )

        btn_guardar_edit = st.form_submit_button("💾 Guardar Cambios")

        if btn_guardar_edit:
          idx = df_contenido[df_contenido["ID"] == id_editar].index[0]
          e_fecha_str = str(e_fecha)[:10]

          df_contenido.at[idx, "Fecha"] = e_fecha_str
          df_contenido.at[idx, "Hora"] = str(e_hora).strip()
          df_contenido.at[idx, "Tema"] = e_tema
          df_contenido.at[idx, "Formato"] = e_formato
          df_contenido.at[idx, "Objetivo"] = e_objetivo
          df_contenido.at[idx, "Contenido"] = e_contenido
          df_contenido.at[idx, "Link_Doc_Copys"] = e_link_doc_copys
          df_contenido.at[idx, "Link_Visual"] = e_link_visual
          df_contenido.at[idx, "Estado"] = e_estado
          df_contenido.at[idx, "Prioridad"] = e_prioridad
          df_contenido.at[idx, "Requiere_Gacetilla"] = e_gacetilla
          df_contenido.at[idx, "Link_Gacetilla"] = e_link_gacetilla

          with st.spinner("Actualizando en GitHub..."):
            guardar_datos_en_github(
                df_contenido, f"Modificado posteo ID: {id_editar}"
            )
            st.success("Publicación modificada con éxito.")
            st.rerun()

    with col_ed2:
      st.subheader("🗑️ Eliminar Publicación")
      opcion_eliminar = st.selectbox(
          "Seleccioná para Eliminar:",
          options=df_contenido["ID"].tolist(),
          format_func=(
              lambda x: (
                  f"ID: {x} -"
                  f" {df_contenido[df_contenido['ID'] == x]['Contenido'].values[0]}"
              )
          ),
          key="select_del",
      )
      if st.button("Eliminar Definitivamente"):
        df_filtrado = df_contenido[df_contenido["ID"] != opcion_eliminar]
        with st.spinner("Actualizando repositorio..."):
          guardar_datos_en_github(
              df_filtrado, f"Eliminado posteo ID: {opcion_eliminar}"
          )
          st.success("Registro eliminado correctamente.")
          st.rerun()

with tab3:
  st.subheader("Distribución de Contenido")
  if not df_contenido.empty and "Tema" in df_contenido.columns:
    col_g1, col_g2 = st.columns(2)
    with col_g1:
      st.write("**Publicaciones por Tema**")
      st.bar_chart(df_contenido["Tema"].value_counts())
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

      link_doc_encontrado = ""

      for index, row in df_semana.iterrows():
        fecha_fmt = (
            pd.to_datetime(row["Fecha"]).strftime("%d/%m")
            if row.get("Fecha")
            else ""
        )
        hora_fmt = (
            f" - {row['Hora']} hs"
            if row.get("Hora") and str(row["Hora"]).strip()
            else ""
        )

        msj += f"*{fecha_fmt}{hora_fmt} - {row.get('Formato', '')}*\n"
        msj += f"• *Tema:* {row.get('Tema', '')}\n"
        msj += f"• *Contenido:* {row.get('Contenido', '')}\n"

        if row.get("Link_Visual") and str(row["Link_Visual"]).strip():
          msj += f"• *Link al contenido:* {row['Link_Visual']}\n"

        if row.get("Requiere_Gacetilla") in ["Sí", "Si"]:
          msj += "• *Gacetilla de prensa:* Sí"
          if row.get("Link_Gacetilla"):
            msj += f" ({row['Link_Gacetilla']})"
          msj += "\n"

        msj += f"• *Estado:* {row.get('Estado', '')}\n\n"

        if not link_doc_encontrado and row.get("Link_Doc_Copys"):
          link_doc_encontrado = row["Link_Doc_Copys"]

      if link_doc_encontrado:
        msj += (
            "📄 *Documento general con Copys de la semana:*"
            f" {link_doc_encontrado}\n\n"
        )

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
