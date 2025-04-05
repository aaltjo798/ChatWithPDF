# Chat with PDF

A powerful web application that allows you to upload PDF documents and chat with them using locally running AI. Built with Flask and powered by Ollama, this application provides an intuitive interface for interacting with PDF content through natural language conversations.

## Features

- 📄 **PDF Upload & Processing**
  - Upload PDF documents up to 16MB
  - Automatic text extraction and processing
  - Smart text chunking for better context management

- 🤖 **AI-Powered Chat**
  - Interactive chat interface with PDF content
  - Support for multiple AI models through Ollama
  - Context-aware responses based on PDF content
  - Bullet-point formatting for better readability

- 💬 **Chat History**
  - Persistent chat history per PDF
  - Ability to clear chat history
  - Automatic history saving

- 🎨 **Modern UI**
  - Clean and intuitive interface
  - Real-time chat updates
  - Responsive design

## Prerequisites

- Python 3.10 or higher
- Ollama installed and running locally
- Git (optional, for version control)

## Installation

1. Clone the repository (if using Git):
   ```bash
   git clone https://github.com/yourusername/ChatWithPDF.git
   cd ChatWithPDF
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv .venv
   .venv\Scripts\activate  # On Windows
   source .venv/bin/activate  # On Unix/MacOS
   ```

3. Install required packages:
   ```bash
   pip install -r requirements.txt
   ```

4. Start Ollama server:
   ```bash
   ollama serve
   ```

5. Run the application:
   ```bash
   python app.py
   ```

   Or use the provided batch file on Windows:
   ```bash
   Chat with PDF.bat
   ```

## Usage

1. Open your web browser and navigate to `http://localhost:5000`
2. Upload a PDF file using the upload button
3. Once processed, click on the PDF to start chatting
4. Type your questions in the chat interface
5. The AI will respond based on the PDF content
6. Use the clear history button to start fresh with a PDF

## Project Structure

```
ChatWithPDF/
├── app.py                 # Main Flask application
├── templates/            # HTML templates
│   └── index.html       # Main page template
├── static/              # Static files (CSS, JS)
├── pdf_vault/          # Directory for processed PDFs
├── chat_history/       # Directory for chat histories
├── .venv/              # Virtual environment
└── requirements.txt    # Python dependencies
```

## Configuration

The application can be configured through environment variables or by modifying `app.py`:

- `UPLOAD_FOLDER`: Directory for storing processed PDFs
- `CHAT_HISTORY_FOLDER`: Directory for storing chat histories
- `MAX_CONTENT_LENGTH`: Maximum file size for uploads (default: 16MB)

## Dependencies

- Flask: Web framework
- PyPDF2: PDF text extraction
- LangChain: Text splitting and processing
- Ollama: AI model integration
- Werkzeug: Utilities for WSGI applications

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Built with [Flask](https://flask.palletsprojects.com/)
- Powered by [Ollama](https://ollama.ai/)
- PDF processing with [PyPDF2](https://pypdf2.readthedocs.io/)
- Text processing with [LangChain](https://www.langchain.com/) 