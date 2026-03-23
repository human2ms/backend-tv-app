from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import psycopg2
import os

app = FastAPI()

# ¡IMPORTANTE! Reemplaza este texto por el enlace larguísimo que copiaste de Neon
DATABASE_URL = "postgresql://neondb_owner:npg_nCKYO6IXkz5i@ep-sweet-lake-am1iz8ot-pooler.c-5.us-east-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require"

# Función para conectarse a la nueva base de datos en la nube
def get_db_connection():
    return psycopg2.connect(DATABASE_URL)

# 1. Crear la tabla en la nube si no existe
def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS usuarios (
            email VARCHAR(255) PRIMARY KEY,
            password VARCHAR(255) NOT NULL
        )
    ''')
    conn.commit()
    cursor.close()
    conn.close()

init_db()

class Usuario(BaseModel):
    email: str
    password: str

# 2. Ruta para REGISTRAR
@app.post("/registro")
def registrar(user: Usuario):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # Postgres usa %s en lugar de ?
        cursor.execute("INSERT INTO usuarios (email, password) VALUES (%s, %s)", (user.email, user.password))
        conn.commit()
        return {"mensaje": "Usuario registrado con éxito"}
    except psycopg2.IntegrityError:
        conn.rollback() # Vital en Postgres cuando hay un error
        raise HTTPException(status_code=400, detail="El correo ya existe")
    finally:
        cursor.close()
        conn.close()

# 3. Ruta para INICIAR SESIÓN
@app.post("/login")
def login(user: Usuario):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM usuarios WHERE email=%s AND password=%s", (user.email, user.password))
    resultado = cursor.fetchone()
    cursor.close()
    conn.close()
    
    if resultado:
        return {"mensaje": "Login exitoso", "email": user.email}
    else:
        raise HTTPException(status_code=401, detail="Credenciales incorrectas")

# 4. NUEVA RUTA: Ver todos los usuarios registrados
@app.get("/ver_usuarios")
def ver_usuarios():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT email FROM usuarios")
    usuarios = cursor.fetchall()
    cursor.close()
    conn.close()
    
    # Formateamos el resultado para que se vea como una lista limpia
    lista_correos = [u[0] for u in usuarios]
    return {"total_usuarios": len(lista_correos), "lista": lista_correos}