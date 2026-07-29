"""
PDF Service Module.
Why this file exists: Handles physical file operations and text extraction.
Why this design was chosen: Decoupling file reading from AI embedding allows us to easily swap out PyPDF for OCR tools (like Tesseract) later if we need to process scanned images.
"""
from io import BytesIO
from typing import List, Dict
from pypdf import PdfReader

def extract_text_from_pdf(file_bytes: bytes) -> List[Dict[str, str]]:
    """
    Extracts text from a PDF, maintaining page numbers.
    Returns a list of dictionaries containing page_number and text.
    """
    reader = PdfReader(BytesIO(file_bytes))
    pages_data = []
    
    for i, page in enumerate(reader.pages):
        text = page.extract_text()
        if text:
            pages_data.append({
                "page_number": i + 1,
                "text": text
            })
            
    return pages_data
