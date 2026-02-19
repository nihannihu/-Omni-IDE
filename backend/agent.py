import logging
import re
import os
import sys
from threading import Thread, Lock as ThreadLock
from dotenv import load_dotenv

# Lightweight Agent Framework
from smolagents import CodeAgent, Tool, InferenceClientModel, ChatMessage, MessageRole, ChatMessageStreamDelta, ActionStep, ToolCall, ToolOutput, FinalAnswerStep
from smolagents.models import get_clean_message_list
import smolagents.utils as smolagents_utils

# API Client for Vision & Chat
from huggingface_hub import InferenceClient

# Load environment variables
load_dotenv()
hf_token = os.getenv("HUGGINGFACE_API_KEY")

logger = logging.getLogger(__name__)

# ------------------------------------------------------------------
# SECURITY SANDBOX & FILE SYSTEM WRAPPERS
# ------------------------------------------------------------------

# This is set by main.py when the user changes directory
WORKING_DIRECTORY = None

def get_desktop_path():
    from pathlib import Path
    return Path(r"C:\Users\nihan\Desktop")

def get_base_path():
    """Returns WORKING_DIRECTORY. Raises error if no folder is open."""
    from pathlib import Path
    if WORKING_DIRECTORY:
        return Path(WORKING_DIRECTORY)
    raise ValueError("No folder is open. Please open a folder first using the Open Folder button.")

def safe_write(filename: str, content: str) -> str:
    """Safely writes content to a file in the WORKING_DIRECTORY."""
    base = get_base_path()
    filename = filename.lstrip("/").lstrip("\\")
    filepath = (base / filename).resolve()
    
    if not str(filepath).startswith(str(base.resolve())):
        raise ValueError(f"Security Block (Path Traversal): {filename}")
        
    filepath.parent.mkdir(parents=True, exist_ok=True)
    filepath.write_text(content, encoding='utf-8')
    logger.info(f"safe_write: Created {filepath}")
    return str(filepath)

def safe_open(filepath_str, mode='r', **kwargs):
    """Safe wrapper for open() rooted to WORKING_DIRECTORY."""
    from pathlib import Path
    import builtins
    base = get_base_path()
    filepath = Path(filepath_str)
    
    if not filepath.is_absolute():
        filepath = base / filepath
    filepath = filepath.resolve()
    
    if any(m in mode for m in ('w', 'a', 'x')) and not str(filepath).startswith(str(base.resolve())):
        raise ValueError(f"Security Block (Write Outside Sandbox): {filepath}")
        
    if any(m in mode for m in ('w', 'a', 'x')):
        filepath.parent.mkdir(parents=True, exist_ok=True)
        
    return builtins.open(str(filepath), mode, **kwargs)

def safe_mkdir(path_str, *args, **kwargs):
    """Safe wrapper for directory creation rooted to WORKING_DIRECTORY."""
    from pathlib import Path
    base = get_base_path()
    path = Path(path_str)
    
    if not path.is_absolute():
        path = base / path
    path = path.resolve()
    
    if not str(path).startswith(str(base.resolve())):
        raise ValueError(f"Security Block (mkdir Outside Sandbox): {path}")
    
    path.mkdir(parents=True, exist_ok=True)
    return str(path)

def safe_delete(filename):
    """Delete a file from the working directory (sandboxed)."""
    from pathlib import Path
    import os
    base = get_base_path()
    path = Path(filename)
    if not path.is_absolute():
        path = base / path
    path = path.resolve()
    
    if not str(path).startswith(str(base.resolve())):
        raise ValueError(f"Security Block (Delete Outside Sandbox): {path}")
    
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")
    
    if path.is_file():
        os.remove(path)
        logger.info(f"Deleted file: {path}")
        return f"Deleted: {filename}"
    elif path.is_dir():
        import shutil
        shutil.rmtree(path)
        logger.info(f"Deleted directory: {path}")
        return f"Deleted directory: {filename}"
    else:
        raise ValueError(f"Cannot delete: {path}")

