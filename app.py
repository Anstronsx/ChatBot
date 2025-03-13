import os
import json
from flask import Flask, request, jsonify, render_template
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import http.client

app = Flask(__name__)

# Configuración de la base de datos
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///metapython.db")
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://")

app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URL
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

class Log(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    fecha_y_hora = db.Column(db.DateTime, default=datetime.utcnow)
    texto = db.Column(db.Text, nullable=False)

with app.app_context():
    db.create_all()

def ordenar_por_fecha_y_hora(registros):
    return sorted(registros, key=lambda x: x.fecha_y_hora or datetime.min, reverse=True)

@app.route('/')
def index():
    registros = Log.query.all()
    registros_ordenados = ordenar_por_fecha_y_hora(registros)
    return render_template('index.html', registros=registros_ordenados)

def agregar_mensajes_log(texto):
    if isinstance(texto, dict):
        texto = json.dumps(texto)
    nuevo_registro = Log(texto=texto)
    db.session.add(nuevo_registro)
    db.session.commit()

TOKEN_OMICTECH = "OMICTECH"

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
                    text = messages["text"]["body"].lower()
                    numero = messages["from"]
                    enviar_mensajes_whatsapp(text, numero)

        return jsonify({'message': 'EVENT_RECEIVED'})
    except Exception as e:
        agregar_mensajes_log(f"ERROR: {str(e)}")
        return jsonify({'message': 'EVENT_RECEIVED'})

def enviar_mensajes_whatsapp(texto, number):
    data = {
        "messaging_product": "whatsapp",    
        "recipient_type": "individual",
        "to": number,
        "type": "text",
        "text": {
            "preview_url": False,
            "body": "Hola, visita nuestra web www.omictechglobal.com para más información.\n1. Escuelas especializadas \n2. Asesorías de tesis \n3. Análisis de datos \n4. Clases Particulares"
        }
    }

    if "hola" in texto:
        data["text"]["body"] = "Hola, ¿Cómo estás? Bienvenido, soy Laura tu asistente."
    elif "1" in texto:
        data["text"]["body"] = "Tenemos diferentes Escuelas: Automatización, Acuicultura de Precisión, Agricultura de Precisión."
    elif "2" in texto:
        data["text"]["body"] = "Ofrecemos asesorías en tesis, metagenómica y procesos de producción."
    elif "3" in texto:
        data = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": number,
            "type": "document",
            "document": {
                "link": "https://www.turnerlibros.com/wp-content/uploads/2021/02/ejemplo.pdf",
                "caption": "Este es nuestro catálogo de cursos #001"
            }
        }

    headers = {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer EAA4tpFA6ORkBOyKtGNCuSvovZBe7G8O1JO8TqamPHSqiZBdFsZC2CK5P4gECKONLZC3WV5sr1HC467VzVtXkLw9LNAOmMBWQ8nyS0W0TuRVSUpvmiqXlKNc4ZBcVJJiiGSd1xM8cdpbtanXLoqhvRT8dxUc3BZCEokfCwCjNd2vuvBKskXT5fDUOlr7hFEtzERpkeayyENSLgAt2ysbxiUjhAT40MZD'
    }

    connection = http.client.HTTPSConnection("graph.facebook.com")
    try:
        connection.request("POST", "/v22.0/567813309755555/messages", json.dumps(data), headers)
        response = connection.getresponse()
        if response.status != 200:
            agregar_mensajes_log(f"ERROR WhatsApp: {response.status} {response.reason}")
    except Exception as e:
        agregar_mensajes_log(f"ERROR en conexión: {str(e)}")
    finally:
        connection.close()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
