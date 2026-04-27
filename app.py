import streamlit as st
import pandas as pd
import sqlite3

# --- 1. CONFIGURACIÓN DE BASE DE DATOS (Integrada) ---
def connection():
    conn = sqlite3.connect('pic_gestion.db', check_same_thread=False)
    return conn

def init_db():
    conn = connection()
    cursor = conn.cursor()
    # Tabla Actividades (PADRE)
    cursor.execute('''CREATE TABLE IF NOT EXISTS actividades_maestro (
        id_actividad INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre_actividad TEXT,
        descripcion TEXT,
        meta_global REAL,
        valor_total_actividad REAL,
        programa_responsable TEXT
    )''')
    # Tabla Subactividades (HIJO)
    cursor.execute('''CREATE TABLE IF NOT EXISTS subactividades (
        id_sub INTEGER PRIMARY KEY AUTOINCREMENT,
        id_actividad INTEGER,
        nombre_subactividad TEXT,
        valor_sub REAL,
        meta_sub REAL,
        peso REAL,
        FOREIGN KEY(id_actividad) REFERENCES actividades_maestro(id_actividad)
    )''')
    conn.commit()
    conn.close()

init_db()

# --- 2. CONFIGURACIÓN DE LA INTERFAZ ---
st.set_page_config(page_title="Sistema PIC - Gestión Institucional", layout="wide")

