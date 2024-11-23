from os import listdir as dir
from os.path import join, isdir
import re


def leer_archivo(arch):
    """
    Modifica la función `leer_archivo` para leer archivos con formato específico
    como el proporcionado, que incluye parámetros con etiquetas como `param capacity`,
    `param in_cost`, `param demand`, y `param cost`.
    """
    capacity = []
    costos_fijos = []
    demandas = []
    costos_transporte = []
    seccion_actual = None

    with open(arch, 'r') as file:
        for linea in file:
            linea = linea.strip()

            # Detectar el inicio de una nueva sección basada en las etiquetas del archivo
            if linea.startswith("param capacity :="):
                seccion_actual = "capacity"
                continue
            elif linea.startswith("param in_cost :="):
                seccion_actual = "costos_fijos"
                continue
            elif linea.startswith("param demand :="):
                seccion_actual = "demandas"
                continue
            elif linea.startswith("param cost :"):
                seccion_actual = "costos"
                continue
            elif linea == ";":
                seccion_actual = None
                continue

            # Procesar cada sección según su formato
            if seccion_actual == "capacity":
                partes = linea.split()
                if len(partes) == 2:
                    capacity.append(float(partes[1]))
            elif seccion_actual == "costos_fijos":
                partes = linea.split()
                if len(partes) == 2:
                    costos_fijos.append(float(partes[1]))
            elif seccion_actual == "demandas":
                partes = linea.split()
                if len(partes) == 2:
                    demandas.append(float(partes[1]))
            elif seccion_actual == "costos":
                partes = linea.split()
                if len(partes) > 1:
                    # Convertir todos los costos en una lista de listas
                    costos_transporte.append([float(costo) for costo in partes[1:]])

    # Retornar los parámetros organizados
    return capacity, costos_fijos, demandas, costos_transporte




def read_results(file_path):
    """
    Lee los resultados de un archivo que contiene datos en formato de matriz dispersa.

    Args:
        file_path (str): Ruta al archivo de resultados.

    Returns:
        dict: Diccionario con las secciones `open` y `proportion` procesadas.
    """
    with open(file_path, 'r') as file:
        content = file.read()

    # Procesar la sección `open`
    open_pattern = r"open \[\*\] :=([\s\S]*?);"
    open_match = re.search(open_pattern, content)
    open_dict = {}
    if open_match:
        open_data = open_match.group(1).strip()
        for line in open_data.splitlines():
            entries = line.split()
            for i in range(0, len(entries), 2):
                facility = int(entries[i])
                state = int(entries[i + 1])
                open_dict[facility] = state

    # Procesar la sección `proportion`
    proportion_pattern = r"proportion \[\*\] :=([\s\S]*?);"
    proportion_match = re.search(proportion_pattern, content)
    proportion_dict = {}
    if proportion_match:
        proportion_data = proportion_match.group(1).strip()
        for line in proportion_data.splitlines():
            entries = line.split()
            facility = int(entries[0])
            for client, value in enumerate(entries[1:], start=1):
                if float(value) > 0:  # Ignorar ceros
                    proportion_dict[(facility, client)] = float(value)

    return {
        "open": open_dict,
        "proportion": proportion_dict,
    }



def read_options(path):
    """
    Lee los nombres y dimensiones de todas las instancias disponibles en el directorio.

    Args:
        path (str): Ruta al directorio que contiene las instancias.

    Returns:
        list: Lista de nombres y dimensiones de las instancias.
    """
    from os.path import isdir

    if not isdir(path):
        raise NotADirectoryError(f"La ruta proporcionada no es un directorio válido: {path}")

    options = []
    for option in dir(path):
        file_path = join(path, option)
        name = option.strip('.txt')

        with open(file_path, 'r') as file:
            while True:
                line = file.readline().strip()
                if not line or not line[0].isdigit():  # Ignorar líneas vacías o no numéricas
                    continue
                try:
                    dims = [int(item) for item in line.split()]
                    options.append([name, dims])
                    break
                except ValueError:
                    continue  # Ignorar líneas mal formateadas
    return options

def read_instance(file_path):
    """
    Modifica la función `read_instance` para integrar la nueva lógica de lectura
    desde archivos formateados como el proporcionado.
    """
    capacity, costos_fijos, demandas, costos_transporte = leer_archivo(file_path)

    data = {
        "params": [len(capacity), len(demandas)],  # Número de centros y clientes
        "capacity": capacity,
        "costos_fijos": costos_fijos,
        "demandas": demandas,
        "costo": costos_transporte,
        "initial_capacity": capacity.copy(),
        "initial_demand": demandas.copy()
    }

    return data


