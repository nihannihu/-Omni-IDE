from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import asyncio
import logging
import os
import sys
import subprocess
import aiofiles
from pathlib import Path
from pydantic import BaseModel

# Configure Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# Global State
WORKING_DIRECTORY = None  # No directory until user selects one

# Input/Output Models
class CodeRequest(BaseModel):
    code: str

class ChatRequest(BaseModel):
    text: str

class ChangeDirRequest(BaseModel):
    path: str

# CORS (Allow all for local dev)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve Static Files
# Detect if running as a PyInstaller bundle
if getattr(sys, 'frozen', False):
    # If bundled, use the temporary _MEIPASS directory
    base_path = sys._MEIPASS
else:
    # If running as a script, use the local directory
    base_path = os.path.dirname(os.path.abspath(__file__))

static_path = os.path.join(base_path, "static")

# Mount the correct path
app.mount("/static", StaticFiles(directory=static_path), name="static")

@app.get("/")
async def read_root():
    return FileResponse(os.path.join(static_path, 'index.html'))

# --- Core API (Emergency Fix) ---

@app.post("/api/change_dir")
async def change_directory(request: ChangeDirRequest):
    """Update the working directory for the File Explorer."""
    global WORKING_DIRECTORY
    target_path = Path(request.path).resolve()
    
    if not target_path.exists() or not target_path.is_dir():
        raise HTTPException(status_code=400, detail="Invalid directory path.")
    
    WORKING_DIRECTORY = str(target_path)
    logger.info(f"Working Directory changed to: {WORKING_DIRECTORY}")
    return {"status": "success", "path": WORKING_DIRECTORY}

@app.post("/api/close_folder")
async def close_folder():
    """Reset WORKING_DIRECTORY to None (Close Folder)."""
    global WORKING_DIRECTORY
    WORKING_DIRECTORY = None
    # Also reset agent's directory
    from agent import WORKING_DIRECTORY as AGENT_WD
    import agent as agent_module
    agent_module.WORKING_DIRECTORY = None
    
    logger.info("Working Directory closed.")
    return {"status": "closed"}

@app.get("/api/files")
async def list_files():
    """List files in the current WORKING_DIRECTORY."""
    global WORKING_DIRECTORY
    files = []
    # Define safe extensions to show
    SAFE_EXTENSIONS = {'.py', '.txt', '.md', '.html', '.css', '.js', '.json', '.env'}
    IGNORED_DIRS = {'venv', 'venv_gpu', 'node_modules', '__pycache__', '.git', '.idea', '.vscode'}
    
    try:
        if not WORKING_DIRECTORY:
            return {"files": [], "current_dir": None, "no_directory": True}
        
        # Scan WORKING_DIRECTORY instead of '.'
        with os.scandir(WORKING_DIRECTORY) as entries:
            for entry in entries:
                if entry.name.startswith('.') and entry.name != '.env': 
                    continue
                
                if entry.is_file() and any(entry.name.endswith(ext) for ext in SAFE_EXTENSIONS):
                    files.append({"name": entry.name, "type": "file"})
                elif entry.is_dir() and entry.name not in IGNORED_DIRS:
                    files.append({"name": entry.name, "type": "directory"})
        
        # Sort directories first, then files
        files.sort(key=lambda x: (x['type'] != 'directory', x['name']))
        return {"files": files, "current_dir": WORKING_DIRECTORY}
    except Exception as e:
        logger.error(f"Error listing files in {WORKING_DIRECTORY}: {e}")
        return {"files": [], "error": str(e)}

