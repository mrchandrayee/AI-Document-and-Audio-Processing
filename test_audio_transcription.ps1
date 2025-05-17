# Test audio transcription endpoint - Updated for PowerShell compatibility
$audioFile = "harvard.wav"
$url = "http://localhost:8000/audio-transcription"

Write-Host "Testing audio transcription with $audioFile..."

$headers = @{
    "Authorization" = "101secretkey"
}

# Create boundary for multipart form data
$boundary = [System.Guid]::NewGuid().ToString()
$LF = "`r`n"

# Start building the multipart/form-data content
$bodyLines = (
    "--$boundary",
    "Content-Disposition: form-data; name=`"remove_noise`"",
    "",
    "true",
    "--$boundary",
    "Content-Disposition: form-data; name=`"force_english`"",
    "",
    "true",
    "--$boundary",
    "Content-Disposition: form-data; name=`"file`"; filename=`"harvard.wav`"",
    "Content-Type: audio/wav",
    "",
    [System.Text.Encoding]::GetEncoding("iso-8859-1").GetString([System.IO.File]::ReadAllBytes("$audioFile")),
    "--$boundary--"
)

# Join the lines with CRLF
$body = $bodyLines -join $LF

# Create the request
try {
    $response = Invoke-WebRequest -Uri $url `
        -Method Post `
        -Headers $headers `
        -ContentType "multipart/form-data; boundary=$boundary" `
        -Body $body `
        -ErrorAction Stop

    Write-Host "Response:"
    $response.Content | ConvertFrom-Json | ConvertTo-Json -Depth 10
}
catch {
    Write-Host "Error: $_"
    if ($_.ErrorDetails) {
        Write-Host $_.ErrorDetails.Message
    }
}
