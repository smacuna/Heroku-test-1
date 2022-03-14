# Importar librerías
from allosaurus.app import read_recognizer
import random
import json
from click import pass_context
from flask import jsonify

# Definir colores. Si bien, parte del código se hizo utilizando esta definición, se puede reemplazar.
# Esta definición de colores fue hecha para poder imprimir en consola con colores (en Linux).
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

# Lista de colores
# colores = [bcolors.MORADO, bcolors.AZUL, bcolors.CYAN, bcolors.VERDE, bcolors.AMARILLO, bcolors.ROJO]

# Este diccionario permite asignar fonemas similares. Esto se debe a que allosaurus diferencia fonemas
#  que en español se podrían considerar como el mismo. Ejemplo: las pronunciaciones distintas de la 'ch'
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


# Clase para manejar las características de las letras, en adición a métodos para poder imprimir en consola.
class Letter:
    def __init__(self, letter, color=bcolors.ROJO, target_index=-1, result_index=-1):
        self.letter = letter
        self.color = color
        self.target_index = target_index
        self.result_index = result_index
        self.status = ''
    
    # Solo para debuggear con prints
    def __str__(self):
        return f"{self.color}{self.letter}{bcolors.ENDC}"
    
    def __repr__(self):
        return f"{self.color}{self.letter}{bcolors.ENDC}"


