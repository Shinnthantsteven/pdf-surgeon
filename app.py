import streamlit as st
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from pdf2image import convert_from_bytes
import easyocr
import io

# --- 1. Load OCR Reader ---
@st.cache_resource
def load_reader():
    return easyocr.Reader(['en'])  # English only

reader = load_reader()

st.title("🛡️ Dubai Document Surgeon")
st.write("Heal document textures and fix numbers seamlessly.")

# --- 2. Upload PDF ---
uploaded_file = st.file_uploader("Upload Certificate (PDF)", type=['pdf'])

if uploaded_file:
    # Convert PDF to high-res images
    images = convert_from_bytes(uploaded_file.read(), dpi=300)
    
    # Page selector for multi-page PDFs
    page_num = st.number_input("Select Page", 1, len(images), 1)
    img_pil = images[page_num - 1].convert("RGB")
    img_np = np.array(img_pil)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("1️⃣ Original Page")
        st.image(img_pil, use_container_width=True)
        
        # --- OCR for numbers ---
        results = reader.readtext(img_np)
        # Filter text containing digits
        options = [f"{res[1]} (at {tuple(map(int,res[0][0]))})" for res in results if any(c.isdigit() for c in res[1])]
        
        if not options:
            st.warning("No numbers detected on this page.")
        else:
            choice = st.selectbox("Select the exact number to fix:", options)
            new_val = st.text_input("Enter the CORRECT value:")

    if st.button("🚀 Apply Seamless Fix") and options and new_val:
        # Find the coordinates for the choice
        idx = options.index(choice)
        bbox, old_text, conf = results[idx]
        tl, tr, br, bl = [list(map(int, p)) for p in bbox]
        rect = np.array([tl, tr, br, bl], dtype=np.int32)

        # --- 1. Inpaint old number ---
        cv_img = cv2.cvtColor(img_np, cv2.COLOR_RGB2BGR)
        mask = np.zeros(cv_img.shape[:2], np.uint8)
        cv2.fillPoly(mask, [rect], 255)
        healed_cv = cv2.inpaint(cv_img, mask, 5, cv2.INPAINT_TELEA)  # smoother result

        # --- 2. Add new number ---
        final_pil = Image.fromarray(cv2.cvtColor(healed_cv, cv2.COLOR_BGR2RGB))
        draw = ImageDraw.Draw(final_pil)
        
        # Determine font size to match original box height
        h_box = int(abs(bl[1] - tl[1]))
        try:
            font = ImageFont.truetype("arial.ttf", int(h_box * 0.9))
        except:
            font = ImageFont.load_default()
        
        # Center new text in the bounding box
        w_text, h_text = draw.textsize(new_val, font=font)
        x_center = (tl[0] + tr[0]) // 2
        y_center = (tl[1] + bl[1]) // 2
        draw.text((x_center - w_text // 2, y_center - h_text // 2), new_val, fill=(0,0,0), font=font)

        with col2:
            st.subheader("2️⃣ Fixed Page")
            st.image(final_pil, use_container_width=True)
            
            # Export fixed page as PDF
            pdf_buf = io.BytesIO()
            final_pil.save(pdf_buf, format="PDF")
            st.download_button("📥 Download Fixed PDF", pdf_buf.getvalue(), "fixed_certificate.pdf")
