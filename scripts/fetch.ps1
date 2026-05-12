$ProgressPreference = 'SilentlyContinue'
$ErrorActionPreference = 'Stop'

$startDate = [DateTime]::Parse('2026-04-12T00:00:00Z').ToUniversalTime()
$endDate   = [DateTime]::Parse('2026-05-12T23:59:59Z').ToUniversalTime()

$outDir = Join-Path $PSScriptRoot '..\output\20260512'
$outDir = (Resolve-Path $outDir -ErrorAction SilentlyContinue).Path
if (-not $outDir) {
    $outDir = Join-Path (Split-Path $PSScriptRoot -Parent) 'output\20260512'
    New-Item -ItemType Directory -Path $outDir -Force | Out-Null
}
$outFile = Join-Path $outDir 'updates.json'

function Convert-HtmlToPlainText {
    param([string]$Html)
    if ([string]::IsNullOrWhiteSpace($Html)) { return '' }
    $text = $Html
    $text = [regex]::Replace($text, '(?is)<(script|style).*?>.*?</\1>', '')
    $text = [regex]::Replace($text, '(?i)<br\s*/?>', "`n")
    $text = [regex]::Replace($text, '(?i)</p>', "`n`n")
    $text = [regex]::Replace($text, '(?i)</li>', "`n")
    $text = [regex]::Replace($text, '<[^>]+>', '')
    $text = [System.Net.WebUtility]::HtmlDecode($text)
    $text = [regex]::Replace($text, '[ \t]+', ' ')
    $text = [regex]::Replace($text, '\r\n?', "`n")
    $text = [regex]::Replace($text, '\n{3,}', "`n`n")
    return $text.Trim()
}

function Parse-CreatedDate {
    param([string]$s)
    if ([string]::IsNullOrWhiteSpace($s)) { return $null }
    $formats = @('MM/dd/yyyy HH:mm:ss','M/d/yyyy H:mm:ss','yyyy-MM-ddTHH:mm:ssZ','yyyy-MM-ddTHH:mm:ss')
    foreach ($f in $formats) {
        try {
            return [DateTime]::ParseExact($s, $f, [System.Globalization.CultureInfo]::InvariantCulture, [System.Globalization.DateTimeStyles]::AssumeUniversal -bor [System.Globalization.DateTimeStyles]::AdjustToUniversal)
        } catch {}
    }
    try { return [DateTime]::Parse($s, [System.Globalization.CultureInfo]::InvariantCulture).ToUniversalTime() } catch { return $null }
}

$all = New-Object System.Collections.Generic.List[object]
$skip = 0
$top = 100
$reachedOlder = $false

while (-not $reachedOlder) {
    $url = "https://www.microsoft.com/releasecommunications/api/v2/azure?`$top=$top&`$skip=$skip&`$orderby=created desc"
    Write-Host "Fetching skip=$skip top=$top ..."
    $resp = Invoke-RestMethod -Uri $url -Method Get -Headers @{ 'Accept' = 'application/json' }
    if (-not $resp.value -or $resp.value.Count -eq 0) { break }
    foreach ($item in $resp.value) {
        $d = Parse-CreatedDate $item.created
        if ($null -eq $d) { continue }
        if ($d -lt $startDate) { $reachedOlder = $true; continue }
        if ($d -gt $endDate) { continue }
        $all.Add([PSCustomObject]@{
            id                                = [string]$item.id
            title                             = $item.title
            description                       = Convert-HtmlToPlainText $item.description
            status                            = $item.status
            created                           = $item.created
            modified                          = $item.modified
            productCategories                 = $item.productCategories
            tags                              = $item.tags
            products                          = $item.products
            generalAvailabilityDate           = $item.generalAvailabilityDate
            previewAvailabilityDate           = $item.previewAvailabilityDate
            privatePreviewAvailabilityDate    = $item.privatePreviewAvailabilityDate
            availabilities                    = $item.availabilities
        }) | Out-Null
    }
    if ($resp.value.Count -lt $top) { break }
    $skip += $top
    if ($skip -gt 5000) { break }
}

$json = $all | ConvertTo-Json -Depth 10
[System.IO.File]::WriteAllText($outFile, $json, [System.Text.UTF8Encoding]::new($false))

$dates = $all | ForEach-Object { Parse-CreatedDate $_.created } | Where-Object { $_ -ne $null }
$minD = ($dates | Measure-Object -Minimum).Minimum
$maxD = ($dates | Measure-Object -Maximum).Maximum

Write-Host "----"
Write-Host "COUNT=$($all.Count)"
Write-Host "MIN_CREATED=$($minD.ToString('o'))"
Write-Host "MAX_CREATED=$($maxD.ToString('o'))"
Write-Host "OUT_FILE=$outFile"