def analyze_comparison(target, result, original, tolerance=3):
    '''
    Función para realizar una comparación entre un fonema objetivo (target) y el resultado 
        de la lectura de un audio (result)

    inputs:
        * target -> lista de strings de los fonemas objetivos a evaluar
        ----> ej: target = ['ʃ', 'a', 'n', 'ʃ', 'o']  # Para la palabra 'chancho'
        * result -> lista de strings de los fonemas obtenidos al analizar audio con allosaurus
        ----> ej: result = ['ʃ', 'a', 'm', 'k', 'o']  # Para la palabra 'chancho' leída como 'chamco'
        * original -> lista de strings de las letras que conforman la palabra a evaluar
        ----> ej: original = ['c', 'h', 'a', 'n', 'c', 'h', 'o']  # Para la palabra 'chancho'
        * tolerance -> int que indica la tolerancia que se le dará al programa para permitir la separación
          máxima entre fonemas de 'result' para seguir considerando como correcta la letra. Se recomienda
          utilizar valores entre 1 y 3. Por defecto se deja como 3.

    output:
        * output_list -> lista de objetos 'Letter' correspondientes a las letras de la palabra original 'original'
           con sus respectivos colores y estados.

    Esta función realiza hartas cosas a la vez y puede ser poco intuitivo el método utilizado.
    * Hay espacio aún para optimizar el método.
    '''

    # Preparación de variables
    ignorable = set()  # Este set contendrá los índices de letras (i) que deben ser ignoradas
    i_target = 0       # índice actual de la lista 'target'
    j_result = 0       # índice actual de la lista 'result'
    output_list = []   # lista de Letter que se formará para finalmente retornar
    first = True       # boolean que es True si es que no se han encontrado fonemas correctos aún
    last_h = False     # boolean que es True si es que la letra anterior a la que se está analizando es una letra 'h'

    # -------------------------------------------------------------------------------------------------
    # Se recorrerán las letras de la palabra original para luego determinar si es que se marcan 
    #   como verdes (se encontró el fonema correspondiente en el audio) o se marcan
    #   como rojas (no se encontró el fonema correspondiente en el audio)
    # En este loop, también se obtendrá el índice 'i' de la letra en cuestión
    for i, letter in enumerate(original):  
        if i in ignorable:  # Si el índice (i) está en 'ignorable', se debe continuar a la siguiente letra
            if i - 1 >= 0:  # Si ya se asignó un color a la letra anterior y esta debe ser ignorada:
                # Entonces a esta letra se le debe asignar el mismo color
                output_list.append(Letter(letter, output_list[-1].color)) 
            continue  # Se continua al siguiente ciclo del for

        if letter == 'q':  # Se deben manejar los casos 'que' y 'qui' ('ke' y 'ki')
            if i + 1 < len(original) and i + 2 < len(original):
                if original[i+1] == 'u' and (
                    original[i+2] == 'e' or original[i+2] == 'i' or original[i+2] == 'é' or original[i+2] == 'í'):
                    ignorable.add(i+1)  # Si se cumple con este caso, la siguiente letra 'u' se debe ignorar
        elif letter == 'g':  # Se deben manejar los casos 'gue' y 'gui' ('ɡe' y 'ɡi')
            if i + 1 < len(original) and i + 2 < len(original):
                if original[i+1] == 'u' and (
                    original[i+2] == 'e' or original[i+2] == 'i' or original[i+2] == 'é' or original[i+2] == 'í'):
                    ignorable.add(i+1)  # Si se cumple con este caso, la siguiente letra 'u' se debe ignorar
        elif letter == 'r':  # Se debe manejar el caso de la 'rr'
            if i + 1 < len(original):
                if original[i+1] == 'r':
                    ignorable.add(i+1)  # Si se cumple con este caso, la siguiente letra 'r' se debe ignorar
        elif letter == 'l':  # Se debe manejar el caso de la 'll'
            if i + 1 < len(original):
                if original[i+1] == 'l':
                    ignorable.add(i+1)  # Si se cumple con este caso, la siguiente letra 'l' se debe ignorar
        elif letter == 'c':  # Se debe manejar el caso de la 'ch' y de la 'cc'
            if i + 1 < len(original):
                if original[i+1] == 'h' or original[i+1] == 'c':
                    ignorable.add(i+1)  # Si se cumple con este caso, la siguiente letra ('h' o 'c') se debe ignorar
        elif letter == 's':  # Se debe manejar el caso de la 'sh' (ejemplo: sushi)
            if i + 1 < len(original):
                if original[i+1] == 'h':
                    ignorable.add(i+1)  # Si se cumple con este caso, la siguiente letra 'hs' se debe ignorar

        if letter == 'h':  # Se debe manejar el caso de la 'h' muda
            # Si se entró acá, significa que no viene de una 'ch' ni de una 'sh' (en ese caso se habría ignorado)
            # En este caso, se debe ignorar esta letra directamente
            last_h = True   # Se indica que se encontró una 'h'
            # Cuando se le asigne color a la siguiente letra, se le asignará el mismo color a la 'h'
            #     se asume que ninguna palabra termina en 'h'
            continue  # Se ignora esta letra
        
        # ---------------------------------------------------------------------------------------------
        ## En esta parte se busca el i-ésimo fonema del objetivo 'target' -----------------------------

        found = False  # boolean que indica si es que el fonema correspondiente a la letra actual está en 'result' (lo que se dijo)
        last_j = j_result + tolerance  # último índice j (índice de 'result') que se revisará + 1
        if first:  # Si es que aún no se han encontrado fonemas correctos,
            last_j = len(result)  # se revisarán todos los fonemas en 'result' (los que se dijeron)

        for j in range(j_result, last_j):  # Desde que empieza la palabra restante en 'result' hasta lo que indica 'last_j'
            if j < len(result):  # Si es que el índice 'j' está dentro del rango evaluable en 'result'
                r_phone = result[j]  # Se obtiene el j-ésimo fonema de 'result' 
                if i_target >= len(target):  # Se agregó para que no se caiga el código, aunque no debería entrar en esto
                    break
                # A continuación, se revisa si es que se encontró el j-ésimo fonema de 'result'
                if r_phone in sim_letters:  # Primero se revisa si es que el fonema actual de 'result' está en el diccionario de fonemas similares
                    if target[i_target] in sim_letters[r_phone]:  # Se encontró el fonema que se buscaba (i-ésimo fonema de target)
                        # print(f'{bcolors.VERDE}{letter}: j = {j} -> r_phone = {r_phone}{bcolors.ENDC}')
                        found = True  # Se encontró el fonema
                        i_result = j  # Se guarda el índice del fonema encontrado en 'result' 
                        j_result = j + 1  # El índice j (desde el cual se empezará a iterar el próximo ciclo avanza en 1)
                        if first:  # Si es el primer fonema en ser encontrado
                            first = False  # Se cambia este boolean a False
                        break 
                    # else:
                        # print(f'{bcolors.CYAN}{letter}: j = {j} -> r_phone = {r_phone}{bcolors.ENDC}')

                elif r_phone == target[i_target]:  # Si el fonema no está en la lista de fonemas similares pero se ha encontrado
                    # print(f'{bcolors.VERDE}{letter}: j = {j} -> r_phone = {r_phone}{bcolors.ENDC}')
                    found = True  # Se encontró el fonema
                    i_result = j  # Se guarda el índice del fonema encontrado en 'result' 
                    j_result = j + 1  # El índice j (desde el cual se empezará a iterar el próximo ciclo avanza en 1)
                    if first:  # Si es el primer fonema en ser encontrado
                        first = False  # Se cambia este boolean a False
                    break
                # else:
                    # print(f'{bcolors.CYAN}{letter}: j = {j} -> r_phone = {r_phone}{bcolors.ENDC}')


            else:
                # print(f'{bcolors.ROJO}{letter}: j = {j} -> r_phone = {r_phone}{bcolors.ENDC}')
                break
        # Fin del ciclo 'for' para encontrar el fonema (target[i_target]) correspondiente a la letra actual (letter)

        # ---------------------------------------------------------------------------------------------
        ## El código a continuación trata los casos si se encontró el fonema correspondiente a la letra actual o no (si se encontró target[i_target])
        if not found:  # Si no se encontró el fonema correspondiente a la letra actual
            if last_h:  # Si es que la letra anterior era una letra 'h'
                output_list.append(Letter(original[i-1], bcolors.ROJO, result_index=-2))  # Entonces se agrega la letra 'h' con color rojo
                last_h = False  # Se vuelve a resetear este boolean a False
            output_list.append(Letter(letter, bcolors.ROJO, result_index=-2))  # Se agrega la letra actual con color rojo

        else:  # Si se encontró el fonema correspondiente a la letra actual
            if last_h:  # Si es que la letra anterior era una letra 'h'
                output_list.append(Letter(original[i-1], bcolors.VERDE))  # Entonces se agrega la letra 'h' con color verde
                last_h = False  # Se vuelve a resetear este boolean a False
            # output_list.append(Letter(letter, bcolors.VERDE, target_index=j_result-1))
            output_list.append(Letter(letter, bcolors.VERDE, target_index=i_target, result_index=i_result))  # Seagrega la letra actual con color rojo

        i_target += 1  # Para el siguiente ciclo, se aumenta el índice del objetivo (target) en 1
        if i_target >= len(target):  # Si es que el índice igualó o sobrepasó el largo del objetivo
            for remaining_letter in original[i+1:]:  # Todas las letras restantes de la palabra original se agregan con color rojo
                output_list.append(Letter(remaining_letter, bcolors.ROJO, result_index=-2))
            break

    # En este punto, se ha obtenido una lista con las letras de la palabra original 
    # con color verde, las letras encontradas y con color rojo, las letras que no se encontraron

    # ---------------------------------------------------------------------------------------------
    ## El código a continuación se encargará de asignar color amarillo a las letras que, si bien,
    ##   no fueron encontradas, tienen un resultado similar al esperado 

    last_green = -10          # El índice en 'target' de la última letra verde encontrada 
    last_green_r_i = -10      # El índice en 'result' de la última letra verde encontrada
    next_green = 1000000      # El índice en 'target' de la siguiente letra verde encontrada
    next_green_r_i = 1000000  # El índice en 'result' de la siguiente letra verde encontrada
    # last_green_index = -10
    # last_was_green = False
    for o_i, output_letter in enumerate(output_list):  # Se recorre la lista de letras "coloreadas"
        # Solo las letras rojas pueden cambiar a letras amarillas
        if output_letter.color == bcolors.ROJO:  # Si la letra en cuestión es roja
            if o_i + 1 < len(output_list):  # Nos aseguramos que podremos obtener el elemento con índice o_i + 1 de la lista
                # A continuación buscamos la próxima letra verde
                for next_i, next_letter in enumerate(output_list[o_i+1:]):
                    # Entre las siguientes letras, si se en encuentra una letra verde, entonces se almacenan los índices asociados
                    if next_letter.color == bcolors.VERDE:  # Si se encuentra una letra verde
                        # Se almacenan los índices asociados
                        next_green = next_letter.target_index
                        next_green_r_i = next_letter.result_index
                        break
                
                # Si es que entre la letra verde anterior y la siguiente letra verde hay una distancia (cantidad de letras) menor o igual a la tolerancia
                #   entonces, las letras se pintarán amarillas con el motivo de que la palabra ha fallado por 
                #   una cantidad de letras pequeña (entre 1 y 3). 
                # Ejemplo: 'k a s a' y 'k a m a'. En este caso, todas las letras son verdes menos la 'm' debido a que solo se falló en una letra intermedia
                #       next_green - last_green <= tolerance   <----->  last_green + tolerance >= next_green 
                # 
                # - NOTA: Esta tolerancia se podría dejar independiente de la utilizada anteriormente
                #      dado a que no representan exactamente lo mismo
                if last_green + tolerance >= next_green:
                    # print(f'last_green = {last_green}, next_green = {next_green}')
                    output_list[o_i].color = bcolors.AMARILLO

                # Si es que una letra fue omitida ([la diferencia entre el indice en 'result' de la letra verde siguiente y la anterior es 1] o [si la letra es la primera y sin embargo, el primer fonema del 'result' es verde])
                #   entonces se indica en el estado de la letra omitida.
                if (next_green_r_i == last_green_r_i + 1) or (last_green_r_i == -10 and next_green_r_i == 0):  # Si la letra en cuestión fue omitida
                    output_list[o_i].status = 'skipped letter'
                    # print(f'letra {output_list[o_i].letter} está saltada')

                # En el caso de haber fallado por una sola letra, se pueden capturar algunos datos que 
                #   podrían ser relevantes o interesantes
                # Por ejemplo: Se pronuncian las 's' como 'ch', las 'r' como 'd', etc.
                
                # Si entre el fonema verde anterior y posterior hay 1 letra de diferencia (y además los índices se pueden evaluar)
                if (next_green_r_i == last_green_r_i + 2) and (
                    0 <= last_green_r_i + 1 < len(result)) and (
                        0 <= last_green + 1 < len(target)):

                    # Se almacenan los fonemas intermedios
                    result_phone = result[last_green_r_i + 1]
                    target_phone = target[last_green + 1]

                    # Si el fonema original era 's'
                    if target_phone == 's':
                        # Si se dijo como 'ch'
                        if result_phone in sim_letters['ʃ']:
                            output_list[o_i].status = 's said like ʃ'
                        # Si se dijo el fonema (θ)
                        elif result_phone in sim_letters['θ']:
                            output_list[o_i].status = 's said like θ'
                        # print(f'letra {output_list[o_i].letter} se dijo como "θ"')
                    
                    # Si el fonema original era 'ɾ' (r suave)
                    elif target_phone == 'ɾ':
                        # Si se dijo como d
                        if result_phone == 'ð':
                            output_list[o_i].status = 'ɾ said like ð'

                    # Si el fonema era 'ɡ' (g suave)    
                    elif target_phone == 'ɡ':
                        # Si se dijo como 'x' (g fuerte):
                        if result_phone == 'x':
                            output_list[o_i].status = 'ɡ said like x'
                            
                    # Si el fonema era 'x' (g fuerte)    
                    elif target_phone == 'x':
                        # Si se dijo como 'ɡ' (g suave):
                        if result_phone == 'ɡ':
                            output_list[o_i].status = 'x said like ɡ'

            # --------------- Fin del 'if' de su la letra es roja -----------------

        # Si es que se encuentra una letra verde, entonces se guardarán los índices de sus respectivos fonemas en 'target' y 'result'
        elif output_letter.color == bcolors.VERDE:
            # Índices de fonemas en 'target' y 'result' de última letra verde encontrada
            last_green = output_letter.target_index
            last_green_r_i = output_letter.result_index
            # Se resetean los índices de la próxima letra verde
            next_green = 1000000
            next_green_r_i = 1000000

            # --------------- Fin del 'if' de su la letra es verde -----------------    

    # --------------------- Fin del 'for' que recorre la lista de letras coloreadas --------------------
    
    return output_list

