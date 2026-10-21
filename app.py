#En la Versión 5.3 se incluye generación del documento en Word
#En la versión 5.4 se incluy las columnas de nombre del referente y el supervisor que aprueba
#En la vesión 5.5 Se incluye y mejora el análisis del dasboard
#En la versión 5.6 se incluye mejorar la visual de los valores del dasboard
# En la versión 5.7 se incluye mejor vsualización del dasboard del municipio
# En la versión 5.8 se incluye mejorar el informe de Word
# En la versión 5.9 se incluye el colocar en todas las tablas de trazabilidad y seguimiento las columnas de id_actividad y # nombre de la actividad
#En esta versión 6 se crear un certificado o acta de conformidad de las actividades realizadas por el referente la cual debe  # generarse de forma automática donde se indique para el municipio las actividades revisadas y aprobadas con un análisis   # de lo operativo y financiero revisado
# En la Versión 6.1 se incluye la columna de observaciones para el supervisor y e referente
# En la versión 6.2 se incluye el seguimiento administrativo del contrato que solo se hace solo por el supervisor del contrato
# En la versión 6.3 se incluye opción de rechazo por parte del referente al igual que el supervisor para que el municipio sudsane la novedad
# En la versión 6.4 se incluye tabla de secuencia para verificar los pagos realizados
# En la versión 6.5 se potencia el análisis de datos del tablero incluyendo la información de pagos con la tabla de secuencia
#En la versión 6.6 Se incluye en el informe Word del supervisión la información financiera de los pagos de los informes de supervisor
#En la versión 6.7 se incluye un filtro para el referente que le permita filtar las actividades a realizar por municipio y por actividad
# En la versión 6.8 e incluye los decimales en el tablero de control
# En la versión 6.9 se incluye la generación del acta del referente en el formato establecido de acta
# en la versión 7 se incluye que se genera control financiero en el reporte  del municipio
# en la versión 7.1 se quita el sobreescribir
# En la versión 7.2 se uita el que se pueda eliminar hoja de seguimiento y se coloca el motivo de rechazo de supevisor
# En la versión 7.3 se ingresa el cambio de en el certificado cambiar la palabra referente por supervisor de apoyo
# En la versión 7.4 se arregla el calculo de la ejecución financiera real
# En la versión 7.5 se realiza protección a la eliminación de la hoja de seguimeinto de pagos
# En la versión 7.7 se realiza cambi de todo el código por el cambio de la BD

import streamlit as st
import pandas as pd
import time
from sqlalchemy import text

# --- 1. CONFIGURACIÓN DE LA INTERFAZ ---
st.set_page_config(page_title="Sistema PIC - Unidad de Medida", layout="wide")

# Crear conexión nativa a PostgreSQL (Supabase) con psycopg2
conn = st.connection("postgresql", type="sql")

# Diccionario de llaves primarias y columnas válidas por tabla en PostgreSQL
ESQUEMA_PG = {
    "usuarios": {
        "pk": "id_usuario",
        "cols": ["id_usuario", "nombre_completo", "email", "password", "cedula", "cargo", "telefono", "rol", "municipio_asignado"]
    },
    "actividades_maestro": {
        "pk": "id_actividad",
        "cols": ["id_actividad", "nombre_actividad", "descripcion", "meta_global", "unidad_medida", "valor_total_actividad", "programa_responsable"]
    },
    "subactividades": {
        "pk": "id_sub",
        "cols": ["id_sub", "id_actividad", "nombre_subactividad", "valor_sub", "meta_sub", "unidad_medida_sub", "peso"]
    },
    "asignacion_municipios": {
        "pk": "id_asig",
        "cols": ["id_asig", "id_sub", "municipio", "num_contrato", "num_pagos", "valor_asignado", "meta_municipal", "unidad_medida_muni"]
    },
    "seguimiento_pagos": {
        "pk": "id_seguimiento",
        "cols": [
            "id_seguimiento", "id_asig", "num_pago_actual", "avance_meta", "valor_calculado", 
            "fecha_registro", "soporte_url", "soporte_municipio", "estado", "referente_aprobador", 
            "acta_referente", "observaciones_referente", "supervisor_aprobador", "motivo_rechazo", 
            "chk_plan_trabajo", "chk_cronograma", "chk_personal", "chk_seg_social", 
            "chk_inf_parcial", "chk_inf_final", "chk_polizas"
        ]
    },
    "secuencia": {
        "pk": "id_secuencia",
        "cols": [
            "id_secuencia", "id_seguimiento", "id_asig", "municipio", "numero_contrato", 
            "cp_nit_beneficiario", "numero_pagos", "primer_pago", "ultimo_pago", 
            "total_pagado_oc", "valor_cp", "saldo_cp", "porcentaje_ejecucion"
        ]
    }
}

