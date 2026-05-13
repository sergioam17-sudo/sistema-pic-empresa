import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection



# URL de tu Excel (asegurate que termina en /edit?usp=sharing o similar)
URL_DB = "https://docs.google.com/spreadsheets/d/TU_ID_AQUÍ/edit?usp=sharing"

# Crear conexión
conn = st.connection("gsheets", type=GSheetsConnection)

# --- FUNCIÓN PARA INICIALIZAR ENCABEZADOS (AUTOMÁTICO) ---
def init_excel_db():
    tablas = {
        "usuarios": ["id_usuario", "nombre_completo", "email", "password", "rol", "municipio_asignado"],
        "actividades_maestro": ["id_actividad", "nombre_actividad", "descripcion", "meta_global", "unidad_medida", "valor_total_actividad", "programa_responsable"]
    }
    
    for nombre, columnas in tablas.items():
        # Intentamos leer la hoja
        df = conn.read(spreadsheet=URL_DB, worksheet=nombre)
        if df.empty:
            # Si está vacía, ponemos los encabezados
            df_init = pd.DataFrame(columns=columnas)
            conn.update(spreadsheet=URL_DB, worksheet=nombre, data=df_init)

# --- REEMPLAZO DE 'INSERT INTO' ---
def guardar_nuevo_usuario(nombre, email, clave, rol, muni):
    # 1. Leer datos actuales
    df_actual = conn.read(spreadsheet=URL_DB, worksheet="usuarios")
    
    # 2. Crear nueva fila (Pandas)
    nuevo_id = 1 if df_actual.empty else df_actual["id_usuario"].max() + 1
    nueva_fila = pd.DataFrame([[nuevo_id, nombre, email, clave, rol, muni]], 
                              columns=df_actual.columns)
    
    # 3. Unir y Subir
    df_final = pd.concat([df_actual, nueva_fila], ignore_index=True)
    conn.update(spreadsheet=URL_DB, worksheet="usuarios", data=df_final)






# --- CONFIGURACIÓN DE LECTURA ---
def get_data(nombre_hoja):
    """Lee datos de la hoja especificada en Google Sheets"""
    return conn.read(spreadsheet=URL_DB, worksheet=nombre_hoja, ttl=0)

# Inicializar encabezados automáticamente si las hojas están vacías
try:
    init_excel_db()
except Exception as e:
    st.error(f"Error al conectar con la base de datos: {e}")

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

# --- 2. CONFIGURACIÓN DE LA INTERFAZ ---
st.set_page_config(page_title="Sistema PIC - Unidad de Medida", layout="wide")

if 'user' not in st.session_state:
    st.sidebar.title("🔐 Acceso PIC Santander")
    user_input = st.sidebar.text_input("Email / Usuario")
    pass_input = st.sidebar.text_input("Contraseña", type="password")
    
    if st.sidebar.button("Ingresar"):
        
        try:
            # 1. Traemos la hoja de usuarios desde Google Sheets
            df_usuarios = get_data("usuarios")
            
            # 2. Filtramos el DataFrame buscando coincidencia
            user_match = df_usuarios[
                (df_usuarios['email'] == user_input) & 
                (df_usuarios['password'].astype(str) == str(pass_input))
            ]
             
            if not user_match.empty:
                # 3. Guardamos los datos en la sesión si hay coincidencia
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