# Estilos personalizados
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stAlert { border-radius: 10px; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. LOGICA DE ACCESO (ROLES) ---
if 'user' not in st.session_state:
    st.sidebar.title("🔐 Acceso Sistema PIC")
    email = st.sidebar.text_input("Correo electrónico institucional")
    rol = st.sidebar.selectbox("Rol de Usuario", [
        "DEPARTAMENTO_PARAMETRIZADOR", 
        "MUNICIPIO_EJECUTOR", 
        "REFERENTE_DEPARTAMENTAL", 
        "SUPERVISOR"
    ])
    if st.sidebar.button("Ingresar al Sistema"):
        if email:
            st.session_state['user'] = email
            st.session_state['rol'] = rol
            st.rerun()
        else:
            st.sidebar.error("Por favor ingrese un correo.")
else:
    # --- MENÚ PRINCIPAL ---
    rol = st.session_state['rol']
    st.sidebar.info(f"**Usuario:** {st.session_state['user']}\n\n**Rol:** {rol}")
    
    opciones = ["🏠 Dashboard", "⚙️ Parametrización", "📝 Ejecución", "⚖️ Revisión"]
    menu = st.sidebar.radio("Navegación", opciones)

    # --- MÓDULO: PARAMETRIZACIÓN ---
    if menu == "⚙️ Parametrización":
        if rol != "DEPARTAMENTO_PARAMETRIZADOR":
            st.warning("Acceso restringido: Solo el Departamento puede parametrizar.")
        else:
            st.title("⚙️ Módulo de Parametrización")
            tab1, tab2 = st.tabs(["1. Registro de Actividades", "2. Configuración de Subactividades"])

            # TAB 1: ACTIVIDADES (PADRE)
            with tab1:
                st.subheader("Crear Nueva Actividad General")
                with st.form("form_actividad"):
                    c1, c2 = st.columns(2)
                    nombre_a = c1.text_input("Nombre de la Actividad")
                    prog = c1.text_input("Programa Responsable")
                    val_total = c2.number_input("Valor Total Actividad ($)", min_value=0.0, step=1000.0)
                    meta_a = c2.number_input("Meta Global", min_value=0.0)
                    desc_a = st.text_area("Descripción de la Actividad")
                    
                    if st.form_submit_button("💾 Guardar Actividad"):
                        conn = connection()
                        conn.execute("""INSERT INTO actividades_maestro 
                            (nombre_actividad, descripcion, meta_global, valor_total_actividad, programa_responsable) 
                            VALUES (?,?,?,?,?)""", (nombre_a, desc_a, meta_a, val_total, prog))
                        conn.commit()
                        st.success(f"✅ Actividad '{nombre_a}' creada correctamente.")

            # TAB 2: SUBACTIVIDADES (HIJO)
            with tab2:
                st.subheader("Desglose de Subactividades")
                df_act = pd.read_sql("SELECT * FROM actividades_maestro", connection())

                if df_act.empty:
                    st.info("Aún no hay actividades creadas. Use la pestaña anterior.")
                else:
                    # Seleccionar Actividad
                    lista_act = df_act['id_actividad'].tolist()
                    nombres_act = {row['id_actividad']: row['nombre_actividad'] for _, row in df_act.iterrows()}
                    act_id = st.selectbox("Seleccione la Actividad Padre:", lista_act, format_func=lambda x: nombres_act[x])
                    
                    # Datos del Padre
                    padre = df_act[df_act['id_actividad'] == act_id].iloc[0]
                    valor_padre = padre['valor_total_actividad']
                    
                    # Calcular pesos actuales
                    df_sub_existentes = pd.read_sql(f"SELECT * FROM subactividades WHERE id_actividad = {act_id}", connection())
                    peso_usado = df_sub_existentes['peso'].sum()
                    valor_usado = df_sub_existentes['valor_sub'].sum()
                    
                    # Mostrar resumen visual
                    c1, c2, c3 = st.columns(3)
                    c1.metric("Valor Total Padre", f"${valor_padre:,.2f}")
                    c2.metric("Peso Acumulado", f"{peso_usado:.2f} / 1.0")
                    c3.metric("Valor Distribuido", f"${valor_usado:,.2f}")

                    if peso_usado >= 1.0:
                        st.success("🎯 Esta actividad ya alcanzó el 100% de su peso.")
                    
                    # Formulario Subactividad
                    with st.form("form_sub"):
                        st.write("---")
                        st.write("**Nueva Subactividad**")
                        cc1, cc2, cc3 = st.columns(3)
                        sub_nombre = cc1.text_input("Nombre Subactividad")
                        sub_meta = cc2.number_input("Meta Específica", min_value=0.0)
                        sub_peso = cc3.number_input("Asignar Peso (0.0 a 1.0)", min_value=0.0, max_value=1.0, step=0.01)
                        
                        if st.form_submit_button("➕ Vincular Subactividad"):
                            if (peso_usado + sub_peso) > 1.0001:
                                st.error(f"❌ Error: El peso total superaría 1.0. (Disponible: {1.0 - peso_usado:.2f})")
                            elif not sub_nombre:
                                st.error("❌ El nombre de la subactividad es obligatorio.")
                            else:
                                sub_valor = valor_padre * sub_peso
                                conn = connection()
                                conn.execute("""INSERT INTO subactividades 
                                    (id_actividad, nombre_subactividad, valor_sub, meta_sub, peso) 
                                    VALUES (?,?,?,?,?)""", (act_id, sub_nombre, sub_valor, sub_meta, sub_peso))
                                conn.commit()
                                st.success("✅ Subactividad agregada.")
                                st.rerun()

                    if not df_sub_existentes.empty:
                        st.write("**Subactividades Registradas:**")
                        st.table(df_sub_existentes[['nombre_subactividad', 'meta_sub', 'peso', 'valor_sub']])

    # --- OTROS MÓDULOS (En desarrollo) ---
    elif menu == "🏠 Dashboard":
        st.title("📊 Dashboard de Control PIC")
        st.write("Resumen ejecutivo del estado de las actividades por municipio.")
        
    elif menu == "📝 Ejecución":
        st.title("📝 Reporte de Ejecución")
        st.info("Módulo para que los Municipios carguen sus soportes mensuales.")

    if st.sidebar.button("Cerrar Sesión"):
        del st.session_state['user']
        st.rerun()
