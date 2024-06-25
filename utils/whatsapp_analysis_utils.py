import pandas as pd
import numpy as np
import datetime as dt

import re
import regex
import emoji
from collections import Counter

from wordcloud import WordCloud, STOPWORDS


# Patron regex para identificar el comienzo de cada línea del txt con la fecha y la hora
def IniciaConFechaYHora(s):
    # Ejemplo: '28/03/23, 18:35 - ...'
    patron = r'^([1-9]|1[0-9]|2[0-9]|3[0-1])(\/)(0[1-9]|1[0-2])(\/)(2[0-9]), ([0-9]+):([0-9][0-9])\s? -'
    resultado = re.match(patron, s)  # Verificar si cada línea del txt hace match con el patrón de fecha y hora
    if resultado:
        return True
    return False


# Separar las partes de cada línea del txt: Fecha, Hora, Miembro y Mensaje
def ObtenerPartes(linea):
    # Ejemplo: '28/03/23, 18:58 - Efrain pizarro soto: Ando en reu'
    splitLinea = linea.split(' - ')
    FechaHora = splitLinea[0]                     # '28/03/23, 18:58'
    splitFechaHora = FechaHora.split(', ')
    Fecha = splitFechaHora[0]                    # '28/03/23'
    Hora = ' '.join(splitFechaHora[1:])          # '18:58'

    Cuerpo = ' '.join(splitLinea[1:])             # 'Efrain pizarro soto: Ando en reu'

    Miembro = Cuerpo.split(": ")[0]             # 'Efrain pizarro soto'
    Mensaje = ' '.join(Cuerpo.split(": ")[1:])            # 'Ando en reu'

    return Fecha, Hora, Miembro, Mensaje


def ObtenerEmojis(Mensaje):
    emoji_lista = []
    data = regex.findall(r'\X', Mensaje) # Obtener lista de caracteres de cada mensaje
    for caracter in data:
        if caracter in emoji.EMOJI_DATA: # Obtener emojis en idioma español
            emoji_lista.append(caracter)
    return emoji_lista


def transform_file_to_data_frame(data_file):
    data_chat = []
    with data_file as fp:
        fp.readline().decode("utf-8") # Deshechar la primera fila del txt relacionada al cifrado de extremo a extremo
        while True:
            linea = fp.readline().decode("utf-8")
            if not linea:
                break
            linea = linea.strip()

            if IniciaConFechaYHora(linea):
                Fecha, Hora, Miembro, Mensaje = ObtenerPartes(linea)
                data_chat.append([Fecha, Hora, Miembro, Mensaje])

    # Convertir la lista con los datos a dataframe
    df = pd.DataFrame(data_chat, columns=['Fecha', 'Hora', 'Miembro', 'Mensaje'])

    # Cambiar la columna Fecha a formato datetime
    df['Fecha'] = pd.to_datetime(df['Fecha'], format="%d/%m/%y")

    # Eliminar los posibles campos vacíos del dataframe
    # y lo que no son mensajes como cambiar el asunto del grupo o agregar a alguien
    df = df.dropna()

    # Resetear el índice
    df.reset_index(drop=True, inplace=True)

    return df


def get_message_types(data_transformed):
    # Obtener la cantidad total de mensajes
    total_mensajes = data_transformed.shape[0]

    # Obtener la cantidad de archivos multimedia enviados
    multimedia_mensajes = data_transformed[data_transformed['Mensaje'] == '<Multimedia omitido>'].shape[0]

    # Obtener la cantidad de emojis enviados
    data_transformed['Emojis'] = data_transformed['Mensaje'].apply(ObtenerEmojis) # Se agrega columna 'Emojis'
    emojis = sum(data_transformed['Emojis'].str.len())

    # Obtener la cantidad de links enviados
    url_patron = r'(https?://\S+)'
    data_transformed['URLs'] = data_transformed.Mensaje.apply(lambda x: len(re.findall(url_patron, x))) # Se agrega columna 'URLs'
    links = sum(data_transformed['URLs'])

    # Obtener la cantidad de tiktoks enviados
    tiktok_url_patron = 'vm.tiktok.com'
    data_transformed['Tiktoks'] = data_transformed.Mensaje.apply(lambda x: len(re.findall(tiktok_url_patron, x))) # Se agrega columna 'URLs'
    tiktoks_links = sum(data_transformed['Tiktoks'])

    # Todos los datos pasarlo a diccionario
    estadistica_dict = {'Tipo': ['Mensajes', 'Multimedia', 'Emojis', 'Links', 'Tiktoks'],
            'Cantidad': [total_mensajes, multimedia_mensajes, emojis, links, tiktoks_links]
            }

    #Convertir diccionario a dataframe
    estadistica_data_transformed = pd.DataFrame(estadistica_dict, columns = ['Tipo', 'Cantidad'])

    # Establecer la columna Tipo como índice
    # estadistica_data_transformed = estadistica_data_transformed.set_index('Tipo')

    return estadistica_data_transformed


