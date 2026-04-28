import streamlit as st
import pandas as pd
import sqlite3

# --- 1. CONFIGURACIÓN DE BASE DE DATOS ---
def connection():
    return sqlite3.connect('pic_gestion.db', check_same_thread=False)

def init_db():
    conn = connection()
    cursor = conn.cursor()
    # Tabla Actividades (PADRE) con Unidad de Medida
    cursor.execute('''CREATE TABLE IF NOT EXISTS actividades_maestro (
        id_actividad INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre_actividad TEXT,
        descripcion TEXT,
        meta_global REAL,
        unidad_medida TEXT,
        valor_total_actividad REAL,
        programa_responsable TEXT
    )''')
    # Tabla Subactividades (HIJO) con Unidad de Medida
    cursor.execute('''CREATE TABLE IF NOT EXISTS subactividades (
        id_sub INTEGER PRIMARY KEY AUTOINCREMENT,
        id_actividad INTEGER,
        nombre_subactividad TEXT,
        valor_sub REAL,
        meta_sub REAL,
        unidad_medida_sub TEXT,
        peso REAL,
        FOREIGN KEY(id_actividad) REFERENCES actividades_maestro(id_actividad)
    )''')
# Tabla: ASIGNACIÓN A MUNICIPIOS (Actualizada con Contrato y Pagos)
    cursor.execute('''CREATE TABLE IF NOT EXISTS asignacion_municipios (
        id_asig INTEGER PRIMARY KEY AUTOINCREMENT,
        id_sub INTEGER,
        municipio TEXT,
        num_contrato TEXT,
        num_pagos INTEGER,
        valor_asignado REAL,
        meta_municipal REAL,
        FOREIGN KEY(id_sub) REFERENCES subactividades(id_sub)
    )''')

# Tabla: SEGUIMIENTO DE PAGOS
    cursor.execute('''CREATE TABLE IF NOT EXISTS seguimiento_pagos (
        id_seguimiento INTEGER PRIMARY KEY AUTOINCREMENT,
        id_asig INTEGER,
        num_pago_actual INTEGER,
        avance_meta REAL,
        valor_calculado REAL,
        soporte_municipio TEXT,
        acta_referente TEXT,
        estado TEXT, -- 'PENDIENTE', 'REVISADO_REFERENTE', 'APROBADO_SUPERVISOR'
        fecha_registro DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(id_asig) REFERENCES asignacion_municipios(id_asig)
    )''')

# Tabla: USUARIOS DEL SISTEMA
    cursor.execute('''CREATE TABLE IF NOT EXISTS usuarios (
        id_usuario INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT UNIQUE,
        password TEXT,
        nombre_completo TEXT,
        cedula TEXT,
        cargo TEXT,
        telefono TEXT,
        rol TEXT,
        municipio_asignado TEXT -- Solo para MUNICIPIO_EJECUTOR
    )''')

    conn.commit()
    conn.close()

init_db()


# --- CÓDIGO TEMPORAL PARA CREAR EL PRIMER USUARIO ---
conn = connection()
cursor = conn.cursor()
# Verifica si ya existe el usuario para no duplicarlo
cursor.execute("SELECT * FROM usuarios WHERE email='admin@santander.gov.co'")
if not cursor.fetchone():
    cursor.execute("""
        INSERT INTO usuarios (email, password, nombre_completo, rol, municipio_asignado) 
        VALUES ('admin@santander.gov.co', 'admin123', 'Administrador Inicial', 'DEPARTAMENTO_PARAMETRIZADOR', 'N/A')
    """)
    conn.commit()
conn.close()


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

# --- 2. CONFIGURACIÓN DE LA INTERFAZ ---
st.set_page_config(page_title="Sistema PIC - Unidad de Medida", layout="wide")

if 'user' not in st.session_state:
    st.sidebar.title("🔐 Acceso PIC Santander")
    user_input = st.sidebar.text_input("Email / Usuario")
    pass_input = st.sidebar.text_input("Contraseña", type="password")
    
    if st.sidebar.button("Ingresar"):
        conn = connection()
        user_data = pd.read_sql(f"SELECT * FROM usuarios WHERE email='{user_input}' AND password='{pass_input}'", conn)
        
        if not user_data.empty:
            st.session_state['user'] = user_data.iloc[0]['email']
            st.session_state['rol'] = user_data.iloc[0]['rol']
            st.session_state['muni_asignado'] = user_data.iloc[0]['municipio_asignado']
            st.rerun()
        else:
            st.sidebar.error("Usuario o contraseña incorrectos.")