def obtain_new_lists(target, original, i):
    '''
    Esta función sirve para ir acortando una palabra y su fonema respectivo desde izquierda a derecha.
    Ejemplo: - original: 'del', fonema: 'ðel'
             - original: 'el',  fonema: 'el'
             - original: 'l',   fonema: 'l'

    inputs:
        * target -> lista de strings de los fonemas objetivos a evaluar
        ----> ej: target = ['ʃ', 'a', 'n', 'ʃ', 'o']  # Para la palabra 'chancho'
        * original -> lista de strings de las letras que conforman la palabra a evaluar
        ----> ej: original = ['c', 'h', 'a', 'n', 'c', 'h', 'o']  # Para la palabra 'chancho'
        * i -> índice de la lista 'original' desde el cual se corta la palabra original
        ----> ej: i = 2 provoca que quede ['a', 'n', 'c', 'h', 'o'] y ['a', 'n', 'ʃ', 'o'] para la palabra 'chancho'

    output:
        * new_target -> lista cortada del fonema objetivo 'target' acorde a cómo se cortó la palabra original
        ----> ej: new_target = ['a', 'n', 'ʃ', 'o']  # Para la palabra 'chancho' con i = 2
        * new_word -> lista cortada del palabra objetivo 'original' acorde al índice 'i'
        ----> ej: new_word = ['a', 'n', 'c', 'h', 'o']  # Para la palabra 'chancho' con i = 2

    El propósito de hacer esto es para considerar los casos de autocorrección de los usuarios. 
    - Ejemplo: Cuando un niño dice "ca-cami-camión"
    Así el programa detectará que sí dijo "camión" y no se quedará con "cacamicamión"
    '''

    # Se eliminan las primeras 'i' letras de la palabra original
    new_word = original[i:]

    k = 0  # Índice en cuestión en 'target'
    # A continuación se busca encontrar el índice para cortar en 'target' y se almacenará en k
    for j in range(i):  # Se itera desde la izquierda hacia la derecha
        remove = True  # boolean que indica que el fonema actual 'target[k]' se debe cortar
        or_letter = original[j]  # letra cortada actual
        # A continuación se manejarán los casos especiales
        # (en los que el fonema relacionado a una letra representa a dos letras)
        if or_letter == 'u':  # Se deben manejar los casos 'que' y 'qui' ('ke' y 'ki') y 'gue' y 'gui' ('ɡe' y 'ɡi')
            if j - 1 >= 0 and j + 1 < len(original):
                condition1 = original[j-1] == 'q' and (
                    original[j+1] == 'e' or original[j+1] == 'i' or original[j+1] == 'é' or original[j+1] == 'í')
                condition2 = original[j-1] == 'g' and (
                    original[j+1] == 'e' or original[j+1] == 'i' or original[j+1] == 'é' or original[j+1] == 'í')
                if condition1 or condition2:
                    # No se debe eliminar del target (No se suma 1 a k)
                    remove = False
        elif or_letter == 'r':  # Se debe manejar el caso de la 'rr'
            if j - 1 >= 0:
                if original[j-1] == 'r':
                    # No se debe eliminar del target (No se suma 1 a k)
                    remove = False
        elif or_letter == 'l':  # Se debe manejar el caso de la 'll'
            if j - 1 >= 0:
                if original[j-1] == 'l':
                    # No se debe eliminar del target (No se suma 1 a k)
                    remove = False
        elif or_letter == 'c':  # S debe manejar el caso de la doble 'c' ('cc')
            if j - 1 >= 0:
                if original[j-1] == 'c':
                    # No se debe eliminar del target (No se suma 1 a k)
                    remove = False
        elif or_letter == 'h':  # La 'h' nunca suena, ni con vocal ni cuando va acompañada de 'c' o 's'
            # No se debe eliminar del target (No se suma 1 a k)
                remove = False
        # Si se debe eliminar el k-ésimo fonema, entonces se aumenta k en 1
        if remove:
            k += 1

    # Se eliminan todos los primeros 'k' fonemas
    new_target = target[k:]

    return new_target, new_word

