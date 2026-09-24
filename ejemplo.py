# Módulo estándar del sistema operativo para gestionar rutas de archivos y directorios
import os

# Módulo estándar de expresiones regulares para buscar y extraer patrones de texto
import re

# Clase de la librería PySWIP para conectar Python con el intérprete de SWI-Prolog
from pyswip import Prolog

# 1. Obtener la ruta exacta de la carpeta donde vive este script
# __file__ indica este archivo; abspath obtiene su ruta absoluta y dirname extrae solo la carpeta contenedora
directorio_actual = os.path.dirname(os.path.abspath(__file__))

# Une la carpeta con el archivo 'ortografia.pl' y reemplaza las barras invertidas '\' por '/' para compatibilidad
ruta_pl = os.path.join(directorio_actual, "ortografia.pl").replace("\\", "/")

# 2. Inicializar el motor Prolog con la ruta directa
# Crea una instancia u objeto del intérprete de Prolog en memoria
prolog = Prolog()

# Carga y compila la base de conocimiento y reglas lógicas desde el archivo 'ortografia.pl'
prolog.consult(ruta_pl)

# Definición de la función que recibe una cadena de texto y busca faltas ortográficas mediante Prolog
def auditar_texto(texto_completo):
    # Extrae en una lista todas las palabras del texto ignorando signos de puntuación, admitiendo acentos y 'ñ'
    palabras = re.findall(r'\b[a-zA-ZáéíóúÁÉÍÓÚñÑ]+\b', texto_completo)
    
    # Lista vacía donde se guardarán los errores y reglas deducidas
    errores_detectados = []
    
    # Itera sobre cada una de las palabras extraídas
    for palabra in palabras:
        # Convierte la palabra a minúsculas para unificar la búsqueda en la base de reglas
        palabra_clean = palabra.lower()
        
        # Construye la consulta formal para el predicado de Prolog pasando la palabra y la variable de salida 'Error'
        query = f"analizar_palabra('{palabra_clean}', Error)"
        
        # Ejecuta la consulta deductiva en Prolog y convierte las respuestas obtenidas a una lista
        resultados = list(prolog.query(query))
        
        # Recorre cada una de las soluciones o reglas infringidas devueltas por Prolog
        for res in resultados:
            # Agrega un diccionario con la palabra original y la regla violada a la lista de errores
            errores_detectados.append({
                "palabra": palabra,
                "regla": res["Error"]
            })
            
    # Retorna la lista con todos los errores encontrados
    return errores_detectados

# Prueba directa por consola:
# Cadena de caracteres con palabras mal escritas o sin tilde para evaluar el sistema
texto_prueba = "El camion choco contra un arbol y el tanbor sono"

# Llama a la función pasándole el texto de prueba y guarda el resultado devuelto
resultado = auditar_texto(texto_prueba)

# Imprime en la consola la cabecera visual del reporte
print("--- RESULTADOS DEL SISTEMA EXPERTO ---")

# Itera sobre cada diccionario guardado en la lista de resultados
for r in resultado:
    # Imprime en la terminal la palabra detectada y la descripción de la regla que violó
    print(f"Palabra: {r['palabra']} -> {r['regla']}")