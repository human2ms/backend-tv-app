from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import psycopg2

app = FastAPI()

# ¡IMPORTANTE! Reemplaza este texto por tu enlace de Neon
DATABASE_URL = "Pega_Aqui_Tu_Enlace_De_Neon"

def get_db_connection():
    return psycopg2.connect(DATABASE_URL)

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

@app.post("/registro")
def registrar(user: Usuario):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO usuarios (email, password) VALUES (%s, %s)", (user.email, user.password))
        conn.commit()
        return {"mensaje": "Usuario registrado con éxito"}
    except psycopg2.IntegrityError:
        conn.rollback()
        raise HTTPException(status_code=400, detail="El correo ya existe")
    finally:
        cursor.close()
        conn.close()

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

@app.get("/ver_usuarios")
def ver_usuarios():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT email FROM usuarios")
    usuarios = cursor.fetchall()
    cursor.close()
    conn.close()
    
    lista_correos = [u[0] for u in usuarios]
    return {"total_usuarios": len(lista_correos), "lista": lista_correos}