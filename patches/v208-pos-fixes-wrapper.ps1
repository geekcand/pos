param([Parameter(Mandatory=$true)][string]$SourceRoot)
$ErrorActionPreference = 'Stop'

# Normalize the patch script and source files to the same CRLF line endings before
# running the exact-block patch. GitHub artifacts preserve LF while Windows checkout
# may use CRLF, which caused the first v2.0.8 run to stop before applying the C# block.
$patch = Join-Path $PSScriptRoot 'v208-pos-fixes.ps1'
$utf8NoBom = [System.Text.UTF8Encoding]::new($false)

function To-Crlf([string]$text) {
    return $text.Replace("`r`n", "`n").Replace("`r", "`n").Replace("`n", "`r`n")
}

$patchText = To-Crlf (Get-Content -LiteralPath $patch -Raw)
[System.IO.File]::WriteAllText($patch, $patchText, $utf8NoBom)

foreach ($relative in @('Pages\PosPage.xaml','Pages\PosPage.xaml.cs','SweetsPOS.csproj','installer.iss')) {
    $file = Join-Path $SourceRoot $relative
    if (!(Test-Path -LiteralPath $file)) { throw "Missing source file: $file" }
    $text = To-Crlf (Get-Content -LiteralPath $file -Raw)
    [System.IO.File]::WriteAllText($file, $text, $utf8NoBom)
}

& $patch -SourceRoot $SourceRoot
