import streamlit as st
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from pdf2image import convert_from_bytes
import easyocr
import io

# Setup OCR for precision
@st.cache_resource
def load_reader():
    return easyocr.Reader(['en', 'ar'])

reader = load_reader()

st.title("🎯 Surgical PDF Repair")
st.write("Click exactly where the error is to heal the document texture.")

uploaded_file = st.file_uploader("Upload Scanned PDF", type=['pdf'])

if uploaded_file:
    # 1. Convert PDF to High-Res Image
    images = convert_from_bytes(uploaded_file.read(), dpi=300)
    img_pil = images[0].convert("RGB")
    img_np = np.array(img_pil)
    
    # 2. UI: Find and Replace
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Target Area")
        # We find the text but we only show you what we FOUND to avoid errors
        results = reader.readtext(img_np)
        options = [f"Replace '{res[1]}'" for res in results]
        choice = st.selectbox("Pick the exact number to fix:", options)
        new_val = st.text_input("Enter the CORRECT replacement:")
        
    if st.button("🚀 Run Seamless Repair") and new_val:
        idx = options.index(choice)
        bbox, original_text, conf = results[idx]
        
        # Convert bbox to integers
        tl, tr, br, bl = [list(map(int, p)) for p in bbox]
        rect = np.array([tl, tr, br, bl], dtype=np.int32)

        # --- THE SURGERY (OpenCV) ---
        cv_img = cv2.cvtColor(img_np, cv2.COLOR_RGB2BGR)
        
        # 1. Create a mask of the old text
        mask = np.zeros(cv_img.shape[:2], np.uint8)
        cv2.fillPoly(mask, [rect], 255)
        
        # 2. HEAL: This is the secret. It 'grows' the paper texture into the hole
        # so there is no white box.
        healed_cv = cv2.inpaint(cv_img, mask, 3, cv2.INPAINT_NS)
        
        # 3. OVERLAY: Put the new text back
        final_img = Image.fromarray(cv2.cvtColor(healed_cv, cv2.COLOR_BGR2RGB))
        draw = ImageDraw.Draw(final_img)
        
        # Auto-font size based on original box height
        font_size = int(abs(bl[1] - tl[1]) * 0.9)
        try:
            font = ImageFont.truetype("arial.ttf", font_size)
        except:
            font = ImageFont.load_default()

        # Draw text at the exact same spot
        draw.text((tl[0], tl[1]), new_val, fill=(0,0,0), font=font)
        
        with col2:
            st.subheader("Fixed Result")
            st.image(final_img, use_container_width=True)
            
            # Export back to PDF
            pdf_buf = io.BytesIO()
            final_img.save(pdf_buf, format="PDF")
            st.download_button("📥 Download Fixed PDF", pdf_buf.getvalue(), "surgical_fix.pdf")
