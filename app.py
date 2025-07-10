import streamlit as st
import subprocess
import os
import tempfile
import uuid
import base64

def trigger_download(pdf_bytes, filename):
    """Injects JavaScript to force a file download in the browser."""
    b64 = base64.b64encode(pdf_bytes).decode()
    js = f"""
    <script>
        // Create a link element
        const link = document.createElement('a');
        // Set its properties
        link.href = 'data:application/pdf;base64,{b64}';
        link.download = '{filename}';
        // Append to the body and click it to trigger the download
        document.body.appendChild(link);
        link.click();
        // Clean up by removing the link
        document.body.removeChild(link);
    </script>
    """
    # Use st.html to execute the script
    st.html(js)

def compress_pdf(input_path, quality):
    """Compresses a PDF and returns its bytes."""
    output_path = os.path.join(tempfile.gettempdir(), f"compressed_{uuid.uuid4().hex}.pdf")
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
        os.remove(output_path)
        return file_bytes
    except Exception as e:
        st.error(f"An error occurred during compression: {e}")
        if os.path.exists(output_path):
            os.remove(output_path)
        return None

# --- Streamlit App Interface ---
st.set_page_config(layout="centered", page_title="PDF Pro")
st.title("📄 PDF Compressor")

# Initialize session state
if 'pdf_result' not in st.session_state:
    st.session_state.pdf_result = None
if 'file_name' not in st.session_state:
    st.session_state.file_name = None

uploaded_file = st.file_uploader("1. Upload your PDF file", type=["pdf"])

if uploaded_file:
    # Clear previous results when a new file is uploaded
    if 'last_file_id' not in st.session_state or st.session_state.last_file_id != uploaded_file.file_id:
        st.session_state.last_file_id = uploaded_file.file_id
        st.session_state.pdf_result = None

    quality = st.selectbox(
        "2. Select a compression quality",
        ('ebook', 'screen', 'printer', 'prepress')
    )

    if st.button("3. Compress PDF", type="primary"):
        input_path = os.path.join(tempfile.gettempdir(), uploaded_file.name)
        with open(input_path, "wb") as f:
            f.write(uploaded_file.getbuffer())

        with st.spinner("Compressing..."):
            st.session_state.pdf_result = compress_pdf(input_path, quality)
            st.session_state.file_name = f"compressed_{uploaded_file.name}"

        os.remove(input_path)

        if st.session_state.pdf_result:
            st.success("✅ Compression successful! Press the download button below.")
        else:
            st.error("Compression failed.")

# The download button appears only after successful compression
if st.session_state.pdf_result:
    st.markdown("---")
    st.markdown("### 4. Download Your File")

    # This is a standard button that triggers the JavaScript download
    if st.button("⬇️ Download Now"):
        trigger_download(st.session_state.pdf_result, st.session_state.file_name)