else:
    rol = st.session_state['rol']
    st.sidebar.info(f"**Usuario:** {st.session_state['user']}\n\n**Rol:** {rol}")
    opciones = ["🏠 Dashboard", "📝 Ejecución"]
    if rol == "DEPARTAMENTO_PARAMETRIZADOR":
        opciones += ["⚙️ Parametrización", "⚖️ Revisión", "👤 Gestión Usuarios"]
    elif rol == "REFERENTE_DEPARTAMENTAL":
        opciones += ["⚖️ Revisión"]
    elif rol == "SUPERVISOR":
        opciones += ["⚖️ Revisión"] # O las opciones que definas para el supervisor

    menu = st.sidebar.radio("Navegación", opciones)


    # --- BOTÓN PARA CAMBIAR DE PERFIL (CERRAR SESIÓN) --- 
    st.sidebar.write("---")
    if st.sidebar.button("🔒 Cerrar Sesión / Cambiar Perfil"):
        # Limpia la sesión para volver al formulario de acceso 
        st.session_state.clear()
        st.rerun()

    # --- MÓDULO: PARAMETRIZACIÓN ---
    if menu == "⚙️ Parametrización":
        st.title("⚙️ Módulo de Parametrización")
        tab1, tab2, tab3 = st.tabs(["1. Registro de Actividades", "2. Configuración de Subactividades", "3. Asignación a Municipios"])

        # TAB 1: ACTIVIDADES
        with tab1:
            st.subheader("Crear Nueva Actividad General")
            with st.form("form_actividad"):
                c1, c2 = st.columns(2)
                nombre_a = c1.text_input("Nombre de la Actividad")
                prog = c1.text_input("Programa Responsable")
                
                val_total = c2.number_input("Valor Total Actividad ($)", min_value=0.0)
                cc1, cc2 = c2.columns(2)
                meta_a = cc1.number_input("Meta Global", min_value=0.0)
                unidad_a = cc2.text_input("Unidad (Ej: Personas, Talleres)")
                
                desc_a = st.text_area("Descripción de la Actividad")
                
                if st.form_submit_button("💾 Guardar Actividad"):
                    conn = connection()
                    conn.execute("""INSERT INTO actividades_maestro 
                        (nombre_actividad, descripcion, meta_global, unidad_medida, valor_total_actividad, programa_responsable) 
                        VALUES (?,?,?,?,?,?)""", (nombre_a, desc_a, meta_a, unidad_a, val_total, prog))
                    conn.commit()
                    st.success("✅ Actividad guardada.")



