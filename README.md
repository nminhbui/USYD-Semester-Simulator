USYD SEMESTER SIMULATOR 
Project type: Browser-based Python application using Flask.
Main script: app.py
Requirements:
- Python 3.10 or later
- Flask (listed in requirements.txt)

Installation and execution:
1. Download all files and place them in the same folder, preserving the original folder structure. Then open a terminal in the project folder.
2. Create a virtual environment:
python3 -m venv .venv
3. Activate the virtual environment:
macOS/Linux:
source .venv/bin/activate
Windows PowerShell:
.venv\Scripts\Activate.ps1
4. Install the required dependencies: (The command might vary depending on where you have placed the file, so open the project folder first)
python -m pip install -r requirements.txt
5. Start the application:
python app.py
6. Open a web browser and visit:
http://127.0.0.1:5000
Keep the terminal running while using the application. Press Ctrl+C in the terminal to stop the server.

Important notes:
- This application uses Flask and runs through a local web server.
- It requires a web browser and cannot run directly in the Ed environment.
- The templates, static, and data folders must remain in the project directory.
- The application stores game progress locally in the saves folder.
- Flask is an external Python library and must be installed before running the application.
