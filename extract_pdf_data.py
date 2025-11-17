import PyPDF2
import os
import re
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from datetime import datetime
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, simpledialog, messagebox

# ==================== FUNCIONES DE EXTRACCIÓN ====================

def extract_text_from_pdf(pdf_input):
    """
    Extrae todo el texto de un PDF.
    pdf_input: puede ser una ruta (str) o un objeto file-like (BytesIO)
    """
    # Si es ruta
    if isinstance(pdf_input, str):
        if not os.path.exists(pdf_input):
            return f"Error: El archivo no se encontró en la ruta: {pdf_input}"
        file = open(pdf_input, 'rb')
        close_file = True
    else:
        # file-like object
        file = pdf_input
        close_file = False

    try:
        reader = PyPDF2.PdfReader(file)
        num_pages = len(reader.pages)
        print(f"El PDF tiene {num_pages} páginas.")

        full_text = ""
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                full_text += page_text + "\n--- Fin de Página ---\n"

        return full_text
    except Exception as e:
        return f"Ocurrió un error al procesar el PDF: {e}"
    finally:
        if close_file:
            file.close()

def extract_vendedor_y_rut(text):
    """Busca el nombre del cliente y su RUT en el texto extraído."""
    pattern_nombre = r"Señor(?:es)?:\s*(.*?)(?=\n|Dirección|R\.U\.T)"
    match_nombre = re.search(pattern_nombre, text, re.DOTALL | re.IGNORECASE)
    
    pattern_rut = r"R\.U\.T[:\s]+(\d{1,2}\.\d{3}\.\d{3}-[\dkK]|\d{7,8}-[\dkK])"
    match_rut = re.search(pattern_rut, text, re.IGNORECASE)
    
    resultado = {}
    resultado['nombre'] = match_nombre.group(1).strip() if match_nombre else "No encontrado"
    resultado['rut'] = match_rut.group(1) if match_rut else "No encontrado"
    
    return resultado

def extract_direccion(text):
    """Extrae la dirección del cliente."""
    pattern = r"Datos Cliente.*?Dirección:\s*(.*?)(?=\n|Actividad)"
    match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
    
    if match:
        return match.group(1).strip()
    return "No encontrada"

def extract_comuna(text):
    """Extrae la comuna del cliente."""
    pattern = r"Comuna:\s*([A-ZÁÉÍÓÚÑa-záéíóúñ\s]+)"
    match = re.search(pattern, text, re.IGNORECASE)
    
    if match:
        return match.group(1).strip()
    return "No encontrada"

def extract_vendedor_info(text):
    """Extrae información del vendedor que atendió."""
    pattern = r"Vendedor:\s*([^\n]+)"
    match = re.search(pattern, text, re.IGNORECASE)
    
    if match:
        return match.group(1).strip()
    return "No encontrado"

def extract_fecha(text):
    """Extrae la fecha de la cotización."""
    pattern = r"Fecha:\s*(\d{2}\.\d{2}\.\d{4})"
    match = re.search(pattern, text, re.IGNORECASE)
    
    if match:
        return match.group(1).strip()
    return "No encontrada"

def extract_totales_bloque(text):
    """Extrae todos los totales de un bloque."""
    pattern = r"TOTAL\s+AFECTO:\s*\n?\s*DESCUENTO:\s*\n?\s*SUBTOTAL:\s*\n?\s*IVA:\s*\n?\s*TOTAL\s*:\s*\n?\s*([\d.,]+)\s*\n?\s*([\d.,]+)\s*\n?\s*([\d.,]+)\s*\n?\s*([\d.,]+)\s*\n?\s*([\d.,]+)"
    
    match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
    
    if match:
        return {
            'total_afecto': match.group(1).strip(),
            'descuento': match.group(2).strip(),
            'subtotal': match.group(3).strip(),
            'iva': match.group(4).strip(),
            'total_final': match.group(5).strip()
        }
    
    return {
        'total_afecto': "No encontrado",
        'descuento': "No encontrado",
        'subtotal': "No encontrado",
        'iva': "No encontrado",
        'total_final': "No encontrado"
    }

def extract_numero_cotizacion(text):
    """Extrae el número de cotización."""
    pattern = r"N°\s*(\d+)"
    match = re.search(pattern, text)
    
    if match:
        return match.group(1).strip()
    return "No encontrado"

import re

import re