# --- MÓDULO: DASHBOARD DINÁMICO ---
    if menu == "🏠 Dashboard":
        st.title(f"📊 Panel de Control - {rol.replace('_', ' ')}")

        if rol == "MUNICIPIO_EJECUTOR":
            muni_user = st.session_state.get('muni_asignado')
            st.subheader(f"Estado de Ejecución: {muni_user}")

            # Datos del Municipio (Carga desde Sheets y filtrado con Pandas)
            df_asig_all = get_data("asignacion_municipios")
            df_pagos_all = get_data("seguimiento_pagos")
            
            # Filtrar asignaciones del municipio
            df_muni = df_asig_all[df_asig_all['municipio'] == muni_user]
            
            # Calcular ejecutado (esto reemplaza las subconsultas SQL)
            if not df_pagos_all.empty:
                pagos_muni = df_pagos_all[(df_pagos_all['estado'] != 'PENDIENTE')]
                total_ejecutado = pagos_muni['valor_calculado'].sum()
            else:
                total_ejecutado = 0

            

            # Métricas Principales con cálculo real desde seguimiento_pagos
            total_asig = df_muni['valor_asignado'].sum()
            
            # El total ejecutado proviene de la variable total_ejecutado calculada arriba [cite: 15]
            total_ejec = total_ejecutado 
            progreso_financiero = (total_ejec / total_asig) if total_asig > 0 else 0

            m1, m2, m3 = st.columns(3)
            m1.metric("Presupuesto Asignado", f"${total_asig:,.2f}")
            m2.metric("Total Ejecutado (Pagos OK)", f"${total_ejec:,.2f}", delta=f"{progreso_financiero:.1%}")
            m3.metric("Pendiente por Cobrar", f"${(total_asig - total_ejec):,.2f}")


            st.write("### Progreso de Metas por Actividad")
            df_asig_g = get_data("asignacion_municipios")
            df_sub_g = get_data("subactividades")
            df_pagos_g = get_data("seguimiento_pagos")

            if not df_asig_g.empty:
                muni_asig = df_asig_g[df_asig_g['municipio'] == muni_user]
                if not muni_asig.empty:
                    df_merge = muni_asig.merge(df_sub_g, on="id_sub")
                    if not df_pagos_g.empty:
                        df_merge = df_merge.merge(df_pagos_g, on="id_asig", how="left")
                    
                    df_grafico = df_merge.groupby('nombre_subactividad').agg({
                        'meta_municipal': 'first',
                        'avance_meta': 'sum'
                    }).reset_index()
                    df_grafico.columns = ['Actividad', 'Programado', 'Realizado']
                    st.bar_chart(df_grafico.set_index('Actividad'))
                else:
                    st.info("No hay asignaciones para este municipio.")
            else:
                st.info("No hay datos de asignación disponibles.")


        else:
            # VISTA DEPARTAMENTAL (Parametrizador, Referente, Supervisor) [cite: 13, 81]
            st.subheader("Análisis Global de Inversión y Cumplimiento")

            # Datos Globales [cite: 20, 53, 87]
            # Datos Globales calculados con Pandas
            df_act_global = get_data("actividades_maestro")
            df_asig_global = get_data("asignacion_municipios")
            df_pagos_global = get_data("seguimiento_pagos")
            
            total_pic = df_act_global['valor_total_actividad'].sum() if not df_act_global.empty else 0
            total_asig = df_asig_global['valor_asignado'].sum() if not df_asig_global.empty else 0
            total_pagos = df_pagos_global[df_pagos_global['estado']=='REVISADO_REFERENTE']['valor_calculado'].sum() if not df_pagos_global.empty else 0

            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Presupuesto Total PIC", f"${total_pic:,.0f}")
            c2.metric("Asignado a Municipios", f"${total_asig:,.0f}")
            c3.metric("Ejecución (Pagos OK)", f"${total_pagos:,.0f}")
            c4.metric("Saldo Disponible", f"${(total_pic - total_asig):,.0f}")

            # Gráficos Dinámicos [cite: 86]
            col_left, col_right = st.columns(2)

            with col_left:
                st.write("#### 💰 Inversión por Municipio (Top 10)")
                df_asig = get_data("asignacion_municipios")
                df_muni_inv = df_asig.groupby('municipio')['valor_asignado'].sum().reset_index()
                st.bar_chart(df_muni_inv.set_index('municipio'))

  
            with col_right:
                st.write("#### 🚦 Estado de los Trámites de Pago")
                df_pagos_est = get_data("seguimiento_pagos")
                if not df_pagos_est.empty:
                    # Usamos value_counts de Pandas para resumir estados
                    df_resumen_est = df_pagos_est['estado'].value_counts().reset_index()
                    df_resumen_est.columns = ['Estado', 'Cantidad']
                    st.write(df_resumen_est)
                else:
                    st.info("No hay trámites de pago iniciados.")
            
            st.write("#### ⚠️ Últimos Movimientos del Sistema")
            
            # Unimos las tablas con Pandas para mostrar los últimos registros
            df_p_ult = get_data("seguimiento_pagos")
            df_a_ult = get_data("asignacion_municipios")
            df_s_ult = get_data("subactividades")

            if not df_p_ult.empty:
                # Unión de tablas para obtener nombres de municipio y actividad
                df_merge_ult = df_p_ult.merge(df_a_ult, on="id_asig").merge(df_s_ult, on="id_sub")
                df_final_ult = df_merge_ult[['fecha_registro', 'municipio', 'nombre_subactividad', 'estado']].tail(5)
                st.table(df_final_ult)            



            






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
                    df_act = get_data("actividades_maestro")
                    nuevo_id = 1 if df_act.empty else df_act['id_actividad'].max() + 1
                    
                    nueva_fila = pd.DataFrame([{
                        "id_actividad": nuevo_id,
                        "nombre_actividad": nombre_a, "descripcion": desc_a,
                        "meta_global": meta_a, "unidad_medida": unidad_a,
                        "valor_total_actividad": val_total, "programa_responsable": prog
                    }])
                    
                    df_final = pd.concat([df_act, nueva_fila], ignore_index=True)
                    conn.update(spreadsheet=URL_DB, worksheet="actividades_maestro", data=df_final)
                    st.success("✅ Actividad guardada en Sheets.")
                    st.rerun()



