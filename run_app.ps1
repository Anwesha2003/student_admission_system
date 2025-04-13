# run_app.ps1
# PowerShell script to run the Student Admission System on Windows

# Configuration
$BACKEND_PORT = 8000
$FRONTEND_PORT = 8501
$VENV_PATH = ".\venv310"
$BACKEND_PATH = ".\backend"
$FRONTEND_PATH = ".\frontend"

# Set Python path to project root
$PROJECT_ROOT = $PWD
$env:PYTHONPATH = "$PROJECT_ROOT"
Write-Host "Setting PYTHONPATH to: $env:PYTHONPATH" -ForegroundColor Yellow

Write-Host "Starting Student Admission System..." -ForegroundColor Cyan

# Function to check if a port is in use
function Test-PortInUse {
    param (
        [int]$Port
    )
    
    $connection = Get-NetTCPConnection -LocalPort $Port -ErrorAction SilentlyContinue
    return ($null -ne $connection)
}

# Check if ports are available
if (Test-PortInUse -Port $BACKEND_PORT) {
    Write-Host "Error: Port $BACKEND_PORT is already in use. Backend cannot start." -ForegroundColor Red
    exit 1
}

if (Test-PortInUse -Port $FRONTEND_PORT) {
    Write-Host "Error: Port $FRONTEND_PORT is already in use. Frontend cannot start." -ForegroundColor Red
    exit 1
}

# Activate virtual environment
Write-Host "Activating virtual environment..." -ForegroundColor Yellow
if (-not (Test-Path $VENV_PATH)) {
    Write-Host "Virtual environment not found. Please run setup script first." -ForegroundColor Red
    exit 1
}

# Start the backend server in a new PowerShell window
Start-Process powershell -ArgumentList "-NoExit", "-Command", "
    Set-Location '$PWD'; 
    & '$VENV_PATH\Scripts\Activate.ps1'; 
    `$env:PYTHONPATH = '$PROJECT_ROOT';
    Write-Host 'Starting Streamlit frontend...' -ForegroundColor Cyan; 
    cd '$FRONTEND_PATH'; 
    streamlit run home.py --server.port=$FRONTEND_PORT

"

# Wait for backend to initialize
Write-Host "Waiting for backend to initialize..." -ForegroundColor Yellow
Start-Sleep -Seconds 5

# Start the frontend in a new PowerShell window
Start-Process powershell -ArgumentList "-NoExit", "-Command", "
    Set-Location '$PWD'; 
    & '$VENV_PATH\Scripts\Activate.ps1'; 
    `$env:PYTHONPATH = '$PROJECT_ROOT';
    Write-Host 'Starting Streamlit frontend...' -ForegroundColor Cyan; 
    cd '$FRONTEND_PATH'; 
    streamlit run home.py --server.port=$FRONTEND_PORT
"

Write-Host "Application started!" -ForegroundColor Cyan
Write-Host "Backend API running at: http://localhost:$BACKEND_PORT" -ForegroundColor Magenta
Write-Host "Frontend running at: http://localhost:$FRONTEND_PORT" -ForegroundColor Magenta
Write-Host "API documentation available at: http://localhost:$BACKEND_PORT/docs" -ForegroundColor Magenta