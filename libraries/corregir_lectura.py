from allosaurus.app import read_recognizer
import random
from flask import json, jsonify

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
    return jsonify(lista)


def evaluar_desempeno(original, grabacion, show=True, api=False):
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
            
            if i == len(partes_res.lista) - 1:  # No hay más verdes al lado derecho
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
        return output_json

    return lista


if __name__ == '__main__':
    print("hola")

    model = read_recognizer()

    a = model.recognize('audio_ejemplos/codigodeejemplo.wav', 'spa')
    #print(*a.split(" "))

    lista_a = a.split(" ")

    # lista_a = 'e s t e s u n k o ð i ɡ o ð e x i m l o t e'.split(" ")
    original = 'e s t e s u n k o ð i ɡ o ð e x e m p l o'.split(" ")
    # letras = comparar_resultado('e s t e s u n k o ð i ɡ o ð e x e m p l o'.split(" "), a.split(" "), show=True)

    print(*original)
    print(*evaluar_desempeno(original, lista_a))