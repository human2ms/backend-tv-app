from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import sqlite3

app = FastAPI()

# 1. Configurar y crear la base de datos SQLite
def init_db():
    conn = sqlite3.connect("usuarios.db")
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS usuarios (
            email TEXT PRIMARY KEY,
            password TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# 2. Estructura de datos que enviará Unity
class Usuario(BaseModel):
    email: str
    password: str

# 3. Ruta para REGISTRAR
@app.post("/registro")
def registrar(user: Usuario):
    conn = sqlite3.connect("usuarios.db")
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO usuarios (email, password) VALUES (?, ?)", (user.email, user.password))
        conn.commit()
        return {"mensaje": "Usuario registrado con éxito"}
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=400, detail="El correo ya existe")
    finally:
        conn.close()

# 4. Ruta para INICIAR SESIÓN
@app.post("/login")
def login(user: Usuario):
    conn = sqlite3.connect("usuarios.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM usuarios WHERE email=? AND password=?", (user.email, user.password))
    resultado = cursor.fetchone()
    conn.close()
    
    if resultado:
        return {"mensaje": "Login exitoso", "email": user.email}
    else:
        raise HTTPException(status_code=401, detail="Credenciales incorrectas")