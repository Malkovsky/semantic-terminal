function sem-run {
    $historyFile = Join-Path -Path $HOME -ChildPath ".local/share/semantic-terminal/last_command"
    $cmd = $null

    if ($args.Count -eq 0) {
        if (-not (Test-Path -LiteralPath $historyFile)) {
            Write-Error "No previous command found at $historyFile"
            return
        }

        $cmd = (Get-Content -LiteralPath $historyFile -Raw).Trim()
        if ([string]::IsNullOrWhiteSpace($cmd)) {
            Write-Error "Last command history is empty."
            return
        }
    }
    else {
        $output = & sem @args 2>&1
        $status = $LASTEXITCODE

        if ($null -ne $output) {
            $output | ForEach-Object { $_ }
        }

        if ($status -ne 0) {
            return
        }

        $lines = @($output | ForEach-Object { "$_" })
        for ($i = $lines.Count - 1; $i -ge 0; $i--) {
            $candidate = $lines[$i].Trim()
            if ($candidate.Length -gt 0) {
                $cmd = $candidate
                break
            }
        }

        if ($null -eq $cmd) {
            Write-Error "Could not parse command from sem output."
            return
        }

        $cmd = $cmd -replace '^\$\s+', ''
        if ([string]::IsNullOrWhiteSpace($cmd)) {
            Write-Error "Parsed command is empty."
            return
        }
    }

    try {
        if (Get-Command -Name Add-History -ErrorAction SilentlyContinue) {
            Add-History -InputObject $cmd -ErrorAction SilentlyContinue
        }

        if (Get-Command -Name Get-PSReadLineOption -ErrorAction SilentlyContinue) {
            [Microsoft.PowerShell.PSConsoleReadLine]::AddToHistory($cmd)
        }
    }
    catch {
    }

    Invoke-Expression $cmd
}
