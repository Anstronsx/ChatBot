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

    
    try:
        req = request.get_json()
        entry =req['entry'][0]
        changes = entry['changes'][0]
        value = changes['value']
        objeto_mensaje = value ['messages']

        if objeto_mensaje:
            messages = objeto_mensaje[0]

            if "type" in messages:
                tipo = messages["type"]

                if tipo == "interactive":
                    return 0
                
                if "text" in messages:
                    text = messages["text"] ["body"]
                    numero = messages["from"]
                    enviar_mensajes_whatsapp(text, numero)
                    

        return jsonify({'message': 'EVENT_RECEIVED'})
    except Exception as e:
        return jsonify({'message': 'EVENT_RECEIVED'})

#Responder mensajes en Whatsapp
def enviar_mensajes_whatsapp (texto, number):
    texto = texto.lower()

    if "Hola" in texto:
        data={
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
        data={
            "messaging_product": "whatsapp",    
            "recipient_type": "individual",
            "to": number,
            "type": "text",
            "text": {
                "preview_url": False,
                "body": "Hola, visita nuestra web www.omictechglobal.com para mas información. \n 1. Escuelas especializadas \n 2. Asesorias de tesis \n 3. Analisis de datos \n 4. Clases Particulares"
                }
            }
        #Convetir el diccionario a formato JSON
        data=json.dumps(data)


        headers = {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer EAA4tpFA6ORkBO0opGrm2sZBrUCwKf0hn5glFEZAMLyxAiyNSesBHeKBEedSGGR01OOJKPSaLskC6zf7887PumZAUFTMZBpkx29eBKodtjRUoSMyAZA7hF0vfyuxRvHopjZAck74ls7UkeSyBZACPtlNt4oNqErgeQqpaaeR2tjIAoJI6DdtL3hZAG7LzdSjJZAoWMUeaJs1iuk1idoAghjA9KcC3ZAYjii'

        }

        connection = http.client.HTTPConnection("graph.facebook.com")

        try:
            connection.request("POST", "/v22.0/567813309755555/messages", data, headers)
            response = connection.getresponse()
            print(response.status, response.reason)

        except Exception as e:
            agregar_mensajes_log(json.dumps(e))

        finally: 
            connection.close()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))  # Render asigna un puerto dinámico
    app.run(host='0.0.0.0', port=port, debug=True)
