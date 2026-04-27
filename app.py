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