def extract_productos_mejorado(text):
    """
    Extrae TODOS los productos/materiales de la cotización con debugging mejorado.
    """
    productos = []
    
    print("\n" + "="*100)
    print("🔍 INICIANDO EXTRACCIÓN DE PRODUCTOS - DEBUG MODE")
    print("="*100)
    
    # 1️⃣ Buscar la sección de productos
    seccion_productos = re.search(
        r'Pos\s*Material\s*Descripción.*?(?=TOTAL AFECTO|DESPACHO:|$)', 
        text, 
        re.DOTALL | re.IGNORECASE
    )
    
    if not seccion_productos:
        print("❌ No se encontró la sección de productos")
        # DEBUG: Buscar dónde están los encabezados
        lines = text.split('\n')
        for i, line in enumerate(lines):
            if 'Pos' in line or 'Material' in line or 'Descripción' in line:
                print(f"📍 Línea {i}: {line}")
        return productos
    
    texto_productos = seccion_productos.group(0)
    
    # DEBUG: Mostrar la sección completa de productos
    print("\n📄 SECCIÓN DE PRODUCTOS ENCONTRADA:")
    print("-" * 100)
    print(texto_productos[:1000])  # Primeros 1000 caracteres
    print("-" * 100)
    
    # 2️⃣ Analizar línea por línea para entender la estructura
    lineas = texto_productos.split('\n')
    print(f"\n📊 Total de líneas en la sección: {len(lineas)}")
    print("\n🔍 ANALIZANDO PRIMERAS 20 LÍNEAS:")
    print("-" * 100)
    for i, linea in enumerate(lineas[:20]):
        if linea.strip():
            print(f"Línea {i:2d}: |{linea}|")
    print("-" * 100)
    
    # 3️⃣ Patrones a probar
    patrones = [
        # Patrón 1: Formato estándar con todos los campos
        r'(\d+)\s+(\d+)\s+([^\n]+?)\s+(\d+)\s+(UN|ROM|KG|MT|M2|M3)\s+([\d.,]+)\s+([\d.,]+)\s+([\d.,]+)\s+([\d.,]+)',
        
        # Patrón 2: Más flexible con espacios
        r'(\d+)\s+(\d+)\s+(.+?)\s+(\d+)\s+(\w+)\s+([\d.,]+)\s+([\d.,]+)\s+([\d.,]+)\s+([\d.,]+)',
        
        # Patrón 3: Considerando posibles saltos de línea
        r'(\d+)\s+(\d+)\s+(.+?)\s+(\d+)\s+(\w+)\s+\$?\s*([\d.,]+)\s+\$?\s*([\d.,]+)\s+\$?\s*([\d.,]+)\s+\$?\s*([\d.,]+)',
        
        # Patrón 4: Con símbolos de moneda opcionales
        r'(\d+)\s+(\d+)\s+(.+?)\s+(\d+)\s+([A-Z]+)\s+\$?\s*([\d\s.,]+)\s+\$?\s*([\d\s.,]+)\s+\$?\s*([\d\s.,]+)\s+\$?\s*([\d\s.,]+)',
    ]
    
    matches = []
    patron_exitoso = None
    
    for idx, pattern in enumerate(patrones, 1):
        print(f"\n🧪 PROBANDO PATRÓN {idx}:")
        print(f"   {pattern[:80]}...")
        temp_matches = re.findall(pattern, texto_productos, re.IGNORECASE)
        print(f"   ✓ Encontrados: {len(temp_matches)} productos")
        
        if temp_matches and len(temp_matches) > len(matches):
            matches = temp_matches
            patron_exitoso = idx
            print(f"   🎯 MEJOR RESULTADO HASTA AHORA!")
    
    if not matches:
        print("\n❌ NO SE ENCONTRARON PRODUCTOS CON NINGÚN PATRÓN")
        print("\n💡 SUGERENCIA: Muestra las primeras 30 líneas del PDF para análisis manual")
        return productos
    
    print(f"\n✅ PATRÓN EXITOSO: #{patron_exitoso}")
    print(f"📦 Total de productos encontrados: {len(matches)}")
    
    # 4️⃣ Procesar cada producto encontrado
    print("\n" + "="*100)
    print("📋 DETALLE DE PRODUCTOS EXTRAÍDOS:")
    print("="*100)
    
    for i, match in enumerate(matches, 1):
        try:
            print(f"\n--- PRODUCTO {i} ---")
            print(f"Raw match: {match}")
            
            producto = {
                'posicion': match[0].strip(),
                'codigo_material': match[1].strip(),
                'descripcion': match[2].strip(),
                'cantidad': match[3].strip(),
                'unidad': match[4].strip(),
                'precio_unitario_original': match[5].strip() if len(match) > 5 else "0",
                'precio_con_descuento': match[6].strip() if len(match) > 6 else "0",
                'valor_con_descuento': match[7].strip() if len(match) > 7 else "0",
                'valor_total': match[8].strip() if len(match) > 8 else "0"
            }
            
            # DEBUG: Mostrar cada campo
            print(f"  Pos: {producto['posicion']}")
            print(f"  Código: {producto['codigo_material']}")
            print(f"  Descripción: {producto['descripcion'][:50]}...")
            print(f"  Cantidad: {producto['cantidad']}")
            print(f"  Unidad: {producto['unidad']}")
            print(f"  Precio Unit Original: {producto['precio_unitario_original']}")
            print(f"  Precio con Descuento: {producto['precio_con_descuento']}")
            print(f"  Valor con Descuento: {producto['valor_con_descuento']}")
            print(f"  Valor Total: {producto['valor_total']}")
            
            productos.append(producto)
            
        except Exception as e:
            print(f"  ❌ ERROR procesando producto {i}: {e}")
            print(f"     Match completo: {match}")
    
    print("\n" + "="*100)
    print(f"🎯 RESUMEN: {len(productos)} productos extraídos exitosamente")
    print("="*100)
    
    return productos
 
