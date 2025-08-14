# Backend Setup Guide

## Converting Your Streamlit App to REST API

Your current `app.py` is a Streamlit application. To integrate with the React frontend, you'll need to create REST API endpoints. Here are two recommended approaches:

### Option 1: FastAPI Wrapper (Recommended)

Create a new file `api_server.py` alongside your existing `app.py`:

```python
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
import json
import tempfile
from typing import List

# Import your existing processing function
from langchain_community.document_loaders import PyMuPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain.vectorstores import FAISS
from langchain.chains import RetrievalQA
from custom_langchain import MyDualEndpointLLM as LLM

app = FastAPI(title="PDF Q&A API")

# Enable CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8080"],  # React dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Store uploaded files and vector stores in memory
uploaded_files = {}
vector_stores = {}

class QuestionRequest(BaseModel):
    question: str
    filename: str

class QuestionResponse(BaseModel):
    answer: str
    source_chunks: List[str]

def process_pdf_and_create_vectorstore(pdf_path: str, filename: str):
    """Process PDF and create vector store"""
    loader = PyMuPDFLoader(pdf_path)
    documents = loader.load()
    splitter = RecursiveCharacterTextSplitter(chunk_size=400, chunk_overlap=50)
    chunks = splitter.split_documents(documents)

    embedding_model = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    vector_store = FAISS.from_documents(chunks, embedding_model)
    
    # Store vector store for later use
    vector_stores[filename] = vector_store
    return vector_store

@app.post("/upload")
async def upload_pdf(file: UploadFile = File(...)):
    """Upload and process PDF file"""
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")
    
    try:
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
            content = await file.read()
            tmp_file.write(content)
            tmp_file_path = tmp_file.name
        
        # Process PDF and create vector store
        process_pdf_and_create_vectorstore(tmp_file_path, file.filename)
        
        # Store file info
        uploaded_files[file.filename] = {
            'path': tmp_file_path,
            'size': len(content)
        }
        
        return {
            "success": True,
            "message": f"PDF '{file.filename}' uploaded and processed successfully",
            "filename": file.filename
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing PDF: {str(e)}")

@app.post("/ask", response_model=QuestionResponse)
async def ask_question(request: QuestionRequest):
    """Ask a question about the uploaded PDF"""
    if request.filename not in vector_stores:
        raise HTTPException(status_code=400, detail="PDF not found. Please upload first.")
    
    try:
        # Load configuration
        with open("keys.txt", "r") as f:
            config = json.load(f)

        # Initialize LLM
        haiku_llm = LLM(
            secret_key=config["API_KEY"],
            non_stream_url=config["AI_Agent_URL"],
            stream_url=config.get("AI_Agent_Stream_URL")
        )

        # Get vector store and create retriever
        vector_store = vector_stores[request.filename]
        retriever = vector_store.as_retriever(search_kwargs={"k": 5})

        # Create QA chain
        qa_chain = RetrievalQA.from_chain_type(
            llm=haiku_llm,
            chain_type="stuff",
            retriever=retriever,
            return_source_documents=True
        )
        
        # Get answer
        result = qa_chain.invoke(request.question)
        answer = result["result"]
        source_chunks = [doc.page_content for doc in result["source_documents"]]
        
        return QuestionResponse(
            answer=answer,
            source_chunks=source_chunks
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing question: {str(e)}")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

### Option 2: Flask Wrapper (Alternative)

If you prefer Flask, create `flask_api.py`:

```python
from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import json
import tempfile

# Import your existing processing logic here
# ... (similar structure to FastAPI version)

app = Flask(__name__)
CORS(app)

# Similar endpoints as FastAPI version
# ... (implement /upload, /ask, /health routes)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
```

## Installation Requirements

Add these to your Python environment:

```bash
pip install fastapi uvicorn python-multipart
# OR for Flask option:
pip install flask flask-cors
```

## Running the Backend

### FastAPI Version:
```bash
python api_server.py
```

### Flask Version:
```bash
python flask_api.py
```

The API will be available at `http://localhost:8000`

## Configuration

1. **keys.txt**: Place this file in the same directory as your API server:
```json
{
    "API_KEY": "your-api-key-here",
    "AI_Agent_URL": "your-ai-agent-url",
    "AI_Agent_Stream_URL": "your-stream-url-if-available"
}
```

2. **custom_langchain.py**: Ensure this file is in the same directory as your API server.

## API Endpoints

- `POST /upload` - Upload PDF file
- `POST /ask` - Ask question about uploaded PDF
- `GET /health` - Health check

## Testing the API

Use curl to test:

```bash
# Upload PDF
curl -X POST "http://localhost:8000/upload" -F "file=@your-document.pdf"

# Ask question
curl -X POST "http://localhost:8000/ask" \
  -H "Content-Type: application/json" \
  -d '{"question": "What is this document about?", "filename": "your-document.pdf"}'
```

## Production Considerations

1. **File Storage**: Consider using cloud storage instead of temp files
2. **Security**: Add authentication and rate limiting
3. **Scalability**: Use Redis or database for vector store persistence
4. **Error Handling**: Implement comprehensive error handling
5. **Logging**: Add proper logging for debugging