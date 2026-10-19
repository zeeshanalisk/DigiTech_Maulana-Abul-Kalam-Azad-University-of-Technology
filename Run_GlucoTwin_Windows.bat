@echo off
setlocal
python --version
if errorlevel 1 (
  echo Python 3.11 or later is required. Install Python, then run this file again.
  pause
  exit /b 1
)
python -m pip install -r requirements.txt
if errorlevel 1 (
  echo Dependency installation failed. Check your internet connection and Python version.
  pause
  exit /b 1
)
python -m src.synthetic_data
if errorlevel 1 goto :fail
python -m src.train_model
if errorlevel 1 goto :fail
python -m streamlit run app.py
if errorlevel 1 goto :fail
exit /b 0
:fail
echo A setup step failed. Read the error message above and check README.md.
pause
