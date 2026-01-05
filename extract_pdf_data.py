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
from io import BytesIO

# ==================== FUNCIONES DE EXTRACCIÓN ====================

def extract_text_from_pdf(pdf_path_or_bytes):
    """Extrae todo el texto de un archivo PDF (ruta o BytesIO)."""
    try:
        full_text = ""
        
        # Manejar tanto rutas de archivo como objetos BytesIO
        if isinstance(pdf_path_or_bytes, (str, bytes)) and os.path.exists(pdf_path_or_bytes):
            # Es una ruta de archivo
            with open(pdf_path_or_bytes, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                num_pages = len(reader.pages)
                print(f"El PDF tiene {num_pages} páginas.")

                for page_num in range(num_pages):
                    page = reader.pages[page_num]
                    page_text = page.extract_text()
                    if page_text:
                        full_text += page_text + "\n--- Fin de Página ---\n"
        
        elif hasattr(pdf_path_or_bytes, 'read'):
            # Es un objeto BytesIO o similar
            pdf_path_or_bytes.seek(0)  # Asegurarse de que estamos al inicio
            reader = PyPDF2.PdfReader(pdf_path_or_bytes)
            num_pages = len(reader.pages)
            print(f"El PDF tiene {num_pages} páginas.")

            for page_num in range(num_pages):
                page = reader.pages[page_num]
                page_text = page.extract_text()
                if page_text:
                    full_text += page_text + "\n--- Fin de Página ---\n"
        
        else:
            return f"Error: Tipo de entrada no válido para PDF: {type(pdf_path_or_bytes)}"
        
        return full_text
        
    except Exception as e:
        return f"Ocurrió un error al procesar el PDF: {e}"

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

def extract_productos_mejorado(text):
    """
    Extrae TODOS los productos/materiales de la cotización - VERSIÓN DEBUG COMPLETA
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
        print("\n🔍 Buscando palabras clave en el texto...")
        if 'Pos' in text:
            print("✓ Encontrado 'Pos'")
        if 'Material' in text:
            print("✓ Encontrado 'Material'")
        if 'Descripción' in text or 'Descripcion' in text:
            print("✓ Encontrado 'Descripción'")
        return productos
    
    texto_productos = seccion_productos.group(0)
    
    print("\n📄 SECCIÓN DE PRODUCTOS ENCONTRADA (primeros 1500 caracteres):")
    print("-" * 100)
    print(texto_productos[:1500])
    print("-" * 100)
    
    # Dividir por líneas para análisis manual
    lineas = texto_productos.split('\n')
    print(f"\n📊 Total de líneas en la sección: {len(lineas)}")
    print("\n🔍 MOSTRANDO TODAS LAS LÍNEAS (primeras 25):")
    print("-" * 100)
    
    for i, linea in enumerate(lineas[:25]):
        if linea.strip():
            # Mostrar con indicadores visuales
            print(f"Línea {i:2d}: |{linea}|")
    print("-" * 100)
    
    # 🆕 MÚLTIPLES PATRONES A PROBAR
    patrones = [
        # Patrón 1: Con espacios variables
        r'(\d+)\s+(\d+)\s+(.+?)\s+(\d+[.,]?\d*)\s+([A-Z]+)\s+([\d.,]+)\s+([\d.,]+)\s+([\d.,]+)\s+([\d.,]+)',
        
        # Patrón 2: Más específico para el formato Easy
        r'^(\d+)\s+(\d+)\s+([^\n]+?)\s+(\d+[.,]?\d*)\s+(\w+)\s+([\d.,]+)\s+([\d.,]+)\s+([\d.,]+)\s+([\d.,]+)',
        
        # Patrón 3: Sin ancla de inicio de línea
        r'(\d{1,3})\s+(\d{5,7})\s+([A-ZÁÉÍÓÚÑ][\w\s/\-\.]+?)\s+(\d+[.,]?\d*)\s+([A-Z]{2,4})\s+([\d.,]+)\s+([\d.,]+)\s+([\d.,]+)\s+([\d.,]+)',
        
        # Patrón 4: Muy flexible
        r'(\d+)\s+(\d+)\s+([^\d]+?)\s+(\d+)\s*,?\s*(\d*)\s+([A-Z]+)\s+([\d.,\s]+)',
    ]
    
    mejor_resultado = []
    patron_exitoso = 0
    
    for idx, patron in enumerate(patrones, 1):
        print(f"\n🧪 PROBANDO PATRÓN {idx}:")
        print(f"   Regex: {patron[:80]}...")
        
        try:
            matches = re.findall(patron, texto_productos, re.MULTILINE | re.IGNORECASE)
            print(f"   ✓ Encontrados: {len(matches)} coincidencias")
            
            if matches:
                print(f"   📋 Primera coincidencia: {matches[0]}")
                
                if len(matches) > len(mejor_resultado):
                    mejor_resultado = matches
                    patron_exitoso = idx
                    print(f"   🎯 MEJOR RESULTADO HASTA AHORA!")
        except Exception as e:
            print(f"   ❌ Error con patrón: {e}")
    
    if not mejor_resultado:
        print("\n❌ NINGÚN PATRÓN FUNCIONÓ")
        print("\n💡 Intentando extracción manual línea por línea...")
        
        # Extracción manual como último recurso
        for i, linea in enumerate(lineas[1:], 1):  # Saltar encabezado
            linea = linea.strip()
            if not linea:
                continue
            
            # Buscar líneas que empiecen con números
            if re.match(r'^\d+\s+\d+', linea):
                print(f"\n🔍 Línea candidata {i}: {linea}")
                
                # Intentar dividir por espacios múltiples
                partes = re.split(r'\s{2,}', linea)
                print(f"   Partes: {partes}")
                
                if len(partes) >= 9:
                    try:
                        producto = {
                            'posicion': partes[0],
                            'codigo_material': partes[1],
                            'descripcion': partes[2],
                            'cantidad': partes[3],
                            'unidad': partes[4],
                            'precio_unitario_original': partes[5],
                            'precio_con_descuento': partes[6],
                            'valor_con_descuento': partes[7],
                            'valor_total': partes[8]
                        }
                        productos.append(producto)
                        print(f"   ✅ Producto extraído manualmente")
                    except Exception as e:
                        print(f"   ❌ Error: {e}")
        
        if productos:
            print(f"\n✅ Extracción manual exitosa: {len(productos)} productos")
        
        return productos
    
    print(f"\n✅ PATRÓN EXITOSO: #{patron_exitoso}")
    print(f"📦 Total de coincidencias: {len(mejor_resultado)}")
    
    print("\n" + "="*100)
    print("📋 PROCESANDO PRODUCTOS:")
    print("="*100)
    
    for i, match in enumerate(mejor_resultado, 1):
        try:
            print(f"\n--- MATCH {i} ---")
            print(f"Raw: {match}")
            
            # Ajustar según cantidad de grupos capturados
            if len(match) >= 9:
                producto = {
                    'posicion': match[0].strip(),
                    'codigo_material': match[1].strip(),
                    'descripcion': match[2].strip(),
                    'cantidad': match[3].replace(',', '.').strip(),
                    'unidad': match[4].strip(),
                    'precio_unitario_original': match[5].strip(),
                    'precio_con_descuento': match[6].strip(),
                    'valor_con_descuento': match[7].strip(),
                    'valor_total': match[8].strip()
                }
            else:
                print(f"   ⚠️ Match incompleto: {len(match)} grupos (necesita 9)")
                continue
            
            print(f"  ✅ Pos: {producto['posicion']} | Código: {producto['codigo_material']}")
            print(f"     Descripción: {producto['descripcion'][:50]}")
            
            productos.append(producto)
            
        except Exception as e:
            print(f"  ❌ ERROR: {e}")
    
    print("\n" + "="*100)
    print(f"🎯 TOTAL: {len(productos)} productos extraídos")
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

def crear_orden_compra_pdf(datos_cotizacion, numero_oc_manual, nombre_archivo="orden_compra.pdf", ruta_logo=None, ruta_firma=None):
    """
    Crea un PDF de Orden de Compra con el formato actualizado usando datos de empresa compradora.
    
    Args:
        datos_cotizacion: Diccionario con los datos extraídos (incluye empresa_compradora)
        numero_oc_manual: Número de orden de compra ingresado manualmente
        nombre_archivo: Nombre del archivo de salida o BytesIO
        ruta_logo: Ruta al archivo de imagen del logo (opcional)
        ruta_firma: Ruta al archivo de imagen de la firma (opcional)
    """
    
    # 🔧 DEBUG: Mostrar qué rutas se están usando
    print(f"\n🔍 DEBUG - Rutas de imágenes:")
    print(f"   Logo: {ruta_logo}")
    print(f"   Logo existe: {os.path.exists(ruta_logo) if ruta_logo else False}")
    print(f"   Firma: {ruta_firma}")
    print(f"   Firma existe: {os.path.exists(ruta_firma) if ruta_firma else False}")
    
    # 🏢 Obtener datos de la empresa compradora
    empresa_compradora = datos_cotizacion.get('empresa_compradora', {})
    
    print(f"\n🏢 Empresa compradora:")
    print(f"   {empresa_compradora.get('razon_social', 'No definida')}")
    
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
        print(f"⚠ Logo omitido. Ruta: {ruta_logo}")
    
    # TÍTULO con número de OC ingresado manualmente
    titulo = Paragraph(f"ORDEN DE COMPRA {numero_oc_manual}", title_style)
    elements.append(titulo)
    elements.append(Spacer(1, 0.3*inch))
    
    # 🏢 DATOS DE LA EMPRESA COMPRADORA (dinámicos) - PARTE SUPERIOR
    elements.append(Paragraph(f"<b>{empresa_compradora.get('razon_social', 'EMPRESA NO DEFINIDA').upper()}</b>", bold_style))
    elements.append(Paragraph(f"RUT: {empresa_compradora.get('rut', 'N/A')}", normal_style))
    
    # Construir dirección completa
    direccion_completa = f"{empresa_compradora.get('direccion', 'N/A')}"
    if empresa_compradora.get('comuna', 'N/A') != 'N/A':
        direccion_completa += f" {empresa_compradora.get('comuna', '').upper()}"
    
    elements.append(Paragraph(direccion_completa.upper(), normal_style))
    elements.append(Paragraph(f"TELÉFONO: {empresa_compradora.get('telefono', 'N/A')}", normal_style))
    elements.append(Paragraph(datetime.now().strftime("%d-%m-%Y"), normal_style))
    elements.append(Spacer(1, 0.3*inch))
    
    # DATOS DEL PROVEEDOR (MANTENER COMO ESTABAN - HARDCODEADOS)
    elements.append(Paragraph("<b>DATOS DEL PROVEEDOR</b>", bold_style))
    elements.append(Spacer(1, 0.1*inch))
    
    # 🔒 DATOS FIJOS DEL PROVEEDOR (EASY)
    proveedor_data = [
        [Paragraph("<b>Razón Social</b>", normal_style), 
         Paragraph("EASY RETAIL S. A", normal_style),
         Paragraph("<b>COMUNA</b>", normal_style), 
         Paragraph("PEDRO AGUIRRE<br/>CERDA", normal_style)],
        [Paragraph("<b>Contacto</b>", normal_style), 
         Paragraph("BARBARA MONDACA", normal_style),
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
        print(f"⚠ Firma omitida. Ruta: {ruta_firma}")
    
    # Construir el PDF
    doc.build(elements)
    print(f"\n✓ Orden de Compra generada exitosamente")
    return nombre_archivo
# ==================== FUNCIÓN PRINCIPAL ====================

def procesar_cotizacion_y_generar_oc(pdf_path_or_bytes, numero_oc_manual, nombre_oc=None, ruta_logo=None, ruta_firma=None, carpeta_salida=None):
    """
    Función principal que extrae datos de una cotización PDF y genera una Orden de Compra.
    
    Args:
        pdf_path_or_bytes: Ruta al archivo PDF de cotización o objeto BytesIO
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
    if hasattr(pdf_path_or_bytes, 'read'):
        print("1. Extrayendo texto del PDF (desde BytesIO)...")
    else:
        print(f"1. Extrayendo texto del PDF: {os.path.basename(pdf_path_or_bytes)}")
    
    extracted_text = extract_text_from_pdf(pdf_path_or_bytes)
    
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
        nombre_archivo = f"ORDEN_DE_COMPRA_{numero_oc_manual}.pdf"
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

def obtener_ruta_pdf():
    """Solicita al usuario la ruta del archivo PDF de cotización."""
    print("\n" + "="*95)
    print("SELECCIÓN DE ARCHIVO PDF")
    print("="*95)
    
    while True:
        pdf_path = input("\n👉 Ruta del PDF: ").strip().strip('"')
        
        if not pdf_path:
            print("❌ No se ingresó ninguna ruta. Intenta nuevamente.")
            continue
            
        if not os.path.exists(pdf_path):
            print(f"❌ El archivo no existe en la ruta: {pdf_path}")
            print("   Verifica la ruta e intenta nuevamente.")
            continue
            
        if not pdf_path.lower().endswith('.pdf'):
            print("❌ El archivo seleccionado no es un PDF.")
            continue
            
        print(f"✓ Archivo seleccionado: {os.path.basename(pdf_path)}")
        return pdf_path

def obtener_numero_oc():
    """Solicita al usuario el número de orden de compra."""
    print("\n" + "="*95)
    print("INGRESO DE NÚMERO DE ORDEN DE COMPRA")
    print("="*95)
    
    while True:
        numero_oc = input("\n👉 Ingresa el número de la Orden de Compra: ").strip()
        
        if not numero_oc:
            print("❌ Debes ingresar un número de orden de compra válido.")
            continue
            
        print(f"✓ Número de OC ingresado: {numero_oc}")
        return numero_oc

if __name__ == "__main__":
    print("\n" + "="*95)
    print("🚀 GENERADOR DE ORDEN DE COMPRA")
    print("="*95)
    
    # 1. Obtener ruta del PDF
    pdf_file_path = obtener_ruta_pdf()
    
    # 2. Obtener número de OC
    numero_oc = obtener_numero_oc()

    # 3. Obtener el directorio donde está el script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # 🔍 DEBUG: Mostrar directorio del script
    print(f"\n🔍 Directorio del script: {script_dir}")

    # 4. Rutas de imágenes
    logo_path = os.path.join(script_dir, "imagenes", "logo.png")
    firma_path = os.path.join(script_dir, "imagenes", "firma.png")
    
    # 🔍 DEBUG: Mostrar rutas completas
    print(f"🔍 Ruta completa logo: {logo_path}")
    print(f"🔍 Ruta completa firma: {firma_path}")
    
    # ✅ VERIFICAR Y AJUSTAR RUTAS (CRÍTICO)
    if not os.path.exists(logo_path):
        print(f"⚠️  Logo NO encontrado en: {logo_path}")
        logo_path = None
    else:
        print(f"✅ Logo encontrado correctamente")
    
    if not os.path.exists(firma_path):
        print(f"⚠️  Firma NO encontrada en: {firma_path}")
        firma_path = None
    else:
        print(f"✅ Firma encontrada correctamente")

    # 5. Carpeta donde se guardarán los PDFs generados
    output_folder = os.path.join(script_dir, "ordenes_generadas")
    os.makedirs(output_folder, exist_ok=True)

    # 6. Procesar la cotización y generar la Orden de Compra
    if os.path.exists(pdf_file_path):
        procesar_cotizacion_y_generar_oc(
            pdf_file_path,
            numero_oc,
            nombre_oc=None,
            ruta_logo=logo_path,
            ruta_firma=firma_path,
            carpeta_salida=output_folder
        )
    else:
        print(f"❌ ERROR: No se encontró el archivo PDF seleccionado")