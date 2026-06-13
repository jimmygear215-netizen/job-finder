import io
from pypdf import PdfReader

def extract_text_from_pdf(file_storage):
    reader = PdfReader(file_storage)
    text = ""
    for page in reader.pages:
        extracted = page.extract_text()
        if extracted:
            text += extracted + "\n"
    return text.strip()
