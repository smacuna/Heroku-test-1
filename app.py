from flask import Flask, request
import os

app = Flask(__name__)

@app.route('/')
def home():
    return '<h1>Hola gente!</h1>'

app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))