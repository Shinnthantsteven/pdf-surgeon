import streamlit as st
import fitz  # PyMuPDF
import io

st.set_page_config(layout="wide")
st.title("🛡️ Native PDF Surgeon (No OCR)")
st.write("This edits the PDF data directly. No conversion, no quality loss, no language errors.")

uploaded_file = st.file_uploader("Upload Native PDF", type=['pdf'])

if uploaded_file:
    # Load the PDF from memory
    file_bytes = uploaded_file.read()
    doc = fitz.open(stream=file_bytes, filetype="pdf")
    
    col1, col2 = st.columns(2)
    
    with col1:
        page_num = st.number_input("Page Number", min_value=1, max_value=len(doc), value=1) - 1
        search_text = st.text_input("Text/Number to Find (e.g., '12345')")
        replace_text = st.text_input("New Text/Number")
        
        # Preview the page
        page = doc[page_num]
        pix = page.get_pixmap(dpi=150)
        img_data = pix.tobytes("png")
        st.image(img_data, caption="Original Page Preview")

    if st.button("🚀 Apply Direct Data Fix") and search_text:
        # 1. Locate the text coordinates in the PDF data
        text_instances = page.search_for(search_text)
        
        if text_instances:
            for inst in text_instances:
                # 2. Add a Redaction (This deletes the old ink/data)
                # fill=(1,1,1) is white. For a scan, you'd match the background.
                page.add_redact_annot(inst, fill=(1, 1, 1)) 
                page.apply_redactions()
                
                # 3. Insert New Text at the exact same spot
                # This uses the PDF's internal coordinate system
                page.insert_text(inst.tl, replace_with, 
                                 fontsize=11, # You can adjust this to match
                                 color=(0, 0, 0)) # Pure Black
            
            # 4. Save the modified PDF
            out_buf = io.BytesIO()
            doc.save(out_buf)
            
            with col2:
                st.success("Surgical fix applied to PDF data!")
                # Show the result
                new_pix = page.get_pixmap(dpi=150)
                st.image(new_pix.tobytes("png"), caption="Edited Result")
                
                st.download_button(
                    label="📥 Download Edited PDF",
                    data=out_buf.getvalue(),
                    file_name="fixed_document.pdf",
                    mime="application/pdf"
                )
        else:
            st.error(f"Text '{search_text}' not found in the PDF's internal data.")
