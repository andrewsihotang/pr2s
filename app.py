import streamlit as st
import subprocess
import os
import tempfile
import uuid
import base64

# --- Helper Function for Creating a Download Link ---
def create_download_link(val, filename):
    """
    Generates a download link for a file from its bytes.
    """
    b64 = base64.b64encode(val).decode()
    # **THE FIX IS HERE:** The MIME type is now 'application/pdf'
    return f'<a href="data:application/pdf;base64,{b64}" download="{filename}">⬇️ Download Your Compressed PDF</a>'

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

# --- Streamlit App Interface ---
st.set_page_config(layout="centered", page_title="PDF Pro")
st.title("📄 PDF Compressor")

# Initialize state
if 'pdf_result' not in st.session_state:
    st.session_state.pdf_result = None

uploaded_file = st.file_uploader("Upload a PDF to compress", type=["pdf"])

if uploaded_file:
    # Clear previous results when a new file is uploaded
    if 'last_file_id' not in st.session_state or st.session_state.last_file_id != uploaded_file.file_id:
        st.session_state.last_file_id = uploaded_file.file_id
        st.session_state.pdf_result = None

    quality = st.selectbox(
        "Select Compression Quality",
        ('ebook', 'screen', 'printer', 'prepress'),
        help="**ebook:** Good balance. **screen:** Smallest size."
    )

    if st.button("Compress PDF", type="primary"):
        input_path = os.path.join(TEMP_DIR, uploaded_file.name)
        with open(input_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        
        with st.spinner("Compressing... This may take a moment."):
            # Store the result directly in session state
            st.session_state.pdf_result = compress_pdf(input_path, quality)
        
        os.remove(input_path) # Clean up

# Display the download link if compression was successful
if st.session_state.pdf_result:
    st.success("✅ Compression successful! Click the link below to download.")
    download_filename = f"compressed_{uploaded_file.name}"
    # Generate and display the custom HTML download link
    download_link = create_download_link(st.session_state.pdf_result, download_filename)
    st.markdown(download_link, unsafe_allow_html=True)