# --- TABLA DE ACTIVIDADES CON OPCIÓN DE ELIMINAR ---
            st.write("---")
            st.subheader("📋 Actividades Generales Registradas")
            
            conn = connection()
            df_maestro = pd.read_sql("SELECT * FROM actividades_maestro", conn)
            
            if not df_maestro.empty:
                # Mostramos la tabla profesional
                st.dataframe(df_maestro[['id_actividad', 'nombre_actividad', 'programa_responsable', 'valor_total_actividad', 'meta_global', 'unidad_medida']], use_container_width=True)
                
                # Opción para eliminar por si hubo error
                with st.expander("🗑️ Zona de eliminación (Usar con precaución)"):
                    id_a_borrar = st.number_input("Ingrese el ID de la actividad a eliminar:", min_value=1, step=1)
                    if st.button("Eliminar Actividad Permanentemente"):
                        # Validamos que no tenga subactividades antes de borrar
                        check_sub = pd.read_sql(f"SELECT * FROM subactividades WHERE id_actividad = {id_a_borrar}", conn)
                        if not check_sub.empty:
                            st.error("No se puede eliminar: Esta actividad ya tiene subactividades vinculadas. Borre primero las subactividades.")
                        else:
                            conn.execute(f"DELETE FROM actividades_maestro WHERE id_actividad = {id_a_borrar}")
                            conn.commit()
                            st.warning(f"Actividad {id_a_borrar} eliminada.")
                            st.rerun()
            else:
                st.info("No hay actividades registradas todavía.")




        # TAB 2: SUBACTIVIDADES
        with tab2:
            st.subheader("Desglose de Subactividades")
            df_act = pd.read_sql("SELECT * FROM actividades_maestro", connection())

            if not df_act.empty:
                nombres_act = {row['id_actividad']: row['nombre_actividad'] for _, row in df_act.iterrows()}
                act_id = st.selectbox("Seleccione Actividad Padre:", df_act['id_actividad'].tolist(), format_func=lambda x: nombres_act[x])
                
                padre = df_act[df_act['id_actividad'] == act_id].iloc[0]
                
                # Resumen de pesos
                df_sub_existentes = pd.read_sql(f"SELECT * FROM subactividades WHERE id_actividad = {act_id}", connection())
                peso_usado = df_sub_existentes['peso'].sum()

                # --- NUEVO BLOQUE DE CONTROL ---
                valor_usado = df_sub_existentes['valor_sub'].sum()
                valor_disponible = padre['valor_total_actividad'] - valor_usado
                peso_disponible = 1.0 - peso_usado

                st.write("---")
                c1, c2, c3 = st.columns(3)
                c1.metric("Presupuesto Total", f"${padre['valor_total_actividad']:,.2f}")
                c2.metric("Peso Disponible", f"{peso_disponible:.2f}", delta=f"{peso_usado:.2f} usado", delta_color="inverse")
                c3.metric("Saldo por Distribuir", f"${valor_disponible:,.2f}")
                
                if peso_usado >= 1.0:
                    st.success("🎯 Esta actividad ya alcanzó el 100% de su peso.")
                # --- FIN DEL BLOQUE ---






                st.write(f"Peso actual: **{peso_usado:.2f} / 1.0**")

                with st.form("form_sub"):
                    sc1, sc2, sc3, sc4 = st.columns([2, 1, 1, 1])
                    sub_nombre = sc1.text_input("Nombre Subactividad")
                    sub_meta = sc2.number_input("Meta", min_value=0.0)
                    sub_unidad = sc3.text_input("Unidad")
                    sub_peso = sc4.number_input("Peso", min_value=0.0, max_value=1.0, step=0.01)
                    
                    if st.form_submit_button("➕ Vincular Subactividad"):
                        if (peso_usado + sub_peso) > 1.0001:
                            st.error("Error: Peso excedido.")
                        else:
                            sub_valor = padre['valor_total_actividad'] * sub_peso
                            conn = connection()
                            conn.execute("""INSERT INTO subactividades 
                                (id_actividad, nombre_subactividad, valor_sub, meta_sub, unidad_medida_sub, peso) 
                                VALUES (?,?,?,?,?,?)""", (act_id, sub_nombre, sub_valor, sub_meta, sub_unidad, sub_peso))
                            conn.commit()
                            st.success("✅ Subactividad agregada.")
                            st.rerun()

                if not df_sub_existentes.empty:
                    st.dataframe(df_sub_existentes[['nombre_subactividad', 'meta_sub', 'unidad_medida_sub', 'peso', 'valor_sub']])


