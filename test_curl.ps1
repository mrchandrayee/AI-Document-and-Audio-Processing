# Test audio transcription using curl
$audioFile = "harvard.wav"
$url = "http://localhost:8000/audio-transcription"

Write-Host "Testing audio transcription with curl and $audioFile..."

$curlCommand = @"
curl --location '$url' `
--header 'Authorization: 101secretkey' `
--form 'file=@"$audioFile"' `
--form 'remove_noise="true"' `
--form 'force_english="true"'
"@

Write-Host "Executing: $curlCommand"
Invoke-Expression $curlCommand
