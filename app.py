import streamlit as st
from PyPDF2 import PdfReader, PdfWriter
from io import BytesIO
import re

st.title("PDF Surgeon - Edit Numbers on Documents")
st.write("Upload a PDF, edit numbers, and download a fixed copy.")

uploaded_file = st.file_uploader("Choose a PDF", type="pdf")

if uploaded_file:
    # Read PDF
    reader = PdfReader(uploaded_file)
    writer = PdfWriter()
    all_text = ""

    # Extract text from all pages
    for page in reader.pages:
        text = page.extract_text()
        all_text += text + "\n"

    # Find all numbers (simple regex)
    numbers = re.findall(r"\d+", all_text)
    st.write("Detected numbers:", numbers)

    # Editable fields for numbers
    new_numbers = []
    for i, num in enumerate(numbers):
        new_num = st.text_input(f"Number {i+1}", value=num)
        new_numbers.append(new_num)

    if st.button("Generate PDF"):
        idx = 0
        for page in reader.pages:
            text = page.extract_text()
            if text:
                # Replace numbers with edited ones
                for old_num, new_num in zip(numbers, new_numbers):
                    text = text.replace(old_num, new_num, 1)
                # Create a new PDF page with updated text
                # (simple way: just write text, layout may differ)
                from reportlab.pdfgen import canvas
                from reportlab.lib.pagesizes import letter
                packet = BytesIO()
                can = canvas.Canvas(packet, pagesize=letter)
                can.drawString(50, 750, text)
                can.save()
                packet.seek(0)
                from PyPDF2 import PdfReader
                new_pdf = PdfReader(packet)
                writer.add_page(new_pdf.pages[0])

        # Save final PDF
        output = BytesIO()
        writer.write(output)
        st.download_button(
            label="Download Fixed PDF",
            data=output.getvalue(),
            file_name="fixed.pdf",
            mime="application/pdf"
        )
        st.success("PDF generated!")