def extract_all_data(text):
    """Extrae todos los datos relevantes del PDF."""
    datos = {}
    
    cliente = extract_vendedor_y_rut(text)
    datos['cliente_nombre'] = cliente['nombre']
    datos['cliente_rut'] = cliente['rut']
    datos['cliente_direccion'] = extract_direccion(text)
    datos['cliente_comuna'] = extract_comuna(text)
    
    datos['numero_cotizacion'] = extract_numero_cotizacion(text)
    datos['fecha'] = extract_fecha(text)
    datos['vendedor'] = extract_vendedor_info(text)
    
    totales = extract_totales_bloque(text)
    datos.update(totales)
    
    datos['productos'] = extract_productos_mejorado(text)
    
    return datos

# ==================== FUNCIONES DE GENERACIÓN PDF ====================

def formatear_precio(precio_str):
    """
    Limpia el string del precio, conservando el punto decimal.
    Ejemplo: "$8,383.44" → "8383.44"
    """
    if isinstance(precio_str, str):
        limpio = precio_str.replace('$', '').replace(',', '').strip()
        return limpio
    return str(precio_str)

def formatear_numero_miles_con_decimales(numero):
    """
    Da formato tipo chileno: separador de miles con punto, SIN decimales.
    Ejemplo: 85140.00 -> 85.140
    """
    try:
        n = int(float(numero))
        return f"{n:,}".replace(",", ".")
    except:
        return str(numero)

def formatear_numero_miles(numero):
    """
    Da formato tipo chileno: separador de miles con punto y decimales con coma.
    Ejemplo: 85140.00 -> 85.140,00
    """
    try:
        n = float(numero)
        entero = int(n)
        decimal = int(round((n - entero) * 100))
        entero_str = f"{entero:,}".replace(",", ".")
        return f"{entero_str},{decimal:02d}"
    except:
        return str(numero)

