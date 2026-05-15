st.warning(f"📋 **Meta Total Asignada:** {meta_total} {unidad_muni} | **Presupuesto Total:** ${valor_total_muni:,.2f}")

                    # --- CORRECCIÓN EXPERTA: ENTRADA FUERA DEL FORMULARIO PARA CÁLCULO DINÁMICO ---
                    # Al estar fuera del form, val_dinamico se actualiza inmediatamente al cambiar el número
                    meta_avanc = st.number_input("Avance de Meta realizado en este periodo", min_value=0.0, step=1.0)
                    
                    val_dinamico = (meta_avanc / meta_total) * valor_total_muni if meta_total > 0 else 0.0
                    porcentaje = (meta_avanc / meta_total * 100) if meta_total > 0 else 0
                    
                    st.write(f"💰 **Valor calculado para este reporte:** :green[${val_dinamico:,.2f}]")
                    st.caption(f"*(Equivale al {porcentaje:.1f}% de la meta total municipal)*")

                    with st.form("form_reporte_muni"):
                        soporte = st.text_input("Link a carpeta de soportes (Evidencias)")
                        
                        if st.form_submit_button("Enviar a Revisión del Referente"):
                            if meta_avanc <= 0:
                                st.error("⚠️ El avance debe ser mayor a 0 para generar un cobro.")
                            else:
                                # Lectura fresca para evitar colisiones de ID
                                df_pagos = get_data("seguimiento_pagos")
                                nuevo_id_seg = 1 if df_pagos.empty else df_pagos['id_seguimiento'].max() + 1
                                
                                # Consolidación del cálculo final para la DB
                                valor_final_pago = (meta_avanc / meta_total) * valor_total_muni
                                
                                nueva_fila_pago = pd.DataFrame([{
                                    "id_seguimiento": nuevo_id_seg,
                                    "id_asig": sel_asig,
                                    "num_pago_actual": siguiente_pago,
                                    "avance_meta": meta_avanc,
                                    "valor_calculado": valor_final_pago,
                                    "soporte_municipio": soporte,
                                    "estado": 'PENDIENTE',
                                    "fecha_registro": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M")
                                }])
                                
                                df_final_pagos = pd.concat([df_pagos, nueva_fila_pago], ignore_index=True)
                                
                                if safe_update("seguimiento_pagos", df_final_pagos):
                                    st.success(f"✅ Reporte enviado exitosamente por ${valor_final_pago:,.2f}")
                                    st.rerun()
