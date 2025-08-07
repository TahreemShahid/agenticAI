# PDF Intelligence – AI-Powered Document Analysis

A modern React frontend for AI-driven document understanding using LangChain and advanced AI. Upload any PDF document to get instant summaries, perform intelligent comparisons, or ask natural language questions—with all features supported by robust backend AI services.

## Features

- 🎯 **Drag & Drop PDF Upload** – Simple and intuitive file upload with visual feedback.
- 📝 **AI-Powered Summarization** – Instantly generate concise or detailed summaries of your PDFs.
- ⚖️ **Document Comparison** – Compare multiple documents or sections side-by-side for differences and similarities.
- 🤖 **Q&A Over Documents** – Ask natural language questions about your document content.
- 📚 **Source Citations** – Get supporting excerpts, references, or evidence with every result.
- 🎨 **Modern UI** – Responsive, clean design with real-time feedback.
- ⚡ **Fast Processing** – Immediate responses and analysis powered by scalable AI.

## Quick Start

### Frontend (React)

1. **Install dependencies:**
```bash
npm install
```

2. **Start development server:**
```bash
npm run dev
```

The frontend will be available at `http://localhost:8080`

### Backend Setup

You need to convert your existing Streamlit app to a REST API. Follow the detailed guide in `backend-setup.md`.

**Quick Backend Setup:**

1. **Install additional Python dependencies:**
```bash
pip install fastapi uvicorn python-multipart
```

2. **Create the API server** (see `backend-setup.md` for complete code):
```bash
# Create api_server.py with the FastAPI code provided
python api_server.py
```

3. **Configure API keys:**
Create `keys.txt` in your backend directory:
```json
{
    "API_KEY": "your-api-key",
    "AI_Agent_URL": "your-ai-agent-url",
    "AI_Agent_Stream_URL": "your-stream-url"
}
```

## Project Structure

```
frontend/
├── src/
│   ├── components/
│   │   ├── PDFUploader.tsx      # File upload component
│   │   ├── QuestionInput.tsx    # Question input form
│   │   ├── AnswerDisplay.tsx    # Answer and sources display
│   │   └── Header.tsx           # App header
│   ├── hooks/
│   │   └── usePDFQA.ts         # Main application logic
│   ├── services/
│   │   └── api.ts              # API communication
│   └── pages/
│       └── Index.tsx           # Main application page

backend/
├── api_server.py              # New FastAPI server (to create)
├── custom_langchain.py        # Your custom LLM wrapper
└── keys.txt                   # API configuration
```

## Development Workflow

1. **Start Backend:**
```bash
cd backend/
python api_server.py
```

2. **Start Frontend:**
```bash
npm run dev
```

3. **Open in Browser:**
Visit `http://localhost:8080`

## Configuration

### Backend Configuration (keys.txt)
```json
{
    "API_KEY": "your-api-key",
    "AI_Agent_URL": "https://your-ai-agent-url",
    "AI_Agent_Stream_URL": "https://your-stream-url"
}
```

### Frontend Configuration
Update API base URL in `src/services/api.ts`:
```typescript
const API_BASE_URL = 'http://localhost:8000'; // Adjust as needed
```

## API Endpoints

- `POST /upload` - Upload PDF file for processing
- `POST /ask` - Ask questions about uploaded PDFs
- `GET /health` - Health check

## Production Deployment

### Frontend
```bash
npm run build
# Deploy the dist/ folder to your hosting service
```

### Backend
```bash
# For production, use gunicorn or similar
pip install gunicorn
gunicorn -w 4 -k uvicorn.workers.UvicornWorker api_server:app
```

## Docker Setup (Optional)

Create `docker-compose.yml`:
```yaml
version: '3.8'
services:
  frontend:
    build: .
    ports:
      - "8080:8080"
    environment:
      - NODE_ENV=production
  
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    volumes:
      - ./backend/keys.txt:/app/keys.txt
```

## Troubleshooting

### Common Issues

1. **CORS Errors**: Ensure CORS is properly configured in your backend
2. **File Upload Fails**: Check file size limits and PDF validation
3. **API Connection**: Verify backend is running on the correct port

### Backend Migration from Streamlit

If you're migrating from the existing Streamlit app:

1. Follow the complete guide in `backend-setup.md`
2. Test the API endpoints with curl before connecting the frontend
3. Ensure all dependencies are installed in your Python environment

## Technologies Used

- **Frontend**: React 18, TypeScript, Tailwind CSS, shadcn/ui
- **Backend**: FastAPI, LangChain, HuggingFace Embeddings, FAISS
- **AI**: Custom LLM integration with retrieval-augmented generation

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test both frontend and backend
5. Submit a pull request

## License

MIT License - see LICENSE file for details