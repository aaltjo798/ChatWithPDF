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

from flask import Flask, render_template, request, jsonify
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
        text += page.extract_text()
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

@app.route('/')
def index():
    """
    Render the main page of the application.
    
    Returns:
        HTML: Rendered template with list of processed PDFs
    """
    # Get list of processed PDFs from the upload folder
    pdfs = [f for f in os.listdir(app.config['UPLOAD_FOLDER']) if f.endswith('.json')]
    return render_template('index.html', pdfs=pdfs)

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
    Delete a PDF and its associated chat history.
    
    Args:
        pdf_name: Name of the PDF file
        
    Returns:
        JSON: Success message or error message if something goes wrong
    """
    try:
        # Delete the PDF file
        pdf_path = os.path.join(app.config['UPLOAD_FOLDER'], pdf_name)
        if os.path.exists(pdf_path):
            os.remove(pdf_path)
            
        # Delete associated chat history
        history_file = get_chat_history_file(pdf_name)
        if os.path.exists(history_file):
            os.remove(history_file)
            
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/upload', methods=['POST'])
def upload_file():
    """
    Handle PDF file uploads, process the PDF, and store its content.
    
    Returns:
        JSON: Success message with number of chunks or error message if something goes wrong
        
    Process:
        1. Validate the uploaded file
        2. Extract text from PDF
        3. Split text into chunks for better processing
        4. Save chunks to JSON file
    """
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    if file and file.filename.endswith('.pdf'):
        try:
            # Extract text from PDF
            text = extract_text_from_pdf(file)
            
            # Split text into manageable chunks
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=1000,  # Size of each text chunk
                chunk_overlap=200  # Overlap between chunks for context
            )
            text_chunks = text_splitter.split_text(text)
            
            # Save processed chunks to JSON file
            filename = secure_filename(file.filename.replace('.pdf', '.json'))
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            with open(filepath, 'w') as f:
                json.dump(text_chunks, f)
            
            return jsonify({
                'success': True,
                'message': f'PDF uploaded with {len(text_chunks)} chunks',
                'filename': filename
            })
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    return jsonify({'error': 'Invalid file type'}), 400

@app.route('/chat', methods=['POST'])
def chat():
    """
    Handle chat interactions with the PDF content using Ollama AI.
    
    Process:
        1. Load the relevant PDF content
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

        # Load the PDF data
        pdf_path = os.path.join(app.config['UPLOAD_FOLDER'], pdf_name)
        if not os.path.exists(pdf_path):
            return jsonify({'error': 'PDF not found'}), 404

        # Load PDF chunks
        with open(pdf_path, 'r') as f:
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


