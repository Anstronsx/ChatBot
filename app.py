import os
import json
from flask import Flask, request, jsonify, render_template
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)

# Configuración de la base de datos (PostgreSQL en producción, SQLite en desarrollo)
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///metapython.db")
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://")  # Para compatibilidad con SQLAlchemy

app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URL
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Instanciamos la base de datos
db = SQLAlchemy(app)

# Definimos la clase modelo
class Log(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    fecha_y_hora = db.Column(db.DateTime, default=datetime.utcnow)
    texto = db.Column(db.Text, nullable=False)  # Se asegura de que no sea NULL

# Crear la tabla si no existe
with app.app_context():
    db.create_all()

# Función para ordenar registros por fecha y hora
def ordenar_por_fecha_y_hora(registros):
    return sorted(registros, key=lambda x: x.fecha_y_hora or datetime.min, reverse=True)

@app.route('/')
def index():
    # Obtener todos los registros de la base de datos
    registros = Log.query.all()
    registros_ordenados = ordenar_por_fecha_y_hora(registros)
    return render_template('index.html', registros=registros_ordenados)

mensajes_log = []

# Función para agregar mensajes y guardar en la base de datos
def agregar_mensajes_log(texto):
    mensajes_log.append(texto)

    # Convertir texto a string si es JSON
    if isinstance(texto, dict):
        texto = json.dumps(texto)

    nuevo_registro = Log(texto=texto)
    db.session.add(nuevo_registro)
    db.session.commit()

# Token de verificación para la configuración
TOKEN_OMICTECH = "OMICTECH"

# Creación del webhook
@app.route('/webhook', methods=['GET', 'POST'])
def webhook():
    if request.method == 'GET':
        challenge = verificar_token(request)
        return challenge
    elif request.method == 'POST':
        response = recibir_mensajes(request)
        return response

def verificar_token(req):
    token = req.args.get('hub.verify_token')
    challenge = req.args.get('hub.challenge')

    if challenge and token == TOKEN_OMICTECH:
        return challenge
    else:
        return jsonify({'ERROR': 'TOKEN INVALIDO'}), 401

def recibir_mensajes(req):
    data = req.get_json()
    
    if data:
        agregar_mensajes_log(data)
    
    return jsonify({'message': 'EVENT_RECEIVED'})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))  # Render asigna un puerto dinámico
    app.run(host='0.0.0.0', port=port, debug=True)