# --- TABLA DE SUBACTIVIDADES CON EDICIÓN Y ELIMINACIÓN ---
                st.write("---")
                st.subheader("📋 Subactividades Vinculadas")
                
                if not df_sub_existentes.empty:
                    # Mostrar tabla para referencia de IDs
                    st.dataframe(df_sub_existentes[['id_sub', 'nombre_subactividad', 'meta_sub', 'unidad_medida_sub', 'peso', 'valor_sub']], use_container_width=True)
                    
                    col_ed, col_del = st.columns(2)
                    
                    # --- BOTÓN EDITAR ---
                    with col_ed.expander("📝 Editar Subactividad"):
                        id_edit = st.number_input("ID de la subactividad a editar:", min_value=1, step=1, key="edit_sub_id")
                        sub_to_edit = df_sub_existentes[df_sub_existentes['id_sub'] == id_edit]
                        
                        if not sub_to_edit.empty:
                            with st.form("form_edit_sub"):
                                new_nom = st.text_input("Nuevo Nombre", value=sub_to_edit.iloc[0]['nombre_subactividad'])
                                new_meta = st.number_input("Nueva Meta", value=float(sub_to_edit.iloc[0]['meta_sub']))
                                new_peso = st.number_input("Nuevo Peso", value=float(sub_to_edit.iloc[0]['peso']), min_value=0.0, max_value=1.0)
                                
                                if st.form_submit_button("Actualizar Subactividad"):
                                    # Recalcular valor basado en el nuevo peso
                                    new_val = padre['valor_total_actividad'] * new_peso
                                    # Verificar que la suma de pesos no supere 1.0 (excluyendo el peso anterior de esta subactividad)
                                    peso_otros = df_sub_existentes[df_sub_existentes['id_sub'] != id_edit]['peso'].sum()
                                    
                                    if (peso_otros + new_peso) > 1.0001:
                                        st.error("Error: El nuevo peso hace que la suma total supere 1.0")
                                    else:
                                        conn = connection()
                                        conn.execute("""UPDATE subactividades SET 
                                            nombre_subactividad=?, meta_sub=?, peso=?, valor_sub=? 
                                            WHERE id_sub=?""", (new_nom, new_meta, new_peso, new_val, id_edit))
                                        conn.commit()
                                        st.success("Subactividad actualizada")
                                        st.rerun()
                        else:
                            st.info("Ingrese un ID válido de la tabla de arriba")

                    # --- BOTÓN ELIMINAR ---
                    with col_del.expander("🗑️ Eliminar Subactividad"):
                        id_del = st.number_input("ID de la subactividad a eliminar:", min_value=1, step=1, key="del_sub_id")
                        if st.button("Confirmar Eliminación", type="primary"):
                            conn = connection()
                            conn.execute(f"DELETE FROM subactividades WHERE id_sub = {id_del}")
                            conn.commit()
                            st.warning(f"Subactividad {id_del} eliminada")
                            st.rerun()
                else:
                    st.info("No hay subactividades vinculadas a esta actividad padre.")


# --- TAB 3: ASIGNACIÓN A MUNICIPIOS ---
        with tab3:
            
            st.subheader("📍 Asignación de Presupuesto por Municipio")
            
            # Consultar todas las subactividades disponibles con el nombre de su actividad padre
            df_sub_todas = pd.read_sql("""
                SELECT s.id_sub, s.nombre_subactividad, s.valor_sub, a.nombre_actividad 
                FROM subactividades s 
                JOIN actividades_maestro a ON s.id_actividad = a.id_actividad
            """, connection())

            if df_sub_todas.empty:
                st.warning("Debe configurar subactividades en la pestaña 2 antes de asignar municipios.")
            else:
                # Selector de subactividad
                sub_sel_id = st.selectbox("Seleccione Subactividad:", 
                                         df_sub_todas['id_sub'].tolist(), 
                                         format_func=lambda x: f"{df_sub_todas[df_sub_todas['id_sub']==x]['nombre_actividad'].values[0]} >> {df_sub_todas[df_sub_todas['id_sub']==x]['nombre_subactividad'].values[0]}",
                                         key="asig_muni_selector")
                
                datos_sub = df_sub_todas[df_sub_todas['id_sub'] == sub_sel_id].iloc[0]
                
                # Cálculos de presupuesto municipal
                df_asig_actual = pd.read_sql(f"SELECT * FROM asignacion_municipios WHERE id_sub = {sub_sel_id}", connection())
                valor_gastado_muni = df_asig_actual['valor_asignado'].sum()
                saldo_muni = datos_sub['valor_sub'] - valor_gastado_muni

                # Cuadros de Control
                col_m1, col_m2 = st.columns(2)
                col_m1.metric("Presupuesto Subactividad", f"${datos_sub['valor_sub']:,.2f}")
                col_m2.metric("Saldo Disponible para Municipios", f"${saldo_muni:,.2f}", delta=f"-${valor_gastado_muni:,.2f} asignado", delta_color="inverse")

                # Formulario de Registro Actualizado
                with st.form("form_municipio"):
                    m1, m2 = st.columns(2)
                    muni_nombre = m1.selectbox("Municipio de Santander", municipios_santander)
                    n_contrato = m1.text_input("Número de Contrato / Convenio")
                    n_pagos = m1.number_input("Número de Pagos (Seguimientos)", min_value=1, step=1, help="Define cuántos reportes de pago tendrá esta actividad")
                    
                    muni_valor = m2.number_input("Valor a asignar ($)", min_value=0.0, max_value=float(datos_sub['valor_sub']), step=1000.0)
                    muni_meta = m2.number_input("Meta Municipal", min_value=0.0)
                    
                    if st.form_submit_button("📍 Confirmar Asignación Municipal"):
                        if muni_valor > (saldo_muni + 0.01):
                            st.error(f"Error: El valor supera el saldo disponible (${saldo_muni:,.2f})")
                        else:
                            conn = connection()
                            conn.execute("""INSERT INTO asignacion_municipios 
                                (id_sub, municipio, num_contrato, num_pagos, valor_asignado, meta_municipal) 
                                VALUES (?,?,?,?,?,?)""", 
                                (sub_sel_id, muni_nombre, n_contrato, n_pagos, muni_valor, muni_meta))
                            conn.commit()
                            st.success(f"Asignación exitosa para {muni_nombre}")
                            st.rerun()

                # Tabla de Visualización Actualizada
                if not df_asig_actual.empty:
                    st.write("---")
                    st.write("**Asignaciones actuales por Municipio:**")
                    st.dataframe(df_asig_actual[['id_asig', 'municipio', 'num_contrato', 'num_pagos', 'valor_asignado', 'meta_municipal']], use_container_width=True)

                    # Opción para Eliminar
                    with st.expander("🗑️ Eliminar Asignación Municipal"):
                        id_asig_del = st.number_input("ID de asignación a eliminar:", min_value=1, step=1, key="del_asig_id")
                        if st.button("Confirmar Borrado Municipal", type="primary"):
                            conn = connection()
                            conn.execute(f"DELETE FROM asignacion_municipios WHERE id_asig = {id_asig_del}")
                            conn.commit()
                            st.rerun()


