# ==============================================================================
# IMPORTACIÓN DE LIBRERÍAS
# ==============================================================================
import os
import json
import re
from flask import Flask, render_template, request, jsonify
from pyswip import Prolog
from google import genai
from google.genai import types

# ==============================================================================
# INICIALIZACIÓN DEL SERVIDOR WEB
# ==============================================================================
app = Flask(__name__)

# ==============================================================================
# CONFIGURACIÓN DEL CLIENTE IA (GEMINI API)
# ==============================================================================
# Se obtiene de la variable de entorno configurada en Render o en el sistema
API_KEY = os.environ.get("GEMINI_API_KEY", "")
client = genai.Client(api_key=API_KEY)

# ==============================================================================
# CONFIGURACIÓN E INICIALIZACIÓN DE PROLOG
# ==============================================================================
prolog = Prolog()
directorio = os.path.dirname(os.path.abspath(__file__))
ruta_pl = os.path.join(directorio, "ortografia.pl").replace("\\", "/")
prolog.consult(ruta_pl)

# Caché en memoria para reutilizar clasificaciones instantáneamente
cache_prolog = {}

# ==============================================================================
# FUNCIONES AUXILIARES
# ==============================================================================
def limpiar(val):
    if isinstance(val, bytes):
        return val.decode("utf-8", errors="ignore")
    return str(val)

def clasificar_con_prolog(original, corregida):
    orig_clean = original.strip().lower()
    corr_clean = corregida.strip().lower()
    clave = (orig_clean, corr_clean)

    if clave in cache_prolog:
        return cache_prolog[clave]

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

    # PROMPT ULTRA-LIGERO: Sin descripciones redundantes para que Gemini genere el JSON al instante
    prompt_instrucciones = f"""Corrige rigurosamente la ortografía, acentuación y unión/separación de palabras de este texto según la RAE.
Texto:
"{texto}"

Devuelve ÚNICAMENTE un JSON con:
{{
  "texto_corregido": "texto íntegro corregido",
  "errores": [
    {{"o": "error", "c": "corrección", "a": null}}
  ],
  "estilo": {{
    "academico": "versión formal resumida",
    "divulgativo": "versión clara resumida",
    "observacion": "apunte sintáctico general"
  }}
}}
Nota: 'a' es una alternativa léxica si hay ambigüedad o null."""

    try:
        # Gemini 3 Flash Preview con cero thinking y temperatura 0 para máxima velocidad
        respuesta = client.models.generate_content(
            model='gemini-3-flash-preview',
            contents=prompt_instrucciones,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                temperature=0.0,
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

    # Procesamiento rápido con caché
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