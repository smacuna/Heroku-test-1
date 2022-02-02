from allosaurus.app import read_recognizer
import random
import json
from flask import jsonify

class bcolors:
    MORADO = '\033[95m'
    AZUL = '\033[94m'
    CYAN = '\033[96m'
    VERDE = '\033[92m'
    AMARILLO = '\033[93m'
    ROJO = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

colores = [bcolors.MORADO, bcolors.AZUL, bcolors.CYAN, bcolors.VERDE, bcolors.AMARILLO, bcolors.ROJO]

sim_letters = {
    'a': {'a', 'æ'}, 
    'æ': {'æ', 'ɛ', 'a', 'e'}, 
    'β': {'β', 'b'}, 
    'b': {'β', 'b'}, 
    'ʃ': {'ʃ', 't͡ʃ'}, 
    't͡ʃ': {'ʃ', 't͡ʃ'}, 
    'ɛ': {'ɛ', 'e', 'æ'}, 
    'e': {'ɛ', 'e', 'æ'}, 
    'i': {'i', 'ʝ', 'j', 'ʤ'}, 
    'j': {'i', 'ʝ', 'j', 'ʤ'}, 
    'ɡ': {'ɡ', 'ɣ'}, 
    'ɣ': {'ɡ', 'ɣ'}, 
    'l̪': {'l̪', 'l'}, 
    'l': {'l̪', 'l'}, 
    'ɔ': {'ɔ', 'o'}, 
    'o': {'ɔ', 'o'}, 
    's': {'s', 's̪'}, 
    's̪': {'s', 's̪'}, 
    't̪': {'t̪', 't'}, 
    't': {'t̪', 't'}, 
    'ʤ': {'ʤ', 'ʝ', 'i', 'j'}, 
    'ʝ': {'ʤ', 'ʝ', 'i', 'j'}
}

class Letra:
    def __init__(self, letra, color) -> None:
        self.letra = letra
        self.color = color
    
    def convertir(self):
        return f"{self.color}{self.letra}"

    def __str__(self):
        return f"{self.color}{self.letra}{bcolors.ENDC}"


class Parte:
    def __init__(self, indice, lista=[], color='1') -> None:
        self.indice = indice
        self.lista = lista
        self.color = color
    
    def append(self, item):
        self.lista.append(item)

    def __getitem__(self, i):
        return self.lista[i]

    def __str__(self) -> str:
        string = f'indice: {self.indice} -> lista: ['
        for item in self.lista:
            string += f'{str(item)}, '
        string = string[:-2] + ']'
        return string


class Partes:
    def __init__(self) -> None:
        self.lista = []
        self.color_actual = '0'
        self.indice_actual = -1

    def agregar_letra(self, letra):
        color = letra.color
        if color == self.color_actual:
            self.lista[-1].append(letra)
        else:
            self.indice_actual += 1
            self.color_actual = color
            parte = Parte(self.indice_actual, lista=[letra], color=color)
            self.lista.append(parte)

    def __iter__(self):
        self._n = -1
        return self

    def __next__(self):
        self._n += 1
        if self._n >= len(self.lista):
            raise StopIteration
        return self.lista[self._n]

    def __getitem__(self, i):
        return self.lista[i]

    
    def __str__(self) -> str:
        string = f'['
        for item in self.lista:
            string += f'{item},\n '
        string = string[:-3] + ']'
        return string
    
    def __len__(self):
        return len(self.hacer_lista())
    
    @property
    def cantidad_letras(self):
        cantidad = 0
        for parte in self.lista:
            cantidad += len(parte.lista)
        return cantidad

    def hacer_lista(self):
        lista = []
        for parte in self.lista:
            for letra in parte.lista:
                lista.append(letra)
        return lista


def obtener_partes(lista_a, original):
    letras = []
    partes_res = Partes()
    partes_or = Partes()
    for i, letra in enumerate(lista_a):
        if i >= len(original):
            color = bcolors.ROJO
        else:
            if letra == original[i]:
                color = bcolors.VERDE
            else:
                color = bcolors.ROJO

        clase_letra = Letra(letra, color)
        letras.append(clase_letra)
        partes_res.agregar_letra(clase_letra)

        if i < len(original):
            letra_original = Letra(original[i], color)
            partes_or.agregar_letra(letra_original)

    return partes_res, partes_or

def formar_listas(parte):
    lista = []
    for letra in parte:
        lista += letra.letra
    
    return lista

def contar_color(res, color):
    suma = 0
    for parte in res:
        if parte.color == color:
            suma += len(parte.lista)
    return suma

def contar_verdes(res):
    # suma = 0
    # for i, parte in enumerate(res):
    #     if parte.color == bcolors.VERDE:
    #         suma += len(parte.lista)
    suma = contar_color(res, bcolors.VERDE)
    return suma