# --- MÓDULO: EJECUCIÓN (MUNICIPIO) ---
    elif menu == "📝 Ejecución":
        if rol != "MUNICIPIO_EJECUTOR":
            st.warning("Este módulo es exclusivo para el perfil MUNICIPIO_EJECUTOR.")
        else:
            st.title("📝 Reporte de Avance Municipal")
            muni_user = st.session_state.get('muni_asignado', 'N/A') 
            
            df_mis_asig = pd.read_sql(f"""
                SELECT a.id_asig, m.nombre_actividad, s.nombre_subactividad, a.num_contrato, a.num_pagos, a.valor_asignado, a.meta_municipal
                FROM asignacion_municipios a
                JOIN subactividades s ON a.id_sub = s.id_sub
                JOIN actividades_maestro m ON s.id_actividad = m.id_actividad
                WHERE a.municipio = '{muni_user}'
            """, connection())

            if df_mis_asig.empty:
                st.info(f"No hay asignaciones pendientes para {muni_user}.")
            else:
                sel_asig = st.selectbox("Seleccione Actividad/Contrato a reportar:", df_mis_asig['id_asig'].tolist(), 
                                       format_func=lambda x: f"Contrato: {df_mis_asig[df_mis_asig['id_asig']==x]['num_contrato'].values[0]} - {df_mis_asig[df_mis_asig['id_asig']==x]['nombre_subactividad'].values[0]}")
                
                datos = df_mis_asig[df_mis_asig['id_asig'] == sel_asig].iloc[0]
                
                # Consultar último pago reportado
                df_pagos_hechos = pd.read_sql(f"SELECT MAX(num_pago_actual) as ultimo FROM seguimiento_pagos WHERE id_asig = {sel_asig}", connection())
                ultimo_pago = df_pagos_hechos['ultimo'].iloc[0] if df_pagos_hechos['ultimo'].iloc[0] is not None else 0
                siguiente_pago = ultimo_pago + 1
                
                if siguiente_pago > datos['num_pagos']:
                    st.success("✅ Todas las cuotas de pago de esta actividad han sido reportadas.")
                else:
                    st.info(f"Reportando Pago N° {siguiente_pago} de {datos['num_pagos']}")
                    with st.form("form_reporte_muni"):
                        meta_avanc = st.number_input("Avance de Meta realizado en este periodo", min_value=0.0)
                        # Cálculo automático del valor del pago
                        valor_pago = datos['valor_asignado'] / datos['num_pagos']
                        st.write(f"Valor a cobrar en este pago: **${valor_pago:,.2f}**")
                        soporte = st.text_input("Link a carpeta de soportes (Evidencias)")
                        
                        if st.form_submit_button("Enviar a Revisión del Referente"):
                            conn = connection()
                            conn.execute("""INSERT INTO seguimiento_pagos 
                                (id_asig, num_pago_actual, avance_meta, valor_calculado, soporte_municipio, estado) 
                                VALUES (?,?,?,?,?,?)""", (sel_asig, siguiente_pago, meta_avanc, valor_pago, soporte, 'PENDIENTE'))
                            conn.commit()
                            st.success("Reporte enviado exitosamente.")
                            st.rerun()


