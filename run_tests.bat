@echo off
chcp 65001 > nul
echo Running Bot Handler Tests...
python run_app_tests.py
if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Tests failed! Traceback saved in test_errors.log
    pause
    exit /b 1
) else (
    echo.
    echo [SUCCESS] All tests passed!
    pause
    exit /b 0
)
