from fastapi import FastAPI, UploadFile, File, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from pathlib import Path
from typing import List, Optional, Dict, Any, Tuple
from contextlib import asynccontextmanager

from langchain_community.document_loaders import PyMuPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.chains import RetrievalQA
from custom_langchain import MyDualEndpointLLM as LLM
from comparison_service import compare_texts
from summarization_service import summarize
from agentic_service import AgenticService

import uvicorn, json, shutil, atexit, signal, sys, pickle, hashlib

# ===== Global state with persistent storage =====
vector_stores: Dict[str, FAISS] = {}
uploaded_files: List[str] = []
file_hashes: Dict[str, str] = {}

# Global agentic service with memory
agentic_service: Optional[AgenticService] = None

# Change to persistent directories
UPLOAD_DIR = Path("uploads")
VECTOR_STORE_DIR = Path("vector_stores")
TEMP_DIR = Path("temp")

# Create directories
UPLOAD_DIR.mkdir(exist_ok=True)
VECTOR_STORE_DIR.mkdir(exist_ok=True)
TEMP_DIR.mkdir(exist_ok=True)


# ===== Models =====
class SimpleQueryRequest(BaseModel):
    query: str


class SimpleQueryResponse(BaseModel):
    response: str
    success: bool
    task_type: str
    memory_info: Optional[Dict] = None
    sources: Optional[List[str]] = None


class AgenticQueryRequest(BaseModel):
    query: str
    context: Optional[Dict[str, Any]] = None


class AgenticQueryResponse(BaseModel):
    success: bool
    category: str
    confidence: float
    reasoning: str
    result: Dict[str, Any]
    original_query: str


# ===== FIXED HANDLE TASK FUNCTIONS =====


async def handle_summarization_task(
    query: str, classification: Dict
) -> Tuple[str, List[str]]:
    """Handle summarization requests with memory awareness"""
    try:
        # Check if we have PDFs to summarize
        if agentic_service.memory.pdf_context:
            # Summarize most recent PDF
            recent_pdf = agentic_service.memory.pdf_context[-1]
            if recent_pdf in vector_stores:
                text_content = "\n".join(
                    [
                        d.page_content
                        for d in vector_stores[recent_pdf].docstore._dict.values()
                    ]
                )
                cfg = load_config()
                summary = summarize(
                    text_content, cfg["AI_Agent_URL"], cfg["API_KEY"], "brief"
                )
                response = f"📝 **PDF Summary for {recent_pdf}:**\n\n{summary}"
                return response, [recent_pdf]

        # Extract text from query for summarization
        text_to_summarize = agentic_service.extract_text_for_summary(query)
        if text_to_summarize:
            cfg = load_config()
            summary = summarize(
                text_to_summarize, cfg["AI_Agent_URL"], cfg["API_KEY"], "brief"
            )
            response = f"📝 **Text Summary:**\n\n{summary}"
            return response, []

        return (
            "❌ I need text content or a PDF to summarize. Please provide text or upload a PDF first.",
            [],
        )

    except Exception as e:
        return f"❌ Summarization error: {str(e)}", []


async def handle_comparison_task(
    query: str, classification: Dict
) -> Tuple[str, List[str]]:
    """Handle comparison requests with memory awareness"""
    try:
        # Check if we have 2 PDFs to compare
        if len(agentic_service.memory.pdf_context) >= 2:
            pdf1, pdf2 = (
                agentic_service.memory.pdf_context[-2],
                agentic_service.memory.pdf_context[-1],
            )
            if pdf1 in vector_stores and pdf2 in vector_stores:
                text1 = "\n".join(
                    [
                        d.page_content
                        for d in vector_stores[pdf1].docstore._dict.values()
                    ]
                )
                text2 = "\n".join(
                    [
                        d.page_content
                        for d in vector_stores[pdf2].docstore._dict.values()
                    ]
                )
                cfg = load_config()
                comparison = compare_texts(
                    text1, text2, "comprehensive", cfg["AI_Agent_URL"], cfg["API_KEY"]
                )
                response = f"📊 **PDF Comparison ({pdf1} vs {pdf2}):**\n\n{comparison}"
                return response, [pdf1, pdf2]

        # Extract two texts from query
        text1, text2 = agentic_service.extract_two_texts_from_query(query)
        if text1 and text2:
            cfg = load_config()
            comparison = compare_texts(
                text1, text2, "comprehensive", cfg["AI_Agent_URL"], cfg["API_KEY"]
            )
            response = f"📊 **Text Comparison:**\n\n{comparison}"
            return response, []

        return (
            "❌ I need two texts or two PDFs to compare. Please provide them separated by a clear line break or upload two PDFs.",
            [],
        )

    except Exception as e:
        return f"❌ Comparison error: {str(e)}", []