def obtener_porcentaje(partes):
    largo = len(partes)
    lista = partes.hacer_lista()
    suma = 0

    # Verdes suman 1
    verdes = [item for item in lista if item.color == bcolors.VERDE]
    suma += len(verdes)

     # Amarillos suman 0.5
    amarillos = [item for item in lista if item.color == bcolors.AMARILLO]
    suma += 0.5*len(amarillos)

    porcentaje = suma/largo
    return porcentaje


def formato_api(partes):
    lista = []
    colores_letras = {
        bcolors.VERDE: 'green',
        bcolors.AMARILLO: 'yellow',
        bcolors.ROJO: 'red'
    }
    i = 0
    for parte in partes:
        for letra in parte:
            lista.append({
                'id'    : i,
                'letter': letra.letra,
                'color' : colores_letras[letra.color],
            })
            i += 1
    # return jsonify(lista)
    return lista

def evaluar_desempeno(original, grabacion, show=True, api=False, lista_b=False, lista_c=False):
    partes_res, partes_or = obtener_partes(grabacion, original)
    # print(partes_res)
    # print(partes_or)

    for i, parte in enumerate(partes_res):
        if parte.color == bcolors.ROJO:
            if len(parte.lista) == 1:
                letra = parte.lista[0]
                letra.color = bcolors.AMARILLO
                # if i - 1 >= 0:
                #     if partes_or.lista[i-1].lista[-1].letra == letra.letra:
                #         letra.color = bcolors.AMARILLO
                # if i + 1 < len(partes_or.lista):
                #     if partes_or.lista[i+1].lista[0].letra == letra.letra:
                # 
                #         letra.color = bcolors.AMARILLO
            
            if i == len(partes_res.lista) - 1 and i < len(partes_or.lista):  # No hay más verdes al lado derecho
                # Subseparar el problema
                # print(partes_or[i])
                lista_or = formar_listas(partes_or[i])

                # print(partes_res[i])
                lista_res = formar_listas(partes_res[i])

                res_izquierda, _ = obtener_partes([0, *lista_res], lista_or)
                res_derecha, _ = obtener_partes(lista_res[1:], lista_or)

                if contar_verdes(res_izquierda) > contar_verdes(res_derecha):  # Pintar amarillo las verdes
                    # print("Nos quedamos con res izquierda")
                    # print(*res_izquierda.hacer_lista())
                    for j, letra in enumerate(res_izquierda.hacer_lista()):
                        if j > 0:
                            if letra.color == bcolors.VERDE:
                                partes_res.lista[i].lista[j-1].color = bcolors.AMARILLO
                else:  # Dejar verdes las verdes y pintar amarillo las rojas que interfieren
                    # print("Nos quedamos con res derecha")
                    for k, parte in enumerate(res_derecha):
                        if parte.color == bcolors.VERDE and k - 1 >= 0:
                            if res_derecha.lista[k-1].color == bcolors.ROJO and len(res_derecha.lista[k-1].lista) <= 2:
                                for j, _ in enumerate(res_derecha.lista[k-1]):
                                    res_derecha.lista[k-1].lista[j].color = bcolors.AMARILLO

                    j = 0
                    for k, parte in enumerate(res_derecha):
                        for letra in parte.lista:
                            if letra.color == bcolors.VERDE:
                                partes_res.lista[i].lista[j+1].color = bcolors.VERDE
                                if partes_res.lista[i].lista[j].color == bcolors.ROJO:
                                    partes_res.lista[i].lista[j].color = bcolors.AMARILLO
                            elif letra.color == bcolors.AMARILLO:
                                partes_res.lista[i].lista[j+1].color = bcolors.AMARILLO
                                if partes_res.lista[i].lista[j].color == bcolors.ROJO:
                                    partes_res.lista[i].lista[j].color = bcolors.AMARILLO
                            j += 1
                        
    # print(res_izquierda, contar_verdes(res_izquierda))
    # print(res_derecha, contar_verdes(res_derecha))

    lista = partes_res.hacer_lista()

    if show:
        print(obtener_porcentaje(partes_res))

    if api:
        lista = formato_api(partes_res)
        score = obtener_porcentaje(partes_res)
        output_json = {'letters-list': lista, 'score': score}
        if lista_b:
            output_json['model_spanish3'] = lista_b
            output_json['model_status'] = 'ok'
        if lista_c:
            output_json['model_spanish8'] = lista_c
        return jsonify(output_json)

    return lista


class Letter:
    def __init__(self, letter, color=bcolors.ROJO, result_index=-1):
        self.letter = letter
        self.color = color
        self.result_index = result_index
    
    def __str__(self):
        return f"{self.color}{self.letter}{bcolors.ENDC}"
    
    def __repr__(self):
        return f"{self.color}{self.letter}{bcolors.ENDC}"


