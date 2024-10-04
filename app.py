import os
import streamlit as st
import google.generativeai as genai
import pdfplumber
from datetime import datetime
from dotenv import load_dotenv


def load_config():
    # Cargar las variables de entorno
    load_dotenv()
    config = {
        "GOOGLE_API_KEY": os.getenv("GOOGLE_API_KEY"),
        "GEMINI_MODEL_NAME": os.getenv("GEMINI_MODEL_NAME", "gemini-1.5-flash-002"),
        "MAX_FILE_SIZE_MB": min(
            int(os.getenv("MAX_FILE_SIZE_MB", 10)), 50
        ),  # Máximo 50 MB
        "MAX_INPUT_LENGTH": int(os.getenv("MAX_INPUT_LENGTH", 6000)),
        "ACCEPTED_MODELS": ["gemini-1.5-flash-002", "gemini-1.5-pro-002"],
    }
    return config


def extraer_texto_de_pdf(archivo_pdf):
    texto = ""
    try:
        with pdfplumber.open(archivo_pdf) as pdf:
            for pagina in pdf.pages:
                texto_pagina = pagina.extract_text() or ""
                texto += texto_pagina
        if not texto.strip():
            st.warning(
                "No se pudo extraer texto del PDF. Por favor, verifica que el archivo sea legible."
            )
            return None
    except Exception as e:
        st.error(f"Error al procesar el PDF: {e}")
        return None
    return texto


def extraer_datos_articulo(texto_pdf, modelo_nombre, max_input_length):
    # Truncar el texto si excede la longitud máxima permitida
    if len(texto_pdf) > max_input_length:
        st.warning(
            "El texto del PDF es demasiado largo y será truncado para ajustarse al límite permitido."
        )
        texto_pdf = texto_pdf[:max_input_length]

    # Construir el prompt (no modificar)
    prompt = f"""
Eres una herramienta de inteligencia artificial de extracción avanzada de datos de artículos científicos necesito realizar distintos post en redes sociales sobre el análisis de distintos artículos científicos y necesito que me ayude se extraer la información necesaria para que después yo pueda realizar esos post necesito que me ayudes en la extracción de los datos yo te facilitará el artículo y tú en base a la día siguiente extraerás la información de manera estructurada punto por punto y contestando a todas las preguntas que te propongo:

Para crear un post eficaz basado en un artículo científico, los detalles que necesito extraer de dicho artículo son los siguientes:

### 0. **En qué revista y en qué fecha se ha publicado? Quienes son los investigadores, de que universidad?**

### 1. **Tema central o enfoque del estudio**
   - **¿De qué trata el estudio?**: Una frase o dos que expliquen el objetivo principal. Ejemplo: *"Este estudio analiza los efectos de la introducción de una nueva dieta en el bienestar de los primates en cautiverio."*
   - Es útil saber el *problema o la pregunta de investigación* que el estudio aborda.

### 2. **Especies o animales estudiados**
   - **¿Qué animales están involucrados en el estudio?**: Enumera las especies específicas que fueron estudiadas. Ejemplo: *"Chimpancés y gorilas de montaña en zoológicos europeos."*
   - Si es un estudio comparativo entre especies, resalta eso.

### 3. **Método o metodología utilizada**
   - **¿Cómo se realizó el estudio?**: Es clave describir las técnicas, herramientas o enfoques aplicados en términos claros. Ejemplo: *"Se utilizó un método de enriquecimiento ambiental basado en juegos interactivos que promueven la actividad física."*
   - **¿Qué tipo de experimento o prueba?**: Observación directa, análisis de muestras, encuestas, tecnología innovadora (ej. cámaras térmicas, láser tridimensional, etc.).

### 4. **Resultados principales**
   - **¿Qué se encontró?**: Los hallazgos más importantes del estudio, idealmente en términos cuantitativos o cualitativos claros. Ejemplo: *"Los primates mostraron un 30% más de actividad física con la nueva dieta."*
   - Si hubo efectos sorprendentes o contrarios a las expectativas, esos detalles son valiosos.
   - **Comparaciones o diferencias clave**: Si el estudio comparó distintas condiciones, se debe mencionar qué opción fue más efectiva o favorable.

### 5. **Importancia o impacto**
   - **¿Por qué es relevante este estudio?**: Describe cómo estos hallazgos afectan el bienestar de los animales, las prácticas de manejo en zoológicos o avances científicos. Ejemplo: *"Este estudio sugiere que los cambios en la dieta pueden reducir el estrés en primates, lo que mejoraría su calidad de vida en cautiverio."*
   - **Aplicaciones prácticas**: ¿Puede ayudar a otras instituciones zoológicas? ¿Es relevante para la conservación, salud animal, o manejo diario?

### 6. **Conclusiones y recomendaciones**
   - **¿Qué conclusiones sacan los autores?**: Un resumen de las conclusiones clave.
   - **¿Hay alguna recomendación específica para la comunidad zoológica?**: Por ejemplo, implementar nuevas tecnologías, ajustar prácticas de alimentación, etc.

### 7. **Detalles adicionales (si es relevante)**
   - **Limitaciones del estudio**: Si el artículo menciona algún aspecto que los autores consideran una limitación (muestra pequeña, corto plazo, etc.), a veces es importante mencionarlo.
   - **Futuras investigaciones**: Si el artículo sugiere nuevas líneas de investigación, esto también puede ser un punto interesante a destacar.

### 8.**Crea en formato APA7 la referencia correcta para este articulo y enlaza el DOI**
---

Si me proporcionas estos puntos en resumen, puedo generar un post atractivo que resalte la información más valiosa del paper. En resumen, lo más importante es el tema del estudio, los animales, los métodos, los resultados clave y su relevancia para la comunidad.

    Contenido del artículo:
    {texto_pdf}
    """

    with st.spinner("Extrayendo datos del artículo científico..."):
        try:
            modelo = genai.GenerativeModel(modelo_nombre)
            respuesta = modelo.generate_content(
                prompt, generation_config=genai.types.GenerationConfig(temperature=0)
            )
            return respuesta.text.strip()
        except Exception as e:
            st.error(f"Error al generar la respuesta con el modelo: {e}")
            return None


