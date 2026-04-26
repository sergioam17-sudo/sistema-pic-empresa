import sqlite3
import pandas as pd

def connection():
    conn = sqlite3.connect('pic_gestion.db', check_same_thread=False)
    return conn

def create_tables():
    conn = connection()
    cursor = conn.cursor()
    # Tabla Usuarios
    cursor.execute('''CREATE TABLE IF NOT EXISTS usuarios (
        id_usuario INTEGER PRIMARY KEY, email TEXT, nombre TEXT, 
        rol TEXT, municipio_asignado TEXT, activo INTEGER)''')
    
    # Tabla Parametrización
    cursor.execute('''CREATE TABLE IF NOT EXISTS param_municipio (
        id_param INTEGER PRIMARY KEY AUTOINCREMENT, municipio TEXT, contrato TEXT,
        cod_actividad TEXT, cod_subactividad TEXT, valor_actividad REAL,
        peso_subactividad REAL, meta_subactividad REAL, valor_subactividad REAL)''')

    # Tabla Seguimiento
    cursor.execute('''CREATE TABLE IF NOT EXISTS seguimiento_mensual (
        id_seg INTEGER PRIMARY KEY AUTOINCREMENT, mes TEXT, id_param INTEGER,
        municipio TEXT, cant_ejecutada REAL, valor_calculado REAL,
        estado_revision TEXT, soporte_url TEXT, acta_url TEXT,
        FOREIGN KEY(id_param) REFERENCES param_municipio(id_param))''')
    conn.commit()
    conn.close()

# Inicializar DB
create_tables()