# PowerShell Script to register the Automated Job Scraper as a Windows Scheduled Task
# Run this script to create the background automated job search.

$taskName = "TanujChandel_AI_Job_Scraper"
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$workDir = Resolve-Path (Join-Path $scriptDir "..")
$scriptPath = Join-Path $workDir "tools\automated_job_scraper.py"

Write-Host "Registering background task: $taskName..."
Write-Host "Workspace directory: $workDir"
Write-Host "Script path: $scriptPath"

# 1. Locate python.exe
$pythonExec = (Get-Command python -ErrorAction SilentlyContinue).Source
if (-not $pythonExec) {
    # Check standard local appdata installation
    $localAppData = [System.Environment]::GetFolderPath('LocalApplicationData')
    $possiblePaths = @(
        (Join-Path $localAppData "Programs\Python\Python312\python.exe"),
        (Join-Path $localAppData "Programs\Python\Python311\python.exe"),
        (Join-Path $localAppData "Programs\Python\Python310\python.exe")
    )
    foreach ($p in $possiblePaths) {
        if (Test-Path $p) {
            $pythonExec = $p
            break
        }
    }
}

if (-not $pythonExec) {
    Write-Error "Could not locate python.exe. Please ensure Python is installed and added to your system PATH."
    Exit 1
}

Write-Host "Using Python executable: $pythonExec"

# 2. Configure Scheduled Task
$action = New-ScheduledTaskAction -Execute $pythonExec -Argument "`"$scriptPath`"" -WorkingDirectory $workDir
$trigger = New-ScheduledTaskTrigger -Daily -At 9:00AM
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable -RunOnlyIfNetworkAvailable

# 3. Register Task (Force overwrite if exists)
try {
    Register-ScheduledTask -TaskName $taskName -Action $action -Trigger $trigger -Settings $settings -Description "Daily background job scraping for Tanuj Chandel's AI Job Search" -Force | Out-Null
    Write-Host "Successfully registered scheduled task: '$taskName'!"
    Write-Host "The scraper will run silently in the background every day at 9:00 AM."
} catch {
    Write-Error "Failed to register scheduled task. Ensure you are running this console with sufficient permissions. Error: $_"
    Exit 1
}
