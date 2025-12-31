from pypdf import PdfReader
import io
import re


def extract_text_from_pdf_bytes(file_bytes: bytes) -> str:
    # Convert bytes to file-like object
    pdf_file = io.BytesIO(file_bytes)
    reader = PdfReader(pdf_file)
    texts = []
    for page in reader.pages:
        try:
            texts.append(page.extract_text() or "")
        except Exception:
            # best-effort
            continue
    full = "\n\n".join(texts)
    return clean_text(full)


def clean_text(text: str) -> str:
    # Basic cleaning: normalize whitespace and remove strange control chars
    text = re.sub(r"\r\n|\r", "\n", text)
    text = re.sub(r"\u0000", "", text)
    # collapse multiple newlines
    text = re.sub(r"\n{2,}", "\n\n", text)
    return text.strip()
