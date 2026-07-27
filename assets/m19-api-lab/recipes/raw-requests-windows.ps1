# DATED RECIPE: raw requests on Windows (PowerShell 5.1+ / PowerShell 7).
# Last verified: 2026-07-24. Two honest paths exist on Windows and this
# file shows both. curl.exe ships with Windows 10 and 11 and takes the
# same flags as the macOS/Linux recipe; in PowerShell, type `curl.exe`
# (with the .exe), because bare `curl` is an alias for Invoke-WebRequest
# and takes different flags. That alias has burned a decade of learners.
#
# Run the lab service first, in another terminal:
#   python mock_service.py
#
# These are commands to run one at a time and READ, not a script to execute.

# ---- Path A: curl.exe (same anatomy as the other recipe) -----------------
curl.exe -s -i -X POST http://127.0.0.1:8124/v1/echo `
  -H "Authorization: Bearer mock-key-local-only" `
  -H "Content-Type: application/json" `
  -d '{\"model\": \"mock-1\", \"input\": \"What is an API?\"}'

# Streaming (-N = unbuffered; Ctrl+C mid-stream is the cancel exercise):
curl.exe -sN -X POST http://127.0.0.1:8124/v1/stream `
  -H "Authorization: Bearer mock-key-local-only"

# Timeout (8-second endpoint, 2-second budget; expect exit code 28):
curl.exe -s --max-time 2 -X POST http://127.0.0.1:8124/v1/slow `
  -H "Authorization: Bearer mock-key-local-only"
Write-Host "exit code: $LASTEXITCODE"

# ---- Path B: native PowerShell ---------------------------------------------
# Same request, PowerShell's own spelling. Note what maps to what:
# -Method is the method, -Headers the headers, -Body the body. The anatomy
# survives the syntax change, which is the whole lesson.
$headers = @{
  "Authorization" = "Bearer mock-key-local-only"
  "Content-Type"  = "application/json"
}
$body = '{"model": "mock-1", "input": "What is an API?"}'
Invoke-RestMethod -Method Post -Uri "http://127.0.0.1:8124/v1/echo" `
  -Headers $headers -Body $body

# The exhibits (Invoke-WebRequest throws on 4xx/5xx by default; catch it
# and the response is still there to read, status and body both):
foreach ($kind in "bad-input","auth","forbidden","missing","rate-limit","server") {
  Write-Host "== $kind =="
  try {
    Invoke-WebRequest -Uri "http://127.0.0.1:8124/v1/error/$kind" | Out-Null
  } catch {
    $resp = $_.Exception.Response
    Write-Host "status:" $resp.StatusCode.value__
    $reader = New-Object System.IO.StreamReader($resp.GetResponseStream())
    Write-Host $reader.ReadToEnd()
  }
}

# Save the raw evidence (headers, body, timing):
$time = Measure-Command {
  $r = Invoke-WebRequest -Method Post -Uri "http://127.0.0.1:8124/v1/echo" `
    -Headers $headers -Body '{"model": "mock-1", "input": "save this one"}'
  $r.RawContent | Out-File response-raw.txt
}
Write-Host "total time:" $time.TotalSeconds "s"
