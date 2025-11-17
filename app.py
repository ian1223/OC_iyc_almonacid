import streamlit as st
from extract_pdf_data import extract_text_from_pdf, extract_all_data, crear_orden_compra_pdf
from io import BytesIO

st.title("Generador de Órdenes de Compra")
st.markdown("Sube tu cotización en PDF y genera la OC automáticamente.")

# Subir archivo
uploaded_file = st.file_uploader("Selecciona un PDF de cotización", type="pdf")

# Número de OC
numero_oc = st.text_input("Número de Orden de Compra")

if uploaded_file and st.button("Procesar y generar OC"):
    # Leer archivo en memoria
    file_bytes = uploaded_file.read()
    
    # Extraer texto y datos
    text = extract_text_from_pdf(BytesIO(file_bytes))
    datos = extract_all_data(text)

    # Crear PDF en memoria
    pdf_buffer = BytesIO()
    crear_orden_compra_pdf(datos, numero_oc, nombre_archivo=pdf_buffer)
    pdf_buffer.seek(0)  # Volver al inicio del buffer

    st.success("✅ Orden de Compra generada exitosamente!")
    st.download_button(
        label="Descargar Orden de Compra",
        data=pdf_buffer,
        file_name=f"ORDEN_DE_COMPRA_{numero_oc}.pdf",
        mime="application/pdf"
    )
