from flask import Flask, request
from flask_cors import CORS  
import subprocess
from libraries.corregir_lectura import evaluar_desempeno
from allosaurus.app import read_recognizer
import os

UPLOAD_FOLDER = '/tmp'

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

CORS(app)


def save_to_webm(audio_data, filename):
    '''
    Función para guardar data en bytes ('audio_data') en un archivo .webm

    inputs:
        audio_data -> bytesarray de información del audio a guardar
        filename   -> string del nombre para poner al archivo del audio a guardar

    outputs:
        webm_path -> ubicación en string del archivo guardado
        tempDir   -> directorio en string donde está guardado el archivo
    '''
    # Basado en pregunta en https://stackoverflow.com/questions/66931280/how-to-use-bytes-instead-of-file-path-in-ffmpeg
    mainDir = os.path.dirname(__file__)
    tempDir = os.path.join(mainDir, 'temp')
    webm_path = os.path.join(tempDir, f'{filename}.webm')
    with open(webm_path, 'wb') as f:
        f.write(audio_data)
    return webm_path, tempDir

def convert_webm_to_wav(file):
    '''
    Función para obtener audio de archivos webm, exportándolos como wav
    
    input:
        file -> string con la ubicación del archivo a convertir
    
    output:
        wav_path -> string con la ubicación del archivo convertido
    '''
    # Basado en pregunta en https://stackoverflow.com/questions/62064665/coverting-webm-to-wav-with-ffmpeg
    wav_path = f'{file[:-5]}.wav'
    command = ['ffmpeg', '-y', '-i', file, '-acodec', 'pcm_s16le', '-ac', '1', '-ar', '16000', wav_path]
    subprocess.run(command,stdout=subprocess.PIPE,stdin=subprocess.PIPE)
    return wav_path

def evaluate(filename, target):
    '''
    Función para evaluar el rendimiento del audio ubicado en 'filename' comparándolo con el objetivo 'target'
    
    inputs:
        filename -> string con la ubicación del archivo a evaluar
        target -> lista de las letras de una pronunciación correcta de la palabra a evaluar
        ----> ej: target = ['e', 'x', 'e', 'm', 'p', 'l', 'o']

    output:
        json: lista cuyos elementos son diccionarios que tienen la información relacionada a cada letra que se dijo
        ----> letra['color'] == 'green'  -> Letra fue bien dicha
              letra['color'] == 'yellow' -> Letra no escuchada como la versión correcta / con errores mínimos
              letra['color'] == 'red'    -> Letra mal dicha 
    '''
    a = model.recognize(filename, 'spa')
    lista_a = a.split(" ")
    print(*target)
    print(*lista_a)
    return evaluar_desempeno(target, lista_a, api=True)


@app.route('/')
def home():
    return '<h1>Hola gente!</h1>'

@app.route('/upload', methods=['GET', 'POST'])
def upload():
    byte_data = bytes(request.json['audio'])
    webm_path, tempDir = save_to_webm(byte_data, 'test')
    wav_path = convert_webm_to_wav(webm_path)
    # target = 'e s t e s u n k o ð i ɡ o ð e x e m p l o'.split(" ")
    target = request.json['target'].split(" ")
    return evaluate(wav_path, target)


model = read_recognizer()
app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
