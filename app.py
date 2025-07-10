import streamlit as st
import subprocess
import os
import tempfile
import uuid # To create unique filenames

# Use a temporary directory to store uploaded and compressed files
TEMP_DIR = tempfile.gettempdir()

def compress_pdf_with_ghostscript(input_path, output_path, quality='ebook'):
    """
    Compresses a PDF using Ghostscript on the server.
    """
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
        process = subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        return True
    except subprocess.CalledProcessError as e:
        st.error("Ghostscript failed during compression.")
        st.code(f"Error from Ghostscript:\n{e.stderr}")
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
    # Create unique file names to avoid conflicts if multiple users were on the app
    unique_id = uuid.uuid4().hex
    input_pdf_path = os.path.join(TEMP_DIR, f"{unique_id}_{uploaded_file.name}")
    output_pdf_path = os.path.join(TEMP_DIR, f"compressed_{unique_id}_{uploaded_file.name}")
    
    # Save the uploaded file to the temporary path
    with open(input_pdf_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
        
    st.markdown("---")
    
    quality = st.selectbox(
        "Select Compression Quality",
        ('ebook', 'screen', 'printer', 'prepress'),
        index=0, 
        help="**ebook:** Good balance (Recommended). **screen:** Smallest size."
    )
    
    compress_button = st.button("Compress PDF", type="primary")

    if compress_button:
        with st.spinner("Compressing your PDF..."):
            success = compress_pdf_with_ghostscript(input_pdf_path, output_pdf_path, quality)
        
        if success:
            st.success("✅ Compression successful!")
            
            # **THE FIX IS HERE**
            # Read the compressed file back into memory as bytes
            with open(output_pdf_path, "rb") as f:
                pdf_bytes = f.read()

            # Provide the bytes directly to the download button
            st.download_button(
                label="⬇️ Download Compressed PDF",
                data=pdf_bytes, # Pass the file's bytes, not a path
                file_name=f"compressed_{uploaded_file.name}",
                mime="application/pdf"
            )
            
            # Clean up the temporary files from the server
            os.remove(input_pdf_path)
            os.remove(output_pdf_path)
