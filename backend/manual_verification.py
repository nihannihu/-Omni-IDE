import os
import webbrowser
from pathlib import Path
import time

# Mock final_answer to make the script executable standalone
def final_answer(content):
    print(f"[FINAL ANSWER]: {content}")

# Rule 1: Imports
# (Already done above)

# Rule 2: Absolute Paths
BASE_DIR = r"C:\Users\nihan\Desktop\LoginApp"
print(f"Creating project at: {BASE_DIR}")
os.makedirs(BASE_DIR, exist_ok=True)

# Rule 3: Pathlib write_text
html_content = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Agent Login</title>
    <link rel="stylesheet" href="style.css">
</head>
<body>
    <div class="login-wrapper">
        <form class="login-form">
            <h2>Welcome Back</h2>
            <div class="input-group">
                <input type="text" required>
                <label>Username</label>
            </div>
            <div class="input-group">
                <input type="password" required>
                <label>Password</label>
            </div>
            <button type="submit">Sign In</button>
        </form>
    </div>
</body>
</html>
"""

css_content = """
body {
    margin: 0;
    font-family: 'Segoe UI', sans-serif;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    height: 100vh;
    display: flex;
    align-items: center;
    justify-content: center;
}
.login-form {
    background: white;
    padding: 2rem;
    border-radius: 10px;
    box-shadow: 0 10px 25px rgba(0,0,0,0.2);
    width: 300px;
}
h2 { text-align: center; color: #333; }
.input-group { position: relative; margin-bottom: 2rem; }
input { width: 100%; padding: 10px 0; border: none; border-bottom: 1px solid #999; outline: none; }
label { position: absolute; left: 0; top: 10px; color: #999; transition: 0.3s; pointer-events: none; }
input:focus ~ label, input:valid ~ label { top: -20px; font-size: 12px; color: #764ba2; }
button { width: 100%; padding: 10px; background: #764ba2; color: white; border: none; border-radius: 5px; cursor: pointer; }
button:hover { background: #5a387a; }
"""

print("Writing files using pathlib...")
Path(os.path.join(BASE_DIR, "index.html")).write_text(html_content, encoding='utf-8')
Path(os.path.join(base_dir := BASE_DIR, "style.css")).write_text(css_content, encoding='utf-8')

# Rule 4: Webbrowser Open
html_path = os.path.join(BASE_DIR, "index.html")
print(f"Opening browser: file://{html_path}")
webbrowser.open('file://' + html_path)

# Rule 5: Final Answer at the very end
final_answer("Login Project Created Successfully at " + BASE_DIR)