# --- TABLA DE ACTIVIDADES CON OPCIÓN DE ELIMINAR ---
            st.write("---")
            st.subheader("📋 Actividades Generales Registradas")
            
            df_maestro = get_data("actividades_maestro")
            
            if not df_maestro.empty:
                # Mostramos la tabla profesional
                st.dataframe(df_maestro[['id_actividad', 'nombre_actividad', 'programa_responsable', 'valor_total_actividad', 'meta_global', 'unidad_medida']], use_container_width=True)
                
                # Opción para eliminar por si hubo error
                with st.expander("🗑️ Zona de eliminación (Usar con precaución)"):
                    id_a_borrar = st.number_input("Ingrese el ID de la actividad a eliminar:", min_value=1, step=1)
                    if st.button("Eliminar Actividad Permanentemente"):
                        # Validamos en el DataFrame de subactividades
                        df_sub_check = get_data("subactividades")
                        check_sub = df_sub_check[df_sub_check['id_actividad'] == id_a_borrar]
                        
                        if not check_sub.empty:
                            st.error("⚠️ No se puede eliminar: Esta actividad tiene subactividades vinculadas.")
                        else:
                            df_maestro_del = get_data("actividades_maestro")
                            df_maestro_del = df_maestro_del[df_maestro_del['id_actividad'] != id_a_borrar]
                            conn.update(spreadsheet=URL_DB, worksheet="actividades_maestro", data=df_maestro_del)
                            st.warning(f"Actividad {id_a_borrar} eliminada del Excel.")
                            st.rerun()
	
            else:
                st.info("No hay actividades registradas todavía.")




        # TAB 2: SUBACTIVIDADES
        with tab2:
            st.subheader("Desglose de Subactividades")
            df_act = get_data("actividades_maestro")

            if not df_act.empty:
                nombres_act = {row['id_actividad']: row['nombre_actividad'] for _, row in df_act.iterrows()}
                act_id = st.selectbox("Seleccione Actividad Padre:", df_act['id_actividad'].tolist(), format_func=lambda x: nombres_act[x])
                
                padre = df_act[df_act['id_actividad'] == act_id].iloc[0]
                
                # Resumen de pesos usando Pandas
                df_all_subs = get_data("subactividades")
                df_sub_existentes = df_all_subs[df_all_subs['id_actividad'] == act_id]
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
                            df_sub = get_data("subactividades")
                            nueva_sub = pd.DataFrame([{
                                "id_sub": len(df_sub) + 1,
                                "id_actividad": act_id,
                                "nombre_subactividad": sub_nombre,
                                "valor_sub": sub_valor,
                                "meta_sub": sub_meta,
                                "unidad_medida_sub": sub_unidad,
                                "peso": sub_peso
                            }])
                            df_final = pd.concat([df_sub, nueva_sub], ignore_index=True)
                            conn.update(spreadsheet=URL_DB, worksheet="subactividades", data=df_final)
                            st.success("✅ Subactividad agregada al Excel.")
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
                                        df_sub_upd = get_data("subactividades")
                                        df_sub_upd.loc[df_sub_upd['id_sub'] == id_edit, ['nombre_subactividad', 'meta_sub', 'peso', 'valor_sub']] = [new_nom, new_meta, new_peso, new_val]
                                        conn.update(spreadsheet=URL_DB, worksheet="subactividades", data=df_sub_upd)
                                        st.success("✅ Subactividad actualizada en Excel")
                                        st.rerun()
                        else:
                            st.info("Ingrese un ID válido de la tabla de arriba")

                    # --- BOTÓN ELIMINAR ---
                    with col_del.expander("🗑️ Eliminar Subactividad"):
                        id_del = st.number_input("ID de la subactividad a eliminar:", min_value=1, step=1, key="del_sub_id")
                        if st.button("Confirmar Eliminación", type="primary"):
                            df_sub_del = get_data("subactividades")
                            # Filtramos para mantener todo menos el ID a borrar
                            df_sub_del = df_sub_del[df_sub_del['id_sub'] != id_del]
                            conn.update(spreadsheet=URL_DB, worksheet="subactividades", data=df_sub_del)
                            st.warning(f"⚠️ Subactividad {id_del} eliminada del Excel")
                            st.rerun()
                else:
                    st.info("No hay subactividades vinculadas a esta actividad padre.")


