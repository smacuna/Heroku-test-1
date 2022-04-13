import noisereduce as nr
from scipy.io import wavfile


def filter_audio(wav_path):
    ''' 
    Esta función permite filtrar el audio ubicado en 'wav_path' usando un spectral gate
    * Esta función no se ha testeado mucho, podría ser inestable
    '''
    # Se abre archivo wav
    rate, data = wavfile.read(wav_path)

    # Se aplica el filtro
    reduced_noise = nr.reduce_noise(y=data, sr=rate)

    # Se escribe el nuevo audio filtrado
    output_path = f'{wav_path[:-4]}f.wav'
    wavfile.write(output_path, rate, reduced_noise)

    return output_path


# import os
# import numpy as np
# filename = '../temp/test4.wav'
# 
# rate, data = wavfile.read(filename)
# # perform noise reduction
# reduced_noise = nr.reduce_noise(y=data, sr=rate)
# print(np.count_nonzero(data!=reduced_noise) == 0)
# 
# output_file = '../temp/test4nr.wav'
# 
# wavfile.write(output_file, rate, reduced_noise)