def get_emojis_count(data_transformed):
    # Obtener emojis más usados y las cantidades en el chat del grupo del dataframe
    emojis_lista = list([a for b in data_transformed.Emojis for a in b])
    emoji_diccionario = dict(Counter(emojis_lista))
    emoji_diccionario = sorted(emoji_diccionario.items(), key=lambda x: x[1], reverse=True)

    # Convertir el diccionario a dataframe
    emoji_df = pd.DataFrame(emoji_diccionario, columns=['Emoji', 'Cantidad'])

    return emoji_df


def get_members_by_messages_count(data_transformed):
    df_MiembrosActivos = data_transformed.groupby('Miembro')['Mensaje'].count().sort_values(ascending=False).to_frame()
    df_MiembrosActivos.reset_index(inplace=True)
    df_MiembrosActivos.index = np.arange(1, len(df_MiembrosActivos)+1)

    return df_MiembrosActivos


def get_statics_by_member(data_transformed):
    # Separar mensajes (sin multimedia) y multimedia (stickers, fotos, videos)
    menssages_to_omit = [
        '<Multimedia omitido>',
        ''
    ]
    multimedia_df = data_transformed[data_transformed['Mensaje'].isin(menssages_to_omit)]
    mensajes_df = data_transformed.drop(multimedia_df.index)

    # Contar la cantidad de palabras y letras por mensaje
    mensajes_df['Letras'] = mensajes_df['Mensaje'].apply(lambda s : len(s))
    mensajes_df['Palabras'] = mensajes_df['Mensaje'].apply(lambda s : len(s.split(' ')))

    # Obtener a todos los miembros
    miembros = mensajes_df.Miembro.unique()

    # Crear diccionario donde se almacenará todos los datos
    dictionario = {}

    for i in range(len(miembros)):
        lista = []
        # Filtrar mensajes de un miembro en específico
        miembro_df= mensajes_df[mensajes_df['Miembro'] == miembros[i]]

        # Agregar a la lista el número total de mensajes enviados
        lista.append(miembro_df.shape[0] + multimedia_df[multimedia_df['Miembro'] == miembros[i]].shape[0])
        
        # Agregar a la lista el número de palabras por total de mensajes (palabras por mensaje)
        palabras_por_msj = (np.sum(miembro_df['Palabras']))/miembro_df.shape[0]
        lista.append(palabras_por_msj)

        # Agregar a la lista el número de mensajes multimedia enviados
        multimedia = multimedia_df[multimedia_df['Miembro'] == miembros[i]].shape[0]
        lista.append(multimedia)

        # Agregar a la lista el número total de emojis enviados
        emojis = sum(miembro_df['Emojis'].str.len())
        lista.append(emojis)

        # Agregar a la lista el número total de links enviados
        links = sum(miembro_df['URLs'])
        lista.append(links)
        
        # Agregar a la lista el número total de tiktoks enviados
        tiktoks = sum(miembro_df['Tiktoks'])
        lista.append(tiktoks)

        # Asignar la lista como valor a la llave del diccionario
        dictionario[miembros[i]] = lista

    # Convertir de diccionario a dataframe
    miembro_stats_df = pd.DataFrame.from_dict(dictionario)

    # Cambiar el índice por la columna agregada 'Estadísticas'
    estadísticas = ['Mensajes', 'Palabras por mensaje', 'Multimedia', 'Emojis', 'Links', 'Tiktoks']
    miembro_stats_df['Estadísticas'] = estadísticas
    miembro_stats_df.set_index('Estadísticas', inplace=True)

    # Transponer el dataframe
    miembro_stats_df = miembro_stats_df.T
    miembro_stats_df = miembro_stats_df.reset_index() #Reiniciamos el indice
    miembro_stats_df = miembro_stats_df.rename(columns={'index': 'Miembro'})

    #Convertir a integer las columnas Mensajes, Multimedia Emojis y Links
    miembro_stats_df['Mensajes'] = miembro_stats_df['Mensajes'].apply(int)
    miembro_stats_df['Multimedia'] = miembro_stats_df['Multimedia'].apply(int)
    miembro_stats_df['Emojis'] = miembro_stats_df['Emojis'].apply(int)
    miembro_stats_df['Links'] = miembro_stats_df['Links'].apply(int)
    miembro_stats_df['Links'] = miembro_stats_df['Links'].apply(int)
    miembro_stats_df['Tiktoks'] = miembro_stats_df['Tiktoks'].apply(int)

    return miembro_stats_df


