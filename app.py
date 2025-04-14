"""
Chat with PDF - A Flask web application that allows users to upload PDFs and chat with them using Ollama AI.
This application provides a simple interface for:
- Uploading PDF documents
- Extracting and processing text from PDFs
- Chatting with the PDF content using AI
- Maintaining chat history per PDF
- Supporting multiple AI models through Ollama

Dependencies:
- Flask: Web framework
- PyPDF2: PDF text extraction
- LangChain: Text splitting and processing
- Ollama: AI model integration
"""

from flask import Flask, render_template, request, jsonify, send_from_directory, url_for
from werkzeug.utils import secure_filename
import os
import json
import PyPDF2
from langchain.text_splitter import RecursiveCharacterTextSplitter
import ollama
import requests

# Initialize Flask application
app = Flask(__name__)

# Application configuration
app.config['UPLOAD_FOLDER'] = 'pdf_vault'  # Directory for storing processed PDFs
app.config['CHAT_HISTORY_FOLDER'] = 'chat_history'  # Directory for storing chat histories
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size for uploads

# Create necessary directories if they don't exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['CHAT_HISTORY_FOLDER'], exist_ok=True)

# Initialize chat history directory with a .gitkeep file to ensure it's tracked
gitkeep_file = os.path.join(app.config['CHAT_HISTORY_FOLDER'], '.gitkeep')
if not os.path.exists(gitkeep_file):
    with open(gitkeep_file, 'w') as f:
        f.write('')

def extract_text_from_pdf(file):
    """
    Extract text content from a PDF file.
    
    Args:
        file: FileStorage object from Flask containing the PDF file
        
    Returns:
        str: Extracted text content from all pages of the PDF
        
    Note:
        This function uses PyPDF2 to read and extract text from each page of the PDF.
    """
    reader = PyPDF2.PdfReader(file)
    text = ""
    for page in reader.pages:
        try:
            page_text = page.extract_text()
            if page_text:
                # Handle potential encoding issues
                try:
                    text += page_text
                except UnicodeDecodeError:
                    # If there's a decode error, try to encode and decode with different encodings
                    text += page_text.encode('utf-8', errors='ignore').decode('utf-8')
        except Exception as e:
            print(f"Error extracting text from page: {str(e)}")
            continue
    return text

def get_chat_history_file(pdf_name):
    """
    Generate the file path for storing chat history of a specific PDF.
    
    Args:
        pdf_name: Name of the PDF file (without extension)
        
    Returns:
        str: Full path to the chat history JSON file
    """
    return os.path.join(app.config['CHAT_HISTORY_FOLDER'], f"{pdf_name}_history.json")

@app.route('/pdf/<filename>')
def serve_pdf(filename):
    """Serve PDF files from the pdf_vault directory."""
    try:
        return send_from_directory(app.config['UPLOAD_FOLDER'], filename)
    except Exception as e:
        return jsonify({'error': str(e)}), 404

@app.route('/')
def index():
    """Render the main page with a list of available PDFs."""
    pdf_files = []
    for filename in os.listdir(app.config['UPLOAD_FOLDER']):
        if filename.endswith('.pdf'):
            pdf_files.append({
                'name': filename,
                'url': url_for('serve_pdf', filename=filename)
            })
    return render_template('index.html', pdf_files=pdf_files)

@app.route('/chat-history/<pdf_name>')
def get_chat_history(pdf_name):
    """
    Retrieve chat history for a specific PDF.
    
    Args:
        pdf_name: Name of the PDF file
        
    Returns:
        JSON: Array of chat messages or error message if something goes wrong
    """
    try:
        history_file = get_chat_history_file(pdf_name)
        if os.path.exists(history_file):
            with open(history_file, 'r') as f:
                return jsonify(json.load(f))
        return jsonify([])
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/clear-history/<pdf_name>', methods=['POST'])
def clear_chat_history(pdf_name):
    """
    Clear the chat history for a specific PDF.
    
    Args:
        pdf_name: Name of the PDF file
        
    Returns:
        JSON: Success message or error message if something goes wrong
    """
    try:
        history_file = get_chat_history_file(pdf_name)
        if os.path.exists(history_file):
            os.remove(history_file)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/delete-pdf/<pdf_name>', methods=['POST'])