# --- 2. GESTOR DE LECTURA DESDE POSTGRESQL CON CACHÉ ---
@st.cache_data(ttl=120, show_spinner=False)
def get_data_cached(nombre_hoja):
    pk = ESQUEMA_PG[nombre_hoja]["pk"]
    query = f"SELECT * FROM {nombre_hoja} ORDER BY {pk} ASC;"
    return conn.query(query, ttl=0)

def get_data(nombre_hoja, forzar=False):
    """
    Recupera los datos desde PostgreSQL en milisegundos sin límite de cuota.
    """
    try:
        if forzar:
            get_data_cached.clear()
        df = get_data_cached(nombre_hoja)
        return df.copy()
    except Exception as e:
        st.error(f"🚨 Error al consultar '{nombre_hoja}' en PostgreSQL: {e}")
        return pd.DataFrame(columns=ESQUEMA_PG[nombre_hoja]["cols"])

# --- 3. ESCRITURA TRANSACCIONAL ACID (CON BARRERA ANTI-BORRADO) ---
def safe_update(worksheet_name, df_final):
    """
    Sincroniza cambios en PostgreSQL mediante UPSERT atómico (ON CONFLICT DO UPDATE).
    Protege tablas críticas contra cualquier eliminación de filas vacías accidentales.
    """
    if df_final is None or not isinstance(df_final, pd.DataFrame):
        st.error(f"🛑 Error Transaccional: El dataset enviado a '{worksheet_name}' no es válido.")
        return False

    pk = ESQUEMA_PG[worksheet_name]["pk"]
    cols_validas = ESQUEMA_PG[worksheet_name]["cols"]

    try:
        with conn.session as session:
            if worksheet_name in ["seguimiento_pagos", "asignacion_municipios", "subactividades"]:
                df_previo = get_data(worksheet_name)
                if not df_previo.empty and len(df_final) == 0:
                    st.error(f"🛑 Bloqueo Crítico de Seguridad: Se intentó vaciar la tabla '{worksheet_name}'. Transacción abortada.")
                    return False

            if worksheet_name not in ["seguimiento_pagos"]:
                if not df_final.empty and pk in df_final.columns:
                    ids_actuales = df_final[pk].dropna().astype(int).tolist()
                    if len(ids_actuales) > 0:
                        session.execute(
                            text(f"DELETE FROM {worksheet_name} WHERE {pk} NOT IN :ids"),
                            {"ids": tuple(ids_actuales)}
                        )

            if not df_final.empty:
                cols_presentes = [c for c in df_final.columns if c in cols_validas]
                df_clean = df_final[cols_presentes].copy()
                df_clean[pk] = pd.to_numeric(df_clean[pk], errors="coerce").astype(int)
                df_clean = df_clean.where(pd.notnull(df_clean), None)

                cols_sql = ", ".join(cols_presentes)
                vals_sql = ", ".join([f":{c}" for c in cols_presentes])
                update_sql = ", ".join([f"{c} = EXCLUDED.{c}" for c in cols_presentes if c != pk])

                sql_upsert = text(f"""
                    INSERT INTO {worksheet_name} ({cols_sql})
                    VALUES ({vals_sql})
                    ON CONFLICT ({pk}) DO UPDATE SET {update_sql};
                """)

                session.execute(sql_upsert, df_clean.to_dict(orient="records"))

            session.commit()

        get_data_cached.clear()
        return True

    except Exception as e:
        st.error(f"❌ Error de persistencia en PostgreSQL ({worksheet_name}): {e}")
        return False