def crear_orden_compra_pdf(datos_cotizacion, numero_oc_manual, nombre_archivo="orden_compra.pdf", ruta_logo="imagenes/logo.png", ruta_firma="imagenes/firma.png"):
    """
    Crea un PDF de Orden de Compra con el formato EASY.
    
    Args:
        datos_cotizacion: Diccionario con los datos extraídos
        numero_oc_manual: Número de orden de compra ingresado manualmente
        nombre_archivo: Nombre del archivo de salida
        ruta_logo: Ruta al archivo de imagen del logo (opcional)
        ruta_firma: Ruta al archivo de imagen de la firma (opcional)
    """
    
    doc = SimpleDocTemplate(
        nombre_archivo,
        pagesize=letter,
        rightMargin=40,
        leftMargin=40,
        topMargin=40,
        bottomMargin=40
    )
    
    elements = []
    styles = getSampleStyleSheet()
    
    # Estilos personalizados
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        textColor=colors.black,
        spaceAfter=12,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )
    
    normal_style = ParagraphStyle(
        'CustomNormal',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.black,
        fontName='Helvetica',
        leading=14
    )
    
    bold_style = ParagraphStyle(
        'CustomBold',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.black,
        fontName='Helvetica-Bold',
        leading=14
    )
    
    # LOGO (si existe)
    if ruta_logo and os.path.exists(ruta_logo):
        try:
            print(f"✓ Cargando logo desde: {ruta_logo}")
            logo = Image(ruta_logo, width=2*inch, height=0.8*inch)
            logo.hAlign = 'CENTER'
            elements.append(logo)
            elements.append(Spacer(1, 0.2*inch))
        except Exception as e:
            print(f"⚠ Error al cargar el logo: {e}")
    else:
        print(f"⚠ Logo no encontrado en: {ruta_logo}")
    
    # TÍTULO con número de OC ingresado manualmente
    titulo = Paragraph(f"ORDEN DE COMPRA {numero_oc_manual}", title_style)
    elements.append(titulo)
    elements.append(Spacer(1, 0.3*inch))
    
    # DATOS DEL COMPRADOR
    cliente_nombre = datos_cotizacion.get('cliente_nombre', 'VICTOR ALMONACID ULLOA')
    cliente_rut = datos_cotizacion.get('cliente_rut', '10.573.124-8')
    
    elements.append(Paragraph(f"<b>{cliente_nombre.upper()}</b>", bold_style))
    elements.append(Paragraph(f"RUT: {cliente_rut}", normal_style))
    elements.append(Paragraph("AVDA LO ESPEJO 01565 LO ESPEJO", normal_style))
    elements.append(Paragraph("TELÉFONO: 974304421", normal_style))
    elements.append(Paragraph(datetime.now().strftime("%d-%m-%Y"), normal_style))
    elements.append(Spacer(1, 0.3*inch))
    
    # DATOS DEL PROVEEDOR
    elements.append(Paragraph("<b>DATOS DEL PROVEEDOR</b>", bold_style))
    elements.append(Spacer(1, 0.1*inch))
    
    vendedor_nombre = datos_cotizacion.get('vendedor', 'BARBARA MONDACA').upper()
    
    proveedor_data = [
        [Paragraph("<b>Razón Social</b>", normal_style), 
         Paragraph("EASY RETAIL S. A", normal_style),
         Paragraph("<b>COMUNA</b>", normal_style), 
         Paragraph("PEDRO AGUIRRE<br/>CERDA", normal_style)],
        [Paragraph("<b>Contacto</b>", normal_style), 
         Paragraph(vendedor_nombre, normal_style),
         Paragraph("<b>RUT</b>", normal_style), 
         Paragraph("76.568.660-1", normal_style)],
        [Paragraph("<b>Dirección</b>", normal_style), 
         Paragraph("JOSE JOAQUIN PRIETO 5531", normal_style),
         Paragraph("<b>Teléfono</b>", normal_style), 
         Paragraph("", normal_style)]
    ]
    
    proveedor_table = Table(proveedor_data, colWidths=[1.3*inch, 2.2*inch, 1*inch, 2.2*inch])
    proveedor_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 3),
        ('RIGHTPADDING', (0, 0), (-1, -1), 3),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
    ]))
    
    elements.append(proveedor_table)
    elements.append(Spacer(1, 0.3*inch))
    
    # TABLA DE PRODUCTOS
    productos_data = [
        [Paragraph("<b>No. Parte /<br/>Tipo</b>", normal_style),
         Paragraph("<b>Descripción del Producto</b>", normal_style),
         Paragraph("<b>Precio<br/>Unitario*</b>", normal_style),
         Paragraph("<b>Cant</b>", normal_style),
         Paragraph("<b>Precio Total*</b>", normal_style)]
    ]
    
    # Agregar productos
    for prod in datos_cotizacion.get('productos', []):
        codigo = prod.get('codigo_material', '')
        descripcion = prod.get('descripcion', '')
        cantidad = prod.get('cantidad', '0')
        
        precio_unit_raw = formatear_precio(prod.get('precio_con_descuento', '0'))
        precio_total_raw = formatear_precio(prod.get('valor_con_descuento', '0'))
        
        precio_unit = formatear_numero_miles(precio_unit_raw)
        precio_total = formatear_numero_miles_con_decimales(precio_total_raw)
        
        productos_data.append([
            Paragraph(codigo, normal_style),
            Paragraph(descripcion, normal_style),
            Paragraph(precio_unit, normal_style),
            Paragraph(cantidad, normal_style),
            Paragraph(precio_total, normal_style)
        ])
    
    productos_table = Table(productos_data, 
                           colWidths=[1*inch, 3*inch, 1*inch, 0.7*inch, 1*inch])
    
    productos_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('ALIGN', (0, 0), (2, -1), 'LEFT'),
        ('ALIGN', (3, 0), (5, -1), 'RIGHT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 4),
        ('RIGHTPADDING', (0, 0), (-1, -1), 4),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LINEBELOW', (0, 0), (-1, 0), 0.5, colors.black),
    ]))
    
    elements.append(productos_table)
    elements.append(Spacer(1, 0.3*inch))
    
    # TOTALES
    neto = datos_cotizacion.get('subtotal', '0')
    iva = datos_cotizacion.get('iva', '0')
    total = datos_cotizacion.get('total_final', '0')
    
    totales_data = [
        ['', '', '', '', Paragraph("<b>NETO</b>", bold_style), Paragraph(neto, normal_style)],
        ['', '', '', '', Paragraph("<b>IVA</b>", bold_style), Paragraph(iva, normal_style)],
        ['', '', '', '', Paragraph("<b>TOTAL</b>", bold_style), Paragraph(total, normal_style)]
    ]
    
    totales_table = Table(totales_data, colWidths=[0.9*inch, 0.7*inch, 2.8*inch, 0.7*inch, 0.7*inch, 1*inch])
    totales_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('ALIGN', (4, 0), (5, -1), 'RIGHT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 4),
        ('RIGHTPADDING', (0, 0), (-1, -1), 4),
    ]))
    
    elements.append(totales_table)
    elements.append(Spacer(1, 0.4*inch))
    
    # FIRMA (si existe)
    if ruta_firma and os.path.exists(ruta_firma):
        try:
            print(f"✓ Cargando firma desde: {ruta_firma}")
            firma = Image(ruta_firma, width=2*inch, height=2*inch)
            firma.hAlign = 'LEFT'
            elements.append(firma)
            elements.append(Spacer(1, 0.1*inch))
        except Exception as e:
            print(f"⚠ Error al cargar la firma: {e}")
    else:
        print(f"⚠ Firma no encontrada en: {ruta_firma}")
    
    # Construir el PDF
    doc.build(elements)
    print(f"\n✓ Orden de Compra generada exitosamente: {nombre_archivo}")
    return nombre_archivo