@app.get("/api/read")
async def read_file(filename: str):
    """Read content of a file from WORKING_DIRECTORY."""
    global WORKING_DIRECTORY
    try:
        if not WORKING_DIRECTORY:
            raise HTTPException(status_code=400, detail="No folder is open. Please open a folder first.")
        base_path = Path(WORKING_DIRECTORY).resolve()
        file_path = (base_path / filename).resolve()
        
        if not str(file_path).startswith(str(base_path)):
             raise HTTPException(status_code=403, detail="Access denied: Path traversal attempt.")
        
        if not file_path.exists() or not file_path.is_file():
            raise HTTPException(status_code=404, detail=f"File not found: {filename} in {WORKING_DIRECTORY}")
            
        async with aiofiles.open(file_path, mode='r', encoding='utf-8') as f:
            content = await f.read()
        return {"content": content, "path": str(file_path)}
        
    except HTTPException:
        raise  # Let HTTP errors pass through
    except Exception as e:
        logger.error(f"Read Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    """Lightweight health check for connection heartbeat."""
    return {"status": "ok"}

@app.get("/workspace/{filepath:path}")
async def serve_workspace_file(filepath: str):
    """Serve ANY file from WORKING_DIRECTORY. This is the key to making HTML previews work
    with relative CSS/JS/image references. When browser loads /workspace/page.html and
    that HTML has <link href='style.css'>, browser resolves to /workspace/style.css ✅"""
    global WORKING_DIRECTORY
    try:
        if not WORKING_DIRECTORY:
            raise HTTPException(status_code=400, detail="No folder is open.")
        base_path = Path(WORKING_DIRECTORY).resolve()
        file_path = (base_path / filepath).resolve()
        
        # Security: must stay within working directory
        if not str(file_path).startswith(str(base_path)):
            raise HTTPException(status_code=403, detail="Access denied.")
        if not file_path.exists() or not file_path.is_file():
            raise HTTPException(status_code=404, detail=f"File not found: {filepath}")
        
        # FileResponse auto-detects MIME type from extension
        return FileResponse(file_path)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Workspace file error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/save")
async def save_file(filename: str, request: CodeRequest):
    """Save editor content back to a file in WORKING_DIRECTORY."""
    global WORKING_DIRECTORY
    try:
        if not WORKING_DIRECTORY:
            raise HTTPException(status_code=400, detail="No folder is open. Please open a folder first.")
        base_path = Path(WORKING_DIRECTORY).resolve()
        file_path = (base_path / filename).resolve()
        
        if not str(file_path).startswith(str(base_path)):
            raise HTTPException(status_code=403, detail="Access denied.")
        
        async with aiofiles.open(file_path, mode='w', encoding='utf-8') as f:
            await f.write(request.code)
        
        logger.info(f"Saved: {file_path}")
        return {"status": "saved", "path": str(file_path)}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Save Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/delete")
async def delete_file(filename: str):
    """Delete a file from WORKING_DIRECTORY (reliable, UI-driven)."""
    global WORKING_DIRECTORY
    try:
        if not WORKING_DIRECTORY:
            raise HTTPException(status_code=400, detail="No folder is open. Please open a folder first.")
        base_path = Path(WORKING_DIRECTORY).resolve()
        file_path = (base_path / filename).resolve()
        
        if not str(file_path).startswith(str(base_path)):
            raise HTTPException(status_code=403, detail="Access denied.")
        if not file_path.exists():
            raise HTTPException(status_code=404, detail=f"File not found: {filename}")
        
        import os, shutil
        if file_path.is_file():
            os.remove(file_path)
        elif file_path.is_dir():
            shutil.rmtree(file_path)
        
        logger.info(f"Deleted: {file_path}")
        return {"status": "deleted", "filename": filename}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Delete Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/run")
async def run_code(request: CodeRequest):
    """Execute Python code and return output."""
    global WORKING_DIRECTORY
    code = request.code
    try:
        # Run code in a subprocess
        result = subprocess.run(
            [sys.executable, "-c", code],
            capture_output=True,
            text=True,
            timeout=10,
            cwd=WORKING_DIRECTORY # Execute in current working dir
        )
        return {
            "stdout": result.stdout,
            "stderr": result.stderr,
            "returncode": result.returncode
        }
    except subprocess.TimeoutExpired:
        return {"stdout": "", "stderr": "Error: Execution timed out (10s limit).", "returncode": -1}
    except Exception as e:
        return {"stdout": "", "stderr": f"System Error: {str(e)}", "returncode": -1}

# --- Agent Logic (Robust REST Endpoint) ---
from agent import OmniAgent
import agent as agent_module  # Access module-level vars
agent = OmniAgent()

@app.post("/chat")
async def chat_endpoint(request: ChatRequest):
    """Synced Chat Endpoint for Stability."""
    global WORKING_DIRECTORY
    user_message = request.text
    try:
        if not WORKING_DIRECTORY:
            return {"reply": "Please open a folder first using the Open Folder button before asking me to create, edit, or delete files."}
        # FIX: Set agent's working directory WITHOUT os.chdir (which breaks static serving)
        agent_module.WORKING_DIRECTORY = WORKING_DIRECTORY
        logger.info(f"Agent will write files to: {WORKING_DIRECTORY}")
        
        full_response = ""
        try:
            response_generator = agent.execute_stream(user_message)
            for token in response_generator:
                full_response += token
        except TypeError:
            async for token in agent.execute_stream(user_message):
                full_response += token

        return {"response": full_response}
        
    except Exception as e:
        logger.error(f"Agent Error: {e}")
        # Return 500 so frontend sees the crash
        raise HTTPException(status_code=500, detail=f"Agent Crash: {str(e)}")

# --- WebSocket Chat Logic (Legacy/Streaming support) ---
class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def send_json(self, message: dict, websocket: WebSocket):
        await websocket.send_json(message)

manager = ConnectionManager()

@app.websocket("/ws/omni")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_json()
            if data.get("type") == "text_input":
                text = data.get("text")
                await manager.send_json({"type": "agent_response_start"}, websocket)
                
                full_response = ""
                # Assuming sync generator for now based on previous code
                for token in agent.execute_stream(text):
                    await manager.send_json({"type": "agent_token", "text": token}, websocket)
                    full_response += token
                
                await manager.send_json({"type": "agent_response_end"}, websocket)

    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket Error: {e}")
        try:
            await manager.send_json({"type": "error", "message": str(e)}, websocket)
        except:
            pass
