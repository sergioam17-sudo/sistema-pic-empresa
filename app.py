def init_excel_db():
    # Diccionario con todas las pestañas y sus columnas exactas
    tablas = {
        "usuarios": ["id_usuario", "nombre_completo", "email", "password", "rol", "municipio_asignado"],
        "actividades_maestro": ["id_actividad", "nombre_actividad", "descripcion", "meta_global", "unidad_medida", "valor_total_actividad", "programa_responsable"],
        "subactividades": ["id_sub", "id_actividad", "nombre_subactividad", "valor_sub", "meta_sub", "unidad_medida_sub", "peso"],
        "asignacion_municipios": ["id_asig", "id_sub", "municipio", "num_contrato", "num_pagos", "valor_asignado", "meta_municipal"],
        "seguimiento_pagos": ["id_seguimiento", "id_asig", "num_pago_actual", "avance_meta", "valor_calculado", "soporte_municipio", "estado", "acta_referente"]
    }
    
    for nombre, columnas in tablas.items():
        try:
            # Intentamos leer la hoja
            df = conn.read(spreadsheet=URL_DB, worksheet=nombre, ttl=0)
            # Si la hoja está vacía o no tiene columnas, la inicializamos
            if df.empty or len(df.columns) < len(columnas):
                df_init = pd.DataFrame(columns=columnas)
                conn.update(spreadsheet=URL_DB, worksheet=nombre, data=df_init)
                st.toast(f"✅ Pestaña '{nombre}' inicializada.")
        except Exception:
            # Si la pestaña no existe físicamente, la crea
            df_init = pd.DataFrame(columns=columnas)
            conn.update(spreadsheet=URL_DB, worksheet=nombre, data=df_init)
