# ==============================================================================
# IMPORTACIÓN DE LIBRERÍAS
# ==============================================================================
import os
#importa el módulo estándar de Python que permite interactuar 
# con el sistema operativo donde se ejecuta el programa (Windows, macOS o Linux).
import json
#importa el módulo estándar para trabajar con datos en 
# formato (JavaScript Object Notation)que es el formato de 
# texto más usado para intercambiar información entre servidores
# web, APIs y aplicaciones.
import re
# FUNCIONES AUXILIARES
from flask import Flask, render_template, request, jsonify
#diseñado para crear aplicaciones web y APIs (servicios backend).

from pyswip import Prolog
#Esta línea importa la clase principal de la biblioteca PySwip, 
# que sirve como un puente bidireccional entre Python y SWI-Prolog
from google import genai
#importa el SDK oficial de Google GenAI,
# que es la biblioteca moderna de Google para interactuar con 
# los modelos de inteligencia artificial de la familia Gemini e Imagen.
from google.genai import types
#importa el módulo types del SDK de Google GenAI, el cual contiene todas las 
# clases de configuración, estructuras de datos, tipos de parámetros
# y esquemas necesarios para controlar con precisión el comportamiento de 
# los modelos Gemini.

# INICIALIZACIÓN DEL SERVIDOR WEB--------------------------------------------
app = Flask(__name__)
#Es el núcleo de el  proyecto backend:

# CONFIGURACIÓN DEL CLIENTE IA (GEMINI API)---------------------------------------


# Se obtiene de la variable de entorno configurada en Render
API_KEY = os.environ.get("GEMINI_API_KEY", "")
#Esta línea intenta obtener la clave de API 
# (API key) de Gemini desde las variables de
# entorno del sistema operativo, asignando un 
# valor de respaldo en caso de que no exista, 
# se puso asi por seguridad a el codigo, 
# Permite cambiar de credenciales entre entornos.
client = genai.Client(api_key=API_KEY)
#crea e inicializa la sesión de conexión 
# con los servidores de Google Gemini, guardándola en la variable


# CONFIGURACIÓN E INICIALIZACIÓN DE PROLOG--------------------------------------------
prolog = Prolog()
directorio = os.path.dirname(os.path.abspath(__file__))
# obtiene la ruta absoluta de la carpeta en la que está guardado el archivo Python actual.
ruta_pl = os.path.join(directorio, "ortografia.pl").replace("\\", "/")
#construye la ruta absoluta al archivo ortografia.pl 
# y se asegura de que todos los separadores de carpetas 
# sean barras normales (/), lo cual es indispensable para
# que Prolog pueda leer el archivo sin errores en Windows.
prolog.consult(ruta_pl)
#Esta línea lee, compila y carga en memoria todas las 
# reglas y hechos lógicos contenidos en el archivo ortografia.pl
# dentro del motor de SWI-Prolog.

# Caché en memoria para reutilizar clasificaciones instantáneamente
cache_prolog = {}

# FUNCIONES AUXILIARES---------------------------------------------------------
def limpiar(val):
    #Esta línea declara una función personalizada
    # llamada limpiar que recibe un único parámetro de entrada llamado val (valor).
    if isinstance(val, bytes):
        
        return val.decode("utf-8", errors="ignore")
    #utf-8 : Es el estándar de codificación universal. 
    # interpreta correctamente acentos y caracteres
    # especiales del español (á, é, í, ó, ú, ñ, ¿).
    #------------------------------------
    #return: Devuelve de inmediato el string limpio resultante.
    #------------------------------------
    #val.decode :Toma los datos binarios (bytes) que devolvió
    # Prolog o la red y los traduce a caracteres legibles de Python.
    return str(val)
################################################################3
def clasificar_con_prolog(original, corregida):
    orig_clean = original.strip().lower()
    corr_clean = corregida.strip().lower()
    clave = (orig_clean, corr_clean)

    if clave in cache_prolog:
        return cache_prolog[clave]
    # Este fragmento de código implementa una técnica de optimización 
    # llamada memoización (caching) para evitar cálculos o consultas 
    # repetidas hacia Prolog.
