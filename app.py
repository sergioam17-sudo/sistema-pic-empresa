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