# --- TABLA DE SEGUIMIENTO PARA MUNICIPIO ---
        st.write("---")
        st.subheader("📋 Historial de mis Reportes y Estados")
        
        muni_actual = st.session_state.get('muni_asignado')
        # Consulta para ver el estado de los pagos del municipio logueado
       
        df_seguimiento_muni = pd.read_sql(f"""
            SELECT p.id_seguimiento, s.nombre_subactividad, p.num_pago_actual, 
                   p.valor_calculado, p.avance_meta, p.estado, p.acta_referente
            FROM seguimiento_pagos p
            JOIN asignacion_municipios a ON p.id_asig = a.id_asig
            JOIN subactividades s ON a.id_sub = s.id_sub
            WHERE a.municipio = '{muni_actual}'
            ORDER BY p.id_seguimiento DESC
        """, connection())

        if not df_seguimiento_muni.empty:
            st.dataframe(df_seguimiento_muni, use_container_width=True)
        else:
            st.info("No hay reportes realizados aún.")




    # --- MÓDULO: REVISIÓN (REFERENTE) ---
    elif menu == "⚖️ Revisión":
        if rol != "REFERENTE_DEPARTAMENTAL":
            st.warning("Acceso exclusivo para REFERENTE_DEPARTAMENTAL.")
        else:
            st.title("⚖️ Validación y Carga de Actas")
            df_pendientes = pd.read_sql("""
                SELECT p.id_seguimiento, a.municipio, a.num_contrato, s.nombre_subactividad, p.num_pago_actual, p.valor_calculado, p.soporte_municipio
                FROM seguimiento_pagos p
                JOIN asignacion_municipios a ON p.id_asig = a.id_asig
                JOIN subactividades s ON a.id_sub = s.id_sub
                WHERE p.estado = 'PENDIENTE'
            """, connection())
            
            if df_pendientes.empty:
                st.write("No hay reportes municipales pendientes de revisión.")
            else:
                st.dataframe(df_pendientes, use_container_width=True)
                with st.form("form_revision_referente"):
                    id_rev = st.number_input("ID de Seguimiento a dar OK:", min_value=1, step=1)
                    acta_link = st.text_input("Enlace al Acta de Conformidad (PDF)")
                    if st.form_submit_button("Dar OK y enviar a Supervisor"):
                        conn = connection()
                        conn.execute("UPDATE seguimiento_pagos SET estado='REVISADO_REFERENTE', acta_referente=? WHERE id_seguimiento=?", (acta_link, id_rev))
                        conn.commit()
                        st.success("Validación registrada.")
                        st.rerun()


# --- CONSOLIDADO GLOBAL DE PAGOS (VISTA DEPARTAMENTO) ---
        st.write("---")
        st.subheader("📑 Trazabilidad General de Pagos")
        
        df_global = pd.read_sql("""
            SELECT p.id_seguimiento, a.municipio, s.nombre_subactividad, 
                   p.num_pago_actual, p.valor_calculado, p.estado,
                   p.soporte_municipio as Link_Evidencia,
                   p.acta_referente as Link_Acta
            FROM seguimiento_pagos p
            JOIN asignacion_municipios a ON p.id_asig = a.id_asig
            JOIN subactividades s ON a.id_sub = s.id_sub
            ORDER BY p.id_seguimiento DESC
        """, connection())

        if not df_global.empty:
            st.dataframe(df_global, use_container_width=True)


