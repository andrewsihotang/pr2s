import streamlit as st
import subprocess
import os
import tempfile

# Use a temporary directory to store uploaded and compressed files
TEMP_DIR = tempfile.gettempdir()

def compress_pdf_with_ghostscript(input_path, output_path, quality='ebook'):
    """
    Compresses a PDF using Ghostscript on the server.
    """
    # CRITICAL CHANGE: On the deployment server, the command is just 'gs'
    # because it will be installed via packages.txt and available in the system PATH.
    ghostscript_path = 'gs' 
    
    command = [
        ghostscript_path,
        '-sDEVICE=pdfwrite',
        '-dCompatibilityLevel=1.4',
        f'-dPDFSETTINGS=/{quality}',
        '-dNOPAUSE',
        '-dQUIET',
        '-dBATCH',
        f'-sOutputFile={output_path}',
        input_path
    ]
    
    try:
        # We capture the output to give more detailed error messages if something goes wrong.
        process = subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        return True
    except subprocess.CalledProcessError as e:
        st.error("Ghostscript failed during compression.")
        st.code(f"Error:\n{e.stderr}") # Show the actual error from Ghostscript
        return False
    except FileNotFoundError:
        st.error("Could not find the 'gs' command. This means Ghostscript is not installed correctly on the server.")
        return False

# --- Streamlit App Interface ---

st.set_page_config(layout="centered", page_title="My PDF Compressor", page_icon="📄")
st.title("📄 My Personal PDF Compressor")
st.write("Upload a PDF, choose a compression level, and get your smaller file.")

uploaded_file = st.file_uploader("Upload a PDF file", type=["pdf"])

if uploaded_file is not None:
    # Define paths for the temporary original and new compressed file
    input_pdf_path = os.path.join(TEMP_DIR, uploaded_file.name)
    output_pdf_path = os.path.join(TEMP_DIR, f"compressed_{uploaded_file.name}")
    
    # Save the uploaded file to the temporary path
    with open(input_pdf_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
        
    st.markdown("---")
    
    # UI for selecting compression quality
    quality = st.selectbox(
        "Select Compression Quality",
        ('ebook', 'screen', 'printer', 'prepress'),
        index=0, 
        help="**ebook:** Good balance (Recommended). **screen:** Smallest size."
    )
    
    compress_button = st.button(f"Compress PDF", type="primary")

    if compress_button:
        with st.spinner("Compressing your PDF..."):
            success = compress_pdf_with_ghostscript(input_pdf_path, output_pdf_path, quality)
        
        if success:
            st.success("✅ Compression successful!")
            
            with open(output_pdf_path, "rb") as f:
                st.download_button(
                    label="⬇️ Download Compressed PDF",
                    data=f,
                    file_name=f"compressed_{uploaded_file.name}",
                    mime="application/pdf"
                )