# --- TAB 3: ASIGNACIÓN A MUNICIPIOS ---
        with tab3:
            
            st.subheader("📍 Asignación de Presupuesto por Municipio")
            
            # Consultar subactividades uniendo DataFrames de Pandas
            df_s_raw = get_data("subactividades")
            df_a_raw = get_data("actividades_maestro")
            
            if not df_s_raw.empty and not df_a_raw.empty:
                df_sub_todas = df_s_raw.merge(df_a_raw[['id_actividad', 'nombre_actividad']], on="id_actividad")
            else:
                df_sub_todas = pd.DataFrame()


            if df_sub_todas.empty:
                st.warning("Debe configurar subactividades en la pestaña 2 antes de asignar municipios.")
            else:
                # Selector de subactividad
                sub_sel_id = st.selectbox("Seleccione Subactividad:", 
                                         df_sub_todas['id_sub'].tolist(), 
                                         format_func=lambda x: f"{df_sub_todas[df_sub_todas['id_sub']==x]['nombre_actividad'].values[0]} >> {df_sub_todas[df_sub_todas['id_sub']==x]['nombre_subactividad'].values[0]}",
                                         key="asig_muni_selector")
                
                datos_sub = df_sub_todas[df_sub_todas['id_sub'] == sub_sel_id].iloc[0]
                
           
                # Cálculos usando el DataFrame ya cargado (df_s_raw)
                df_asig_all = get_data("asignacion_municipios")
                df_asig_actual = df_asig_all[df_asig_all['id_sub'] == sub_sel_id]

                valor_gastado_muni = df_asig_actual['valor_asignado'].sum() if not df_asig_actual.empty else 0
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
                            df_asig_muni = get_data("asignacion_municipios")
                            # Generamos nuevo ID y nueva fila
                            nuevo_id_asig = 1 if df_asig_muni.empty else df_asig_muni['id_asig'].max() + 1
                            nueva_asig = pd.DataFrame([{
                                "id_asig": nuevo_id_asig,
                                "id_sub": sub_sel_id, 
                                "municipio": muni_nombre, 
                                "num_contrato": n_contrato, 
                                "num_pagos": n_pagos, 
                                "valor_asignado": muni_valor, 
                                "meta_municipal": muni_meta
                            }])
                            df_final_asig = pd.concat([df_asig_muni, nueva_asig], ignore_index=True)
                            conn.update(spreadsheet=URL_DB, worksheet="asignacion_municipios", data=df_final_asig)
                            st.success(f"✅ Asignación exitosa para {muni_nombre} en Excel")
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
                            df_asig_del = get_data("asignacion_municipios")
                            df_asig_del = df_asig_del[df_asig_del['id_asig'] != id_asig_del]
                            conn.update(spreadsheet=URL_DB, worksheet="asignacion_municipios", data=df_asig_del)
                            st.warning("⚠️ Asignación eliminada del Excel")
                            st.rerun()


