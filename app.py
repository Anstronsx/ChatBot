import os
import json
from flask import Flask, request, jsonify, render_template
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import http.client

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
        return verificar_token(request)
    elif request.method == 'POST':
        return recibir_mensajes(request)

def verificar_token(req):
    token = req.args.get('hub.verify_token')
    challenge = req.args.get('hub.challenge')

    if challenge and token == TOKEN_OMICTECH:
        return challenge
    else:
        return jsonify({'ERROR': 'TOKEN INVALIDO'}), 401

def recibir_mensajes(req):
    try:
        data = req.get_json()
        
        if not data or "entry" not in data:
            return jsonify({'message': 'INVALID_REQUEST'}), 400
        
        entry = data['entry'][0]
        changes = entry.get('changes', [{}])[0]
        value = changes.get('value', {})
        objeto_mensaje = value.get('messages', [])

        if objeto_mensaje:
            messages = objeto_mensaje[0]
            if "type" in messages:
                tipo = messages["type"]

                if tipo == "interactive":
                    return jsonify({'message': 'INTERACTIVE_MESSAGE_IGNORED'})

                if "text" in messages:
                    text = messages["text"]["body"]
                    numero = messages["from"]
                    
                    enviar_mensajes_whatsapp(text, numero)

        return jsonify({'message': 'EVENT_RECEIVED'})

    except Exception as e:
        agregar_mensajes_log(f"ERROR: {str(e)}")
        return jsonify({'message': 'EVENT_RECEIVED'})

# Responder mensajes en WhatsApp
def enviar_mensajes_whatsapp(texto, number):
    texto = texto.lower()
    
    if "hola" in texto:
        mensaje = {
            "messaging_product": "whatsapp",    
            "recipient_type": "individual",
            "to": number,
            "type": "text",
            "text": {
                "preview_url": False,
                "body": "Hola, ¿Cómo estás? Bienvenido, soy Laura tu asistente."
            }
        }
    else:
        mensaje = {
            "messaging_product": "whatsapp",    
            "recipient_type": "individual",
            "to": number,
            "type": "text",
            "text": {
                "preview_url": False,
                "body": "Hola, visita nuestra web www.omictechglobal.com para más información. \n1. Escuelas especializadas \n2. Asesorías de tesis \n3. Análisis de datos \n4. Clases Particulares"
            }
        }

    # Convertir el diccionario a formato JSON
    data = json.dumps(data)

    headers = {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer EAA4tpFA6ORkBOyKtGNCuSvovZBe7G8O1JO8TqamPHSqiZBdFsZC2CK5P4gECKONLZC3WV5sr1HC467VzVtXkLw9LNAOmMBWQ8nyS0W0TuRVSUpvmiqXlKNc4ZBcVJJiiGSd1xM8cdpbtanXLoqhvRT8dxUc3BZCEokfCwCjNd2vuvBKskXT5fDUOlr7hFEtzERpkeayyENSLgAt2ysbxiUjhAT40MZD'
    }

    connection = http.client.HTTPSConnection("graph.facebook.com")

    try:
        connection.request("POST", "/v22.0/567813309755555/messages", data, headers)
        response = connection.getresponse()
        print(response.status, response.reason)

        if response.status != 200:
            agregar_mensajes_log(f"ERROR WhatsApp: {response.status} {response.reason}")

    except Exception as e:
        agregar_mensajes_log(f"ERROR en conexión: {str(e)}")

    finally:
        connection.close()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))  # Render asigna un puerto dinámico
    app.run(host='0.0.0.0', port=port, debug=True)
