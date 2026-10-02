function Copy-VerifiedDesignSources([string]$ProjectRoot, [string]$RunDir) {
    $manifestPath = Join-Path $ProjectRoot 'source-manifest.json'
    $manifest = Get-Content -LiteralPath $manifestPath -Raw -Encoding UTF8 | ConvertFrom-Json
    foreach ($entry in $manifest.design_sources) {
        $source = Join-Path $ProjectRoot $entry.path
        if ((Get-FileHash -LiteralPath $source -Algorithm SHA256).Hash.ToLowerInvariant() -ne $entry.sha256) {
            throw "Source changed after IP audit: $source"
        }
        $destination = Join-Path $RunDir $entry.stage_name
        Copy-Item -LiteralPath $source -Destination $destination
        if ((Get-FileHash -LiteralPath $destination -Algorithm SHA256).Hash.ToLowerInvariant() -ne $entry.sha256) {
            throw "Staged source differs: $destination"
        }
    }
    $xciSource = Join-Path $ProjectRoot $manifest.xci.path
    if ((Get-FileHash -LiteralPath $xciSource -Algorithm SHA256).Hash.ToLowerInvariant() -ne $manifest.xci.sha256) {
        throw 'XCI changed after parameter audit.'
    }
    Copy-Item -LiteralPath $xciSource -Destination (Join-Path $RunDir 'led_state_concat.xci')
    Copy-Item -LiteralPath $manifestPath -Destination (Join-Path $RunDir 'source-manifest.json')
}
