from flask import Flask, request, jsonify, render_template_string
import os
import glob
from datetime import datetime
from validators import validate_pdf
from utilities.pdf_parser import extract_text_and_structure
from utilities.image_detector import extract_images
from utilities.table_extractor import extract_tables
from utilities.metadata_extractor import extract_metadata
from utilities.ocr import perform_ocr

app = Flask(__name__)

# Configuration
STATIC_FOLDER = 'static'
OUTPUT_FOLDER = 'output'
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB

# Ensure directories exist
os.makedirs(STATIC_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

def process_pdf(pdf_path, filename):
    """
    Process a single PDF file through all utilities
    """
    try:
        print(f"Processing {filename}...")
        
        # Initialize results dictionary
        results = {
            'filename': filename,
            'processed_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'text_content': '',
            'structure': {},
            'images': [],
            'tables': [],
            'metadata': {},
            'ocr_text': ''
        }
        
        # Step 1: Validate PDF
        validation_result = validate_pdf(pdf_path)
        if not validation_result['valid']:
            results['error'] = validation_result['error']
            return results
        
        # Step 2: Extract text and structure
        print("Extracting text and structure...")
        text_data = extract_text_and_structure(pdf_path)
        results['text_content'] = text_data.get('text', '')
        results['structure'] = text_data.get('structure', {})
        
        # Step 3: Extract images
        print("Extracting images...")
        images_data = extract_images(pdf_path)
        results['images'] = images_data
        
        # Step 4: Extract tables
        print("Extracting tables...")
        tables_data = extract_tables(pdf_path)
        results['tables'] = tables_data
        
        # Step 5: Extract metadata
        print("Extracting metadata...")
        metadata = extract_metadata(pdf_path)
        results['metadata'] = metadata
        
        # Step 6: Perform OCR if needed
        print("Performing OCR...")
        ocr_text = perform_ocr(pdf_path)
        results['ocr_text'] = ocr_text
        
        return results
        
    except Exception as e:
        return {
            'filename': filename,
            'error': f"Processing failed: {str(e)}",
            'processed_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }

def generate_output_text(results):
    """
    Generate comprehensive text output from processing results
    """
    output_lines = []
    
    # Header
    output_lines.append("=" * 80)
    output_lines.append(f"PDF PROCESSING RESULTS: {results['filename']}")
    output_lines.append(f"Processed at: {results['processed_at']}")
    output_lines.append("=" * 80)
    output_lines.append("")
    
    # Error handling
    if 'error' in results:
        output_lines.append(f"ERROR: {results['error']}")
        return "\n".join(output_lines)
    
    # Metadata section
    if results.get('metadata'):
        output_lines.append("DOCUMENT METADATA:")
        output_lines.append("-" * 40)
        for key, value in results['metadata'].items():
            if value:
                output_lines.append(f"{key.title()}: {value}")
        output_lines.append("")
    
    # Document structure
    if results.get('structure'):
        output_lines.append("DOCUMENT STRUCTURE:")
        output_lines.append("-" * 40)
        structure = results['structure']
        output_lines.append(f"Total Pages: {structure.get('total_pages', 'Unknown')}")
        
        if 'headings' in structure:
            output_lines.append("Headings Found:")
            for heading in structure['headings']:
                output_lines.append(f"  - {heading}")
        output_lines.append("")
    
    # Images section
    if results.get('images'):
        output_lines.append("EXTRACTED IMAGES:")
        output_lines.append("-" * 40)
        for i, img_info in enumerate(results['images'], 1):
            output_lines.append(f"Image {i}:")
            output_lines.append(f"  Page: {img_info.get('page', 'Unknown')}")
            output_lines.append(f"  Size: {img_info.get('size', 'Unknown')}")
            output_lines.append(f"  Format: {img_info.get('format', 'Unknown')}")
            if img_info.get('description'):
                output_lines.append(f"  Description: {img_info['description']}")
        output_lines.append("")
    
    # Tables section
    if results.get('tables'):
        output_lines.append("EXTRACTED TABLES:")
        output_lines.append("-" * 40)
        for i, table_info in enumerate(results['tables'], 1):
            output_lines.append(f"Table {i}:")
            output_lines.append(f"  Page: {table_info.get('page', 'Unknown')}")
            output_lines.append(f"  Dimensions: {table_info.get('shape', 'Unknown')}")
            output_lines.append(f"  Accuracy: {table_info.get('accuracy', 'Unknown')}%")
            
            # Include table content summary
            if 'content' in table_info:
                output_lines.append("  Content Summary:")
                content = table_info['content']
                if isinstance(content, str):
                    preview = content[:200] + "..." if len(content) > 200 else content
                    output_lines.append(f"    {preview}")
        output_lines.append("")
    
    # Main text content
    if results.get('text_content'):
        output_lines.append("EXTRACTED TEXT CONTENT:")
        output_lines.append("-" * 40)
        output_lines.append(results['text_content'])
        output_lines.append("")
    
    # OCR text (if different from main text)
    if results.get('ocr_text') and results['ocr_text'] != results.get('text_content', ''):
        output_lines.append("OCR EXTRACTED TEXT:")
        output_lines.append("-" * 40)
        output_lines.append(results['ocr_text'])
        output_lines.append("")
    
    # Summary
    output_lines.append("PROCESSING SUMMARY:")
    output_lines.append("-" * 40)
    output_lines.append(f"Text Length: {len(results.get('text_content', ''))} characters")
    output_lines.append(f"Images Found: {len(results.get('images', []))}")
    output_lines.append(f"Tables Found: {len(results.get('tables', []))}")
    output_lines.append(f"OCR Length: {len(results.get('ocr_text', ''))} characters")
    
    return "\n".join(output_lines)

@app.route('/')
def index():
    """
    Simple web interface
    """
    html_template = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>PDF Processor</title>
    </head>
    <body>
        <h1>PDF Processing System</h1>
        <p>Place your PDF files in the 'static' folder and click process.</p>
        <form action="/process" method="post">
            <button type="submit">Process All PDFs</button>
        </form>
        
        <h2>Available PDFs:</h2>
        <ul>
        {% for pdf in pdfs %}
            <li>{{ pdf }}</li>
        {% endfor %}
        </ul>
    </body>
    </html>
    """
    
    pdf_files = glob.glob(os.path.join(STATIC_FOLDER, '*.pdf'))
    pdf_names = [os.path.basename(f) for f in pdf_files]
    
    return render_template_string(html_template, pdfs=pdf_names)

@app.route('/process', methods=['POST'])
def process_all_pdfs():
    """
    Process all PDFs in static folder
    """
    pdf_files = glob.glob(os.path.join(STATIC_FOLDER, '*.pdf'))
    
    if not pdf_files:
        return jsonify({'error': 'No PDF files found in static folder'})
    
    processed_files = []
    
    for pdf_file in pdf_files:
        filename = os.path.basename(pdf_file)
        
        # Process the PDF
        results = process_pdf(pdf_file, filename)
        
        # Generate output text
        output_text = generate_output_text(results)
        
        # Save to output file
        output_filename = f"{os.path.splitext(filename)[0]}_processed.txt"
        output_path = os.path.join(OUTPUT_FOLDER, output_filename)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(output_text)
        
        processed_files.append({
            'input': filename,
            'output': output_filename,
            'status': 'success' if 'error' not in results else 'error'
        })
    
    return jsonify({
        'message': f'Processed {len(processed_files)} files',
        'files': processed_files
    })

if __name__ == '__main__':
    print("PDF Processing System Starting...")
    print(f"Place PDF files in: {os.path.abspath(STATIC_FOLDER)}")
    print(f"Output will be saved to: {os.path.abspath(OUTPUT_FOLDER)}")
    print("Visit http://127.0.0.1:5000 to use the web interface")
    
    app.run(debug=True)
