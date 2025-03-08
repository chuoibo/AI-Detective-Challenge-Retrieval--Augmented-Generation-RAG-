import subprocess
import os
import argparse
import logging
import time
import uvicorn
import signal
import sys

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

api_process = None
ui_process = None

def start_api_server(host="0.0.0.0", port=8000, reload=False):
    try:
        logger.info(f"Starting API server on {host}:{port}")
        return uvicorn.run(
            "app.api.main:app",
            host=host,
            port=port,
            reload=reload,
            log_level="info",
        )
    except Exception as e:
        logger.error(f"Failed to start API server: {e}")
        return None

def start_ui(port=8501):
    try:
        logger.info(f"Starting Streamlit UI on port {port}")
        env = os.environ.copy()
        env["API_URL"] = f"http://localhost:8000/api/v1"
        
        app_path = os.path.join("app", "ui", "streamlit_app.py")
        
        cmd = [
            "streamlit", "run", app_path,
            "--server.port", str(port),
            "--server.address", "0.0.0.0",
            "--browser.serverAddress", "localhost",
            "--browser.gatherUsageStats", "false"
        ]
        
        process = subprocess.Popen(
            cmd,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
            universal_newlines=True
        )
        
        logger.info(f"Streamlit UI started with PID {process.pid}")
        return process
        
    except Exception as e:
        logger.error(f"Failed to start Streamlit UI: {e}")
        return None

def cleanup(signum=None, frame=None):
    """Cleanup function to terminate processes"""
    logger.info("Cleaning up processes...")
    
    if ui_process:
        logger.info(f"Terminating Streamlit UI (PID: {ui_process.pid})")
        ui_process.terminate()
        ui_process.wait(timeout=5)
    
    logger.info("Application shutdown complete")
    sys.exit(0)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Crypto Detective RAG System")
    parser.add_argument("--api-port", type=int, default=8000, help="Port for the API server")
    parser.add_argument("--ui-port", type=int, default=8501, help="Port for the Streamlit UI")
    parser.add_argument("--api-only", action="store_true", help="Run only the API server")
    parser.add_argument("--ui-only", action="store_true", help="Run only the Streamlit UI")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload for development")
    args = parser.parse_args()
    
    signal.signal(signal.SIGINT, cleanup)
    signal.signal(signal.SIGTERM, cleanup)
    
    try:
        if args.api_only:
            start_api_server(port=args.api_port, reload=args.reload)
        elif args.ui_only:
            ui_process = start_ui(port=args.ui_port)
            if ui_process:
                while ui_process.poll() is None:
                    time.sleep(1)
        else:
            ui_process = start_ui(port=args.ui_port)
            if ui_process:
                start_api_server(port=args.api_port, reload=args.reload)
    
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received")
    
    finally:
        cleanup()