# --- 4. REGISTRO DE USUARIOS SEGURO ---
def guardar_nuevo_usuario(nombre, email, clave, rol, muni):
    df_actual = get_data("usuarios", forzar=True)
    nuevo_id = 1 if df_actual.empty or "id_usuario" not in df_actual.columns else int(df_actual["id_usuario"].max()) + 1
    nueva_fila = pd.DataFrame([{
        "id_usuario": nuevo_id,
        "nombre_completo": nombre,
        "email": email,
        "password": clave,
        "rol": rol,
        "municipio_asignado": muni
    }])
    df_final = pd.concat([df_actual, nueva_fila], ignore_index=True)
    if safe_update("usuarios", df_final):
        st.success("Usuario registrado exitosamente.")

# --- LISTA DE MUNICIPIOS ---
municipios_santander = [
    "Aguada", "Albania", "Aratoca", "Barbosa", "Barichara", "Barrancabermeja", "Betulia", "Bolívar", 
    "Bucaramanga", "Cabrera", "California", "Capitanejo", "Carcasí", "Cepitá", "Cerrito", "Charalá", 
    "Charta", "Chima", "Chipatá", "Cimitarra", "Concepción", "Confines", "Contratación", "Coromoro", 
    "Curití", "El Carmen de Chucurí", "El Guacamayo", "El Peñón", "El Playón", "Encino", "Enciso", 
    "Floridablanca", "Florián", "Galán", "Gambita", "Girón", "Guaca", "Guadalupe", "Guapotá", "Guavatá", 
    "Güepsa", "Hato", "Jesús María", "Jordán", "La Belleza", "La Paz", "Landázuri", "Lebrija", "Los Santos", 
    "Macaravita", "Málaga", "Matanza", "Mogotes", "Molagavita", "Ocamonte", "Oiba", "Onzaga", "Palmar", 
    "Palmas del Socorro", "Páramo", "Piedecuesta", "Pinchote", "Puente Nacional", "Puerto Parra", 
    "Puerto Wilches", "Rionegro", "Sabana de Torres", "San Andrés", "San Benito", "San Gil", 
    "San Joaquín", "San José de Miranda", "San Miguel", "San Vicente de Chucurí", "Santa Bárbara", 
    "Santa Helena del Opón", "Simacota", "Socorro", "Suaita", "Sucre", "Suratá", "Tona", "Valle de San José", 
    "Vélez", "Vetas", "Villanueva", "Zapatoca"
]

# --- 5. CONTROL DE ACCESO ---
if 'user' not in st.session_state:
    st.sidebar.title("🔐 Acceso PIC Santander")
    user_input = st.sidebar.text_input("Email / Usuario")
    pass_input = st.sidebar.text_input("Contraseña", type="password")
    
    if st.sidebar.button("Ingresar"):
        try:
            df_usuarios = get_data("usuarios")
            user_match = df_usuarios[
                (df_usuarios['email'] == user_input) & 
                (df_usuarios['password'].astype(str) == str(pass_input))
            ]
             
            if not user_match.empty:
                st.session_state['user'] = user_match.iloc[0]['email']
                st.session_state['rol'] = user_match.iloc[0]['rol']
                st.session_state['muni_asignado'] = user_match.iloc[0]['municipio_asignado']
                st.success(f"Bienvenido {user_match.iloc[0]['nombre_completo']}")
                st.rerun()
            else:
                st.sidebar.error("Usuario o contraseña incorrectos.")
        except Exception as e:
            st.sidebar.error(f"Error al conectar con la base de datos: {e}")
