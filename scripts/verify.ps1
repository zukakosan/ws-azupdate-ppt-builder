$f = "C:\Users\koishizu\Documents\github\ws-azupdate-catcher\output\20260512\updates.json"
$data = Get-Content $f -Raw | ConvertFrom-Json
Write-Host "Items: $($data.Count)"
Write-Host "File size: $((Get-Item $f).Length) bytes"
Write-Host "Sample title: $($data[0].title)"
Write-Host "Sample id: $($data[0].id)"
$desc = $data[0].description
$len = [Math]::Min(150, $desc.Length)
Write-Host "Sample desc: $($desc.Substring(0, $len))"