def compare(target, result, original):
    # Esta función está hecha para el idioma español
    ignorable = set()  # Este set es para índices de palabras (i) que deben ser ignoradas
    i_target = 0
    j_result_start = 0
    j_result = 0
    output_list = []
    first = True

    warning_more =  len(result) > len(target)
    warning_less =  len(result) < len(target)

    last_h = False

    for i, letter in enumerate(original):
        

        if i in ignorable:  # Si el índice (i) está en 'ignorable', se debe continuar al nuevo ciclo
            if i - 1 >= 0:
                output_list.append(Letter(letter, output_list[-1].color))
            continue

        if letter == 'q':  # Se deben manejar los casos 'que' y 'qui' ('ke' y 'ki')
            if i + 1 < len(original) and i + 2 < len(original):
                if original[i+1] == 'u' and (original[i+2] == 'e' or original[i+2] == 'i'):
                    ignorable.add(i+1)
        elif letter == 'g':  # Se deben manejar los casos 'gue' y 'gui' ('ɡe' y 'ɡi')
            if i + 1 < len(original) and i + 2 < len(original):
                if original[i+1] == 'u' and (original[i+2] == 'e' or original[i+2] == 'i'):
                    ignorable.add(i+1)
        elif letter == 'r':  # Se debe manejar el caso de la 'rr'
            if i + 1 < len(original):
                if original[i+1] == 'r':
                    ignorable.add(i+1)
        elif letter == 'l':  # Se debe manejar el caso de la 'll'
            if i + 1 < len(original):
                if original[i+1] == 'l':
                    ignorable.add(i+1)
        # elif letter == 'ch':  # Se debe manejar el caso de la 'ch'
        elif letter == 'c':  # Se debe manejar el caso de la 'ch' y de la 'cc'
            if i + 1 < len(original):
                if original[i+1] == 'h' or original[i+1] == 'c':
                    ignorable.add(i+1)
        elif letter == 's':  # Se debe manejar el caso de la 'sh' (ejemplo: sushi)
            if i + 1 < len(original):
                if original[i+1] == 'h':
                    ignorable.add(i+1)

        if letter == 'h':  # Se debe manejar el caso de la 'h' muda
            # Si se entró acá, significa que no viene de una 'ch' ni de una 'sh'
            # En este caso, se debe ignorar directamente
            last_h = True
            continue
        
        found = False
        tolerance = 3  # Este número indica el grado de tolerancia de letras entremedio de letras correctas
        last_j = j_result + tolerance
        if first:
            last_j = len(result)
        
        for j in range(j_result, last_j):  # Desde que empieza la palabra restante en 'result' hasta lo que indica 'last_j'
            if j < len(result):
                r_phone = result[j]
                # print(f'{letter}: j = {j} -> r_phone = {r_phone}')
                if r_phone in sim_letters:
                    if target[i_target] in sim_letters[r_phone]:
                        found = True
                        j_result = j + 1
                        if first:  # Si es la primera letra
                            first = False
                            j_result_start = j
                        break 
                elif r_phone == target[i_target]:  # Si encontramos el fonema actual 'i_target'
                    found = True
                    j_result = j + 1
                    if first:  # Si es la primera letra
                        first = False
                        j_result_start = j
                    break
            else:
                break
            
        if not found:  # Si no se encontró el fonema correspondiente a la letra actual
            if last_h:
                output_list.append(Letter(original[i-1], bcolors.ROJO))
                last_h = False
            output_list.append(Letter(letter, bcolors.ROJO))


        else:  # Si se encontró
            if last_h:
                output_list.append(Letter(original[i-1], bcolors.VERDE))
                last_h = False
            output_list.append(Letter(letter, bcolors.VERDE, result_index=j_result-1))

        i_target += 1

    last_green = -10
    next_green = -100
    # last_green_index = -10
    # last_was_green = False
    for o_i, output_letter in enumerate(output_list):
        if output_letter.color == bcolors.ROJO:
            if o_i + 1 < len(output_list):
                for next_i, next_letter in enumerate(output_list[o_i+1:]):
                    if next_letter.color == bcolors.VERDE:
                        next_green = next_letter.result_index
                        # print(last_green, next_green)
                        break
                if last_green + tolerance <= next_green:  # El 2 aquí tambien marca un grado de tolerancia
                    output_list[o_i].color = bcolors.AMARILLO
            # last_was_green = False
        elif output_letter.color == bcolors.VERDE:
            # Si es que entre dos verdes hay fonemas en result, los colores de las letras que lo rodean deben ser amarillo
            
            
            # if last_was_green:
            #     if last_green + 1 != output_letter.result_index:
                    # output_list[last_green_index].color = bcolors.AMARILLO
            #         output_list[o_i].color = bcolors.AMARILLO
            # last_green_index = o_i
            # last_was_green = True

            last_green = output_letter.result_index

    return output_list

