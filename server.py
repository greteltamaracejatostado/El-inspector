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

    # Instrucción del sistema estricta y compacta
    system_inst = (
        "Auditor ortográfico RAE ultrarrápido. "
        "Devuelve únicamente un objeto JSON con este formato exacto: "
        "{\"errores\": [{\"o\": \"palabra_erronea\", \"c\": \"palabra_corregida\", \"a\": null}], "
        "\"estilo\": {\"academico\": \"reescritura formal breve\", \"divulgativo\": \"reescritura fluida breve\", \"observacion\": \"apunte sintáctico breve\"}}. "
        "'a' es una alternativa léxica o null si no aplica."
    )

    try:
        # Consulta optimizada con límite de tokens y cero presupuesto de razonamiento
        respuesta = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=texto,
            config=types.GenerateContentConfig(
                system_instruction=system_inst,
                response_mime_type="application/json",
                temperature=0.0,
                max_output_tokens=600,
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

    # Reconstrucción instantánea del texto en Python (sin esperar a la IA)
    texto_reconstruido = texto
    hallazgos = []
    lista_errores = resultado_ia.get("errores", [])

    for item in lista_errores:
        orig = item.get("o") or item.get("original", "")
        corr = item.get("c") or item.get("corregida", "")
        alt = item.get("a") if "a" in item else item.get("alternativa")

        if not orig or not corr:
            continue

        # Reemplazar en el texto manteniendo coherencia
        patron = rf"\b{re.escape(orig)}\b"
        texto_reconstruido = re.sub(patron, corr, texto_reconstruido, flags=re.IGNORECASE)

        # Clasificación lógica vía Prolog
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
        "texto_corregido": texto_reconstruido,
        "estilo": resultado_ia.get("estilo", {})
    })

# ==============================================================================
# PUNTO DE ENTRADA PRINCIPAL (MAIN)
# ==============================================================================
if __name__ == "__main__":
    app.run(debug=True, port=5000)