#---------------------------------------------------------------------
    # Limpieza de comillas simples para evitar errores de sintaxis en Prolog
    o_query = orig_clean.replace("'", "\\'")
    c_query = corr_clean.replace("'", "\\'")
    query = f"clasificar_regla('{o_query}', '{c_query}', Categoria, Fundamento)"

    try:
        soluciones = list(prolog.query(query))
        if soluciones:
            res = (limpiar(soluciones[0]["Categoria"]), limpiar(soluciones[0]["Fundamento"]))
            cache_prolog[clave] = res
            return res
    except Exception:
        pass

    res_defecto = ("Norma RAE", "Ajuste morfosintáctico conforme a la norma estándar.")
    cache_prolog[clave] = res_defecto
    return res_defecto

# ==============================================================================
# RUTAS Y CONTROLADORES HTTP (FLASK)
# ==============================================================================
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/auditar", methods=["POST"])
def auditar():
    datos = request.get_json() or {}
    texto = datos.get("texto", "").strip()

    if not texto:
        return jsonify({
            "errores": [],
            "texto_corregido": "",
            "estilo": {"academico": "", "divulgativo": "", "observacion": ""}
        })

    prompt_instrucciones = f"""Actúa como un auditor ortográfico estricto de la Real Academia Española (RAE).
Corrige minuciosamente todos los errores de grafías (b/v, c/s/z, g/j, ll/y, h), acentuación (tildes diacríticas, agudas, llanas, esdrújulas) y separación/unión de palabras del siguiente texto:

"{texto}"

Devuelve EXCLUSIVAMENTE un JSON válido con esta estructura:
{{
  "texto_corregido": "texto completo corregido con máxima fidelidad",
  "errores": [
    {{"o": "palabra_con_error", "c": "palabra_corregida", "a": null}}
  ],
  "estilo": {{
    "academico": "Reescritura en registro formal o académico",
    "divulgativo": "Reescritura en registro fluido o divulgativo",
    "observacion": "Comentario general sobre la ortografía y sintaxis"
  }}
}}
Nota: en 'errores' incluye CADA una de las palabras corregidas individualmente. 'a' es una alternativa léxica o null."""

    try:
        respuesta = client.models.generate_content(
            model='gemini-3-flash-preview',
            contents=prompt_instrucciones,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                temperature=0.1,
                max_output_tokens=3000,
                thinking_config=types.ThinkingConfig(thinking_budget=0)
            )
        )

        texto_limpio = respuesta.text.strip()
        if texto_limpio.startswith("```"):
            texto_limpio = re.sub(r"^```[a-zA-Z]*\n?", "", texto_limpio)
            texto_limpio = re.sub(r"\n?```$", "", texto_limpio)

        resultado_ia = json.loads(texto_limpio)

    except Exception as e:
        print(f"\n[ERROR GEMINI API]: {e}\n")
        return jsonify({
            "errores": [],
            "texto_corregido": texto,
            "estilo": {
                "academico": "Fallo temporal en la consulta.",
                "divulgativo": "Revisa los registros de la consola.",
                "observacion": f"Detalle técnico: {str(e)}"
            }
        })

    # Procesar errores encontrados y clasificarlos con Prolog
    hallazgos = []
    lista_errores = resultado_ia.get("errores", [])

    for item in lista_errores:
        orig = item.get("o") or item.get("original", "")
        corr = item.get("c") or item.get("corregida", "")
        alt = item.get("a") if "a" in item else item.get("alternativa")

        if not orig or not corr:
            continue

        cat_prolog, fund_prolog = clasificar_con_prolog(orig, corr)

        hallazgos.append({
            "original": orig,
            "corregida": corr,
            "alternativa": alt,
            "nota": "",
            "categoria": cat_prolog,
            "fundamento": fund_prolog
        })

    return jsonify({
        "errores": hallazgos,
        "texto_corregido": resultado_ia.get("texto_corregido", texto),
        "estilo": resultado_ia.get("estilo", {})
    })

# ==============================================================================
# PUNTO DE ENTRADA PRINCIPAL (MAIN)
# ==============================================================================
if __name__ == "__main__":
    app.run(debug=True, port=5000)