# --- MÓDULO: EJECUCIÓN (MUNICIPIO) ---
    elif menu == "📝 Ejecución":
        if rol != "MUNICIPIO_EJECUTOR":
            st.warning("Este módulo es exclusivo para el perfil MUNICIPIO_EJECUTOR.")
        else:
            st.title("📝 Reporte de Avance Municipal")
            muni_user = st.session_state.get('muni_asignado', 'N/A') 
            

            # Carga de datos uniendo hojas de Excel con Pandas [cite: 206]
            df_a_exec = get_data("asignacion_municipios")
            df_s_exec = get_data("subactividades")
            df_m_exec = get_data("actividades_maestro")

            if not df_a_exec.empty:
                # Reemplazo del JOIN SQL por MERGE de Pandas [cite: 206]
                df_merge_exec = df_a_exec.merge(df_s_exec, on="id_sub").merge(df_m_exec, on="id_actividad")
                # Filtrar por el municipio asignado al usuario [cite: 207]
                df_mis_asig = df_merge_exec[df_merge_exec['municipio'] == muni_user]
            else:
                df_mis_asig = pd.DataFrame()



            if df_mis_asig.empty:
                st.info(f"No hay asignaciones pendientes para {muni_user}.")
            else:
                sel_asig = st.selectbox("Seleccione Actividad/Contrato a reportar:", df_mis_asig['id_asig'].tolist(), 
                                       format_func=lambda x: f"Contrato: {df_mis_asig[df_mis_asig['id_asig']==x]['num_contrato'].values[0]} - {df_mis_asig[df_mis_asig['id_asig']==x]['nombre_subactividad'].values[0]}")
                
                datos = df_mis_asig[df_mis_asig['id_asig'] == sel_asig].iloc[0]
                
            # Consultar último pago reportado filtrando el DataFrame
            df_pagos_all = get_data("seguimiento_pagos")
            if not df_pagos_all.empty:
                pagos_asig = df_pagos_all[df_pagos_all['id_asig'] == sel_asig]
                ultimo_pago = pagos_asig['num_pago_actual'].max() if not pagos_asig.empty else 0
            else:
                ultimo_pago = 0

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
                            df_pagos = get_data("seguimiento_pagos")
                            nuevo_id_seg = 1 if df_pagos.empty else df_pagos['id_seguimiento'].max() + 1
                            nueva_fila_pago = pd.DataFrame([{
                                "id_seguimiento": nuevo_id_seg,
                                "id_asig": sel_asig, 
                                "num_pago_actual": siguiente_pago, 
                                "avance_meta": meta_avanc, 
                                "valor_calculado": valor_pago, 
                                "soporte_municipio": soporte, 
                                "estado": 'PENDIENTE'
                            }])
                            df_final_pagos = pd.concat([df_pagos, nueva_fila_pago], ignore_index=True)
                            conn.update(spreadsheet=URL_DB, worksheet="seguimiento_pagos", data=df_final_pagos)
                            st.success("✅ Reporte enviado exitosamente al Excel.")

                            st.rerun()


# --- TABLA DE SEGUIMIENTO PARA MUNICIPIO ---
        st.write("---")
        st.subheader("📋 Historial de mis Reportes y Estados")
        
        muni_actual = st.session_state.get('muni_asignado')
        # Consulta para ver el estado de los pagos del municipio logueado
       
        # Obtener historial filtrando con Pandas
        df_p_muni = get_data("seguimiento_pagos")
        df_a_muni = get_data("asignacion_municipios")
        df_s_muni = get_data("subactividades")
        
        if not df_p_muni.empty:
            df_merge_muni = df_p_muni.merge(df_a_muni, on="id_asig").merge(df_s_muni, on="id_sub")
            df_seguimiento_muni = df_merge_muni[df_merge_muni['municipio'] == muni_actual]
            df_seguimiento_muni = df_seguimiento_muni[['id_seguimiento', 'nombre_subactividad', 'num_pago_actual', 'valor_calculado', 'avance_meta', 'estado', 'acta_referente']]
        else:
            df_seguimiento_muni = pd.DataFrame()



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
            # Cargamos las tablas necesarias
            df_p = get_data("seguimiento_pagos")
            df_a = get_data("asignacion_municipios")
            df_s = get_data("subactividades")

            if not df_p.empty:
                # Realizamos los "JOIN" usando Pandas
                df_merge = df_p.merge(df_a, on="id_asig").merge(df_s, on="id_sub")
                df_pendientes = df_merge[df_merge['estado'] == 'PENDIENTE']
                # Seleccionamos solo las columnas necesarias para mostrar
                df_pendientes = df_pendientes[['id_seguimiento', 'municipio', 'num_contrato', 'nombre_subactividad', 'num_pago_actual', 'valor_calculado', 'soporte_municipio']]
            else:
                df_pendientes = pd.DataFrame()
            
            if df_pendientes.empty:
                st.write("No hay reportes municipales pendientes de revisión.")
            else:
                st.dataframe(df_pendientes, use_container_width=True)
                with st.form("form_revision_referente"):
                    id_rev = st.number_input("ID de Seguimiento a dar OK:", min_value=1, step=1)
                    acta_link = st.text_input("Enlace al Acta de Conformidad (PDF)")
                    if st.form_submit_button("Dar OK y enviar a Supervisor"):
                        df_rev = get_data("seguimiento_pagos")
                        # Actualizamos estado y link del acta
                        df_rev.loc[df_rev['id_seguimiento'] == id_rev, ['estado', 'acta_referente']] = ['REVISADO_REFERENTE', acta_link]
                        conn.update(spreadsheet=URL_DB, worksheet="seguimiento_pagos", data=df_rev)
                        st.success("✅ Validación registrada en Excel.")
                        st.rerun()


