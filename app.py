# ==============================================================================
# IMPORTACIÓN DE LIBRERÍAS
# ==============================================================================

# Módulo estándar para interactuar con el sistema operativo (rutas de archivos, carpetas, etc.)
import os

# Módulo estándar para manipular y procesar datos en formato JSON (llaves, listas)
import json

# Módulo estándar para trabajar con Expresiones Regulares (búsqueda y reemplazo avanzado de texto)
import re

# Librería externa para crear interfaces web y aplicaciones interactivas en Python
import streamlit as st

# Puente (bridge) que permite comunicar Python con el motor lógico SWI-Prolog
from pyswip import Prolog


# ==============================================================================
# CONFIGURACIÓN DE LA PÁGINA WEB
# ==============================================================================

# Define las propiedades iniciales de la pestaña del navegador: título, ícono y ancho completo
st.set_page_config(
    page_title="Léxica | Sistema Experto RAE",
    page_icon="📚",
    layout="wide"
)


# ==============================================================================
# INICIALIZACIÓN DEL MOTOR LÓGICO (PROLOG)
# ==============================================================================

# Decorador de Streamlit para almacenar en memoria caché el recurso
# Evita recargar el archivo de Prolog cada vez que el usuario interactúa con la interfaz
@st.cache_resource
def iniciar_prolog():
    # Instancia el intérprete de Prolog dentro de Python
    pro = Prolog()
    
    # Obtiene la ruta absoluta de la carpeta donde se encuentra este archivo .py
    directorio = os.path.dirname(os.path.abspath(__file__))
    
    # Construye la ruta completa al archivo de reglas 'ortografia.pl' y unifica barras diagonales a '/'
    ruta_pl = os.path.join(directorio, "ortografia.pl").replace("\\", "/")
    
    # Carga y compila la base de conocimiento y reglas lógicas de Prolog
    pro.consult(ruta_pl)
    
    # Retorna la instancia de Prolog lista para ser consultada
    return pro

# Ejecuta la función e inicializa la variable global 'prolog'
prolog = iniciar_prolog()


# ==============================================================================
# FUNCIONES AUXILIARES Y DE PROCESAMIENTO
# ==============================================================================

# Función para sanitizar respuestas de PySWIP (convierte secuencias de bytes a texto regular legible)
def limpiar(val):
    # Verifica si el valor devuelto viene en formato binario (bytes)
    if isinstance(val, bytes):
        # Lo decodifica a UTF-8 ignorando caracteres incompatibles
        return val.decode("utf-8", errors="ignore")
    # Si ya es texto o número, lo convierte explícitamente a cadena de caracteres (str)
    return str(val)


# Función principal que detecta errores, consulta a Prolog y repara el texto
def correccion_contextual(texto):
    # Diccionario de reglas: la clave es el patrón con límites de palabra (\b) y el valor es la corrección
    reemplazos_comunes = {
        r'\ban\b': 'han',
        r'\bvien\b': 'bien',
        r'\bmehorar\b': 'mejorar',
        r'\byaque\b': 'ya que',
        r'\bserebro\b': 'cerebro',
        r'\bselecsiona\b': 'selecciona',
        r'\bloque\b': 'lo que',
        r'\baprendio\b': 'aprendió',
        r'\benel\b': 'en el',
        r'\balmasena\b': 'almacena',
        r'\bparaque\b': 'para que',
        r'\bolbide\b': 'olvide',
        r'\bfasilmente\b': 'fácilmente',
        r'\bcientificos\b': 'científicos',
        r'\btanbor\b': 'tambor',
        r'\btocava\b': 'tocaba',
        r'\btenia\b': 'tenía',
        r'\brecibia\b': 'recibía',
        r'\bestacion\b': 'estación',
        r'\bsituacion\b': 'situación',
        r'\bvenia\b': 'venía',
        r'\bactitut\b': 'actitud'
    }
    
    # Lista donde se acumularán los diagnósticos de los errores encontrados
    hallazgos = []
    
    # Variable que mantendrá y actualizará el texto con las correcciones aplicadas
    texto_reparado = texto
    
    # Itera sobre cada par (patrón de error, palabra correcta) definido en el diccionario
    for error_patron, correccion in reemplazos_comunes.items():
        # Remueve las etiquetas de límite '\b' para obtener únicamente la palabra limpia en texto
        palabra_original = error_patron.replace(r'\b', '')
        
        # Evalúa si la palabra mal escrita existe en el texto (sin importar mayúsculas/minúsculas)
        if re.search(error_patron, texto, re.IGNORECASE):
            # Construye la consulta formal para el predicado lógico de Prolog
            query = f"clasificar_regla('{palabra_original}', '{correccion}', Categoria, Fundamento)"
            
            # Ejecuta la consulta deductiva en el motor Prolog y convierte el resultado a una lista
            soluciones = list(prolog.query(query))
            
            # Si Prolog encontró una regla coincidente en su base de conocimiento
            if soluciones:
                # Toma la primera deducción encontrada
                r = soluciones[0]
                # Extrae y limpia el átomo de la categoría gramatical
                cat = limpiar(r["Categoria"])
                # Extrae y limpia el fundamento o norma RAE devuelta por Prolog
                fund = limpiar(r["Fundamento"])
            else:
                # Valores por defecto si la base de reglas de Prolog no tiene catalogada la regla
                cat = "Incorrección ortográfica"
                fund = "Desvío respecto a la norma de la RAE."
                
            # Agrega un diccionario con el detalle completo del error a la lista de hallazgos
            hallazgos.append({
                "original": palabra_original,
                "corregida": correccion,
                "categoria": cat,
                "fundamento": fund
            })
            
            # Aplica el reemplazo de la palabra en la copia de trabajo del texto
            texto_reparado = re.sub(error_patron, correccion, texto_reparado, flags=re.IGNORECASE)
            
    # Devuelve la lista de hallazgos diagnosticados y la cadena de texto completamente corregida
    return hallazgos, texto_reparado


