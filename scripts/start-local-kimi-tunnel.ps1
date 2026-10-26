# The model remains on this computer. No cloud tags or public Ollama listener.
$kimiTunnel = Start-Process -FilePath "$env:WINDIR\System32\OpenSSH\ssh.exe" -ArgumentList @('-N','-R','127.0.0.1:11435:127.0.0.1:11434','-o','BatchMode=yes','-o','ExitOnForwardFailure=yes','-o','ServerAliveInterval=30','-o','ServerAliveCountMax=3','weddingos-hostinger-staging') -WindowStyle Hidden -PassThru
Write-Output "Local Kimi SSH tunnel started (PID $($kimiTunnel.Id)). Keep Ollama and this computer running."
