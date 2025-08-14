#!/usr/bin/env python3
"""
Enhanced script to run the PDF Q&A backend server with persistent storage
"""

import subprocess
import sys
import os
from pathlib import Path

def check_directories():
    """Create required directories if they don't exist"""
    dirs = ['uploads', 'vector_stores', 'temp']
    for dir_name in dirs:
        Path(dir_name).mkdir(exist_ok=True)
        print(f"✅ Directory '{dir_name}' ready")

def check_dependencies():
    """Check if required packages are installed"""
    required_packages = [
        'fastapi',
        'uvicorn',
        'langchain',
        'langchain_community', 
        'langchain_huggingface',
        'pymupdf',
        'faiss-cpu',  # or 'faiss-gpu'
        'sentence_transformers'
    ]
    
    missing = []
    for package in required_packages:
        try:
            if package == 'faiss-cpu':
                import faiss
            elif package == 'pymupdf':
                import fitz
            else:
                __import__(package.replace('-', '_'))
        except ImportError:
            missing.append(package)
    
    if missing:
        print("❌ Missing required packages:")
        for pkg in missing:
            print(f"   - {pkg}")
        print("\n📦 Install missing packages with:")
        print("pip install " + " ".join(missing))
        return False
    
    print("✅ All required packages are installed")
    return True

def check_custom_llm():
    """Check if custom LLM file exists"""
    if not os.path.exists('custom_langchain.py'):
        print("⚠️  custom_langchain.py not found")
        print("   The API will work with mock responses until you add your custom LLM")
        return False
    print("✅ custom_langchain.py found")
    return True

def check_keys():
    """Check if keys.txt exists"""
    if not os.path.exists('keys.txt'):
        print("⚠️  keys.txt not found")
        print("   Copy keys.txt.example to keys.txt and add your API keys")
        print("   The API will work with mock responses until configured")
        return False
    print("✅ keys.txt found")
    return True

def check_services():
    """Check if service files exist"""
    services = ['agentic_service.py', 'comparison_service.py', 'summarization_service.py']
    all_present = True
    
    for service in services:
        if os.path.exists(service):
            print(f"✅ {service} found")
        else:
            print(f"⚠️  {service} not found")
            all_present = False
    
    return all_present

def main():
    print("🚀 Starting Enhanced PDF Q&A Backend Server")
    print("=" * 60)
    
    # Check and create directories
    check_directories()
    print()
    
    # Check dependencies
    if not check_dependencies():
        sys.exit(1)
    print()
    
    # Check service files
    check_services()
    print()
    
    # Check optional files
    check_custom_llm()
    check_keys()
    
    print("\n📁 Persistent Storage:")
    print("   - PDFs: ./uploads/")
    print("   - Vector stores: ./vector_stores/")
    print("   - Temp files: ./temp/")
    
    print("\n🌐 Starting server on http://localhost:8000")
    print("📚 API docs available at http://localhost:8000/docs") 
    print("📋 File management at http://localhost:8000/files")
    print("🔄 Press Ctrl+C to stop the server")
    print("=" * 60)
    
    try:
        # Run the server
        subprocess.run([
            sys.executable,
            "api_server.py"
        ], check=True)
    except KeyboardInterrupt:
        print("\n👋 Server stopped gracefully")
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Error running server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
