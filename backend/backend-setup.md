# Backend Setup Guide

## Requirements

Python3 == 3.13 or 3.12

## Setup virtual environment

Initialize venv

```bash
python3 -m venv env
```

Activate venv

```bash
# Windows
.\env\Scripts\activate

# Linux or MacOs
source ./env/bin/activate
```

## Install Requirements

```bash
pip install -r requirements.txt
```

## Configure API keys

Create a file named `keys.txt` alongside `custom_langchain.py` and place following content in it:

```json
{
  "API_KEY": "your-api-key-here",
  "AI_Agent_URL": "your-ai-agent-url",
  "AI_Agent_Stream_URL": "your-stream-url-if-available"
}
```

## Starting the Backend

```bash
python api_server.py
```

The API will be available at `http://localhost:8000`

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
