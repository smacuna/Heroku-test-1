from flask import Flask, request, make_response, jsonify
from flask_cors import CORS, cross_origin
import subprocess
from libraries.corregir_lectura import compare_words
from libraries.filter_noise import filter_audio
from allosaurus.app import read_recognizer
import os
import shutil

# import noisereduce as nr

# Se prepara la app
UPLOAD_FOLDER = '/tmp'

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

cors = CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'

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

def evaluate(filename, target, word):
    '''
    Función para evaluar el rendimiento del audio ubicado en 'filename' comparándolo con el objetivo 'target'
    
    inputs:
        filename -> string con la ubicación del archivo a evaluar
        target -> lista de las letras de una pronunciación correcta de la palabra a evaluar
        ----> ej: target = ['e', 'x', 'e', 'm', 'p', 'l', 'o']
        word -> lista de las letras de la palabra a evaluar
        ----> ej: word = ['e', 'j', 'e', 'm', 'p', 'l', 'o']

    output:
        json:
        - 'warning': tipo de advertencia ('more': la palabra reconocida tiene más fonemas que el 'target'
                                          'less': la palabra reconocida tiene menos fonemas que el 'target')
        - 'warning_text': texto detallado de la advertencia
        - 'list': lista cuyos elementos son diccionarios que tienen la información relacionada a cada letra que se dijo
            ----> letra['color'] == 'green'  -> Letra fue bien dicha
                  letra['color'] == 'yellow' -> Letra no escuchada como la versión correcta / con errores mínimos
                  letra['color'] == 'red'    -> Letra mal dicha 
    '''
    a = model.recognize(filename, 'spa')
    lista_a = a.split(" ")

    b = model_2.recognize(filename, 'spa')
    lista_b = b.split(" ")

    c = model_3.recognize(filename, 'spa')
    lista_c = c.split(" ")

    d = model_4.recognize(filename, 'spa')
    lista_d = d.split(" ")

    e = model_5.recognize(filename, 'spa')
    lista_e = e.split(" ")

    f = model_6.recognize(filename, 'spa')
    lista_f = f.split(" ")

    # print(*target)
    # print(*lista_a)
    output = compare_words(target, lista_f, word, api=True, show=False, jsonif=False)
    output['model_original'] = lista_a
    output['model_spanish3'] = lista_b
    output['model_spanish8'] = lista_c
    output['model_spanish9'] = lista_d
    output['result_spanish9'] = compare_words(target, lista_d, word, api=True, show=False, jsonif=False)
    output['model_spanish10'] = lista_e
    output['model_spanish11'] = lista_f

    return jsonify(output)

def _build_cors_prelight_response():
    response = make_response()
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', '*')
    response.headers.add('Access-Control-Allow-Methods', '*')
    return response

# A continuación se hacen las rutas
@app.route('/')
def home():
    return '<h1>Hola gente!</h1>'

@cross_origin
@app.route('/upload', methods=['GET', 'POST', 'OPTIONS'])
def upload():
    if request.method == 'OPTIONS':  # CORS prelight
        print('Options!')
        return _build_cors_prelight_response()
    elif request.method == 'POST':
        print('Post!')
        byte_data = bytes(request.json['audio'])
        # Guardar datos en archivo webm
        webm_path, tempDir = save_to_webm(byte_data, 'test')
        # Convertir webm a wav
        wav_path = convert_webm_to_wav(webm_path)
        # Filtrar audio (descomentar la siguiente línea si se quiere filtrar el audio antes de procesar)
        # wav_path = filter_audio(wav_path)
        target = request.json['target'].split(" ")
        word = list(request.json['word'])
        # Evaluar resultado
        return evaluate(wav_path, target, word)


# La función a continuación (test_speed) tenía el propósito de encontrar cuánto tiempo se demora en encontrar los resultados
#   sin embargo, no se alcanzó a desarrollar 
'''
@cross_origin
@app.route('/test_speed', methods=['GET', 'POST', 'OPTIONS'])
def test_speed():
    if request.method == 'OPTIONS':  # CORS prelight
        print('Options!')
        return _build_cors_prelight_response()
    elif request.method == 'POST':
        print('Post!')
        # byte_data = bytes(request.json['audio'])
        # webm_path, tempDir = save_to_webm(byte_data, 'test')
        # wav_path = convert_webm_to_wav(webm_path)
        target = request.json['target'].split(" ")
        word = list(request.json['word'])
        result = request.json['result'].split(" ")
        # return evaluate(wav_path, target)
        return jsonify(compare_words(target, result, word, api=True, show=False, jsonif=False))
'''

# Se cargan los modelos
model = read_recognizer()

src = 'models/spanish3'
dst = '/usr/local/lib/python3.8/site-packages/allosaurus/pretrained'
shutil.move(src, dst)

model_2 = read_recognizer('spanish3')

src = 'models/spanish8'
dst = '/usr/local/lib/python3.8/site-packages/allosaurus/pretrained'
shutil.move(src, dst)
model_3 = read_recognizer('spanish8')

src = 'models/spanish9'
dst = '/usr/local/lib/python3.8/site-packages/allosaurus/pretrained'
shutil.move(src, dst)
model_4 = read_recognizer('spanish9')

src = 'models/spanish10'
dst = '/usr/local/lib/python3.8/site-packages/allosaurus/pretrained'
shutil.move(src, dst)
model_5 = read_recognizer('spanish10')

src = 'models/spanish11'
dst = '/usr/local/lib/python3.8/site-packages/allosaurus/pretrained'
shutil.move(src, dst)
model_6 = read_recognizer('spanish11')

# Se corre la app
app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