def compare(target, result, original):
    '''
    Función que permite hacer una evaluación completa de la palabra original en base a un fonema 'result'
      que representa lo que fue dicho en el audio en cuestión

    inputs:
        * target -> lista de strings de los fonemas objetivos a evaluar
        ----> ej: target = ['ʃ', 'a', 'n', 'ʃ', 'o']  # Para la palabra 'chancho'
        * result -> lista de strings de los fonemas obtenidos al analizar audio con allosaurus
        ----> ej: result = ['ʃ', 'a', 'm', 'k', 'o']  # Para la palabra 'chancho' leída como 'chamco'
        * original -> lista de strings de las letras que conforman la palabra a evaluar
        ----> ej: original = ['c', 'h', 'a', 'n', 'c', 'h', 'o']  # Para la palabra 'chancho'

    output:
        * best_list -> lista de strings de fonemas que obtiene la mejor evaluación 

    * Esta función está hecha para el idioma español
    '''
    max_tolerance = 3  # Este número indica el máximo grado de tolerancia de letras entremedio de letras correctas
    # Iteraremos entre los distintos grados de tolerancia hasta el máximo
    best_list = []  # La mejor lista se almacenará en esta
    best_score = -1  # Se parte con el peor de los casos para obetener el mejor

    for i in range(len(original)):  # Se obtendrán las listas de las palabras cortadas
        new_target, new_word = obtain_new_lists(target, original, i)
        # Para cada grado de tolerancia entre 0 y 'max_tolerance'
        for tolerance in range(1, max_tolerance+1):
            # Se obtiene la lista de fonemas ya evaluados
            output_list = analyze_comparison(new_target, result, new_word, tolerance=tolerance)
            # Ahora, si es que se cortó la palabra anteriormente, se deben agregar las primeras letras con color rojo
            new_list = []
            for letter in original[:i]:
                new_list.append(Letter(letter, bcolors.ROJO))
            for letter_class in output_list:
                new_list.append(letter_class)
            output_list = new_list[:]
            # Se obtiene el puntaje (esto con motivos de comparar las opciones y obtener la mejor)
            list_score = score_results(output_list, list_length=len(original))
            # Se verifica si el resultado actual es el mejor
            if list_score >= best_score:
                best_list = output_list.copy()
                best_score = list_score
                if best_score == 1:  # Si ya encontró un resultado que tiene 100%, entonces se debe retornar la lista
                    return best_list
    return best_list