# Define a function to create the "Range Hour" column
def create_range_hour(hour):
    start_hour = hour.hour
    end_hour = (hour + pd.Timedelta(hours=1)).hour
    return f'{start_hour:02d} - {end_hour:02d} h'


def get_analysis_by_hour_range(data_transformed):
    data_by_hour = data_transformed.copy()
    data_by_hour['rangoHora'] = pd.to_datetime(data_by_hour['Hora'])

    # # Apply the function to create the "Range Hour" column
    data_by_hour['rangoHora'] = data_by_hour['rangoHora'].apply(create_range_hour)

    # Crear una columna de 1 para realizar el conteo de mensajes
    data_by_hour['# Mensajes por hora'] = 1

    # Sumar (contar) los mensajes que tengan la misma fecha
    date_df = data_by_hour.groupby('rangoHora')['# Mensajes por hora'].sum().to_frame()
    date_df.reset_index(inplace=True)

    return date_df


def get_analysis_by_day(data_transformed):
    data_by_day = data_transformed.copy()

    # Selección de columnas relevantes para el ejercicio y formato de fecha
    data_by_day = data_by_day[["Fecha"]]
    data_by_day['Fecha'] = data_by_day['Fecha'].dt.strftime('%m/%d/%Y')

    # Crear una columna de 1 para realizar el conteo de mensajes
    data_by_day['# Mensajes por día'] = 1

    # Sumar (contar) los mensajes que tengan la misma fecha
    date_df = data_by_day.groupby('Fecha').sum()
    date_df.reset_index(inplace=True)

    return date_df


def words_most_used(data_transformed):
    # Separar mensajes (sin multimedia) y multimedia (stickers, fotos, videos)
    menssages_to_omit = [
        '<Multimedia omitido>',
        ''
    ]
    multimedia_df = data_transformed[data_transformed['Mensaje'].isin(menssages_to_omit)]
    mensajes_df = data_transformed.drop(multimedia_df.index)

    # Crear un string que contendrá todas las palabras
    total_palabras = ' '
    stopwords = STOPWORDS.update(['que', 'qué', 'con', 'de', 'te', 'en', 'la', 'lo', 'le', 'el', 'las', 'los', 'les', 'por', 'es',
                                'son', 'se', 'para', 'un', 'una', 'chicos', 'su', 'si', 'chic','nos', 'ya', 'hay', 'esta',
                                'pero', 'del', 'mas', 'más', 'eso', 'este', 'como', 'así', 'todo', 'https','Media','omitted',
                                'y', 'mi', 'o', 'q', 'yo', 'al'])

    # Obtener y acumular todas las palabras de cada mensaje
    for mensaje in mensajes_df['Mensaje'].values:
        palabras = str(mensaje).lower().split() # Obtener las palabras de cada línea del txt
        for palabra in palabras:
            total_palabras = total_palabras + palabra + ' ' # Acumular todas las palabras

    return total_palabras