import streamlit as st
import subprocess
import os
import tempfile
import uuid

# --- State Management ---
# Initialize session state variables to None if they don't exist.
# This is crucial for the app's logic.
if 'pdf_bytes' not in st.session_state:
    st.session_state.pdf_bytes = None
if 'file_name' not in st.session_state:
    st.session_state.file_name = None

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
        st.error("Ghostscript command 'gs' not found. The app is likely misconfigured.")
        return False

# --- Streamlit App Interface ---
st.set_page_config(layout="centered", page_title="My PDF Compressor", page_icon="📄")
st.title("📄 My Personal PDF Compressor")
st.write("Upload a PDF, choose a compression level, and get your smaller file.")

uploaded_file = st.file_uploader(
    "Upload a PDF file",
    type=["pdf"],
    # When a new file is uploaded, clear any old compressed data
    on_change=lambda: st.session_state.update(pdf_bytes=None, file_name=None)
)

if uploaded_file is not None:
    st.markdown("---")
    quality = st.selectbox(
        "Select Compression Quality",
        ('ebook', 'screen', 'printer', 'prepress'),
        index=0,
        help="**ebook:** Good balance (Recommended). **screen:** Smallest size."
    )
    
    if st.button("Compress PDF", type="primary"):
        # Create unique file paths for processing
        unique_id = uuid.uuid4().hex
        input_path = os.path.join(TEMP_DIR, f"{unique_id}_{uploaded_file.name}")
        output_path = os.path.join(TEMP_DIR, f"compressed_{unique_id}.pdf")

        # Save uploaded file to disk for Ghostscript to access
        with open(input_path, "wb") as f:
            f.write(uploaded_file.getbuffer())

        with st.spinner("Compressing your PDF..."):
            success = compress_pdf(input_path, output_path, quality)
            
            if success:
                # Read the compressed file's data into memory
                with open(output_path, "rb") as f:
                    compressed_bytes = f.read()
                
                # **THE FIX: Store the data and filename in session state**
                st.session_state.pdf_bytes = compressed_bytes
                st.session_state.file_name = f"compressed_{uploaded_file.name}"
                
                st.success("✅ Compression successful!")
            
            # Clean up the temporary files from the server
            os.remove(input_path)
            os.remove(output_path)

# **Display the download button ONLY if there's data in the session state**
if st.session_state.pdf_bytes:
    st.download_button(
        label="⬇️ Download Compressed PDF",
        data=st.session_state.pdf_bytes,
        file_name=st.session_state.file_name,
        mime="application/pdf"
    )
