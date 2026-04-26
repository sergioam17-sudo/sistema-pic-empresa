import streamlit as st
import pandas as pd
from database import connection

st.set_page_config(page_title="Gestión PIC", layout="wide")

# --- ESTILOS ---
st.markdown("""
    <style>
    .stMetric { background-color: #f0f2f6; padding: 10px; border-radius: 10px; }
    .status-aprobado { color: green; font-weight: bold; }
    .status-revision { color: orange; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# --- LOGIN SIMPLIFICADO ---
if 'user' not in st.session_state:
    st.sidebar.title("🔐 Acceso")
    user_email = st.sidebar.text_input("Email")
    user_rol = st.sidebar.selectbox("Rol", ["DEPARTAMENTO_PARAMETRIZADOR", "MUNICIPIO_EJECUTOR", "REFERENTE_DEPARTAMENTAL", "SUPERVISOR"])
    if st.sidebar.button("Entrar"):
        st.session_state['user'] = user_email
        st.session_state['rol'] = user_rol
        st.rerun()
else:
    rol = st.session_state['rol']
    st.sidebar.write(f"Usuario: {st.session_state['user']}")
    st.sidebar.write(f"Rol: **{rol}**")
    
    menu = st.sidebar.radio("Menú", ["Dashboard", "Parametrización", "Ejecución", "Revisión", "Supervisión"])

    # --- MÓDULO: PARAMETRIZACIÓN ---
    if menu == "Parametrización" and rol == "DEPARTAMENTO_PARAMETRIZADOR":
        st.header("⚙️ Parametrización de Actividades")
        with st.form("form_param"):
            col1, col2 = st.columns(2)
            muni = col1.text_input("Municipio")
            cont = col1.text_input("Contrato")
            val_act = col2.number_input("Valor Actividad", min_value=0.0)
            peso = col2.slider("Peso Subactividad (0-1)", 0.0, 1.0, 0.1)
            meta = col2.number_input("Meta Física", min_value=1.0)
            
            if st.form_submit_button("Guardar Parámetros"):
                val_sub = val_act * peso
                conn = connection()
                conn.execute("INSERT INTO param_municipio (municipio, contrato, valor_actividad, peso_subactividad, meta_subactividad, valor_subactividad) VALUES (?,?,?,?,?,?)",
                             (muni, cont, val_act, peso, meta, val_sub))
                conn.commit()
                st.success(f"Parametrizado. Valor calculado: ${val_sub:,.2f}")

    # --- MÓDULO: EJECUCIÓN ---
    elif menu == "Ejecución" and rol == "MUNICIPIO_EJECUTOR":
        st.header("📝 Registro de Ejecución Mensual")
        # Cargar datos de parametrización para el combo
        df_p = pd.read_sql("SELECT * FROM param_municipio", connection())
        
        if not df_p.empty:
            option = st.selectbox("Seleccione Actividad Parametrizada", df_p['id_param'].tolist(), format_func=lambda x: f"ID {x} - {df_p[df_p['id_param']==x]['municipio'].values[0]}")
            row = df_p[df_p['id_param'] == option].iloc[0]
            
            cant = st.number_input(f"Cantidad Ejecutada (Meta: {row['meta_subactividad']})", min_value=0.0)
            archivo = st.file_uploader("Cargar Soporte (PDF/JPG)")
            
            if st.button("Enviar a Revisión"):
                if cant > row['meta_subactividad']:
                    st.error("Error: La cantidad ejecutada supera la meta.")
                else:
                    v_pagar = (cant / row['meta_subactividad']) * row['valor_subactividad']
                    conn = connection()
                    conn.execute("INSERT INTO seguimiento_mensual (mes, id_param, municipio, cant_ejecutada, valor_calculado, estado_revision) VALUES (?,?,?,?,?,?)",
                                 ("Octubre", option, row['municipio'], cant, v_pagar, "ENVIADO_POR_MUNICIPIO"))
                    conn.commit()
                    st.success(f"Enviado. Valor a pagar calculado: ${v_pagar:,.2f}")

    # --- MÓDULO: DASHBOARD / SUPERVISIÓN ---
    elif menu == "Dashboard" or menu == "Supervisión":
        st.header("📊 Tablero de Control Institucional")
        df_seg = pd.read_sql("SELECT * FROM seguimiento_mensual", connection())
        
        if not df_seg.empty:
            col1, col2, col3 = st.columns(3)
            total_ejec = df_seg[df_seg['estado_revision'] == 'APROBADO_REFERENTE']['valor_calculado'].sum()
            col1.metric("Total Ejecutado (Aprobado)", f"${total_ejec:,.2f}")
            col2.metric("Registros Pendientes", len(df_seg[df_seg['estado_revision'] == 'ENVIADO_POR_MUNICIPIO']))
            
            st.subheader("Detalle de Seguimiento")
            st.dataframe(df_seg)
        else:
            st.info("No hay datos registrados aún.")

    if st.sidebar.button("Cerrar Sesión"):
        del st.session_state['user']
        st.rerun()