def score_results(letters_list, list_length=-1):
    '''
    Función que calcula el puntaje asociado a la lista de fonemas con sus colores respectivos

    inputs:
        * letters_list -> lista de objetos 'Letter' de los fonemas evaluados con sus colores respectivos
        * list_length -> es un atributo de tipo int opcional que sirve para indicar manualmente el largo de la lista a considerar

    output:
        * score -> float (entre 0 y 1) que representa el puntaje asignado a la lista 'letters_list'
    '''
    # Si es que no se especificó un largo en 'list_length' se obtiene el largo de la lista 'letters_list'
    length = len(letters_list)
    if list_length != -1:
        length = list_length

    suma = 0  # Almacena el puntaje no normalizado

    # Verdes suman 1
    greens = [letter for letter in letters_list if letter.color == bcolors.VERDE]
    suma += len(greens)

     # Amarillos suman 0.25
    yellows = [letter for letter in letters_list if letter.color == bcolors.AMARILLO]
    suma += 0.25*len(yellows)

    # Rojos suman 0

    score = suma/length  # El puntaje final se normaliza a números entre 0 y 1
    return score

def api_format(letters_list, warning='', warning_text='', jsonif=False):
    '''
    Función que permite ordenar los resultados en un diccionario con formato que permite enviarlo a la API 
      (usualmente se obtendrán los resultados en JSON) 

    inputs:
        * letters_list -> lista de objetos 'Letter' de los fonemas evaluados con sus colores respectivos
        * warning -> string que resume la advertencia (si es que hay)
        * warning_text -> string que explica el detalle de la advertencia (si es que hay)
        * jsonif -> boolean que es True si es que se prepararán en formato JSON

    output:
        * json_dict -> dict/json que representa lo mismo que hay en 'letters_list' pero en formato 
            para comunicarse con la API

    '''
    # Se inicializa el dict con los datos de la advertencia
    json_dict = {
        'warning': warning, 
        'warning_text': warning_text
    }
    json_list = []  # Lista de dicts donde se almacenarán las letras con sus respectivas características
    letter_colors = {
        bcolors.VERDE: 'green',
        bcolors.AMARILLO: 'yellow',
        bcolors.ROJO: 'red'
    }  # Diccionario para decodificar los colores
    # Se iterará por cada letra en la lista 'letters_list'
    for i, letter in enumerate(letters_list):
        # Se agrega un dict con la información de la letra
        json_list.append({
            'id'    : i,
            'letter': letter.letter,
            'color' : letter_colors[letter.color],
            'status': letter.status,
        })
    # Se agrega la lista de dicts en 'json_dict'
    json_dict['letters-list'] = json_list
    # Se agrega el puntaje obtenido con la lista 'letters_list'
    json_dict['score'] = score_results(letters_list)
    # Si es que se quería en formato JSON se retorna utilizando antes jsonify
    if jsonif:
        return jsonify(json_dict)
    return json_dict

