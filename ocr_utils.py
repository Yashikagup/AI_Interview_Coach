import os
from PIL import Image
import pytesseract
from pdfminer.high_level import extract_text

# Optional: OCR for scanned PDFs
try:
    from pdf2image import convert_from_path
    POPPLER_AVAILABLE = True
except ImportError:
    POPPLER_AVAILABLE = False

# Set tesseract path
pytesseract.pytesseract.tesseract_cmd = r"D:\Tesseract-OCR\tesseract.exe"


def extract_text_from_image(image_path):
    """Extract text from an image (JPG/PNG) using pytesseract"""
    try:
        image = Image.open(image_path)
        text = pytesseract.image_to_string(image)
        return text
    except Exception as e:
        print("❌ OCR failed for image:", e)
        return ""


def extract_text_from_pdf(pdf_path):
    """
    Extract text from PDF.
    Uses pdfminer for text PDFs.
    Falls back to OCR for scanned PDFs if poppler is available.
    """
    text = ""
    # First try pdfminer
    try:
        text = extract_text(pdf_path)
        if text.strip():
            return text
    except Exception as e:
        print("⚠️ pdfminer failed:", e)
        text = ""

    # If pdfminer gave nothing, try OCR (scanned PDF)
    if POPPLER_AVAILABLE:
        try:
            pages = convert_from_path(pdf_path, dpi=300)  # Will raise error if Poppler missing
            text_pages = [pytesseract.image_to_string(page) for page in pages]
            text = "\n".join(text_pages)
        except Exception as e:
            print("❌ OCR for PDF failed:", e)
            text = ""
    else:
        print("⚠️ Poppler not installed. Cannot OCR scanned PDFs.")

    return text


def extract_text_from_resume(file_path):
    """
    Detect file type and extract text:
    - PDF → pdfminer / OCR
    - Image → OCR
    Returns empty string if unreadable
    """
    file_path = str(file_path)

    if file_path.lower().endswith(".pdf"):
        text = extract_text_from_pdf(file_path)
    elif file_path.lower().endswith((".jpg", ".jpeg", ".png")):
        text = extract_text_from_image(file_path)
    else:
        print("❌ Unsupported file type:", file_path)
        text = ""

    return text
