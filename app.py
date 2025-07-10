import streamlit as st
import subprocess
import os
import tempfile
import uuid
import base64

# --- Main Functions ---
TEMP_DIR = tempfile.gettempdir()

def compress_pdf(input_path, quality):
    """Compresses a PDF and returns the resulting bytes."""
    output_path = os.path.join(TEMP_DIR, f"compressed_{uuid.uuid4().hex}.pdf")
    ghostscript_path = 'gs'
    command = [
        ghostscript_path, '-sDEVICE=pdfwrite', '-dCompatibilityLevel=1.4',
        f'-dPDFSETTINGS=/{quality}', '-dNOPAUSE', '-dQUIET', '-dBATCH',
        f'-sOutputFile={output_path}', input_path
    ]
    try:
        subprocess.run(command, check=True, capture_output=True, text=True)
        with open(output_path, "rb") as f:
            file_bytes = f.read()
        os.remove(output_path) # Clean up
        return file_bytes
    except Exception as e:
        st.error(f"An error occurred during compression: {e}")
        if os.path.exists(output_path):
            os.remove(output_path)
        return None

def trigger_download(pdf_bytes, filename):
    """
    Injects JavaScript to trigger the file download in the browser.
    """
    b64 = base64.b64encode(pdf_bytes).decode()
    
    # The JavaScript code
    js = f"""
    <script>
        // Create a link element
        const link = document.createElement('a');
        // Set the link's properties
        link.href = 'data:application/pdf;base64,{b64}';
        link.download = '{filename}';
        // Append the link to the body (required for Firefox)
        document.body.appendChild(link);
        // Programmatically click the link to trigger the download
        link.click();
        // Remove the link from the document
        document.body.removeChild(link);
    </script>
    """
    # Use st.html to inject the script
    st.html(js)

# --- Streamlit App Interface ---
st.set_page_config(layout="centered", page_title="PDF Pro")
st.title("📄 PDF Compressor")

uploaded_file = st.file_uploader("1. Upload a PDF to compress", type=["pdf"])

if uploaded_file:
    quality = st.selectbox(
        "2. Select Compression Quality",
        ('ebook', 'screen', 'printer', 'prepress'),
        help="**ebook:** Good balance. **screen:** Smallest size."
    )

    if st.button("3. Compress & Download", type="primary"):
        input_path = os.path.join(TEMP_DIR, uploaded_file.name)
        with open(input_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        
        with st.spinner("Compressing... Your download will start shortly."):
            compressed_bytes = compress_pdf(input_path, quality)
        
        os.remove(input_path)

        if compressed_bytes:
            st.success("✅ Compression successful! Starting download...")
            download_filename = f"compressed_{uploaded_file.name}"
            # Call the function to trigger the download via JavaScript
            trigger_download(compressed_bytes, download_filename)
        else:
            st.error("Compression failed. Could not start download.")