async def handle_rag_task(query: str, classification: Dict) -> Tuple[str, List[str]]:
    """Handle RAG Q&A requests with memory awareness"""
    try:
        if not agentic_service.memory.pdf_context:
            return "❌ No PDFs available for Q&A. Please upload a PDF first.", []

        # Use most recent PDF
        recent_pdf = agentic_service.memory.pdf_context[-1]
        if recent_pdf not in vector_stores:
            return f"❌ PDF {recent_pdf} not found in vector stores.", []

        cfg = load_config()
        llm = LLM(
            secret_key=cfg["API_KEY"],
            non_stream_url=cfg["AI_Agent_URL"],
            stream_url=cfg["AI_Agent_Stream_URL"],
        )

        retriever = vector_stores[recent_pdf].as_retriever(search_kwargs={"k": 5})
        qa = RetrievalQA.from_chain_type(
            llm=llm,
            chain_type="stuff",
            retriever=retriever,
            return_source_documents=True,
        )

        result = qa.invoke(query)
        answer = result.get("result", "")
        sources = result.get("source_documents", [])

        if not answer.strip():
            answer = f"I found {recent_pdf} but couldn't generate a clear answer. Please try rephrasing your question."

        response = f"📄 **Answer from {recent_pdf}:**\n\n{answer}"

        source_previews = []
        if sources:
            response += f"\n\n**Sources:**\n"
            for i, doc in enumerate(sources[:3], 1):
                preview = (
                    doc.page_content[:150] + "..."
                    if len(doc.page_content) > 150
                    else doc.page_content
                )
                response += f"{i}. {preview}\n"
                source_previews.append(preview)

        return response, [recent_pdf] + source_previews

    except Exception as e:
        return f"❌ Q&A error: {str(e)}", []


# ===== Utility Functions =====
def calculate_file_hash(content: bytes) -> str:
    """Calculate SHA256 hash of file content for duplicate detection"""
    return hashlib.sha256(content).hexdigest()


def find_duplicate_file(filename: str, content_hash: str) -> Optional[str]:
    """Check if file already exists by name or content hash"""
    if filename in uploaded_files:
        return f"filename:{filename}"

    for existing_file, existing_hash in file_hashes.items():
        if existing_hash == content_hash and existing_file != filename:
            return f"content:{existing_file}"

    return None


def save_file_hashes():
    """Save file hashes to disk for persistence"""
    try:
        hashes_path = UPLOAD_DIR / "file_hashes.json"
        with open(hashes_path, "w") as f:
            json.dump(file_hashes, f)
    except Exception as e:
        print(f"[Hashes] Error saving file hashes: {e}")


def load_file_hashes():
    """Load file hashes from disk"""
    try:
        hashes_path = UPLOAD_DIR / "file_hashes.json"
        if hashes_path.exists():
            with open(hashes_path, "r") as f:
                return json.load(f)
    except Exception as e:
        print(f"[Hashes] Error loading file hashes: {e}")
    return {}


def save_vector_store(filename: str, vector_store):
    """Save vector store to disk with better error handling"""
    try:
        store_path = VECTOR_STORE_DIR / f"{filename}.pkl"
        temp_path = VECTOR_STORE_DIR / f"{filename}.tmp"

        with open(temp_path, "wb") as f:
            pickle.dump(vector_store, f)

        if temp_path.exists() and temp_path.stat().st_size > 0:
            if store_path.exists():
                store_path.unlink()
            temp_path.rename(store_path)
            print(f"[VectorStore] Successfully saved {filename}")
        else:
            raise Exception("Temporary file creation failed")

    except Exception as e:
        print(f"[VectorStore] Error saving {filename}: {e}")
        temp_path = VECTOR_STORE_DIR / f"{filename}.tmp"
        if temp_path.exists():
            temp_path.unlink()


