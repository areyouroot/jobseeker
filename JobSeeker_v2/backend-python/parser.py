from pdfminer.high_level import extract_text
import re

def parse_pdf_to_json(file_path: str) -> dict:
    text = extract_text(file_path)

    # Very basic regex-based extraction (Mocking a real parser for now)
    # In a real world, we would use Spacy or a dedicated resume parser library

    email = re.search(r'[\w.+-]+@[\w-]+\.[\w.-]+', text)
    phone = re.search(r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}', text)

    return {
        "basics": {
            "name": "Candidate Name", # Placeholder or need NLP to extract
            "email": email.group(0) if email else "",
            "phone": phone.group(0) if phone else "",
            "summary": text[:200] # First 200 chars as summary approximation
        },
        "raw_text": text
    }
