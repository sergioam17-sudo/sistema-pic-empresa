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
    conn.commit()
    conn.close()

init_db()

# --- 2. CONFIGURACIÓN DE LA INTERFAZ ---
st.set_page_config(page_title="Sistema PIC - Unidad de Medida", layout="wide")

if 'user' not in st.session_state:
    st.sidebar.title("🔐 Acceso Sistema PIC")
    email = st.sidebar.text_input("Correo electrónico")
    rol = st.sidebar.selectbox("Rol", ["DEPARTAMENTO_PARAMETRIZADOR", "MUNICIPIO_EJECUTOR", "REFERENTE_DEPARTAMENTAL", "SUPERVISOR"])
    if st.sidebar.button("Ingresar"):
        st.session_state['user'] = email
        st.session_state['rol'] = rol
        st.rerun()
else:
    rol = st.session_state['rol']
    st.sidebar.info(f"**Usuario:** {st.session_state['user']}\n\n**Rol:** {rol}")
    menu = st.sidebar.radio("Navegación", ["🏠 Dashboard", "⚙️ Parametrización", "📝 Ejecución"])

    # --- MÓDULO: PARAMETRIZACIÓN ---
    if menu == "⚙️ Parametrización":
        st.title("⚙️ Módulo de Parametrización")
        tab1, tab2 = st.tabs(["1. Registro de Actividades", "2. Configuración de Subactividades"])

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