# --- CONSOLIDADO GLOBAL DE PAGOS (VISTA DEPARTAMENTO) ---
        st.write("---")
        st.subheader("📑 Trazabilidad General de Pagos")
        
        # Consolidado global uniendo hojas de Excel
        df_p_glob = get_data("seguimiento_pagos")
        df_a_glob = get_data("asignacion_municipios")
        df_s_glob = get_data("subactividades")
        
        if not df_p_glob.empty:
            df_global = df_p_glob.merge(df_a_glob, on="id_asig").merge(df_s_glob, on="id_sub")
            df_global = df_global[['id_seguimiento', 'municipio', 'nombre_subactividad', 'num_pago_actual', 'valor_calculado', 'estado', 'soporte_municipio', 'acta_referente']]
            df_global.columns = ['ID', 'Municipio', 'Actividad', 'Pago N°', 'Valor', 'Estado', 'Link Evidencia', 'Link Acta']
        else:
            df_global = pd.DataFrame()

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
                    df_users = get_data("usuarios")
                    if u_email in df_users['email'].values:
                        st.error("Error: El correo ya existe.")
                    else:
                        nueva_fila = pd.DataFrame([{
                            "id_usuario": len(df_users) + 1,
                            "email": u_email, "password": u_pass, "nombre_completo": u_nombre,
                            "cedula": u_cedula, "cargo": u_cargo, "telefono": u_tel,
                            "rol": u_rol, "municipio_asignado": u_muni
                        }])
                        df_final = pd.concat([df_users, nueva_fila], ignore_index=True)
                        conn.update(spreadsheet=URL_DB, worksheet="usuarios", data=df_final)
                        st.success(f"Usuario {u_email} registrado correctamente.")
                        st.rerun()

# --- VISUALIZACIÓN Y GESTIÓN DE USUARIOS EXISTENTES ---
            st.write("---")
            st.subheader("👥 Usuarios Registrados")
            
            
            df_usuarios = get_data("usuarios")
            
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
                            df_u = get_data("usuarios")
                            df_u.loc[df_u['id_usuario'] == id_update, ['nombre_completo', 'rol']] = [new_nombre, new_rol]
                            conn.update(spreadsheet=URL_DB, worksheet="usuarios", data=df_u)
                            st.success("✅ Usuario actualizado en Excel.")
                            st.rerun()

                # --- OPCIÓN: ELIMINAR ---
                with col_del.expander("🗑️ Eliminar Usuario"):
                    id_delete = st.number_input("ID del usuario a eliminar:", min_value=1, step=1, key="del_user_id")
                    if st.button("Confirmar Eliminación de Usuario", type="primary"):
                        if id_delete == 1: # Protección para no borrar al admin principal
                            st.error("No se puede eliminar el usuario administrador maestro.")
                        else:
                            df_u_del = get_data("usuarios")
                            df_u_del = df_u_del[df_u_del['id_usuario'] != id_delete]
                            conn.update(spreadsheet=URL_DB, worksheet="usuarios", data=df_u_del)
                            st.warning(f"⚠️ Usuario {id_delete} eliminado del Excel")
                            st.rerun()
            else:
                st.info("No hay usuarios registrados además del administrador.")