def delete_pdf(pdf_name):
    """
    Delete a PDF and its associated JSON file.
    
    Args:
        pdf_name: Name of the PDF file to delete
        
    Returns:
        JSON response indicating success or failure
    """
    try:
        # Delete the PDF file
        pdf_path = os.path.join(app.config['UPLOAD_FOLDER'], pdf_name)
        if os.path.exists(pdf_path):
            os.remove(pdf_path)
            print(f"Deleted PDF file: {pdf_path}")
        
        # Delete the associated JSON file
        json_filename = pdf_name.replace('.pdf', '.json')
        json_path = os.path.join(app.config['UPLOAD_FOLDER'], json_filename)
        if os.path.exists(json_path):
            os.remove(json_path)
            print(f"Deleted JSON file: {json_path}")
        
        return jsonify({'success': True})
    except Exception as e:
        print(f"Error deleting files: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/upload', methods=['POST'])
def upload_file():
    """
    Handle PDF file uploads, process the PDF, and store its content.
    
    Returns:
        JSON: Success message with number of chunks or error message if something goes wrong
        
    Process:
        1. Validate the uploaded file
        2. Save the PDF file
        3. Extract text from PDF
        4. Split text into chunks for better processing
        5. Save chunks to JSON file
    """
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    if file and file.filename.endswith('.pdf'):
        try:
            # Save the PDF file
            pdf_filename = secure_filename(file.filename)
            pdf_filepath = os.path.join(app.config['UPLOAD_FOLDER'], pdf_filename)
            file.save(pdf_filepath)
            
            # Extract text from PDF
            text = extract_text_from_pdf(file)
            
            # Split text into manageable chunks
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=1000,  # Size of each text chunk
                chunk_overlap=200  # Overlap between chunks for context
            )
            text_chunks = text_splitter.split_text(text)
            
            # Save processed chunks to JSON file
            json_filename = secure_filename(file.filename.replace('.pdf', '.json'))
            json_filepath = os.path.join(app.config['UPLOAD_FOLDER'], json_filename)
            with open(json_filepath, 'w') as f:
                json.dump(text_chunks, f)
            
            return jsonify({
                'success': True,
                'chunks': len(text_chunks)
            })
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    else:
        return jsonify({'error': 'Invalid file type. Please upload a PDF file.'}), 400

@app.route('/chat', methods=['POST'])
def chat():
    """
    Handle chat interactions with the PDF content using Ollama AI.
    
    Process:
        1. Load the relevant PDF content from JSON
        2. Prepare context from the PDF
        3. Load chat history
        4. Generate AI response
        5. Update and save chat history
        
    Returns:
        JSON: AI response or error message if something goes wrong
    """
    try:
        data = request.get_json()
        pdf_name = data.get('pdf_name')
        message = data.get('message')
        model = data.get('model', 'gemma:latest')  # Default to gemma if no model specified
        
        # Validate model parameter
        if not model or not isinstance(model, str):
            model = 'gemma:latest'  # Fallback to default model
        
        if not pdf_name or not message:
            return jsonify({'error': 'Missing required fields'}), 400

        # Load the processed PDF data from JSON
        json_path = os.path.join(app.config['UPLOAD_FOLDER'], pdf_name.replace('.pdf', '.json'))
        if not os.path.exists(json_path):
            return jsonify({'error': 'Processed PDF data not found'}), 404

        # Load PDF chunks
        with open(json_path, 'r') as f:
            text_chunks = json.load(f)
        
        # Prepare context from first 5 chunks
        context = " ".join(text_chunks[:5])
        
        # Load chat history
        history_file = get_chat_history_file(pdf_name)
        history = []
        if os.path.exists(history_file):
            try:
                with open(history_file, 'r') as f:
                    history = json.load(f)
            except json.JSONDecodeError:
                # If history file is corrupted, start fresh
                history = []
        
        # Prepare messages array for AI
        messages = [
            {
                'role': 'system',
                'content': f'''You are a helpful assistant analyzing PDF content. When appropriate, use bullet points to structure your responses.
                Context from PDF: {context}
                
                Guidelines:
                - Use bullet points (•) when listing items or steps
                - Keep responses clear and concise
                - If the question is about lists, steps, or multiple items, always use bullet points
                - For general questions, use regular paragraph format'''
            }
        ]
        
        # Add chat history and current message
        messages.extend(history)
        messages.append({
            'role': 'user',
            'content': message
        })
        
        try:
            # Get the response from Ollama
            response = ollama.chat(model=model, messages=messages)
            
            # Update history with new messages
            history.append({
                'role': 'user',
                'content': message
            })
            history.append({
                'role': 'assistant',
                'content': response['message']['content']
            })
            
            # Save updated history
            with open(history_file, 'w') as f:
                json.dump(history, f)
            
            return jsonify({'response': response['message']['content']})
        except Exception as e:
            print(f"Error in Ollama chat: {e}")
            return jsonify({'error': 'Failed to get response from Ollama. Please check that Ollama is running.'}), 500
            
    except Exception as e:
        print(f"Error in chat endpoint: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/models')
def get_models():
    """
    Retrieve available AI models from Ollama.
    
    Returns:
        JSON: Array of available model names or empty array if error occurs
    """
    try:
        response = requests.get('http://localhost:11434/api/tags')
        if response.status_code == 200:
            models = [model['name'] for model in response.json()['models']]
            return jsonify(models)
        else:
            return jsonify([])
    except Exception as e:
        print(f"Error fetching models: {e}")
        return jsonify([])

if __name__ == '__main__':
    try:
        # Ensure all required directories exist
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
        os.makedirs(app.config['CHAT_HISTORY_FOLDER'], exist_ok=True)
        
        # Initialize chat history directory with a .gitkeep file
        gitkeep_file = os.path.join(app.config['CHAT_HISTORY_FOLDER'], '.gitkeep')
        if not os.path.exists(gitkeep_file):
            with open(gitkeep_file, 'w') as f:
                f.write('')
        
        # Start the Flask server
        print("Starting Flask server...")
        app.run(debug=True, host='127.0.0.1', port=5000)
    except Exception as e:
        print(f"Error starting server: {e}")
        input("Press Enter to exit...")  # Keep window open if there's an error 