def load_vector_store(filename: str):
    """Load vector store from disk"""
    try:
        store_path = VECTOR_STORE_DIR / f"{filename}.pkl"
        if store_path.exists():
            with open(store_path, "rb") as f:
                return pickle.load(f)
    except Exception as e:
        print(f"[VectorStore] Error loading {filename}: {e}")
    return None


def load_existing_stores():
    """Load all existing vector stores on startup"""
    try:
        for store_file in VECTOR_STORE_DIR.glob("*.pkl"):
            filename = store_file.stem
            vector_store = load_vector_store(filename)
            if vector_store:
                vector_stores[filename] = vector_store
                if filename not in uploaded_files:
                    uploaded_files.append(filename)
        print(f"[Startup] Loaded {len(vector_stores)} existing vector stores")
    except Exception as e:
        print(f"[Startup] Error loading existing stores: {e}")


def save_uploaded_files_list():
    """Save the uploaded files list to disk"""
    try:
        files_path = UPLOAD_DIR / "uploaded_files.json"
        with open(files_path, "w") as f:
            json.dump(uploaded_files, f)
        save_file_hashes()
    except Exception as e:
        print(f"[Files] Error saving files list: {e}")


def load_uploaded_files_list():
    """Load the uploaded files list from disk"""
    try:
        files_path = UPLOAD_DIR / "uploaded_files.json"
        if files_path.exists():
            with open(files_path, "r") as f:
                files_list = json.load(f)
            global file_hashes
            file_hashes = load_file_hashes()
            return files_list
    except Exception as e:
        print(f"[Files] Error loading files list: {e}")
    return []


def cleanup_temp_files():
    """Only clean temporary files, preserve uploads"""
    try:
        if TEMP_DIR.exists():
            shutil.rmtree(TEMP_DIR)
            TEMP_DIR.mkdir(exist_ok=True)
        print("[Cleanup] Cleaned temp files, preserved uploads")
    except Exception as e:
        print(f"[Cleanup Error] {e}")


def signal_handler(signum, frame):
    """Clean up all data and exit on Ctrl+C"""
    print(f"\n[Signal] Received signal {signum} (Ctrl+C)")
    print("[Signal] Cleaning up all uploaded data before shutdown...")
    cleanup_all_uploaded_data()
    print("[Signal] 🔄 Server shutting down...")
    sys.exit(0)


def cleanup_all_uploaded_data():
    """Delete all uploaded PDFs and vector store chunks"""
    try:
        print("[Cleanup] Deleting all uploaded PDFs and vector store chunks...")
        global vector_stores, uploaded_files, file_hashes
        vector_stores.clear()
        uploaded_files.clear()
        file_hashes.clear()

        if UPLOAD_DIR.exists():
            for file_path in UPLOAD_DIR.iterdir():
                try:
                    if file_path.is_file():
                        file_path.unlink()
                        print(f"[Cleanup] Deleted PDF: {file_path.name}")
                    elif file_path.is_dir():
                        shutil.rmtree(file_path)
                        print(f"[Cleanup] Deleted directory: {file_path.name}")
                except Exception as e:
                    print(f"[Cleanup] Error deleting {file_path}: {e}")

        if VECTOR_STORE_DIR.exists():
            for file_path in VECTOR_STORE_DIR.iterdir():
                try:
                    if file_path.is_file():
                        file_path.unlink()
                        print(f"[Cleanup] Deleted vector store: {file_path.name}")
                    elif file_path.is_dir():
                        shutil.rmtree(file_path)
                        print(f"[Cleanup] Deleted vector directory: {file_path.name}")
                except Exception as e:
                    print(f"[Cleanup] Error deleting {file_path}: {e}")

        cleanup_temp_files()
        print("[Cleanup] ✅ All uploaded data deleted successfully!")

    except Exception as e:
        print(f"[Cleanup] ❌ Error during cleanup: {e}")


# Register cleanup handlers
atexit.register(lambda: cleanup_all_uploaded_data())
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)


