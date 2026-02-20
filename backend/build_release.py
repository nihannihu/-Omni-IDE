import PyInstaller.__main__
import os
import shutil

# clean previous build
if os.path.exists('build'):
    shutil.rmtree('build')
if os.path.exists('dist'):
    shutil.rmtree('dist')

print("❄️  Freezing OmniIDE for Production...")

args = [
    'desktop.py',
    '--name=OmniIDE',
    '--onedir', # Folder output for easier debugging
    '--noconsole', # Hide console for production
    '--add-data=static;static',
    '--add-data=.env;.',
    '--clean',
    '--hidden-import=uvicorn',
    '--hidden-import=engineio.async_drivers.threading',
    '--collect-all=smolagents',
    '--exclude-module=torch',
    '--exclude-module=uvloop',
    '--exclude-module=tkinter',
]

if os.path.exists('static/icon.ico'):
    args.append('--icon=static/icon.ico')

PyInstaller.__main__.run(args)

print("✅ Build Complete! Check dist/OmniIDE.exe")