def compare_words(target, result, original, api=False, show=False, jsonif=False):
    '''
    Esta función recopila todo lo necesario para poder comparar la palabra con lo dicho en el audio
      y realiza esta comparación, retornando los resultados ya sea en formato para la API o para poder imprimirlos en consola 

    inputs:
        * target -> lista de strings de los fonemas objetivos a evaluar
        ----> ej: target = ['ʃ', 'a', 'n', 'ʃ', 'o']  # Para la palabra 'chancho'
        * result -> lista de strings de los fonemas obtenidos al analizar audio con allosaurus
        ----> ej: result = ['ʃ', 'a', 'm', 'k', 'o']  # Para la palabra 'chancho' leída como 'chamco'
        * original -> lista de strings de las letras que conforman la palabra a evaluar
        ----> ej: original = ['c', 'h', 'a', 'n', 'c', 'h', 'o']  # Para la palabra 'chancho'
        * api -> boolean que es True si es que se quieren los resultados en formato para enviarlos a la API
        * show -> boolean que es True si es que se quieren imprimir en consola los resultados
        * jsonif -> boolean que es True si es que se prepararán en formato JSON

    output:
        * output_list -> dict/json de los resultados recopilados de la evaluación

    '''
    # Primero se realiza la evaluación
    output_list = compare(target, result, original)
    
    # A continuación, se capturan algunas advertencias relacionadas a diferencias en las listas de fonemas 'target' y 'result'
    warning = ''
    warning_text = ''
    # Si es que se tienen más fonemas en 'result'
    if len(result) > len(target):
        warning = 'more'
        warning_text = f'Result has more phonemes than target (len(result) = {len(result)} > len(target) = {len(target)})'
    # Si es que se tienen más fonemas en 'target'
    elif len(result) < len(target):
        warning = 'less'
        warning_text = f'Result has less phonemes than target (len(result) = {len(result)} < len(target) = {len(target)})'

    # Si es que se desea imprimir en consola
    if show:
        if warning_text != '':
            print(f"{bcolors.MORADO}{warning_text}{bcolors.ENDC}")
        print(*output_list)

    # Si es que se quiere en formato API    
    if api:
        return api_format(output_list, warning=warning, warning_text=warning_text, jsonif=jsonif)

    return output_list


