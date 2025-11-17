"""Test script to diagnose application issues."""
import sys
from pathlib import Path

# Add app directory to path
sys.path.insert(0, str(Path(__file__).parent / "app"))

def test_imports():
    """Test all imports."""
    print("Testing imports...")
    try:
        import chromadb
        from chromadb.config import Settings
        print("[OK] ChromaDB import OK")
        
        from fastapi import FastAPI
        from fastapi.templating import Jinja2Templates
        from fastapi.staticfiles import StaticFiles
        print("[OK] FastAPI imports OK")
        
        import pdfplumber
        print("[OK] pdfplumber import OK")
        
        import docx
        print("[OK] python-docx import OK")
        
        from PIL import Image
        print("[OK] Pillow import OK")
        
        import httpx
        print("[OK] httpx import OK")
        
        return True
    except Exception as e:
        print(f"[ERROR] Import error: {e}")
        return False

def test_directories():
    """Test directory creation."""
    print("\nTesting directories...")
    try:
        BASE_DIR = Path(__file__).parent
        UPLOAD_DIR = BASE_DIR / "uploads"
        STATIC_DIR = BASE_DIR / "app" / "static"
        TEMPLATES_DIR = BASE_DIR / "app" / "templates"
        
        UPLOAD_DIR.mkdir(exist_ok=True)
        print(f"[OK] Upload directory: {UPLOAD_DIR}")
        
        if STATIC_DIR.exists():
            print(f"[OK] Static directory exists: {STATIC_DIR}")
        else:
            print(f"[ERROR] Static directory missing: {STATIC_DIR}")
            
        if TEMPLATES_DIR.exists():
            print(f"[OK] Templates directory exists: {TEMPLATES_DIR}")
        else:
            print(f"[ERROR] Templates directory missing: {TEMPLATES_DIR}")
            
        return True
    except Exception as e:
        print(f"[ERROR] Directory error: {e}")
        return False

def test_chromadb():
    """Test ChromaDB setup."""
    print("\nTesting ChromaDB...")
    try:
        import chromadb
        from chromadb.config import Settings
        
        BASE_DIR = Path(__file__).parent
        test_db = BASE_DIR / "test_chroma_db"
        
        client = chromadb.PersistentClient(
            path=str(test_db),
            settings=Settings(anonymized_telemetry=False)
        )
        collection = client.get_or_create_collection(name="test_collection")
        
        # Test add
        collection.add(
            ids=["test1"],
            documents=["test document"],
            embeddings=[[0.1] * 1024]
        )
        print("[OK] ChromaDB add() works")
        
        # Test query
        results = collection.query(
            query_embeddings=[[0.1] * 1024],
            n_results=1
        )
        print(f"[OK] ChromaDB query() works: {len(results['documents'][0])} results")
        
        # Cleanup - skip if locked (Windows file locking issue)
        import shutil
        try:
            if test_db.exists():
                shutil.rmtree(test_db)
        except PermissionError:
            pass  # File is locked, that's OK for test
            
        return True
    except Exception as e:
        print(f"[ERROR] ChromaDB error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_app_creation():
    """Test app creation."""
    print("\nTesting app creation...")
    try:
        from main import app
        print("[OK] App created successfully")
        print(f"[OK] App has {len(app.routes)} routes")
        return True
    except Exception as e:
        print(f"[ERROR] App creation error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("=" * 50)
    print("UTAS-AI Application Diagnostic Test")
    print("=" * 50)
    
    results = []
    results.append(("Imports", test_imports()))
    results.append(("Directories", test_directories()))
    results.append(("ChromaDB", test_chromadb()))
    results.append(("App Creation", test_app_creation()))
    
    print("\n" + "=" * 50)
    print("Test Results Summary")
    print("=" * 50)
    for name, result in results:
        status = "[PASS]" if result else "[FAIL]"
        print(f"{name}: {status}")
    
    if all(r[1] for r in results):
        print("\n[SUCCESS] All tests passed! The app should work correctly.")
    else:
        print("\n[FAILED] Some tests failed. Please check the errors above.")

