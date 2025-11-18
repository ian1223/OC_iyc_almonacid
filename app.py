import streamlit as st
from extract_pdf_data import extract_text_from_pdf, extract_all_data, crear_orden_compra_pdf
from io import BytesIO
import os

st.title("Generador de Órdenes de Compra")
st.markdown("Sube tu cotización en PDF y genera la OC automáticamente.")

# 🔧 SOLUCIÓN: Obtener rutas de las imágenes
script_dir = os.path.dirname(os.path.abspath(__file__))
logo_path = os.path.join(script_dir, "imagenes", "logo.png")
firma_path = os.path.join(script_dir, "imagenes", "firma.png")

# Verificar existencia de imágenes
logo_exists = os.path.exists(logo_path)
firma_exists = os.path.exists(firma_path)

# Mostrar estado de las imágenes en la sidebar
with st.sidebar:
    st.subheader("📁 Configuración de Imágenes")
    st.write(f"🖼️ Logo: {'✅ Encontrado' if logo_exists else '❌ No encontrado'}")
    st.write(f"✍️ Firma: {'✅ Encontrada' if firma_exists else '❌ No encontrada'}")
    
    if not logo_exists:
        st.warning(f"Logo no encontrado en: {logo_path}")
    if not firma_exists:
        st.warning(f"Firma no encontrada en: {firma_path}")

# 🏢 SELECTOR DE EMPRESA
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
        "direccion": "PJE SAN INDIGO 3322",
        "comuna": "LA FLORIDA",
        "ciudad": "SANTIAGO",
        "telefono": "940264963",
    }
}

empresa_seleccionada = st.selectbox(
    "¿Desde qué empresa realizas la orden de compra?",
    options=list(empresas.keys()),
    help="Selecciona la empresa que está realizando la compra"
)

# Mostrar información de la empresa seleccionada
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
      

# Advertencia si se selecciona empresa sin configurar
if empresa_seleccionada == "Otra Empresa (Configurar después)":
    st.warning("⚠️ Has seleccionado una empresa que aún no está configurada. Los datos aparecerán como 'Por definir' en la orden de compra.")

st.divider()

# Subir archivo
uploaded_file = st.file_uploader("Selecciona un PDF de cotización", type="pdf")

# Número de OC
numero_oc = st.text_input("Número de Orden de Compra", help="Ejemplo: OC-2025-001")

if uploaded_file and numero_oc and st.button("Procesar y generar OC", type="primary"):
    with st.spinner("Procesando cotización..."):
        # Leer archivo en memoria
        file_bytes = uploaded_file.read()
        
        # Extraer texto y datos
        text = extract_text_from_pdf(BytesIO(file_bytes))
        datos = extract_all_data(text)
        
        # 🏢 AGREGAR INFORMACIÓN DE LA EMPRESA COMPRADORA
        datos['empresa_compradora'] = empresas[empresa_seleccionada]
        
        # Debug: Verificar que los datos están correctos
        print(f"\n🏢 Empresa seleccionada: {empresa_seleccionada}")
        print(f"📋 Datos de la empresa: {datos['empresa_compradora']}")

        # Crear PDF en memoria con las rutas de las imágenes
        pdf_buffer = BytesIO()
        crear_orden_compra_pdf(
            datos, 
            numero_oc, 
            nombre_archivo=pdf_buffer,
            ruta_logo=logo_path if logo_exists else None,
            ruta_firma=firma_path if firma_exists else None
        )
        pdf_buffer.seek(0)  # Volver al inicio del buffer

    st.success("✅ Orden de Compra generada exitosamente!")

# Card con información completa
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
    
    # Mostrar resumen detallado
    with st.expander("📄 Ver resumen completo"):
        st.write("**Empresa Compradora:**")
        st.write(f"- {empresa_info['razon_social']}")
        st.write(f"- RUT: {empresa_info['rut']}")
        st.write(f"- {empresa_info['direccion']}, {empresa_info['comuna']}")
        st.write("")
        st.write(f"**Número de Orden de Compra:** {numero_oc}")
        st.write(f"**Fecha:** {datos.get('fecha', 'N/A')}")
        st.write(f"**Vendedor/a:** {datos.get('vendedor', 'N/A')}")
    
    razon_social_limpia = empresa_info['razon_social'].replace(' ', '_').replace('.', '')

    st.download_button(
        label="📥 Descargar Orden de Compra",
        data=pdf_buffer,
        file_name=f"OC_{razon_social_limpia}_{numero_oc}.pdf",
        mime="application/pdf",
        type="primary"
    )