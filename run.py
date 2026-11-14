import os
import sys
import uvicorn

# Ensure the root directory is on the python search path
root_dir = os.path.dirname(os.path.abspath(__file__))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

if __name__ == "__main__":
    print("=" * 65)
    print("      FinSight — Financial Intelligence & Payment Reconciliation")
    print("=" * 65)
    print("🚀 Starting FinSight Application Server...")
    print("🌐 Open your browser and navigate to: http://127.0.0.1:8000")
    print("🔑 Demo Credentials: admin@finsight.pk / admin123")
    print("📚 API Documentation: http://127.0.0.1:8000/docs")
    print("=" * 65)
    uvicorn.run("backend.main:app", host="127.0.0.1", port=8000, reload=False)