else:
    rol = st.session_state['rol']
    st.sidebar.info(f"**Usuario:** {st.session_state['user']}\n\n**Rol:** {rol}")
    
    df_act_raw = get_data("actividades_maestro")
    df_sub_raw = get_data("subactividades")
    df_asig_raw = get_data("asignacion_municipios")
    df_pagos_raw = get_data("seguimiento_pagos")
    df_secuencia_raw = get_data("secuencia")
    
    opciones = ["🏠 Dashboard", "📝 Ejecución"]

    if rol == "DEPARTAMENTO_PARAMETRIZADOR":
        opciones += ["⚙️ Parametrización", "⚖️ Revisión", "👤 Gestión Usuarios"]
    elif rol == "REFERENTE_DEPARTAMENTAL":
        opciones += ["⚖️ Revisión"]
    elif rol == "SUPERVISOR":
        opciones += ["⚖️ Revisión"]

    menu = st.sidebar.radio("Navegación", opciones)

    st.sidebar.write("---")
    if st.sidebar.button("🔒 Cerrar Sesión / Cambiar Perfil"):
        st.session_state.clear()
        st.rerun()

    # --- MÓDULO: DASHBOARD ---
    if menu == "🏠 Dashboard":
        st.title(f"📊 Seguimiento - PIC Santander")
        st.caption(f"Sistema Integrado de Analítica para el Plan de Intervenciones Colectivas")

        if df_asig_raw.empty or df_sub_raw.empty:
            st.info("ℹ️ Esperando la parametrización de actividades y asignaciones municipales para proyectar métricas.")
        else:
            df_master = df_asig_raw.merge(df_sub_raw, on="id_sub", suffixes=('_muni', '_sub'))
            if not df_act_raw.empty:
                df_master = df_master.merge(df_act_raw[['id_actividad', 'nombre_actividad', 'programa_responsable']], on="id_actividad", how="left")
            
            if not df_pagos_raw.empty:
                df_pagos_validados = df_pagos_raw[df_pagos_raw['estado'] == 'ACEPTADA'].copy()
                df_pagos_agg = df_pagos_validados.groupby('id_asig').agg({
                    'valor_calculado': 'sum',
                    'avance_meta': 'sum'
                }).reset_index()
                df_pagos_agg.columns = ['id_asig', 'total_ejecutado_financiero', 'total_ejecutado_fisico']
                df_master = df_master.merge(df_pagos_agg, on="id_asig", how="left")
            else:
                df_master['total_ejecutado_financiero'] = 0.0
                df_master['total_ejecutado_fisico'] = 0.0

            df_master['total_ejecutado_financiero'] = df_master['total_ejecutado_financiero'].fillna(0.0)
            df_master['total_ejecutado_fisico'] = df_master['total_ejecutado_fisico'].fillna(0.0)
            df_master['valor_asignado'] = df_master['valor_asignado'].astype(float)
            df_master['meta_municipal'] = df_master['meta_municipal'].astype(float)

            if rol == "MUNICIPIO_EJECUTOR":
                muni_user = st.session_state.get('muni_asignado')
                st.subheader(f"📍 Panel de Fiscalización Local - Municipio: {muni_user}")
                df_muni_data = df_master[df_master['municipio'] == muni_user].copy()
                
                if df_muni_data.empty:
                    st.warning(f"⚠️ El municipio {muni_user} no cuenta con asignaciones presupuestales registradas en el sistema.")
                else:
                    muni_total_asig = df_muni_data['valor_asignado'].sum()
                    muni_total_ejec = df_muni_data['total_ejecutado_financiero'].sum()
                    muni_saldo_pendiente = muni_total_asig - muni_total_ejec
                    muni_porc_global = (muni_total_ejec / muni_total_asig * 100) if muni_total_asig > 0 else 0
                    
                    if muni_porc_global < 33.3:
                        color_semaforo = "🔴 EJECUCIÓN CRÍTICA"
                    elif 33.3 <= muni_porc_global < 66.6:
                        color_semaforo = "🟡 EN ALERTA TEMPRANA"
                    else:
                        color_semaforo = "🟢 CUMPLIMIENTO ÓPTIMO"

                    fmt_muni_asig = f"${muni_total_asig:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
                    fmt_muni_ejec = f"${muni_total_ejec:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
                    fmt_muni_saldo = f"${muni_saldo_pendiente:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
                    fmt_muni_porc = f"{muni_porc_global:.2f}%".replace('.', ',')

                    kpi_m1, kpi_m2, kpi_m3, kpi_m4 = st.columns(4)
                    kpi_m1.metric("📋 Presupuesto Asignado", fmt_muni_asig)
                    kpi_m2.metric("✅ Total Ejecutado", fmt_muni_ejec, f"{fmt_muni_porc}")
                    kpi_m3.metric("📥 Saldo Líquido", fmt_muni_saldo)
                    kpi_m4.metric("🚨 Estatus", color_semaforo)
            else:
                st.subheader("🌐 Visión Global Departamental - Santander")
                dep_total_pic = df_act_raw['valor_total_actividad'].sum() if not df_act_raw.empty else 0
                dep_total_asig = df_master['valor_asignado'].sum()
                dep_total_ejec = df_master['total_ejecutado_financiero'].sum()
                
                c_dep1, c_dep2, c_dep3 = st.columns(3)
                c_dep1.metric("📋 Techo Total PIC", f"${dep_total_pic:,.2f}")
                c_dep2.metric("📍 Total Asignado", f"${dep_total_asig:,.2f}")
                c_dep3.metric("💰 Ejecución Real", f"${dep_total_ejec:,.2f}")

    # --- MÓDULO: PARAMETRIZACIÓN ---
    elif menu == "⚙️ Parametrización":
        st.title("⚙️ Módulo de Parametrización")
        tab1, tab2, tab3 = st.tabs(["1. Registro de Actividades", "2. Configuración de Subactividades", "3. Asignación a Municipios"])

        with tab1:
            st.subheader("Crear Nueva Actividad General")
            with st.form("form_actividad"):
                c1, c2 = st.columns(2)
                nombre_a = c1.text_input("Nombre de la Actividad")
                prog = c1.text_input("Programa Responsable")
                val_total = c2.number_input("Valor Total Actividad ($)", min_value=0.0)
                meta_a = c2.number_input("Meta Global", min_value=0.0)
                unidad_a = c2.text_input("Unidad (Ej: Personas, Talleres)")
                desc_a = st.text_area("Descripción de la Actividad")
                
                if st.form_submit_button("💾 Guardar Actividad"):
                    df_act = get_data("actividades_maestro")
                    nuevo_id = 1 if df_act.empty else int(df_act['id_actividad'].max()) + 1
                    nueva_fila = pd.DataFrame([{
                        "id_actividad": nuevo_id, "nombre_actividad": nombre_a, "descripcion": desc_a,
                        "meta_global": meta_a, "unidad_medida": unidad_a,
                        "valor_total_actividad": val_total, "programa_responsable": prog
                    }])
                    df_final = pd.concat([df_act, nueva_fila], ignore_index=True)
                    if safe_update("actividades_maestro", df_final):
                        st.success("✅ Actividad guardada en PostgreSQL.")
                        st.rerun()

        with tab2:
            st.subheader("Desglose de Subactividades")
            df_act = get_data("actividades_maestro")
            if not df_act.empty:
                nombres_act = {row['id_actividad']: row['nombre_actividad'] for _, row in df_act.iterrows()}
                act_id = st.selectbox("Seleccione Actividad Padre:", df_act['id_actividad'].tolist(), format_func=lambda x: nombres_act[x])
                padre = df_act[df_act['id_actividad'] == act_id].iloc[0]
                
                df_all_subs = get_data("subactividades")
                df_sub_existentes = df_all_subs[df_all_subs['id_actividad'] == act_id] if not df_all_subs.empty else pd.DataFrame()
                peso_usado = df_sub_existentes['peso'].sum() if not df_sub_existentes.empty else 0.0

                with st.form("form_sub"):
                    sc1, sc2, sc3, sc4 = st.columns([2, 1, 1, 1])
                    sub_nombre = sc1.text_input("Nombre Subactividad")
                    sub_meta = sc2.number_input("Meta", min_value=0.0)
                    sub_unidad = sc3.text_input("Unidad")
                    sub_peso = sc4.number_input("Peso", min_value=0.0, max_value=1.0, step=0.01)
                    
                    if st.form_submit_button("➕ Vincular Subactividad"):
                        if (peso_usado + sub_peso) > 1.0001:
                            st.error("Error: El peso total excede 1.0.")
                        else:
                            sub_valor = padre['valor_total_actividad'] * sub_peso
                            df_sub = get_data("subactividades")
                            nuevo_id_sub = 1 if df_sub.empty else int(df_sub['id_sub'].max()) + 1
                            nueva_sub = pd.DataFrame([{
                                "id_sub": nuevo_id_sub, "id_actividad": act_id,
                                "nombre_subactividad": sub_nombre, "valor_sub": sub_valor,
                                "meta_sub": sub_meta, "unidad_medida_sub": sub_unidad, "peso": sub_peso
                            }])
                            df_final = pd.concat([df_sub, nueva_sub], ignore_index=True)
                            if safe_update("subactividades", df_final):
                                st.success("✅ Subactividad agregada correctamente.")
                                st.rerun()

        with tab3:
            st.subheader("📍 Asignación de Presupuesto por Municipio")
            df_s_raw = get_data("subactividades")
            df_a_raw = get_data("actividades_maestro")
            if not df_s_raw.empty and not df_a_raw.empty:
                df_sub_todas = df_s_raw.merge(df_a_raw[['id_actividad', 'nombre_actividad']], on="id_actividad")
            else:
                df_sub_todas = pd.DataFrame()

            if df_sub_todas.empty:
                st.warning("Debe configurar subactividades primero.")
            else:
                sub_sel_id = st.selectbox("Seleccione Subactividad:", 
                                         df_sub_todas['id_sub'].tolist(), 
                                         format_func=lambda x: f"{df_sub_todas[df_sub_todas['id_sub']==x]['nombre_actividad'].values[0]} >> {df_sub_todas[df_sub_todas['id_sub']==x]['nombre_subactividad'].values[0]}")
                datos_sub = df_sub_todas[df_sub_todas['id_sub'] == sub_sel_id].iloc[0]
                
                with st.form("form_municipio"):
                    m1, m2 = st.columns(2)
                    muni_nombre = m1.selectbox("Municipio de Santander", municipios_santander)
                    n_contrato = m1.text_input("Número de Contrato / Convenio")
                    n_pagos = m1.number_input("Número de Pagos", min_value=1, step=1)
                    muni_valor = m2.number_input("Valor a asignar ($)", min_value=0.0, step=1000.0)
                    muni_meta = m2.number_input("Meta Municipal", min_value=0.0)
                    muni_unidad = m2.text_input("Unidad de Medida Municipal")
                    
                    if st.form_submit_button("📍 Confirmar Asignación"):
                        df_asig_muni = get_data("asignacion_municipios")
                        nuevo_id_asig = 1 if df_asig_muni.empty else int(df_asig_muni['id_asig'].max()) + 1
                        nueva_asig = pd.DataFrame([{
                            "id_asig": nuevo_id_asig, "id_sub": sub_sel_id, "municipio": muni_nombre, 
                            "num_contrato": n_contrato, "num_pagos": n_pagos, "valor_asignado": muni_valor, 
                            "meta_municipal": muni_meta, "unidad_medida_muni": muni_unidad
                        }])
                        df_final_asig = pd.concat([df_asig_muni, nueva_asig], ignore_index=True)
                        if safe_update("asignacion_municipios", df_final_asig):
                            st.success("✅ Asignación exitosa.")
                            st.rerun()

    # --- MÓDULO: EJECUCIÓN ---
    elif menu == "📝 Ejecución":
        if rol != "MUNICIPIO_EJECUTOR":
            st.warning("Este módulo es exclusivo para municipios.")
        else:
            st.title("📝 Reporte de Avance Municipal")
            muni_user = st.session_state.get('muni_asignado', 'N/A')
            
            df_a_exec = get_data("asignacion_municipios")
            df_s_exec = get_data("subactividades")
            df_m_exec = get_data("actividades_maestro")

            if not df_a_exec.empty and not df_s_exec.empty and not df_m_exec.empty:
                df_merge_exec = df_a_exec.merge(df_s_exec, on="id_sub").merge(df_m_exec, on="id_actividad")
                df_mis_asig = df_merge_exec[df_merge_exec['municipio'] == muni_user]
            else:
                df_mis_asig = pd.DataFrame()

            if df_mis_asig.empty:
                st.info(f"No hay asignaciones pendientes para {muni_user}.")
            else:
                dict_subactividades = {row['id_asig']: f"Contrato: {row['num_contrato']} >> {row['nombre_subactividad']}" for _, row in df_mis_asig.iterrows()}
                sel_asig = st.selectbox("Seleccione Subactividad a Reportar:", options=list(dict_subactividades.keys()), format_func=lambda x: dict_subactividades[x])
                datos = df_mis_asig[df_mis_asig['id_asig'] == sel_asig].iloc[0]
                
                meta_total = datos['meta_municipal']
                valor_total_muni = datos['valor_asignado']
                
                df_pagos_all = get_data("seguimiento_pagos")
                ultimo_pago = df_pagos_all[df_pagos_all['id_asig'] == sel_asig]['num_pago_actual'].max() if not df_pagos_all.empty else 0
                siguiente_pago = int(ultimo_pago) + 1 if pd.notnull(ultimo_pago) else 1

                if siguiente_pago > datos['num_pagos']:
                    st.success("✅ Todas las cuotas de pago de esta actividad han sido reportadas.")
                else:
                    meta_avanc = st.number_input("Avance de Meta realizado en este periodo", min_value=0.0, step=1.0)
                    with st.form("form_reporte_muni"):
                        soporte = st.text_input("Link a carpeta de soportes (Evidencias)")
                        if st.form_submit_button("Enviar a Revisión"):
                            df_pagos = get_data("seguimiento_pagos")
                            nuevo_id_seg = 1 if df_pagos.empty else int(df_pagos['id_seguimiento'].max()) + 1
                            valor_final_pago = (meta_avanc / meta_total) * valor_total_muni if meta_total > 0 else 0.0
                            
                            nueva_fila_pago = pd.DataFrame([{
                                "id_seguimiento": nuevo_id_seg, "id_asig": sel_asig,
                                "num_pago_actual": siguiente_pago, "avance_meta": meta_avanc,
                                "valor_calculado": valor_final_pago, "soporte_municipio": soporte,
                                "estado": 'PENDIENTE', "fecha_registro": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M")
                            }])
                            df_final_pagos = pd.concat([df_pagos, nueva_fila_pago], ignore_index=True)
                            if safe_update("seguimiento_pagos", df_final_pagos):
                                st.success("✅ Reporte enviado exitosamente.")
                                st.rerun()

    # --- MÓDULO: GESTIÓN DE USUARIOS Y MIGRACIÓN ---
    elif menu == "👤 Gestión Usuarios":
        if rol != "DEPARTAMENTO_PARAMETRIZADOR":
            st.warning("Acceso denegado.")
        else:
            st.title("👤 Administración de Usuarios y Migración")
            with st.form("crear_usuario"):
                c1, c2 = st.columns(2)
                u_nombre = c1.text_input("Nombre Completo")
                u_email = c1.text_input("Correo Electrónico (Usuario)")
                u_pass = c1.text_input("Contraseña", type="password")
                u_rol = c2.selectbox("Asignar Rol", ["DEPARTAMENTO_PARAMETRIZADOR", "MUNICIPIO_EJECUTOR", "REFERENTE_DEPARTAMENTAL", "SUPERVISOR"])
                u_muni = c2.selectbox("Municipio Asignado", ["N/A"] + municipios_santander)

                if st.form_submit_button("Registrar Usuario"):
                    guardar_nuevo_usuario(u_nombre, u_email, u_pass, u_rol, u_muni)
                    st.rerun()

            st.write("---")
            st.subheader("👥 Usuarios Registrados")
            df_usuarios = get_data("usuarios")
            if not df_usuarios.empty:
                st.dataframe(df_usuarios, use_container_width=True)

            # ==============================================================================
            # 🚀 HERRAMIENTA TEMPORAL DE MIGRACIÓN: GOOGLE SHEETS -> POSTGRESQL
            # ==============================================================================
            st.write("---")
            st.subheader("🚀 Migración Automática de Datos desde Google Sheets")
            st.caption("Si aún tienes datos en tu Google Sheets anterior y deseas pasarlos a PostgreSQL, haz clic aquí una sola vez.")

            if st.button("🔄 Iniciar Migración (Sheets ➔ PostgreSQL)", type="primary"):
                try:
                    from streamlit_gsheets import GSheetsConnection
                    conn_gsheets = st.connection("gsheets", type=GSheetsConnection)
                    URL_DB = "https://docs.google.com/spreadsheets/d/1jRdZX0gNfjWhlb86hHopVkJJrs_9bRIaulZDRzKR0pA/edit?usp=sharing"
                    
                    for tabla, config in ESQUEMA_PG.items():
                        df_sheet = conn_gsheets.read(spreadsheet=URL_DB, worksheet=tabla, ttl=0)
                        if df_sheet is not None and not df_sheet.empty:
                            pk = config["pk"]
                            df_sheet = df_sheet.dropna(subset=[pk]).copy()
                            safe_update(tabla, df_sheet)
                            st.success(f"✅ Tabla '{tabla}' migrada con {len(df_sheet)} registros.")
                    st.balloons()
                except Exception as e:
                    st.error(f"Error en la migración: {e}")
