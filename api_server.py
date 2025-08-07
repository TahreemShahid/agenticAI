from fastapi import FastAPI, UploadFile, File, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
import json
import shutil
from typing import List
import uvicorn

import gspread
from google.oauth2.service_account import Credentials

# LangChain and your LLM wrapper imports
from langchain_community.document_loaders import PyMuPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.chains import RetrievalQA

# Import your custom LLM wrapper 
from custom_langchain import MyDualEndpointLLM as LLM

# Import comparison service
from comparison_service import compare_texts

# Import summarization service
from summarization_service import summarize


app = FastAPI(title="PDF Q&A API", version="1.0.0")

# CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Change to your domain in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

uploaded_files = {}
vector_stores = {}

TMP_FOLDER = "./tmp_uploads"
os.makedirs(TMP_FOLDER, exist_ok=True)  # Ensure temp folder exists


class QuestionRequest(BaseModel):
    question: str
    filename: str


class QuestionResponse(BaseModel):
    answer: str
    source_chunks: List[str]


class ComparisonRequest(BaseModel):
    text1: str
    text2: str
    comparison_type: str = "comprehensive"


class ComparisonResponse(BaseModel):
    comparison: str
    success: bool


class SummarizationRequest(BaseModel):
    text: str
    summary_type: str = "brief"
    audience: str = None


class SummarizationResponse(BaseModel):
    summary: str
    success: bool


def load_config():
    if not os.path.exists("keys.txt"):
        raise FileNotFoundError("keys.txt not found. Please create it with your API configuration.")
    with open("keys.txt", "r") as f:
        config = json.load(f)
    required_keys = ["API_KEY", "AI_Agent_URL", "AI_Agent_Stream_URL"]
    missing_keys = [key for key in required_keys if key not in config]
    if missing_keys:
        raise ValueError(f"Missing keys in keys.txt: {missing_keys}")
    return config


def process_pdf_and_create_vectorstore(pdf_path: str, filename: str):
    try:
        loader = PyMuPDFLoader(pdf_path)
        documents = loader.load()
        splitter = RecursiveCharacterTextSplitter(chunk_size=400, chunk_overlap=50)
        chunks = splitter.split_documents(documents)

        embedding_model = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
        vector_store = FAISS.from_documents(chunks, embedding_model)
        vector_stores[filename] = vector_store
        return vector_store
    except Exception as e:
        print(f"Error processing PDF: {e}")
        raise e


def append_to_google_sheet(spreadsheet_name: str, row: list, worksheet_name: str = "Sheet1"):
    scopes = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
    creds = Credentials.from_service_account_file('stately-pulsar-466013-m4-dfb94f40c3d3.json', scopes=scopes)
    client = gspread.authorize(creds)

    sheet = client.open(spreadsheet_name).worksheet(worksheet_name)
    sheet.append_row(row)


@app.get("/")
async def root():
    return {"message": "PDF Q&A API is running", "status": "healthy"}


@app.get("/health")
async def health_check():
    try:
        config = load_config()
        return {
            "status": "healthy",
            "uploaded_files": len(uploaded_files),
            "ai_service_configured": True
        }
    except Exception as e:
        return {
            "status": "degraded",
            "uploaded_files": len(uploaded_files),
            "ai_service_configured": False,
            "error": str(e)
        }


@app.post("/upload")
async def upload_pdf(file: UploadFile = File(...)):
    if not file.filename or not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")
    try:
        file_path = os.path.join(TMP_FOLDER, file.filename)
        content = await file.read()
        with open(file_path, "wb") as f:
            f.write(content)
        
        process_pdf_and_create_vectorstore(file_path, file.filename)

        uploaded_files[file.filename] = {
            'path': file_path,
            'size': len(content)
        }

        print(f"Successfully processed: {file.filename}")

        return {
            "success": True,
            "message": f"PDF '{file.filename}' uploaded and processed successfully",
            "filename": file.filename
        }
    except Exception as e:
        print(f"Error processing PDF: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing PDF: {str(e)}")


