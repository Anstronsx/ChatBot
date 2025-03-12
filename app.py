#Instalamos flask en nuestro entorno venv 
from flask import Flask, render_template 

app = Flask (__name__)

@app.route('/')
def hola_mundo():
    return render_template('holaflask.html')

if __name__== '__main__':
    app.run(host='0.0.0.0',port=80, debug=True)