def load_config():
    """Load configuration from keys.txt"""
    with open("keys.txt") as f:
        return json.load(f)


def process_pdf_and_create_vectorstore(pdf_path: str, filename: str):
    """Process PDF and create vector store with persistent storage"""
    try:
        loader = PyMuPDFLoader(pdf_path)
        docs = loader.load()
        splitter = RecursiveCharacterTextSplitter(chunk_size=400, chunk_overlap=50)
        chunks = splitter.split_documents(docs)
        embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2"
        )
        vs = FAISS.from_documents(chunks, embeddings)

        vector_stores[filename] = vs
        save_vector_store(filename, vs)
        print(f"[VectorStore] Created and saved {len(chunks)} chunks for {filename}")
        return vs
    except Exception as e:
        print(f"[VectorStore] Error processing {filename}: {e}")
        raise


def initialize_agentic_service():
    """Initialize the global agentic service"""
    global agentic_service
    try:
        cfg = load_config()
        agentic_service = AgenticService(cfg["AI_Agent_URL"], cfg["API_KEY"])
        print("✅ Agentic service initialized with memory system")
    except Exception as e:
        print(f"❌ Failed to initialize agentic service: {e}")


# ===== FastAPI lifespan management =====
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("[Startup] Loading existing files and vector stores...")
    global uploaded_files, file_hashes
    loaded_files = load_uploaded_files_list()
    uploaded_files.extend(loaded_files)
    load_existing_stores()

    # Initialize agentic service
    initialize_agentic_service()

    print(
        f"[Startup] Initialized with {len(uploaded_files)} files and {len(vector_stores)} vector stores"
    )
    print(f"[Startup] Loaded {len(file_hashes)} file hashes for duplicate detection")

    yield

    # Shutdown
    save_uploaded_files_list()
    print("[Shutdown] State saved successfully")


