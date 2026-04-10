import PyPDF2
import re
from typing import Optional

def extract_text_from_pdf(pdf_path: str) -> Optional[str]:
    """Extract and clean text content from a PDF file optimized for resume layouts."""
    try:
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            text_parts = []
            
            for page in pdf_reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(page_text)
            
            # Combine all pages
            full_text = "\n".join(text_parts)
            
            # Clean the text
            cleaned_text = _clean_text(full_text)
            
            return cleaned_text
            
    except Exception as e:
        raise Exception(f"Error extracting PDF text: {str(e)}")

def _clean_text(text: str) -> str:
    """Clean extracted text by removing extra whitespace and formatting issues."""
    # Replace multiple spaces with single space
    text = re.sub(r' +', ' ', text)
    
    # Replace multiple newlines with double newline (preserve paragraph breaks)
    text = re.sub(r'\n{3,}', '\n\n', text)
    
    # Remove spaces before punctuation
    text = re.sub(r'\s+([.,;:!?])', r'\1', text)
    
    # Fix common OCR/extraction issues
    text = re.sub(r'([a-z])([A-Z])', r'\1 \2', text)  # Add space between camelCase
    
    # Remove bullet point artifacts
    text = re.sub(r'[•●○■□▪▫]', '', text)
    
    # Normalize dashes
    text = re.sub(r'[–—]', '-', text)
    
    # Remove excessive tabs
    text = re.sub(r'\t+', ' ', text)
    
    # Strip leading/trailing whitespace from each line
    lines = [line.strip() for line in text.split('\n')]
    
    # Remove empty lines
    lines = [line for line in lines if line]
    
    # Join with single newline
    text = '\n'.join(lines)
    
    # Final strip
    return text.strip()