if __name__ == '__main__':
    # Para propósitos de debuggear. No debería correrse este código desde app.py
    model = read_recognizer()

    original = list('plelomina')
    target   = 'p l e l o m i n a'.split(' ')
    result   = 'o h k a a'.split(' ')

    original = list('aralón')
    target   = 'a ɾ a l o n'.split(' ')
    result   = 'a ð a l o n'.split(' ')


    # original = list('químico')
    # target   = 'k i m i k o'.split(' ')
    # result   = 'k i i k'.split(' ')

    # original = list('elimina')
    # target   = 'e l i m i n a'.split(' ')
    # result   = 'l e m i n a'.split(' ')

    # original = list('zarapito')
    # target   = 's a ɾ a p i t o'.split(' ')
    # result   = 's ɾ p o'.split(' ')
    output_list = compare_words(target, result, original, api=True, show=True)
    # print(compare_words(target, result, original, api=True, show=True, jsonif=True))
    

    original = list('limina')
    target   = 'l i m i n a'.split(' ')
    result   = 'l e m i n a'.split(' ')
    output_list = compare_words(target, result, original, api=True, show=True)
    
    
    original = 'c h a n c h o'.split(' ')
    target   = 'ʃ a n ʃ o'.split(' ')
    result   = 'a s g k h f h ʃ a n a n ʃ o s o p'.split(' ')

    output_list = compare_words(target, result, original, api=False, show=True)
    """
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

    """

    
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
    