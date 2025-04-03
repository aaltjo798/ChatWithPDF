import os
import tkinter as tk
from tkinter import filedialog, messagebox
import PyPDF2
import json
from langchain.text_splitter import RecursiveCharacterTextSplitter

class PDFUploader:
    def __init__(self, upload_callback):
        self.root = tk.Toplevel()
        self.root.title("Upload PDF")
        self.root.geometry("400x200")
        
        self.vault_dir = "pdf_vault"
        os.makedirs(self.vault_dir, exist_ok=True)
        
        self.upload_callback = upload_callback
        
        # Create upload button
        self.upload_btn = tk.Button(
            self.root, 
            text="Select PDF to Upload", 
            command=self.upload_pdf,
            width=30,
            height=2
        )
        self.upload_btn.pack(expand=True, pady=50)
        
    def upload_pdf(self):
        # Open file dialog to select PDF
        file_path = filedialog.askopenfilename(
            title="Select PDF", 
            filetypes=[("PDF files", "*.pdf")]
        )
        
        if not file_path:
            return
        
        try:
            # Extract text from PDF
            text = self.extract_text_from_pdf(file_path)
            
            # Split text into chunks
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=1000,
                chunk_overlap=200
            )
            text_chunks = text_splitter.split_text(text)
            
            # Prompt for filename
            filename = os.path.basename(file_path)
            
            # Save chunks to vault
            filepath = os.path.join(self.vault_dir, filename.replace('.pdf', '.json'))
            with open(filepath, 'w') as f:
                json.dump(text_chunks, f)
            
            # Call upload callback
            if self.upload_callback:
                self.upload_callback(text_chunks)
            
            # Show success message
            messagebox.showinfo(
                "Upload Successful", 
                f"PDF uploaded with {len(text_chunks)} chunks"
            )
            
            # Hide upload window
            self.root.withdraw()
        
        except Exception as e:
            messagebox.showerror("Upload Error", str(e))
        
    def extract_text_from_pdf(self, file_path):
        """Extract text from PDF file"""
        with open(file_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            text = ""
            for page in reader.pages:
                text += page.extract_text()
        return text