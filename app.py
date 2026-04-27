import streamlit as st
import pandas as pd
from database import connection

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Gestión PIC v2", layout="wide")

# --- LOGIN ---
if 'user' not in st.session_state:
    st.sidebar.title("🔐 Acceso Institucional")
    email = st.sidebar.text_input("Correo electrónico")
    rol = st.sidebar.selectbox("Su Rol", ["DEPARTAMENTO_PARAMETRIZADOR", "MUNICIPIO_EJECUTOR", "REFERENTE_DEPARTAMENTAL", "SUPERVISOR"])
    if st.sidebar.button("Entrar"):
        st.session_state['user'] = email
        st.session_state['rol'] = rol
        st.rerun()
else:
    rol = st.session_state['rol']
    st.sidebar.success(f"Sesión activa: {rol}")
    
    opciones = ["Dashboard", "Parametrización", "Registro Ejecución", "Revisión"]
    menu = st.sidebar.radio("Módulos del Sistema", opciones)

    # --- MÓDULO PARAMETRIZACIÓN (Actualizado) ---
    if menu == "Parametrización" and rol == "DEPARTAMENTO_PARAMETRIZADOR":
        st.header("⚙️ Configuración de Plan de Intervenciones")
        
        with st.expander("➕ Registrar Nueva Actividad/Subactividad", expanded=True):
            with st.form("form_nueva_param"):
                col1, col2 = st.columns(2)
                muni = col1.selectbox("Municipio", ["Bucaramanga", "Floridablanca", "Girón", "Piedecuesta"])
                act_nom = col1.text_input("Nombre de la Actividad General")
                act_desc = col1.text_area("Descripción detallada de la Actividad")
                
                sub_nom = col2.text_input("Nombre de la Subactividad")
                meta = col2.number_input("Meta Física (Cantidad)", min_value=1)
                val_total = col2.number_input("Valor Total de la Actividad ($)", min_value=0.0)
                peso = col2.slider("Peso de esta Subactividad (0.0 a 1.0)", 0.0, 1.0, 0.1)
                
                if st.form_submit_button("Guardar Parametrización"):
                    v_sub = val_total * peso
                    conn = connection()
                    # Aquí agregamos el campo de descripción a la lógica (asegúrate de que database.py tenga la columna)
                    conn.execute("""INSERT INTO param_municipio 
                        (municipio, cod_actividad, cod_subactividad, valor_actividad, peso_subactividad, meta_subactividad, valor_subactividad) 
                        VALUES (?,?,?,?,?,?,?)""", 
                        (muni, act_nom, sub_nom, val_total, peso, meta, v_sub))
                    conn.commit()
                    st.success(f"✅ Guardado: {sub_nom} para {muni}. Valor calculado: ${v_sub:,.2f}")

        # --- VISUALIZACIÓN DE LO PARAMETRIZADO ---
        st.subheader("📋 Plan Parametrizado Actual")
        df_p = pd.read_sql("SELECT * FROM param_municipio", connection())
        st.dataframe(df_p, use_container_width=True)

    # --- MÓDULO DASHBOARD ---
    elif menu == "Dashboard":
        st.title("📊 Indicadores de Avance")
        st.info("Aquí verás el cumplimiento físico y financiero una vez los municipios empiecen a registrar.")

    if st.sidebar.button("Cerrar Sesión"):
        del st.session_state['user']
        st.rerun()