# ==================== FUNCIÓN PRINCIPAL ====================

def procesar_cotizacion_y_generar_oc(pdf_path, numero_oc_manual, nombre_oc=None, ruta_logo=None, ruta_firma=None, carpeta_salida=None):
    """
    Función principal que extrae datos de una cotización PDF y genera una Orden de Compra.
    
    Args:
        pdf_path: Ruta al archivo PDF de cotización
        numero_oc_manual: Número de orden de compra ingresado manualmente
        nombre_oc: Nombre opcional para el archivo de salida
        ruta_logo: Ruta al archivo de imagen del logo (opcional)
        ruta_firma: Ruta al archivo de imagen de la firma (opcional)
        carpeta_salida: Carpeta donde guardar el archivo
    """
    print("="*95)
    print("PROCESANDO COTIZACIÓN Y GENERANDO ORDEN DE COMPRA")
    print("="*95 + "\n")
    
    # 1. Extraer texto del PDF
    print(f"1. Extrayendo texto del PDF: {os.path.basename(pdf_path)}")
    extracted_text = extract_text_from_pdf(pdf_path)
    
    if "Error:" in extracted_text:
        print(f"❌ {extracted_text}")
        return None
    
    # 2. Extraer todos los datos
    print("2. Extrayendo datos de la cotización...")
    datos = extract_all_data(extracted_text)
    
    # 3. Mostrar resumen
    print("\n" + "="*95)
    print("RESUMEN DE LA COTIZACIÓN EXTRAÍDA")
    print("="*95)
    print(f"\nNúmero de Cotización: {datos['numero_cotizacion']}")
    print(f"Número de OC Manual: {numero_oc_manual}")
    print(f"Fecha: {datos['fecha']}")
    print(f"Cliente: {datos['cliente_nombre']}")
    print(f"RUT: {datos['cliente_rut']}")
    print(f"Vendedor: {datos['vendedor']}")
    print(f"Total de productos: {len(datos['productos'])}")
    print(f"Total Final: ${datos['total_final']}")
    
    # 4. Generar nombre de archivo de salida
    if nombre_oc is None:
        nombre_archivo = f"ORDEN_DE_COMPRA_EASY_{numero_oc_manual}.pdf"
        if carpeta_salida:
            nombre_oc = os.path.join(carpeta_salida, nombre_archivo)
        else:
            nombre_oc = nombre_archivo
    
    # 5. Generar la Orden de Compra
    print(f"\n3. Generando Orden de Compra: {nombre_oc}")
    pdf_generado = crear_orden_compra_pdf(datos, numero_oc_manual, nombre_oc, ruta_logo, ruta_firma)
    
    print("\n" + "="*95)
    print("✅ PROCESO COMPLETADO EXITOSAMENTE")
    print("="*95)
    print(f"\n📄 Archivo generado: {pdf_generado}")
    print(f"📊 Productos incluidos: {len(datos['productos'])}")
    print(f"💰 Total: ${datos['total_final']}\n")
    
    return pdf_generado