def open_in_browser(filepath_str):
    """Opens a file in the default web browser (Desktop rooted)."""
    import webbrowser as wb
    from pathlib import Path
    desktop = get_desktop_path()
    filepath = Path(filepath_str)
    
    if not filepath.is_absolute():
        filepath = desktop / filepath
    filepath = filepath.resolve()
    
    wb.open(filepath.as_uri())
    return str(filepath)

def create_web_page(folder_name: str, page_type: str = "landing", title: str = "My Page", theme: str = "dark") -> str:
    """
    Generates professional HTML/CSS templates for standard pages.
    """
    folder_path = safe_mkdir(folder_name)
    from pathlib import Path
    folder = Path(folder_path)
    
    bg = "#0f0f1a" if theme == "dark" else "#f0f2f5"
    text = "#e0e0e0" if theme == "dark" else "#333333"
    accent = "#6c63ff"
    
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>{title}</title>
    <style>
        body {{ background: {bg}; color: {text}; font-family: sans-serif; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }}
        .container {{ text-align: center; padding: 40px; border: 1px solid {accent}; border-radius: 10px; }}
        h1 {{ color: {accent}; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>{title}</h1>
        <p>Generated by Omni-Agent Studio ({page_type})</p>
    </div>
</body>
</html>"""

    (folder / "index.html").write_text(html_content, encoding='utf-8')
    return open_in_browser(str(folder / "index.html"))

# ------------------------------------------------------------------
# CODE CLEANER & MONKEY PATCHES
# ------------------------------------------------------------------

def clean_code_output(code: str) -> str:
    lines = code.split('\n')
    cleaned = []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith('Thought:') or stripped.startswith('Code:') or re.match(r'^\d+\.\s+[A-Z]', stripped):
            continue
        cleaned.append(line)
    
    result = '\n'.join(cleaned).strip()
    if not result:
        return code
        
    if 'final_answer' not in result:
        result += '\nfinal_answer("Done!")'
    return result

_original_parse_code_blobs = smolagents_utils.parse_code_blobs
def _patched_parse_code_blobs(text: str, code_block_tags: tuple) -> str:
    try:
        code = _original_parse_code_blobs(text, code_block_tags)
        return clean_code_output(code)
    except ValueError:
        raise

smolagents_utils.parse_code_blobs = _patched_parse_code_blobs
try:
    import smolagents.agents as smolagents_agents
    smolagents_agents.parse_code_blobs = _patched_parse_code_blobs
except Exception:
    pass

# ------------------------------------------------------------------
# VISION TOOL (SERVERLESS)
# ------------------------------------------------------------------

class VisionTool(Tool):
    name = "analyze_screen"
    description = "Analyze the latest screen frame to answer a question. Use this tool when the user asks you to 'see', 'look', or describe what is on the screen."
    inputs = {
        "question": {
            "type": "string",
            "description": "The question to ask about the screen content (e.g., 'What do you see?', 'Read the error')."
        }
    }
    output_type = "string"

    def __init__(self, get_image_func, **kwargs):
        super().__init__(**kwargs)
        self.get_image_func = get_image_func
        # Use Hugging Face Inference API for Vision
        self.client = InferenceClient(token=os.getenv("HUGGINGFACE_API_KEY"))

    def forward(self, question: str) -> str:
        try:
            image_data = self.get_image_func()
            if not image_data:
                return "No screen frame available. Ask the user to verify screen sharing is on."
            
            # Clean base64 string
            if "," in image_data:
                 image_data = image_data.split(",")[1]
            
            logger.info(f"VisionTool: Analyzing screen with question: '{question}' (Cloud Vision)")
            
            # Use Qwen2.5-VL-7B-Instruct or Llama-3.2-11B-Vision
            # Trying Qwen/Qwen2.5-VL-7B-Instruct first as it matches our Coder model family
            messages = [
                {
                    "role": "user",
                    "content": [
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_data}"}},
                        {"type": "text", "text": question}
                    ]
                }
            ]
            
            response = self.client.chat_completion(
                model="Qwen/Qwen2.5-VL-7B-Instruct",
                messages=messages,
                max_tokens=500
            )
            
            result = response.choices[0].message.content
            logger.info(f"VisionTool Result: {result[:50]}...")
            return f"Screen Insight: {result}"
            
        except Exception as e:
            logger.error(f"VisionTool Error: {e}")
            return f"Error analyzing screen: {str(e)}"

# ------------------------------------------------------------------
# OMNI AGENT (CLOUD BRAIN)
# ------------------------------------------------------------------

class OmniAgent:
    def __init__(self):
        logger.info("Initializing Cloud Brain (Qwen2.5-Coder-32B)...")
        
        if not hf_token:
            logger.error("CRITICAL: HUGGINGFACE_API_KEY missing!")
        
        try:
            self.model = InferenceClientModel(
                model_id="Qwen/Qwen2.5-Coder-32B-Instruct",
                token=hf_token
            )
            
            # Vision Caching
            self.image_lock = ThreadLock()
            self.latest_image = None
            
            def get_latest_image():
                with self.image_lock:
                    return self.latest_image
            
            self.vision_tool = VisionTool(get_latest_image)
            
            # PROMPT: Ultra-Aggressive Direct Execution Engine
            SYSTEM_PROMPT = r"""
You are a Senior Full-Stack Developer and AI Coding Engine, created by Nihan Nihu.
CRITICAL RULE: You are a File Creation Engine.
When generating code, you MUST immediately write it to the disk using pathlib.

CORRECT PATTERN:
from pathlib import Path
Path('index.html').write_text('...content...', encoding='utf-8')

INCORRECT PATTERN (DO NOT DO THIS):
html_content = '...content...' # This is useless! Write it to disk!

If asked "Who created you?", answer "I was created by Nihan Nihu."

=== ABSOLUTE RULES (VIOLATION = FAILURE) ===

RULE 1 - FILE CREATION (when user says "create", "make", "build"):
  - Call `safe_write(filename, content)` DIRECTLY with the full file content.
  - DO NOT assign to variables. DO NOT show in markdown blocks.
  - After writing: `final_answer("DONE: filename1.html, filename2.css")`

RULE 2 - FILE EDITING (when user says "edit", "modify", "add", "change", "update", "fix"):
  THIS IS THE MOST IMPORTANT RULE. To EDIT an existing file you MUST:
  Step 1: READ the existing file content:
    `existing = safe_open("filename.html", "r").read()`
  Step 2: MODIFY the content (add/change/remove what the user requested)
  Step 3: WRITE the modified content back:
    `safe_write("filename.html", modified_content)`
  Step 4: `final_answer("DONE: filename.html")`
  
  WARNING: You MUST include ALL the original content plus your changes.
  If you only write new content, you will DELETE the original file content!

RULE 3 - RESPONSE FORMAT (MANDATORY):
  - ALWAYS end with: `final_answer("DONE: file1.ext, file2.ext")`
  - List ALL files you created or modified.
  - NEVER say just "Done!" — you MUST include the filenames after "DONE:"

RULE 4 - TOOLS AVAILABLE:
  - `safe_write(filename, content)` - Create or overwrite a file
  - `safe_open(path, mode)` - Open/read a file (mode="r" for reading)
  - `safe_delete(filename)` - Delete a file or directory
  - `safe_mkdir(dirname)` - Create a directory
  - `analyze_screen(question)` - See the user's screen

RULE 5 - FILE DELETION (when user says "delete", "remove"):
  - Call `safe_delete(filename)` for each file to delete.
  - After deleting: `final_answer("DELETED: filename1.html, filename2.css")`

=== CORRECT EXAMPLES ===

EXAMPLE 1 - CREATE new files:
User: "Create a login page"
```python
safe_write("login.html", '''<!DOCTYPE html>
<html><head><title>Login</title><link rel="stylesheet" href="style.css"></head>
<body><div class="container"><h1>Login</h1>
<form><input type="email" placeholder="Email"><input type="password" placeholder="Password">
<button type="submit">Sign In</button></form></div></body></html>''')

safe_write("style.css", '''body { background: linear-gradient(135deg, #667eea, #764ba2); min-height: 100vh; display: flex; align-items: center; justify-content: center; font-family: sans-serif; }
.container { background: rgba(255,255,255,0.1); backdrop-filter: blur(10px); padding: 40px; border-radius: 16px; }
button { padding: 12px; background: #667eea; color: white; border: none; border-radius: 8px; cursor: pointer; }''')

final_answer("DONE: login.html, style.css")
```

EXAMPLE 2 - EDIT an existing file:
User: "Edit login.html, add a Register button and make buttons blue"
```python
# Step 1: READ existing content
existing_html = safe_open("login.html", "r").read()

# Step 2: MODIFY - replace the closing </form> with new button + closing tag
modified_html = existing_html.replace(
    '</form>',
    '<button type="button" class="register-btn">Register</button>\n</form>'
)

# Step 3: WRITE back
safe_write("login.html", modified_html)

# Also update CSS
existing_css = safe_open("style.css", "r").read()
modified_css = existing_css + '''
.register-btn { padding: 12px; background: #2196F3; color: white; border: none; border-radius: 8px; cursor: pointer; margin-top: 10px; width: 100%; }
button { background: #2196F3 !important; }'''
safe_write("style.css", modified_css)

final_answer("DONE: login.html, style.css")
```

=== WRONG (NEVER DO THIS) ===
```python
html = '''<!DOCTYPE html>...'''  # WRONG! Do not assign to variables!
print(content)                    # WRONG! Do not print content!
final_answer("Done!")             # WRONG! Must include filenames: "DONE: file.html"
```
"""
            self.agent = CodeAgent(
                tools=[self.vision_tool], 
                model=self.model, 
                add_base_tools=True,
                max_steps=5, 
                verbosity_level=logging.INFO,
                instructions=SYSTEM_PROMPT,
                additional_authorized_imports=["datetime", "math", "random", "time", "json", "re"],
                stream_outputs=True,
                executor_kwargs={
                    "additional_functions": {
                        "safe_write": safe_write,
                        "safe_open": safe_open,
                        "safe_delete": safe_delete,
                        "safe_mkdir": safe_mkdir,
                        "open_in_browser": open_in_browser,
                        "create_web_page": create_web_page,
                        "VisionTool": VisionTool
                    }
                }
            )
            logger.info("Cloud Brain initialized successfully.")
            
        except Exception as e:
            logger.error(f"Failed to initialize AI Agent: {e}")
            raise e

    def update_vision_context(self, base64_image: str):
        with self.image_lock:
            # logger.debug("Updated latest screen frame")
            self.latest_image = base64_image

    def execute_stream(self, task: str):
        """Execute a task and yield ONLY the clean final answer to the frontend.
        All internal steps (Thought, ToolCall, Observation) are logged to server only."""
        logger.info(f"Agent task: {task}")
        final_answer = None
        try:
            for step in self.agent.run(task, stream=True):
                # Log internals for debugging (NOT sent to frontend)
                if isinstance(step, ToolCall):
                    logger.info(f"  Tool: {step.name}")
                elif isinstance(step, ActionStep):
                    if step.error:
                        logger.error(f"  Step Error: {step.error}")
                    if hasattr(step, "observations") and step.observations:
                        logger.info(f"  Observation: {step.observations[:200]}...")
                    if step.is_final_answer and step.action_output is not None:
                        final_answer = str(step.action_output)
                elif isinstance(step, FinalAnswerStep):
                    final_answer = str(step.output)
                elif isinstance(step, ToolOutput):
                    logger.info(f"  Tool Output: {str(step.observation)[:200]}...")
                # ChatMessageStreamDelta is just intermediate thinking - skip

            if final_answer:
                yield final_answer
            else:
                yield "Task completed."
                
        except GeneratorExit:
            logger.info("Client disconnected.")
            return
        except Exception as e:
            logger.error(f"Execution Error: {e}")
            yield f"Error: {e}"

