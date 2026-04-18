import pdfplumber
import io

def extract_text_from_pdf(file_bytes: bytes) -> str:
    text = ""
    with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
        for page in pdf.pages:
            content = page.extract_text()
            if content:
                text += content + "\n"
    
    if not text.strip():
        raise ValueError("The PDF appears to be empty or image-based.")
        
    return text