# --- MÓDULO: GESTIÓN DE USUARIOS ---
    elif menu == "👤 Gestión Usuarios":
        if rol != "DEPARTAMENTO_PARAMETRIZADOR":
            st.warning("Acceso denegado.")
        else:
            st.title("👤 Administración de Usuarios")
            with st.form("crear_usuario"):
                c1, c2 = st.columns(2)
                u_nombre = c1.text_input("Nombre Completo")
                u_email = c1.text_input("Correo Electrónico (Usuario)")
                u_pass = c1.text_input("Contraseña", type="password")
                u_cedula = c2.text_input("Cédula")
                u_cargo = c2.text_input("Cargo")
                u_tel = c2.text_input("Teléfono")
                u_rol = st.selectbox("Asignar Rol", ["DEPARTAMENTO_PARAMETRIZADOR", "MUNICIPIO_EJECUTOR", "REFERENTE_DEPARTAMENTAL", "SUPERVISOR"])
                u_muni = st.selectbox("Municipio Asignado", ["N/A"] + municipios_santander)

                if st.form_submit_button("Registrar Usuario"):
                    conn = connection()
                    try:
                        conn.execute("""INSERT INTO usuarios (email, password, nombre_completo, cedula, cargo, telefono, rol, municipio_asignado) 
                                     VALUES (?,?,?,?,?,?,?,?)""", (u_email, u_pass, u_nombre, u_cedula, u_cargo, u_tel, u_rol, u_muni))
                        conn.commit()
                        st.success(f"Usuario {u_email} creado exitosamente.")
                    except:
                        st.error("Error: El correo ya existe o faltan datos.")

# --- VISUALIZACIÓN Y GESTIÓN DE USUARIOS EXISTENTES ---
            st.write("---")
            st.subheader("👥 Usuarios Registrados")
            
            conn = connection()
            df_usuarios = pd.read_sql("SELECT id_usuario, nombre_completo, email, rol, municipio_asignado, cargo FROM usuarios", conn)
            
            if not df_usuarios.empty:
                st.dataframe(df_usuarios, use_container_width=True)
                
                col_edit, col_del = st.columns(2)
                
                # --- OPCIÓN: ACTUALIZAR ---
                with col_edit.expander("📝 Editar Usuario"):
                    id_update = st.number_input("ID del usuario a editar:", min_value=1, step=1, key="upd_user_id")
                    user_to_edit = df_usuarios[df_usuarios['id_usuario'] == id_update]
                    
                    if not user_to_edit.empty:
                        new_nombre = st.text_input("Nuevo Nombre", value=user_to_edit.iloc[0]['nombre_completo'])
                        new_rol = st.selectbox("Nuevo Rol", ["DEPARTAMENTO_PARAMETRIZADOR", "MUNICIPIO_EJECUTOR", "REFERENTE_DEPARTAMENTAL", "SUPERVISOR"], 
                                             index=["DEPARTAMENTO_PARAMETRIZADOR", "MUNICIPIO_EJECUTOR", "REFERENTE_DEPARTAMENTAL", "SUPERVISOR"].index(user_to_edit.iloc[0]['rol']))
                        
                        if st.button("Guardar Cambios"):
                            conn.execute("UPDATE usuarios SET nombre_completo=?, rol=? WHERE id_usuario=?", (new_nombre, new_rol, id_update))
                            conn.commit()
                            st.success("Usuario actualizado correctamente")
                            st.rerun()

                # --- OPCIÓN: ELIMINAR ---
                with col_del.expander("🗑️ Eliminar Usuario"):
                    id_delete = st.number_input("ID del usuario a eliminar:", min_value=1, step=1, key="del_user_id")
                    if st.button("Confirmar Eliminación de Usuario", type="primary"):
                        if id_delete == 1: # Protección para no borrar al admin principal
                            st.error("No se puede eliminar el usuario administrador maestro.")
                        else:
                            conn.execute(f"DELETE FROM usuarios WHERE id_usuario = {id_delete}")
                            conn.commit()
                            st.warning(f"Usuario {id_delete} eliminado")
                            st.rerun()
            else:
                st.info("No hay usuarios registrados además del administrador.")