@app.delete("/delete_file")
async def delete_file(filename: str = Query(...)):
    file_info = uploaded_files.pop(filename, None)
    vector_stores.pop(filename, None)
    if file_info and os.path.exists(file_info['path']):
        try:
            os.remove(file_info['path'])
            return {"success": True}
        except Exception as e:
            return {"success": False, "message": f"Error deleting file: {str(e)}"}
    return {"success": False, "message": "File not found"}


@app.post("/ask", response_model=QuestionResponse)
async def ask_question(request: QuestionRequest):
    if request.filename not in vector_stores:
        raise HTTPException(status_code=400, detail="PDF not found. Please upload first.")
    try:
        config = load_config()
        haiku_llm = LLM(
            secret_key=config["API_KEY"],
            non_stream_url=config["AI_Agent_URL"],
            stream_url=config["AI_Agent_Stream_URL"]
        )

        vector_store = vector_stores[request.filename]
        retriever = vector_store.as_retriever(search_kwargs={"k": 5})

        qa_chain = RetrievalQA.from_chain_type(
            llm=haiku_llm,
            chain_type="stuff",
            retriever=retriever,
            return_source_documents=True
        )
        result = qa_chain.invoke(request.question)
        answer = result["result"]
        source_chunks = [doc.page_content for doc in result["source_documents"]]

        # Append Q&A to Google Sheet
        try:
            row_data = [
                request.filename,
                request.question,
                answer,
                "\n\n".join(source_chunks[:3])  # limit excerpts
            ]
            append_to_google_sheet("PDF Q/A", row_data, worksheet_name="Sheet1")
        except Exception as e:
            print(f"Failed to write to Google Sheet: {e}")

        return QuestionResponse(
            answer=answer,
            source_chunks=source_chunks
        )
    except Exception as e:
        print(f"Error processing question: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing question: {str(e)}")


@app.post("/compare", response_model=ComparisonResponse)
async def compare_texts_endpoint(request: ComparisonRequest):
    try:
        config = load_config()
        ai_agent_url = config.get("AI_Agent_URL")
        secret_key = config.get("API_KEY")

        comparison_result = compare_texts(
            request.text1,
            request.text2,
            request.comparison_type,
            ai_agent_url,
            secret_key
        )

        if comparison_result.startswith("Error:"):
            return ComparisonResponse(
                comparison=comparison_result,
                success=False
            )
        return ComparisonResponse(comparison=comparison_result, success=True)
    except Exception as e:
        print(f"Error in text comparison: {e}")
        return ComparisonResponse(
            comparison=f"Error occurred during comparison: {str(e)}",
            success=False
        )


@app.post("/summarize", response_model=SummarizationResponse)
async def summarize_text_endpoint(request: SummarizationRequest):
    try:
        config = load_config()
        ai_agent_url = config.get("AI_Agent_URL")
        secret_key = config.get("API_KEY")

        summary_result = summarize(
            request.text,
            ai_agent_url,
            secret_key,
            request.summary_type,
            request.audience
        )

        if summary_result.startswith("ERROR"):
            return SummarizationResponse(
                summary=summary_result,
                success=False
            )
        return SummarizationResponse(summary=summary_result, success=True)
    except Exception as e:
        print(f"Error in text summarization: {e}")
        return SummarizationResponse(
            summary=f"Error occurred during summarization: {str(e)}",
            success=False
        )


# Cleanup temp folder on shutdown
@app.on_event("shutdown")
def cleanup_tmp_folder():
    if os.path.exists(TMP_FOLDER):
        print(f"Cleaning up temp uploads folder {TMP_FOLDER} ...")
        shutil.rmtree(TMP_FOLDER)


if __name__ == "__main__":
    print("Starting API server...")
    print("\nServer will start on http://localhost:8000")
    print("API docs available at http://localhost:8000/docs")
    uvicorn.run(app, host="0.0.0.0", port=8000)
