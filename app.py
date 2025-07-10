import streamlit as st
import subprocess
import os
import tempfile
import uuid

# --- State Management: Initialize the session state key ---
if 'pdf_bytes' not in st.session_state:
    st.session_state.pdf_bytes = None

# --- Main Functions ---
TEMP_DIR = tempfile.gettempdir()

def compress_pdf(input_path, output_path, quality):
    """Compresses a PDF using Ghostscript and returns success status."""
    ghostscript_path = 'gs'
    command = [
        ghostscript_path, '-sDEVICE=pdfwrite', '-dCompatibilityLevel=1.4',
        f'-dPDFSETTINGS=/{quality}', '-dNOPAUSE', '-dQUIET', '-dBATCH',
        f'-sOutputFile={output_path}', input_path
    ]
    try:
        subprocess.run(command, check=True, capture_output=True, text=True)
        return True
    except subprocess.CalledProcessError as e:
        st.error("Ghostscript failed during compression.")
        st.code(f"Error from Ghostscript:\n{e.stderr}")
        return False
    except FileNotFoundError:
        st.error("Ghostscript command 'gs' not found. App might be misconfigured.")
        return False

# --- Streamlit App Interface ---
st.set_page_config(layout="centered", page_title="PDF Pro")
st.title("📄 PDF Compressor")

# We create two columns to separate the uploader and the download button
col1, col2 = st.columns([3, 2])

with col1:
    uploaded_file = st.file_uploader(
        "Upload a PDF to compress",
        type=["pdf"]
    )

if uploaded_file:
    # When a new file is uploaded, clear any previous result
    if 'last_uploaded_id' not in st.session_state or st.session_state.last_uploaded_id != uploaded_file.file_id:
        st.session_state.last_uploaded_id = uploaded_file.file_id
        st.session_state.pdf_bytes = None

    quality = st.selectbox(
        "Select Compression Quality",
        ('ebook', 'screen', 'printer', 'prepress'),
        index=0,
        help="**ebook:** Good balance. **screen:** Smallest size."
    )

    if st.button("Compress PDF", type="primary"):
        with st.spinner("Compressing..."):
            unique_id = uuid.uuid4().hex
            input_path = os.path.join(TEMP_DIR, f"{unique_id}_{uploaded_file.name}")
            output_path = os.path.join(TEMP_DIR, f"compressed_{unique_id}.pdf")

            with open(input_path, "wb") as f:
                f.write(uploaded_file.getbuffer())

            success = compress_pdf(input_path, output_path, quality)

            if success:
                with open(output_path, "rb") as f:
                    # **THE FIX: Store result directly in session state**
                    st.session_state.pdf_bytes = f.read()
                st.success("✅ Compression successful!")
            
            # Clean up temporary files
            if os.path.exists(input_path):
                os.remove(input_path)
            if os.path.exists(output_path):
                os.remove(output_path)

# The download button is now in the second column and checks the state
with col2:
    if st.session_state.pdf_bytes:
        st.write("### Your file is ready!")
        st.download_button(
            label="⬇️ Download Compressed PDF",
            data=st.session_state.pdf_bytes,
            file_name=f"compressed_{uploaded_file.name}",
            mime="application/pdf",
            type="primary"
        )
