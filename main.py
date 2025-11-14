import os
import traceback
import asyncio
import html
import re
from datetime import datetime

# --- IMPORTACIONES DE TUS DEPENDENCIAS ---
try:
    from flask import Flask, request, send_file, after_this_request
    from reportlab.lib.pagesizes import A4
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable, Table, TableStyle
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import cm
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_JUSTIFY, TA_CENTER
    import g4f
except ImportError:
    print("Instalando dependencias... esto puede tardar un momento en Replit.")
    # Replit a veces necesita que instales desde el shell,
    # pero a menudo detecta las importaciones.
    pass

# --- TU CÓDIGO HTML (AHORA DENTRO DE PYTHON) ---
# En lugar de un archivo templates/index.html, lo ponemos aquí.
HTML_CONTENT = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Generador Académico</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f9fafe;
            color: #1F2937;
        }
        .container {
            max-width: 600px;
            margin: 0 auto;
            background: #FFFFFF;
            padding: 25px;
            border-radius: 15px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.05);
        }
        h1 {
            font-size: 24px;
            font-weight: bold;
            text-align: center;
            color: #1F2937;
            margin-bottom: 25px;
        }
        label {
            display: block;
            margin-bottom: 5px;
            font-weight: 600;
            font-size: 14px;
            color: #4B5563;
        }
        input, textarea {
            width: 100%;
            padding: 12px;
            box-sizing: border-box; /* Importante para el padding */
            border: 1px solid #E5E7EB;
            border-radius: 8px;
            margin-bottom: 15px;
            font-size: 16px;
            background: #F9FAFB;
        }
        textarea {
            height: 120px;
            resize: vertical;
        }
        button {
            width: 100%;
            padding: 15px;
            background-color: #1F2937;
            color: white;
            border: none;
            border-radius: 8px;
            font-size: 16px;
            font-weight: bold;
            cursor: pointer;
            transition: background-color 0.2s;
        }
        button:hover {
            background-color: #374151;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Redactor Académico IA</h1>
        
        <form action="/generar" method="POST">
            <label for="nombre">Nombre del Estudiante:</label>
            <input type="text" id="nombre" name="nombre" required>

            <label for="matricula">Matrícula:</label>
            <input type="text" id="matricula" name="matricula" required>

            <label for="fecha">Fecha:</label>
            <input type="text" id="fecha" name="fecha" required>

            <label for="tema">Tema General:</label>
            <input type="text" id="tema" name="tema" required>

            <label for="contexto">Instrucciones / Texto (Opcional):</label>
            <textarea id="contexto" name="contexto"></textarea>

            <button type="submit">Generar Informe PDF</button>
        </form>
    </div>
</body>
</html>
"""


# --- TU LÓGICA DE IA (SIN CAMBIOS) ---
async def obtener_respuesta_ia(tema, contexto_extra):
    try:
        if contexto_extra and len(contexto_extra) > 5:
            prompt_sistema = (
                "Eres un asistente académico experto. Responde basándote en las instrucciones proporcionadas. "
                "Usa un tono formal. Usa negritas (**) para resaltar títulos."
            )
            mensaje_usuario = f"TEMA: {tema}\n\nINSTRUCCIONES/TEXTO BASE:\n{contexto_extra}"
        else:
            prompt_sistema = (
                "Eres un investigador académico. Redacta un informe técnico.y no te puedes dar el lujo de decirme algo como esto,¿Desea que profundice en algún aspecto específico? o algo asi no me puedes poner preguntas que son para mi al final "
                "Estructura: **Introducción**, **Desarrollo**, **Conclusión**."
                "Usa un tono formal y denso. y debes agregar las bibliografias correspondientes y correctas "
            )
            mensaje_usuario = f"Informe sobre: {tema}"

        response = await g4f.ChatCompletion.create_async(
            model=g4f.models.gpt_4,
            messages=[
                {"role": "system", "content": prompt_sistema},
                {"role": "user", "content": mensaje_usuario}
            ],
        )
        if not response: return "Error: Respuesta vacía."
        return response
    except Exception as e:
        return f"Error generando respuesta: {str(e)}"

def consultar_ia_sync(tema, contexto_extra):
    try:
        return asyncio.run(obtener_respuesta_ia(tema, contexto_extra))
    except Exception as e:
        return f"Error de conexión: {e}"

# --- TU LÓGICA DE PDF (SIN CAMBIOS) ---
def generar_pdf_profesional(nombre, matricula, fecha, tema, contenido):
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        # El archivo se guarda temporalmente en el servidor
        nombre_archivo = f"temp_informe_{timestamp}.pdf" 
        
        doc = SimpleDocTemplate(nombre_archivo, pagesize=A4,
                                rightMargin=2.5*cm, leftMargin=2.5*cm,
                                topMargin=2.5*cm, bottomMargin=2.5*cm)
        
        estilos = getSampleStyleSheet()
        elementos = []
        color_titulo = colors.HexColor("#1F2937") 
        color_acento = colors.HexColor("#2563EB") 
        color_texto = colors.HexColor("#374151")  
        estilo_titulo = ParagraphStyle('TituloDoc', parent=estilos['Title'], fontSize=24, textColor=color_titulo, alignment=TA_CENTER, spaceAfter=20, fontName='Helvetica-Bold')
        estilo_cuerpo = ParagraphStyle('Cuerpo', parent=estilos['Normal'], fontSize=11, leading=16, alignment=TA_JUSTIFY, textColor=color_texto, fontName='Helvetica')
        estilo_tabla_lbl = ParagraphStyle('TB', parent=estilos['Normal'], fontSize=11, fontName='Helvetica-Bold', textColor=color_titulo)
        estilo_tabla_txt = ParagraphStyle('TT', parent=estilos['Normal'], fontSize=11, textColor=colors.black)
        elementos.append(Paragraph("INFORME ACADÉMICO", estilo_titulo))
        elementos.append(HRFlowable(width="100%", thickness=2, color=color_acento, spaceAfter=20))
        datos = [
            [Paragraph("Estudiante:", estilo_tabla_lbl), Paragraph(html.escape(nombre), estilo_tabla_txt)],
            [Paragraph("Matrícula:", estilo_tabla_lbl), Paragraph(html.escape(matricula), estilo_tabla_txt)],
            [Paragraph("Fecha:", estilo_tabla_lbl), Paragraph(html.escape(fecha), estilo_tabla_txt)],
            [Paragraph("Tema:", estilo_tabla_lbl), Paragraph(html.escape(tema), estilo_tabla_txt)]
        ]
        t = Table(datos, colWidths=[4*cm, 11*cm])
        t.setStyle(TableStyle([('ALIGN', (0,0), (-1,-1), 'LEFT'), ('VALIGN', (0,0), (-1,-1), 'MIDDLE'), ('BOTTOMPADDING', (0,0), (-1,-1), 8)]))
        elementos.append(t)
        elementos.append(HRFlowable(width="100%", thickness=0.5, color=colors.lightgrey, spaceAfter=20))
        txt = html.escape(contenido)
        txt = re.sub(r'(?m)^#+\s*(.*?)$', r'<b>\1</b>', txt)
        txt = txt.replace("\n", "<br/>")
        while "**" in txt:
            txt = txt.replace("**", "<b>", 1)
            txt = txt.replace("**", "</b>", 1)
        elementos.append(Paragraph(txt, estilo_cuerpo))
        doc.build(elementos)
        
        return nombre_archivo

    except Exception as e:
        traceback.print_exc()
        return None

# --- EL SERVIDOR WEB FLASK ---

app = Flask(__name__)

# Ruta para mostrar la página principal (el formulario HTML)
@app.route('/')
def index():
    # Devuelve el HTML que guardamos en la variable de arriba
    return HTML_CONTENT

# Ruta que recibe los datos del formulario
@app.route('/generar', methods=['POST'])
def generar_informe():
    try:
        # 1. Obtener datos del formulario web
        nombre = request.form.get('nombre')
        matricula = request.form.get('matricula')
        fecha = request.form.get('fecha')
        tema = request.form.get('tema')
        contexto = request.form.get('contexto')

        # 2. Llamar a tu lógica de IA
        respuesta = consultar_ia_sync(tema, contexto)

        if not respuesta or "Error" in respuesta:
            return f"Fallo en la IA: {respuesta}", 500

        # 3. Llamar a tu lógica de PDF
        archivo_pdf = generar_pdf_profesional(nombre, matricula, fecha, tema, respuesta)

        if not archivo_pdf:
            return "Error: No se pudo crear el PDF.", 500

        # 4. Enviar el archivo PDF al usuario para que lo descargue
        @after_this_request
        def remove_file(response):
            try:
                os.remove(archivo_pdf)
            except Exception as e:
                print(f"Error borrando archivo: {e}")
            return response

        return send_file(
            archivo_pdf,
            as_attachment=True,
            download_name=f"Informe_{nombre.replace(' ', '_')}.pdf"
        )
    except Exception as e:
        traceback.print_exc()
        return f"Error interno del servidor: {str(e)}", 500

# --- INICIA EL SERVIDOR ---
# Esto permite que Replit ejecute la app
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
