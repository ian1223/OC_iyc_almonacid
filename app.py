import streamlit as st
from extract_pdf_data import extract_text_from_pdf, extract_all_data, crear_orden_compra_pdf
from io import BytesIO
import os
import fitz  # PyMuPDF
import json

st.title("Generador de Órdenes de Compra")
st.markdown("Sube tu cotización en PDF y genera la OC automáticamente.")

# 🔧 Obtener rutas de las imágenes y archivo de datos
script_dir = os.path.dirname(os.path.abspath(__file__))
logo_path = os.path.join(script_dir, "imagenes", "logo.png")
firma_path = os.path.join(script_dir, "imagenes", "firma.png")
datos_oc_path = os.path.join(script_dir, "datos_oc.json")

logo_exists = os.path.exists(logo_path)
firma_exists = os.path.exists(firma_path)

# 💾 FUNCIONES PARA PERSISTENCIA DE DATOS
def cargar_ultima_oc():
    """Carga la última OC desde el archivo JSON"""
    try:
        if os.path.exists(datos_oc_path):
            with open(datos_oc_path, 'r', encoding='utf-8') as f:
                datos = json.load(f)
                return datos.get('ultima_oc', '')
    except Exception as e:
        print(f"Error al cargar última OC: {e}")
    return ''

def guardar_ultima_oc(numero_oc):
    """Guarda la última OC en el archivo JSON"""
    try:
        datos = {'ultima_oc': numero_oc}
        with open(datos_oc_path, 'w', encoding='utf-8') as f:
            json.dump(datos, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Error al guardar última OC: {e}")

# 🏢 Selector de empresa
st.subheader("🏢 Selecciona la Empresa Compradora")

empresas = {
    "VICTOR HUGO ALMONACID ULLOA": {
        "razon_social": "VICTOR HUGO ALMONACID ULLOA",
        "rut": "10573124-8",
        "direccion": "AVDA LO ESPEJO 01565",
        "comuna": " LO ESPEJO",
        "ciudad": "SANTIAGO",
        "telefono": "974304421",
        
    },
    "INGENIERIA Y CONSTRUCCION ALMONACID LIMITADA": {
        "razon_social": "INGENIERIA Y CONSTRUCCION ALMONACID LIMITADA",
        "rut": "77556476-8",
        "direccion": "PJE SAN IGIDIO 3322",
        "comuna": "LA FLORIDA",
        "ciudad": "SANTIAGO",
        "telefono": "974534770",
    }
}

empresa_seleccionada = st.selectbox(
    "¿Desde qué empresa realizas la orden de compra?",
    options=list(empresas.keys()),
    help="Selecciona la empresa que está realizando la compra"
)

# Mostrar información empresa
with st.expander("ℹ️ Ver información de la empresa seleccionada"):
    empresa_info = empresas[empresa_seleccionada]
    
    col1, col2 = st.columns(2)
    with col1:
        st.write(f"**Razón Social:** {empresa_info['razon_social']}")
        st.write(f"**RUT:** {empresa_info['rut']}")
        st.write(f"**Dirección:** {empresa_info['direccion']}")
        st.write(f"**Comuna:** {empresa_info['comuna']}")
    with col2:
        st.write(f"**Ciudad:** {empresa_info['ciudad']}")
        st.write(f"**Teléfono:** {empresa_info['telefono']}")

st.divider()

# Subida PDF
st.markdown("<h3 style='font-size:20px;'>Selecciona un PDF de cotización</h3>", unsafe_allow_html=True)
uploaded_file = st.file_uploader("", type="pdf")

# ✅ PREVISUALIZACIÓN DEL PDF - CONVERTIR A IMAGEN
if uploaded_file:
    st.subheader("📄 Vista previa del PDF")
    
    try:
        # Leer el PDF
        uploaded_file.seek(0)
        pdf_bytes = uploaded_file.read()
        
        # Convertir primera página a imagen
        pdf_document = fitz.open(stream=pdf_bytes, filetype="pdf")
        first_page = pdf_document[0]
        
        # Renderizar como imagen (mayor zoom = mejor calidad)
        pix = first_page.get_pixmap(matrix=fitz.Matrix(2, 2))
        img_bytes = pix.tobytes("png")
        
        # Mostrar imagen
        st.image(img_bytes, caption=f"Primera página - {uploaded_file.name}", use_container_width=True)
        
        pdf_document.close()
        
        # Regresar el puntero al inicio
        uploaded_file.seek(0)
        
    except Exception as e:
        st.warning(f"⚠️ No se pudo previsualizar el PDF: {str(e)}")
        st.info(f"✅ Archivo cargado: {uploaded_file.name}")

# 📊 CONTADOR DE ÓRDENES DE COMPRA CON PERSISTENCIA
st.markdown("<h3 style='font-size:20px;'>Número de Orden de Compra</h3>", unsafe_allow_html=True)

# Cargar última OC del archivo
ultima_oc_guardada = cargar_ultima_oc()

# Mostrar última OC registrada
col1, col2 = st.columns([1, 2])
with col1:
    if ultima_oc_guardada:
        st.info(f"📋 Última OC: **{ultima_oc_guardada}**")
    else:
        st.info("📋 Sin OC previas")

with col2:
    numero_oc = st.text_input("Ingresa el número de OC", help="Ejemplo: OC-2025-001", label_visibility="collapsed")

# Procesar PDF y generar OC
if uploaded_file and numero_oc and st.button("Procesar y generar OC", type="primary"):
    with st.spinner("Procesando cotización..."):

        # Importante: regresar el puntero al inicio
        uploaded_file.seek(0)
        file_bytes = uploaded_file.read()

        # Extracción de datos
        text = extract_text_from_pdf(BytesIO(file_bytes))
        datos = extract_all_data(text)
        
        # Agregar empresa
        datos['empresa_compradora'] = empresas[empresa_seleccionada]

        # Crear PDF final
        pdf_buffer = BytesIO()
        crear_orden_compra_pdf(
            datos, 
            numero_oc, 
            nombre_archivo=pdf_buffer,
            ruta_logo=logo_path if logo_exists else None,
            ruta_firma=firma_path if firma_exists else None
        )
        pdf_buffer.seek(0)
        
        # Guardar última OC en archivo (persiste después de F5)
        guardar_ultima_oc(numero_oc)

    st.success("✅ Orden de Compra generada exitosamente!")

    # Resumen tarjeta
    with st.container():
        col1, col2, col3 = st.columns([2, 1, 1])

        with col1:
            st.markdown(f"""
            **🏢 Empresa Compradora:**  
            {empresa_info['razon_social']}
            """)

        with col2:
            st.markdown(f"""
            **📦 Productos:**  
            {len(datos.get('productos', []))} items
            """)

        with col3:
            st.markdown(f"""
            **💰 Total:**  
            ${datos.get('total_final', '0')}
            """)

    st.divider()
    
    # Resumen detallado
    with st.expander("📄 Ver resumen completo"):
        st.write("**Empresa Compradora:**")
        st.write(f"- {empresa_info['razon_social']}")
        st.write(f"- RUT: {empresa_info['rut']}")
        st.write(f"- {empresa_info['direccion']}, {empresa_info['comuna']}")
        st.write("")
        st.write(f"**Número de Orden de Compra:** {numero_oc}")
        st.write(f"**Fecha:** {datos.get('fecha', 'N/A')}")
        st.write(f"**Vendedor/a:** {datos.get('vendedor', 'N/A')}")
        st.write("")
        
        # Detalle de productos
        st.write("**📦 Detalle de Productos:**")
        productos = datos.get('productos', [])
        if productos:
            for idx, prod in enumerate(productos, 1):
                st.write(f"**{idx}. {prod.get('descripcion', 'Sin descripción')}**")
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.write(f"Código: {prod.get('codigo_material', 'N/A')}")
                with col2:
                    st.write(f"Cantidad: {prod.get('cantidad', 'N/A')} {prod.get('unidad', '')}")
                with col3:
                    st.write(f"Precio Unit: ${prod.get('precio_con_descuento', 'N/A')}")
                st.write(f"Total: ${prod.get('valor_con_descuento', 'N/A')}")
                if idx < len(productos):
                    st.divider()
        else:
            st.write("No se encontraron productos")
        
        st.write("")
        st.write("**💰 Totales:**")
        st.write(f"- Subtotal: ${datos.get('subtotal', 'N/A')}")
        st.write(f"- IVA: ${datos.get('iva', 'N/A')}")
        st.write(f"- **TOTAL: ${datos.get('total_final', 'N/A')}**")

    razón_social_limpia = empresa_info['razon_social'].replace(' ', '_').replace('.', '')

    st.download_button(
        label="📥 Descargar Orden de Compra",
        data=pdf_buffer,
        file_name=f"OC_{razón_social_limpia}_{numero_oc}.pdf",
        mime="application/pdf",
        type="primary"
    )