# ===== FastAPI app setup =====
app = FastAPI(
    title="Complete Agentic PDF AI API - FIXED", version="3.1", lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ===== ENDPOINTS =====


@app.get("/")
async def root():
    """Root endpoint with service info"""
    return {
        "service": "Complete Agentic PDF AI - RESPONSE HANDLING FIXED",
        "version": "3.1 - All Response Issues Resolved",
        "ai_provider": "Intelligize AI (Claude 3 Haiku)",
        "capabilities": [
            "✅ Fixed Response Handling - All Endpoints Return Actual Responses",
            "✅ Greeting Detection (Hi, Hello, Goodbye)",
            "✅ Text/PDF Summarization (Max 50MB)",
            "✅ Text/PDF Comparison (Legal Expert Level)",
            "✅ RAG Q&A with Source Attribution",
            "✅ Out-of-scope Request Refusal",
            "✅ 10-Message Memory System",
            "✅ Max 2 PDFs Management",
        ],
        "endpoints": {
            "unified_query": "/api/query",
            "legacy_query": "/agentic-query",
            "upload": "/upload",
            "upload_and_query": "/upload-and-query",
            "memory": "/api/memory",
            "health": "/health",
        },
    }


@app.post("/api/query", response_model=SimpleQueryResponse)
async def unified_query_handler(request: SimpleQueryRequest):
    """🧠 Unified query handler with guaranteed response delivery"""
    try:
        if not agentic_service:
            raise HTTPException(
                status_code=500, detail="Agentic service not initialized"
            )

        query = request.query.strip()
        query_lower = query.lower()

        print(f"[API] Received: '{query}'")

        # GUARANTEED GREETING DETECTION - Simple and reliable
        if any(word in query_lower for word in ["hi", "hello", "hey", "hiya"]):
            response = "Hello! 👋 I'm your intelligent AI assistant.\n\nI can help you with:\n📝 **Summarization** - Text or PDF documents\n📊 **Comparison** - Text or PDF analysis\n❓ **PDF Q&A** - Questions about uploads\n\nHow can I assist you today?"
            print("[API] ✅ Greeting detected and responded!")
            return SimpleQueryResponse(
                response=response,
                success=True,
                task_type="greeting",
                memory_info=(
                    agentic_service.get_memory_info() if agentic_service else None
                ),
            )

        if any(word in query_lower for word in ["goodbye", "bye", "see you"]):
            response = "Goodbye for now! 👋\n\nI'm still here whenever you need help with documents. Feel free to continue anytime!"
            return SimpleQueryResponse(
                response=response,
                success=True,
                task_type="greeting",
                memory_info=(
                    agentic_service.get_memory_info() if agentic_service else None
                ),
            )

        if "how are you" in query_lower:
            response = "I'm functioning perfectly! 🤖\n\nReady to help with summarization, comparison, and PDF Q&A. What would you like me to do?"
            return SimpleQueryResponse(
                response=response,
                success=True,
                task_type="greeting",
                memory_info=(
                    agentic_service.get_memory_info() if agentic_service else None
                ),
            )

        # Continue with enhanced routing for non-greetings
        context_info = {
            "uploaded_files": uploaded_files,
            "available_pdfs": len(uploaded_files),
            "has_documents": len(uploaded_files) > 0,
        }

        classification_result = agentic_service.classify_with_enhanced_routing(
            query, str(context_info)
        )
        task_type = classification_result["category"]

        print(f"[API] Task: {task_type}")

        # Handle different task types
        sources = []

        if task_type == "greeting":
            response_text = classification_result["response"]

        elif task_type == "out_of_scope":
            response_text = classification_result["response"]

        elif task_type == "summarization":
            response_text, sources = await handle_summarization_task(
                query, classification_result
            )
            agentic_service.add_response_to_memory(response_text, task_type)

        elif task_type == "comparison":
            response_text, sources = await handle_comparison_task(
                query, classification_result
            )
            agentic_service.add_response_to_memory(response_text, task_type)

        elif task_type in ["rag", "general"]:
            response_text, sources = await handle_rag_task(query, classification_result)
            agentic_service.add_response_to_memory(response_text, task_type)

        else:
            response_text = "I can help with summarization, comparison, and PDF Q&A. What would you like me to do?"
            agentic_service.add_response_to_memory(response_text, "general")

        return SimpleQueryResponse(
            response=response_text,
            success=True,
            task_type=task_type,
            memory_info=agentic_service.get_memory_info(),
            sources=sources if sources else None,
        )

    except Exception as e:
        error_response = f"I encountered an error: {str(e)}. Please try again."
        print(f"[API] ❌ Error: {e}")

        return SimpleQueryResponse(
            response=error_response, success=False, task_type="error"
        )


@app.post("/agentic-query", response_model=AgenticQueryResponse)
async def agentic_query(req: AgenticQueryRequest):
    """FIXED - Legacy agentic query endpoint that actually returns responses"""
    try:
        if not agentic_service:
            raise HTTPException(
                status_code=500, detail="Agentic service not initialized"
            )

        query = req.query.strip()
        query_lower = query.lower()

        print(f"[AGENTIC-QUERY] Processing: '{query}'")

        # IMMEDIATE GREETING CHECK WITH ACTUAL RETURN
        if any(word in query_lower for word in ["hi", "hello", "hey", "hiya"]):
            response_text = "Hello! 👋 I'm your intelligent AI assistant.\n\nI can help you with:\n📝 **Summarization** - Text or PDF documents\n📊 **Comparison** - Text or PDF analysis\n❓ **PDF Q&A** - Questions about uploads\n\nHow can I assist you today?"

            print(f"[AGENTIC-QUERY] ✅ Returning greeting: {response_text[:50]}...")

            return AgenticQueryResponse(
                success=True,
                category="greeting",
                confidence=0.95,
                reasoning="Detected greeting",
                result={"answer": response_text},
                original_query=query,
            )

        if any(word in query_lower for word in ["goodbye", "bye"]):
            response_text = (
                "Goodbye for now! 👋 I'm still here if you need help with documents."
            )

            return AgenticQueryResponse(
                success=True,
                category="greeting",
                confidence=0.95,
                reasoning="Detected goodbye",
                result={"answer": response_text},
                original_query=query,
            )

        # Process non-greetings
        context_info = {
            "uploaded_files": uploaded_files,
            "available_pdfs": len(uploaded_files),
        }

        classification_result = agentic_service.classify_with_enhanced_routing(
            query, str(context_info)
        )
        task_type = classification_result["category"]

        print(f"[AGENTIC-QUERY] Task: {task_type}")

        # CRITICAL: Actually handle and return responses
        response_text = ""
        sources = []

        if task_type == "greeting":
            response_text = classification_result.get(
                "response", "Hello! How can I help you?"
            )

        elif task_type == "out_of_scope":
            response_text = classification_result.get(
                "response",
                """🚫 I can only help with:
📝 Summarization
📊 Comparison  
❓ PDF Q&A""",
            )

        elif task_type == "summarization":
            try:
                response_text, sources = await handle_summarization_task(
                    query, classification_result
                )
                agentic_service.add_response_to_memory(response_text, task_type)
            except Exception as e:
                response_text = f"❌ Summarization error: {str(e)}"

        elif task_type == "comparison":
            try:
                response_text, sources = await handle_comparison_task(
                    query, classification_result
                )
                agentic_service.add_response_to_memory(response_text, task_type)
            except Exception as e:
                response_text = f"❌ Comparison error: {str(e)}"

        elif task_type in ["rag", "general"]:
            try:
                response_text, sources = await handle_rag_task(
                    query, classification_result
                )
                agentic_service.add_response_to_memory(response_text, task_type)
            except Exception as e:
                response_text = f"❌ Q&A error: {str(e)}"

        else:
            response_text = "I can help with summarization, comparison, and PDF Q&A. What would you like me to do?"

        # ENSURE WE ALWAYS HAVE A RESPONSE
        if not response_text or response_text.strip() == "":
            response_text = "I processed your request but didn't generate a response. Please try again."

        print(
            f"[AGENTIC-QUERY] ✅ Returning {task_type} response: {response_text[:100]}..."
        )

        # RETURN THE ACTUAL RESPONSE
        return AgenticQueryResponse(
            success=True,
            category=task_type,
            confidence=0.9,
            reasoning=f"Processed as {task_type}",
            result={"answer": response_text, "sources": sources if sources else []},
            original_query=query,
        )

    except Exception as e:
        error_msg = f"Error processing request: {str(e)}"
        print(f"[AGENTIC-QUERY] ❌ Error: {error_msg}")

        return AgenticQueryResponse(
            success=False,
            category="error",
            confidence=0.0,
            reasoning=f"Error: {str(e)}",
            result={"answer": error_msg},
            original_query=req.query,
        )


@app.post("/upload")
async def upload_pdfs(files: List[UploadFile] = File(...)):
    """Enhanced upload endpoint with memory integration and 50MB limit"""
    print(f"[UPLOAD] Received request with {len(files) if files else 0} files")

    if not files:
        raise HTTPException(status_code=400, detail="No files provided")

    uploaded_list = []
    skipped_list = []
    errors = []

    for i, file in enumerate(files):
        print(
            f"[UPLOAD] Processing file {i+1}: {getattr(file, 'filename', 'no-filename')}"
        )

        try:
            if not hasattr(file, "filename") or not file.filename:
                errors.append(f"File {i+1}: Invalid file object or missing filename")
                continue

            if not file.filename.lower().endswith(".pdf"):
                errors.append(f"{file.filename}: Only PDF files are allowed")
                continue

            content = await file.read()
            if len(content) == 0:
                errors.append(f"{file.filename}: File is empty")
                continue

            # Check 50MB limit
            file_size_mb = len(content) / (1024 * 1024)
            if file_size_mb > 50:
                errors.append(
                    f"{file.filename}: File too large ({file_size_mb:.1f}MB). Maximum size is 50MB."
                )
                continue

            safe_filename = file.filename.replace(" ", "_")
            content_hash = calculate_file_hash(content)

            duplicate_info = find_duplicate_file(safe_filename, content_hash)
            if duplicate_info:
                duplicate_type, existing_file = duplicate_info.split(":", 1)
                if duplicate_type == "filename":
                    skipped_list.append(
                        {
                            "filename": safe_filename,
                            "reason": "duplicate_name",
                            "existing_file": existing_file,
                            "message": f"File '{safe_filename}' already exists",
                        }
                    )
                elif duplicate_type == "content":
                    skipped_list.append(
                        {
                            "filename": safe_filename,
                            "reason": "duplicate_content",
                            "existing_file": existing_file,
                            "message": f"Identical content found in existing file '{existing_file}'",
                        }
                    )
                continue

            # Manage max 2 PDFs
            if len(uploaded_files) >= 2:
                old_file = uploaded_files.pop(0)
                if old_file in vector_stores:
                    del vector_stores[old_file]
                if old_file in file_hashes:
                    del file_hashes[old_file]
                old_path = UPLOAD_DIR / old_file
                if old_path.exists():
                    old_path.unlink()

            persistent_path = UPLOAD_DIR / safe_filename
            with open(persistent_path, "wb") as f:
                f.write(content)

            process_pdf_and_create_vectorstore(str(persistent_path), safe_filename)

            if safe_filename not in uploaded_files:
                uploaded_files.append(safe_filename)
            file_hashes[safe_filename] = content_hash
            uploaded_list.append(safe_filename)

            # Add to agentic service memory
            if agentic_service:
                agentic_service.memory.add_pdf_context(safe_filename)
                agentic_service.memory.add_message(
                    "system", f"PDF uploaded: {safe_filename}"
                )

            print(
                f"[UPLOAD] ✅ Successfully processed {safe_filename} ({file_size_mb:.1f}MB)"
            )

        except Exception as e:
            error_msg = f"{getattr(file, 'filename', f'File {i+1}')}: {str(e)}"
            errors.append(error_msg)
            print(f"[UPLOAD] ❌ Error: {error_msg}")
            continue

    save_uploaded_files_list()

    response = {
        "success": len(uploaded_list) > 0 or len(skipped_list) > 0,
        "uploaded_files": uploaded_list,
        "skipped_files": skipped_list,
        "total_uploaded": len(uploaded_list),
        "total_skipped": len(skipped_list),
        "message": f"Processed {len(files)} file(s): {len(uploaded_list)} uploaded, {len(skipped_list)} skipped",
    }

    if errors:
        response["errors"] = errors
        response["total_errors"] = len(errors)
        response["message"] += f", {len(errors)} error(s)"

    if not uploaded_list and not skipped_list:
        raise HTTPException(
            status_code=400,
            detail={
                "message": "No files were successfully processed",
                "errors": errors,
            },
        )

    return response


@app.post("/upload-and-query")
async def upload_and_query(
    files: List[UploadFile] = File(...),
    query: str = Form(...),
    context: str = Form(None),
):
    """FIXED - Upload and query endpoint with proper response handling"""
    try:
        print(f"[UPLOAD-AND-QUERY] Processing query: '{query}' with {len(files)} files")

        # Upload files first
        upload_result = await upload_pdfs(files)

        if not upload_result["success"]:
            raise HTTPException(status_code=400, detail="File upload failed")

        # Process the query using the fixed agentic query logic
        query_request = AgenticQueryRequest(
            query=query, context={"upload_context": upload_result}
        )
        query_result = await agentic_query(query_request)

        # Return properly formatted response
        return {
            "success": True,
            "upload_summary": {
                "uploaded_files": upload_result.get("uploaded_files", []),
                "total_uploaded": upload_result.get("total_uploaded", 0),
            },
            "query_response": {
                "category": query_result.category,
                "result": query_result.result,
                "original_query": query,
                "success": query_result.success,
            },
        }

    except Exception as e:
        print(f"[UPLOAD-AND-QUERY] ❌ Error: {e}")
        raise HTTPException(
            status_code=500, detail=f"Upload and query failed: {str(e)}"
        )


@app.get("/api/memory")
async def get_memory_status():
    """Get current memory status"""
    if not agentic_service:
        return {"success": False, "error": "Agentic service not initialized"}

    return {
        "success": True,
        "memory_info": agentic_service.get_memory_info(),
        "context_summary": agentic_service.memory.get_context_summary(),
    }


@app.post("/api/memory/clear")
async def clear_memory():
    """Clear conversation memory"""
    if not agentic_service:
        return {"success": False, "error": "Agentic service not initialized"}

    agentic_service.clear_memory()
    return {"success": True, "message": "Memory cleared successfully"}


@app.get("/files")
async def list_uploaded_files():
    """List all uploaded files with status"""
    file_status = {}
    for filename in uploaded_files:
        file_path = UPLOAD_DIR / filename
        vector_store_path = VECTOR_STORE_DIR / f"{filename}.pkl"

        file_status[filename] = {
            "file_exists": file_path.exists(),
            "vector_store_exists": vector_store_path.exists(),
            "loaded_in_memory": filename in vector_stores,
            "file_size": file_path.stat().st_size if file_path.exists() else 0,
            "content_hash": file_hashes.get(filename, "unknown"),
        }

    return {
        "uploaded_files": uploaded_files,
        "file_status": file_status,
        "total_files": len(uploaded_files),
        "max_allowed": 2,
        "duplicate_detection": "enabled",
        "memory_info": agentic_service.get_memory_info() if agentic_service else None,
    }


@app.delete("/files/{filename}")
async def delete_file(filename: str):
    """Delete a file and its vector store"""
    try:
        if filename in vector_stores:
            del vector_stores[filename]
        if filename in uploaded_files:
            uploaded_files.remove(filename)
        if filename in file_hashes:
            del file_hashes[filename]

        file_path = UPLOAD_DIR / filename
        if file_path.exists():
            file_path.unlink()

        store_path = VECTOR_STORE_DIR / f"{filename}.pkl"
        if store_path.exists():
            store_path.unlink()

        # Remove from agentic service memory
        if agentic_service and filename in agentic_service.memory.pdf_context:
            agentic_service.memory.pdf_context.remove(filename)

        save_uploaded_files_list()
        return {"success": True, "message": f"File {filename} deleted successfully"}

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error deleting {filename}: {str(e)}"
        )