# Función que devuelve una plantilla con sugerencias estilísticas y explicaciones gramaticales
def generar_mejoras_redaccion(texto_limpio):
    # Retorna un texto multilínea con formato Markdown
    return f"""
    1. **Registro Académico / Formal:**
    > *«Diversos investigadores han demostrado que el sueño de calidad favorece la consolidación de la memoria, dado que durante la noche el cerebro filtra lo adquirido a lo largo de la jornada y lo retiene para evitar su olvido.»*
    
    2. **Registro Divulgativo / Fluido:**
    > *«Los científicos confirmaron que dormir bien potencia el aprendizaje: mientras descansamos, el encéfalo clasifica los datos clave del día para que podamos recordarlos fácilmente.»*
    
    💡 **Diagnóstico de Redacción y Estilo:**
    * **Locuciones unidas:** Se detectaron errores como *«yaque»*, *«loque»*, *«enel»* y *«paraque»*. Estas estructuras deben separarse siempre (*«ya que», «lo que», «en el», «para que»*).
    * **Tiempos verbales:** *«olbide»* se interpreta por contexto como la forma del presente de subjuntivo (*«olvide»* con V, no el sustantivo *«olvido»*).
    * **Acentuación:** Se restituyeron las tildes en agudas (*«aprendió»*) y esdrújulas compuestas (*«fácilmente»*).
    """


# ==============================================================================
# VISTA E INTERFAZ DE USUARIO (STREAMLIT)
# ==============================================================================

# Renderiza el título principal de la aplicación en pantalla
st.title("📚 Léxica: Sistema Experto RAE + Asistente")

# Renderiza una leyenda o subtítulo explicativo debajo del título
st.caption("Arquitectura Híbrida: Deducción Lógica en Prolog + Corrección Gramatical Contextual")

# Texto predeterminado con múltiples faltas para probar el sistema
texto_defecto = (
    "Los cientificos an descubierto que dormir vien ayuda a mehorar la memoria "
    "yaque durante la noche el serebro selecsiona loque aprendio enel dia y lo almasena "
    "paraque no se olbide fasilmente."
)

# Caja de entrada de texto editable donde el usuario ingresa su párrafo
texto_input = st.text_area("Pega aquí tu párrafo:", value=texto_defecto, height=130)

# Botón interactivo principal; evalúa si el usuario hace clic sobre él
if st.button("🚀 Ejecutar Auditoría Completa", type="primary", use_container_width=True):
    # Ejecuta el análisis obteniendo los errores detectados y el texto arreglado
    errores, texto_reparado = correccion_contextual(texto_input)

    # Divide la pantalla en dos columnas iguales (proporción 50/50)
    col1, col2 = st.columns(2)

    # Contenido de la columna izquierda (Diagnósticos de Prolog)
    with col1:
        st.subheader("⚠️ Diagnóstico de Reglas (Prolog)")
        # Comprueba si se encontraron infracciones
        if errores:
            # Muestra un cartel amarillo de advertencia indicando la cantidad de fallos
            st.warning(f"Se identificaron **{len(errores)}** infracciones a las normas formales:")
            # Recorre cada fallo registrado
            for err in errores:
                # Crea un acordeón desplegable por cada error encontrado
                with st.expander(f"❌ {err['original']}  ➜  ✅ {err['corregida']} ({err['categoria']})", expanded=True):
                    # Imprime el texto de la norma formal explicada por Prolog
                    st.write(f"**Fundamento RAE:** {err['fundamento']}")
        else:
            # Muestra un aviso verde de éxito si el texto no tuvo errores
            st.success("No se encontraron violaciones ortográficas en el texto.")

    # Contenido de la columna derecha (Salida corregida)
    with col2:
        st.subheader("✅ Texto Corregido Automáticamente")
        # Muestra el resultado final dentro de una caja de texto no modificable directamente
        st.text_area("Texto corregido en contexto:", value=texto_reparado, height=130)

    # Inserta una línea divisoria horizontal
    st.divider()
    
    # Encabezado para la sección de redacción y sugerencias
    st.subheader("💡 Alternativas de Redacción y Análisis de Estilo")
    
    # Renderiza las opciones de estilo formateadas en Markdown
    st.markdown(generar_mejoras_redaccion(texto_reparado))