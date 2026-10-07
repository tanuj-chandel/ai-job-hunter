# PowerShell script to register AI Job Search daily 8:00 AM Task in Windows Task Scheduler
$TaskName = "AI_Job_Search_Daily_8AM"
$ScriptPath = "d:\AI AUTOMATION\ai job search\auto_daily_job_search.py"

$Trigger8AM = New-ScheduledTaskTrigger -Daily -At 8:00AM
$Action = New-ScheduledTaskAction -Execute "python.exe" -Argument "`"$ScriptPath`"" -WorkingDirectory "d:\AI AUTOMATION\ai job search"

try {
    Register-ScheduledTask -TaskName $TaskName -Trigger $Trigger8AM -Action $Action -Description "Automated AI Job Search Daily 8:00 AM Scrape" -Force
    Write-Host "Successfully registered Windows Task '$TaskName' to run daily at 8:00 AM!" -ForegroundColor Green
} catch {
    Write-Host "Failed to register scheduled task: $_" -ForegroundColor Red
}