def mostrar_resultados(texto_extraido):
    if texto_extraido:
        st.header("Datos Extraídos del Artículo Científico")
        st.text_area("Contenido Extraído", texto_extraido, height=400, disabled=True)

        # Botón de descarga para el archivo Markdown
        md_filename = f"articulo_extraido_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        st.download_button(
            label="Descargar como Markdown",
            data=texto_extraido,
            file_name=md_filename,
            mime="text/markdown",
        )

        st.info("Puedes seleccionar y copiar el texto del área de texto si lo deseas.")
    else:
        st.warning("No se pudieron extraer datos del artículo.")


def main():
    config = load_config()

    # Verificar la API key
    if not config["GOOGLE_API_KEY"]:
        st.error(
            "No se encontró la GOOGLE_API_KEY en el archivo .env. Por favor, asegúrate de definir esta clave en el archivo .env siguiendo las instrucciones proporcionadas."
        )
        st.stop()

    # Configurar la API de GenAI
    genai.configure(api_key=config["GOOGLE_API_KEY"])

    st.set_page_config(
        page_title="Extractor de Artículos Científicos", page_icon="📄", layout="wide"
    )

    st.title("📄 Extractor de Datos de Artículos Científicos")

    st.markdown("""
    Esta aplicación te permite extraer información clave de artículos científicos en formato PDF usando la API de Google Gemini.

    ### Cómo usar:
    1. Sube tu archivo PDF.
    2. Espera mientras procesamos y extraemos la información clave del artículo.
    3. Explora los resultados extraídos y utiliza los botones para copiar o descargar la información.
    """)

    archivo_pdf = st.file_uploader("Selecciona tu archivo PDF", type="pdf")

    if archivo_pdf is not None:
        if archivo_pdf.size > config["MAX_FILE_SIZE_MB"] * 1024 * 1024:
            st.error(
                f"El archivo es demasiado grande. Por favor, sube un archivo de menos de {config['MAX_FILE_SIZE_MB']} MB."
            )
            return

        texto_pdf = extraer_texto_de_pdf(archivo_pdf)

        if texto_pdf:
            modelo_nombre = config["GEMINI_MODEL_NAME"]
            if modelo_nombre not in config["ACCEPTED_MODELS"]:
                st.error(
                    f"El modelo especificado ({modelo_nombre}) no es válido. Por favor, verifica la configuración."
                )
                st.stop()

            texto_extraido = extraer_datos_articulo(
                texto_pdf, modelo_nombre, config["MAX_INPUT_LENGTH"]
            )

            if texto_extraido:
                st.success("¡Datos extraídos con éxito!")
                mostrar_resultados(texto_extraido)
            else:
                st.error("No se pudieron extraer datos del artículo.")
        else:
            st.error(
                "No se pudo extraer texto del PDF. Por favor, verifica que el archivo sea legible."
            )


if __name__ == "__main__":
    main()
