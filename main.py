from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import psycopg2
import smtplib
from email.message import EmailMessage
import uuid
from fastapi.responses import HTMLResponse

app = FastAPI()

# ================= CONFIGURACIÓN =================
DATABASE_URL = "postgresql://neondb_owner:npg_nCKYO6IXkz5i@ep-sweet-lake-am1iz8ot-pooler.c-5.us-east-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require"
CORREO_APP = "soporte.tranki@gmail.com"
PASSWORD_APP = "xdxy stza vijv hwjk"
URL_SERVIDOR = "https://api-tv-mahum.onrender.com" # Cambia esto por tu enlace de Render
# =================================================

def get_db_connection():
    return psycopg2.connect(DATABASE_URL)

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    # Reiniciamos la tabla para agregar las nuevas columnas (Solo útil en fase de prototipo)
    cursor.execute('DROP TABLE IF EXISTS usuarios')
    cursor.execute('''
        CREATE TABLE usuarios (
            email VARCHAR(255) PRIMARY KEY,
            password VARCHAR(255) NOT NULL,
            verificado BOOLEAN DEFAULT FALSE,
            token_validacion VARCHAR(255)
        )
    ''')
    conn.commit()
    cursor.close()
    conn.close()

init_db()

class Usuario(BaseModel):
    email: str
    password: str

# Función para enviar el correo
def enviar_correo_verificacion(destinatario, token):
    msg = EmailMessage()
    msg['Subject'] = "Verifica tu cuenta - App TV"
    msg['From'] = CORREO_APP
    msg['To'] = destinatario
    
    enlace = f"{URL_SERVIDOR}/verificar/{token}"
    msg.set_content(f"¡Hola!\n\nGracias por registrarte. Para poder iniciar sesión en tu Smart TV, por favor verifica tu cuenta haciendo clic en el siguiente enlace:\n\n{enlace}\n\n¡Te esperamos!")

    # Conexión al servidor de Gmail
    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
        smtp.login(CORREO_APP, PASSWORD_APP)
        smtp.send_message(msg)

# ================= RUTAS DE LA API =================

@app.post("/registro")
def registrar(user: Usuario):
    conn = get_db_connection()
    cursor = conn.cursor()
    token = str(uuid.uuid4()) # Generamos un código único aleatorio
    
    try:
        cursor.execute("INSERT INTO usuarios (email, password, verificado, token_validacion) VALUES (%s, %s, FALSE, %s)", (user.email, user.password, token))
        conn.commit()
        
        # Enviamos el correo justo después de guardar en la BD
        enviar_correo_verificacion(user.email, token)
        
        return {"mensaje": "Usuario registrado. Por favor, revisa tu correo electrónico para verificar tu cuenta antes de iniciar sesión."}
    except psycopg2.IntegrityError:
        conn.rollback()
        raise HTTPException(status_code=400, detail="El correo ya existe")
    finally:
        cursor.close()
        conn.close()

@app.get("/verificar/{token}", response_class=HTMLResponse)
def verificar_cuenta(token: str):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Buscamos el token y actualizamos el estado
    cursor.execute("UPDATE usuarios SET verificado = TRUE, token_validacion = NULL WHERE token_validacion = %s RETURNING email", (token,))
    resultado = cursor.fetchone()
    conn.commit()
    cursor.close()
    conn.close()
    
    if resultado:
        # Esto es lo que verá el usuario en su celular/PC al hacer clic en el enlace
        return """
        <html>
            <body style='text-align: center; padding: 50px; font-family: Arial;'>
                <h1 style='color: #4CAF50;'>¡Cuenta Verificada!</h1>
                <p>Tu correo ha sido validado exitosamente.</p>
                <p><b>Ya puedes iniciar sesión en tu Smart TV.</b></p>
            </body>
        </html>
        """
    else:
        raise HTTPException(status_code=400, detail="Enlace inválido o la cuenta ya fue verificada.")

@app.post("/login")
def login(user: Usuario):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT verificado FROM usuarios WHERE email=%s AND password=%s", (user.email, user.password))
    resultado = cursor.fetchone()
    cursor.close()
    conn.close()
    
    if not resultado:
        raise HTTPException(status_code=401, detail="Credenciales incorrectas")
    
    # Comprobamos la nueva columna "verificado"
    if not resultado[0]: 
        raise HTTPException(status_code=403, detail="Cuenta no verificada. Revisa tu correo.")
        
    return {"mensaje": "Login exitoso", "email": user.email}

@app.get("/ver_usuarios")
def ver_usuarios():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT email, verificado FROM usuarios")
    usuarios = cursor.fetchall()
    cursor.close()
    conn.close()
    
    lista = [{"email": u[0], "verificado": u[1]} for u in usuarios]
    return {"total_usuarios": len(lista), "lista": lista}