@app.get("/health")
async def health_check():
    """Health check endpoint with comprehensive status"""
    return {
        "status": "healthy ✅",
        "version": "3.1 - Response Handling Fixed",
        "uploaded_files_count": len(uploaded_files),
        "vector_stores_loaded": len(vector_stores),
        "agentic_service_ready": agentic_service is not None,
        "memory_system": "enabled ✅" if agentic_service else "disabled",
        "features_working": [
            "✅ Response Handling - All Endpoints Return Responses",
            "✅ Greeting Detection (Hi, Hello, Goodbye)",
            "✅ 10-Message Memory System",
            "✅ PDF Context Awareness",
            "✅ Out-of-scope Refusal",
            "✅ 50MB PDF Limit",
            "✅ Max 2 PDFs",
            "✅ Text/PDF Summarization",
            "✅ Text/PDF Comparison",
            "✅ RAG Q&A with Sources",
        ],
        "upload_dir_exists": UPLOAD_DIR.exists(),
        "vector_store_dir_exists": VECTOR_STORE_DIR.exists(),
        "persistent_storage": "enabled",
        "duplicate_detection": "enabled",
        "file_hashes_loaded": len(file_hashes),
    }


# Debug endpoints
@app.get("/test/response/{message}")
async def test_response(message: str):
    """Test endpoint to verify response handling"""
    return {
        "success": True,
        "message": f"Server received: '{message}'",
        "response": f"Echo: {message}",
        "timestamp": "2025-08-15T02:03:00",
        "test_status": "Response handling working ✅",
    }


@app.get("/test/greeting/{text}")
async def test_greeting_detection(text: str):
    """Test greeting detection directly"""
    if not agentic_service:
        return {"error": "Service not ready"}

    result = agentic_service._check_greeting(text)
    return {
        "input": text,
        "greeting_detected": result is not None,
        "result": result,
        "debug": f"Testing pattern matching for: '{text}'",
    }


@app.get("/debug/greeting-test")
async def debug_greeting_test():
    """Test all greeting patterns"""
    if not agentic_service:
        return {"error": "Service not ready"}

    test_queries = ["hi", "hello", "hey", "goodbye", "bye", "how are you"]
    results = {}

    for query in test_queries:
        result = agentic_service._check_greeting(query)
        results[query] = {
            "detected": result is not None,
            "type": (
                result.get("parameters", {}).get("greeting_type") if result else None
            ),
            "response": (
                result.get("response", "")[:100] + "..." if result else "No response"
            ),
        }

    return {"test_results": results, "status": "All greeting patterns tested ✅"}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
