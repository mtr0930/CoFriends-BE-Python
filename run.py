"""
Quick start script for local development
"""
import subprocess
import sys
import os


def main():
    """Run the FastAPI application"""
    # Change to script directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    
    # Check if .env exists
    if not os.path.exists(".env"):
        print("⚠️  .env file not found. Creating from env.example...")
        if os.path.exists("env.example"):
            import shutil
            shutil.copy("env.example", ".env")
            print("✅ Created .env file. Please update it with your actual values.")
        else:
            print("❌ env.example not found!")
            sys.exit(1)
    
    # Run uvicorn
    print("🚀 Starting CoFriends FastAPI server...")
    subprocess.run([
        sys.executable, "-m", "uvicorn",
        "main:app",
        "--host", "0.0.0.0",
        "--port", "5000",
        "--reload"
    ])


if __name__ == "__main__":
    main()