def score_results(letters_list):
    length = len(letters_list)
    suma = 0

    # Verdes suman 1
    greens = [letter for letter in letters_list if letter.color == bcolors.VERDE]
    suma += len(greens)

     # Amarillos suman 0.5
    yellows = [letter for letter in letters_list if letter.color == bcolors.AMARILLO]
    suma += 0.5*len(yellows)

    score = suma/length
    return score


def api_format(letters_list, warning='', warning_text='', jsonif=False):
    json_dict = {
        'warning': warning, 
        'warning_text': warning_text
    }
    json_list = []
    letter_colors = {
        bcolors.VERDE: 'green',
        bcolors.AMARILLO: 'yellow',
        bcolors.ROJO: 'red'
    }
    i = 0
    for i, letter in enumerate(letters_list):
        json_list.append({
            'id'    : i,
            'letter': letter.letter,
            'color' : letter_colors[letter.color],
        })
    json_dict['letters-list'] = json_list
    json_dict['score'] = score_results(letters_list)
    if jsonif:
        return jsonify(json_dict)
    return json_dict

def compare_words(target, result, original, api=False, show=False, jsonif=False):

    output_list = compare(target, result, original)
    
    warning = ''
    warning_text = ''
    if len(result) > len(target):
        warning = 'more'
        warning_text = f'Result has more phonemes than target (len(result) = {len(result)} > len(target) = {len(target)})'
    elif len(result) < len(target):
        warning = 'less'
        warning_text = f'Result has less phonemes than target (len(result) = {len(result)} < len(target) = {len(target)})'

    if show:
        if warning_text != '':
            print(f"{bcolors.MORADO}{warning_text}{bcolors.ENDC}")
        print(*output_list)
        
    if api:
        return api_format(output_list, warning=warning, warning_text=warning_text, jsonif=jsonif)

    return output_list


if __name__ == '__main__':

    model = read_recognizer()
    
    # original = 'c ó m o d o'.split(' ')
    # target   = 'k o m o ð o'.split(' ')
    # result   = 'k o m o s o'.split(' ')

    original = 'c h a n c h o'.split(' ')
    target   = 'ʃ a n ʃ o'.split(' ')
    result   = 'a s g k h f h ʃ a n a a n ʃ o s o p'.split(' ')

    # print(*compare(target, result, original))
    output_list = compare_words(target, result, original, api=False, show=True)

    original = 'q u i q u e'.split(' ')
    target   = 'k i k e'.split(' ')
    result   = 'k i k e'.split(' ')

    output_list = compare_words(target, result, original, api=False, show=True)

    original = 'p r ó x i m o'.split(' ')
    target   = 'p ɾ o ks i m o'.split(' ')
    result   = 'p ɾ o ks i m o'.split(' ')

    output_list = compare_words(target, result, original, api=False, show=True)

    original = 'a c c i ó n'.split(' ')
    target   = 'a ks i o n'.split(' ')
    result   = 'a ks i o n'.split(' ')

    output_list = compare_words(target, result, original, api=False, show=True)


    original = 'g u i t a r r a'.split(' ')
    target   = 'ɡ i t a r a'.split(' ')
    result   = 'ɡ i t a a'.split(' ')

    output_list = compare_words(target, result, original, api=False, show=True)


    original = 'h a l l a r'.split(' ')
    target   = 'a y a ɾ'.split(' ')
    result   = 'a y a ɾ'.split(' ')

    output_list = compare_words(target, result, original, api=False, show=True)

    original = list('guitarra')
    print(original)
    target   = 'ɡ i t a r a'.split(' ')
    result   = 'ɡ i t a t l a'.split(' ')
    print(compare_words(target, result, original, api=True, show=True))
    # print(compare_words(target, result, original, api=True, show=True, jsonif=True))

    
    '''
    # a = model.recognize('audio_ejemplos/codigodeejemplo.wav', 'spa')
    #print(*a.split(" "))

    # lista_a = a.split(" ")

    lista_a = 'e s t e s u n k o ð i ɡ o ð e x i m l o t e'.split(" ")
    original = 'e s t e s u n k o ð i ɡ o ð e x e m p l o'.split(" ")
    # letras = comparar_resultado('e s t e s u n k o ð i ɡ o ð e x e m p l o'.split(" "), a.split(" "), show=True)

    print(*original)
    print(evaluar_desempeno(original, lista_a, api=True))
    '''
    