# ==================== EJECUCIÓN ====================

if __name__ == "__main__":
    # Crear ventana oculta de tkinter
    root = tk.Tk()
    root.withdraw()
    
    print("="*95)
    print("SELECCIÓN DE ARCHIVO PDF")
    print("="*95)
    print("\n📁 Por favor, selecciona el archivo PDF de cotización a procesar...\n")
    
    # Abrir diálogo para seleccionar archivo PDF
    pdf_file_path = filedialog.askopenfilename(
        title="Selecciona el PDF de cotización",
        filetypes=[("Archivos PDF", "*.pdf"), ("Todos los archivos", "*.*")]
    )
    
    # Verificar si el usuario seleccionó un archivo
    if not pdf_file_path:
        print("❌ No se seleccionó ningún archivo. Proceso cancelado.")
        exit()
    
    print(f"✓ Archivo seleccionado: {os.path.basename(pdf_file_path)}\n")
    
    # Solicitar número de orden de compra
    print("="*95)
    print("INGRESO DE NÚMERO DE ORDEN DE COMPRA")
    print("="*95)
    
    numero_oc = simpledialog.askstring(
        "Número de Orden de Compra",
        "Ingrese el número de la Orden de Compra:",
        parent=root
    )
    
    if not numero_oc or numero_oc.strip() == "":
        messagebox.showerror("Error", "Debe ingresar un número de orden de compra válido.")
        print("❌ No se ingresó un número de OC válido. Proceso cancelado.")
        exit()
    
    numero_oc = numero_oc.strip()
    print(f"✓ Número de OC ingresado: {numero_oc}\n")

    # Obtener el directorio donde está el script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)

    # Rutas de imágenes
    logo_path = os.path.join(project_root, "imagenes", "logo.png")
    firma_path = os.path.join(project_root, "imagenes", "firma.png")

    # Carpeta donde se guardarán los PDFs generados
    output_folder = Path.home() / "Downloads"
    os.makedirs(output_folder, exist_ok=True)

    # Verificar rutas de archivos
    print("="*95)
    print("VERIFICANDO RUTAS DE ARCHIVOS")
    print("="*95)
    print(f"\nPDF: {pdf_file_path}  ¿Existe? {os.path.exists(pdf_file_path)}")
    print(f"Logo: {logo_path}  ¿Existe? {os.path.exists(logo_path)}")
    print(f"Firma: {firma_path}  ¿Existe? {os.path.exists(firma_path)}")
    print(f"Carpeta de salida: {output_folder}")
    print("="*95 + "\n")

    # Procesar la cotización y generar la Orden de Compra
    if os.path.exists(pdf_file_path):
        procesar_cotizacion_y_generar_oc(
            pdf_file_path,
            numero_oc,  # Número de OC ingresado manualmente
            nombre_oc=None,
            ruta_logo=logo_path if os.path.exists(logo_path) else None,
            ruta_firma=firma_path if os.path.exists(firma_path) else None,
            carpeta_salida=output_folder
        )
    else:
        print(f"❌ ERROR: No se encontró el archivo seleccionado")