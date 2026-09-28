param([switch]$NoRestore)
$ErrorActionPreference = 'Stop'
$project = Join-Path $PSScriptRoot 'SweetsPOS.csproj'
$appOutput = Join-Path $PSScriptRoot 'artifacts\final-win-x64'
$publishArgs = @('publish', $project, '-c', 'Release', '-r', 'win-x64', '--self-contained', 'true', '-p:Platform=x64', '-p:WindowsAppSDKSelfContained=true', '-o', $appOutput)
if ($NoRestore) { $publishArgs += '--no-restore' }
& dotnet @publishArgs
if ($LASTEXITCODE -ne 0) { throw "Publish failed: $LASTEXITCODE" }
Copy-Item (Join-Path $appOutput 'SweetsPOS.exe') (Join-Path $appOutput 'App.exe') -Force
# App-local Microsoft Visual C++ runtime: no elevation or runtime installation needed.
$runtimeFiles = @('vcruntime140.dll','vcruntime140_1.dll','msvcp140.dll','msvcp140_1.dll','msvcp140_2.dll','msvcp140_atomic_wait.dll','msvcp140_codecvt_ids.dll','concrt140.dll')
foreach ($name in $runtimeFiles) {
    $source = Join-Path $env:WINDIR "System32\$name"
    if (!(Test-Path -LiteralPath $source)) { throw "Missing x64 VC++ runtime: $source. Install Microsoft VC++ x64 redistributable before building." }
    Copy-Item -LiteralPath $source -Destination $appOutput -Force
}
$iscc = "${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe"
if (!(Test-Path -LiteralPath $iscc)) {
    $iscc = (Get-Command ISCC.exe -ErrorAction Stop).Source
}
& $iscc (Join-Path $PSScriptRoot 'installer.iss')
if ($LASTEXITCODE -ne 0) { throw "Setup compilation failed: $LASTEXITCODE" }
Write-Host "Setup ready: $PSScriptRoot\artifacts\installer-fixed\SweetsPOS-Setup-x64.exe"

