#!/usr/bin/env python3
"""
Startup script for VietVoice-TTS API server with deterministic behavior.
This script ensures all random seeds are frozen before starting the server.
"""

# CRITICAL: Import deterministic module FIRST, before any other imports
import vietvoicetts.deterministic

import uvicorn
import sys
from pathlib import Path

def main():
    """Start the API server with deterministic configuration"""
    
    print("🔒 Starting VietVoice-TTS API server with deterministic behavior...")
    print("🎯 All random seeds have been frozen for reproducible output")
    print("=" * 60)
    
    # Default configuration
    host = "0.0.0.0"
    port = 8000
    
    # Parse command line arguments
    if len(sys.argv) > 1:
        if sys.argv[1] in ["-h", "--help"]:
            print("Usage: python run_api_server.py [host] [port]")
            print("  host: Server host (default: 0.0.0.0)")
            print("  port: Server port (default: 8000)")
            print()
            print("Examples:")
            print("  python run_api_server.py")
            print("  python run_api_server.py localhost 8080")
            return
        host = sys.argv[1]
    
    if len(sys.argv) > 2:
        try:
            port = int(sys.argv[2])
        except ValueError:
            print("❌ Error: Port must be a number")
            return
    
    print(f"🚀 Starting server at http://{host}:{port}")
    print("📝 API documentation: http://localhost:8000/schema")
    print("🔍 Health check: http://localhost:8000/api/v1/health")
    print()
    print("Press Ctrl+C to stop the server")
    print("=" * 60)
    
    try:
        # Start the server
        uvicorn.run(
            "vietvoicetts.api.app:app",
            host=host,
            port=port,
            reload=False,  # Disable reload to maintain deterministic state
            workers=1,     # Single worker for deterministic behavior
            log_level="info"
        )
    except KeyboardInterrupt:
        print("\n👋 Server stopped")
    except Exception as e:
        print(f"❌ Error starting server: {e}")

if __name__ == "__main__":
    main() 