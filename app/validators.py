import os
import magic
import PyPDF2
from typing import Dict, Any

def validate_pdf(file_path: str) -> Dict[str, Any]:
    """
    Comprehensive PDF validation
    """
    try:
        # Check if file exists
        if not os.path.exists(file_path):
            return {'valid': False, 'error': 'File does not exist'}
        
        # Check file size (50MB limit)
        file_size = os.path.getsize(file_path)
        max_size = 50 * 1024 * 1024  # 50MB
        
        if file_size == 0:
            return {'valid': False, 'error': 'File is empty'}
        
        if file_size > max_size:
            return {'valid': False, 'error': f'File too large: {file_size / (1024*1024):.1f}MB (max: 50MB)'}
        
        # Check file type using magic
        try:
            file_type = magic.from_file(file_path, mime=True)
            if file_type != 'application/pdf':
                return {'valid': False, 'error': f'Invalid file type: {file_type}. Expected PDF.'}
        except Exception:
            # Fallback to extension check
            if not file_path.lower().endswith('.pdf'):
                return {'valid': False, 'error': 'File does not have .pdf extension'}
        
        # Try to open with PyPDF2
        try:
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                num_pages = len(pdf_reader.pages)
                
                if num_pages == 0:
                    return {'valid': False, 'error': 'PDF has no pages'}
                
                # Try to read first page to ensure it's not corrupted
                first_page = pdf_reader.pages[0]
                text = first_page.extract_text()
                
        except PyPDF2.errors.PdfReadError as e:
            return {'valid': False, 'error': f'Corrupted PDF: {str(e)}'}
        except Exception as e:
            return {'valid': False, 'error': f'PDF validation failed: {str(e)}'}
        
        return {
            'valid': True,
            'file_size': file_size,
            'num_pages': num_pages,
            'has_text': len(text.strip()) > 0
        }
        
    except Exception as e:
        return {'valid': False, 'error': f'Validation error: {str(e)}'}

def validate_file_extension(filename: str) -> bool:
    """
    Check if file has valid PDF extension
    """
    allowed_extensions = ['.pdf']
    return any(filename.lower().endswith(ext) for ext in allowed_extensions)

def check_file_size(file_path: str, max_size_mb: int = 50) -> Dict[str, Any]:
    """
    Check if file size is within limits
    """
    try:
        file_size = os.path.getsize(file_path)
        max_size_bytes = max_size_mb * 1024 * 1024
        
        return {
            'valid': file_size <= max_size_bytes,
            'size_mb': file_size / (1024 * 1024),
            'max_size_mb': max_size_mb
        }
    except Exception as e:
        return {'valid': False, 'error': str(e)}
