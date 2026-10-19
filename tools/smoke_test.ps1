param([string]$Port = 'COM11')

function OpenPort([string]$name) {
  $s = New-Object System.IO.Ports.SerialPort $name,115200,None,8,'One'
  $s.ReadTimeout = 300
  $s.DtrEnable = $true
  $s.Open()
  Start-Sleep -Milliseconds 1500
  return $s
}

function Cmd($p, [string]$c) {
  Write-Output ("> " + $c)
  try { $p.Write($c + "`n") } catch { Write-Output ("  WRITE FAILED: " + $_); return }
  $acc = ''
  $sw = [Diagnostics.Stopwatch]::StartNew()
  while ($sw.ElapsedMilliseconds -lt 900) {
    if (-not $p.IsOpen) { break }
    try { $r = $p.ReadExisting() } catch { break }
    if ($r) { $acc += $r }
    Start-Sleep -Milliseconds 60
  }
  if ($acc) { ($acc -split "`r?`n") | Where-Object { $_ -ne '' } | ForEach-Object { Write-Output ("  " + $_) } }
}

$p = OpenPort $Port

Cmd $p 'GARBAGE'
Cmd $p 'PING'
Cmd $p 'ID'
Cmd $p 'GET'
Write-Output '--- set commands ---'
Cmd $p 'SET LED:255:0:80:255'
Cmd $p 'SET LED:2:255:120:0'
Cmd $p 'SET ENA:3:0'
Cmd $p 'SET PRESS:255:40:160'
Cmd $p 'SET BRIGHT:30:120'
Cmd $p 'SET FX:3:4:7:1:50'
Cmd $p 'SET KEY:6:99'
Write-Output '--- verify ---'
Cmd $p 'GET'
Write-Output '--- reboot to test eeprom persistence ---'
Cmd $p 'REBOOT'
Start-Sleep -Seconds 3
$p.Close()
Start-Sleep -Seconds 2

$p2 = OpenPort $Port
Write-Output '--- after reboot (expect previous values) ---'
Cmd $p2 'GET'
Write-Output '--- reset to defaults ---'
Cmd $p2 'RESET'
Cmd $p2 'GET'
$p2.Close()
Write-Output 'smoke test done'
