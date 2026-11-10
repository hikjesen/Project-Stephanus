param()
$ErrorActionPreference = 'Stop'
$projectRoot = [IO.Path]::GetFullPath((Split-Path -Parent $PSScriptRoot))
$stageRoot = Join-Path $projectRoot 'data\runtime-candidate'
$reportRoot = Join-Path $projectRoot 'data\reports'
$acceptancePath = Join-Path $reportRoot 'compact-acceptance.json'
$cleanupPath = Join-Path $reportRoot 'compact-cleanup.json'
if (Test-Path -LiteralPath $cleanupPath) { throw 'Cleanup has already been recorded. Do not repeat it.' }
$acceptance = Get-Content -LiteralPath $acceptancePath -Raw | ConvertFrom-Json
if (-not $acceptance.passed) { throw 'Single acceptance did not pass. Preserve the old database and raw files.' }
$runtimeSize = Get-Content -LiteralPath (Join-Path $stageRoot 'runtime-size.json') -Raw | ConvertFrom-Json
if (-not $runtimeSize.within_budget) { throw 'Runtime exceeds the 500 MiB budget.' }

function Resolve-WorkspaceTarget([string]$path) {
    $absolute = [IO.Path]::GetFullPath($path)
    $prefix = $projectRoot.TrimEnd('\') + '\'
    if (-not $absolute.StartsWith($prefix, [StringComparison]::OrdinalIgnoreCase)) {
        throw "Filesystem target must stay inside the project: $absolute"
    }
    return $absolute
}
function Measure-Tree([string]$path) {
    if (-not (Test-Path -LiteralPath $path)) { return [long]0 }
    $item = Get-Item -LiteralPath $path -Force
    if (-not $item.PSIsContainer) { return [long]$item.Length }
    $sum = (Get-ChildItem -LiteralPath $path -Recurse -Force -File | Measure-Object -Property Length -Sum).Sum
    return [long]$sum
}
$deleted = [Collections.Generic.List[object]]::new()
function Remove-Original([string]$path) {
    $absolute = Resolve-WorkspaceTarget $path
    if (Test-Path -LiteralPath $absolute) {
        $bytes = Measure-Tree $absolute
        Remove-Item -LiteralPath $absolute -Recurse -Force
        $deleted.Add([ordered]@{ path = $absolute.Substring($projectRoot.Length + 1); bytes = $bytes })
    }
}
function Move-Inside([string]$from, [string]$to) {
    $source = Resolve-WorkspaceTarget $from
    $target = Resolve-WorkspaceTarget $to
    Move-Item -LiteralPath $source -Destination $target
}

# All candidate files were exercised from this independent resource root.
# Replacements use native PowerShell operations and explicit verified paths.
Remove-Original (Join-Path $projectRoot 'vendor')
Move-Inside (Join-Path $stageRoot 'vendor') (Join-Path $projectRoot 'vendor')
Remove-Original (Join-Path $projectRoot 'data\raw')
Move-Inside (Join-Path $stageRoot 'data\raw') (Join-Path $projectRoot 'data\raw')
Move-Inside (Join-Path $stageRoot 'data\source-notices') (Join-Path $projectRoot 'data\source-notices')
foreach ($suffix in @('-wal', '-shm', '')) {
    Remove-Original (Join-Path $projectRoot ('data\stephanus.sqlite' + $suffix))
}
Move-Inside (Join-Path $stageRoot 'data\stephanus.sqlite') (Join-Path $projectRoot 'data\stephanus.sqlite')
Move-Inside (Join-Path $stageRoot 'data\compact-build.json') (Join-Path $reportRoot 'compact-build.json')
Move-Inside (Join-Path $stageRoot 'runtime-size.json') (Join-Path $reportRoot 'compact-runtime-size.json')

$manifestPath = Join-Path $projectRoot 'resources.json'
$manifest = Get-Content -LiteralPath $manifestPath -Raw | ConvertFrom-Json
foreach ($resource in $manifest) {
    $localPath = Resolve-WorkspaceTarget (Join-Path $projectRoot $resource.local_path)
    if ($resource.group -in @('sources', 'data')) {
        $state = if (Test-Path -LiteralPath $localPath) {
            if ($resource.method -eq 'git') { 'runtime_subset' } else { 'present' }
        } else { 'pruned' }
        $resource | Add-Member -NotePropertyName storage_state -NotePropertyValue $state -Force
        $resource | Add-Member -NotePropertyName storage_policy -NotePropertyValue 'compact-v1' -Force
    }
}
$manifest | ConvertTo-Json -Depth 100 | Set-Content -LiteralPath $manifestPath -Encoding utf8NoBOM

# Candidate leftovers are transient copies, not part of the reported original-file deletion.
$checkedStage = Resolve-WorkspaceTarget $stageRoot
Remove-Item -LiteralPath $checkedStage -Recurse -Force
$baseline = Get-Content -LiteralPath (Join-Path $projectRoot 'storage-usage.local.json') -Raw | ConvertFrom-Json
$finalFiles = @(Get-ChildItem -LiteralPath $projectRoot -Recurse -Force -File)
$workspaceBytes = [long](($finalFiles | Measure-Object -Property Length -Sum).Sum)
$runtimePrefixes = @('data\stephanus.sqlite', 'data\raw\', 'data\source-notices\', 'data\references\', 'vendor\')
$runtimeFiles = @($finalFiles | Where-Object {
    $relative = $_.FullName.Substring($projectRoot.Length + 1)
    $include = $relative -in @('resources.json', 'targets.json', 'data-policy.json')
    foreach ($prefix in $runtimePrefixes) {
        if ($relative.StartsWith($prefix, [StringComparison]::OrdinalIgnoreCase)) { $include = $true }
    }
    $include
})
$installedRuntimeBytes = [long](($runtimeFiles | Measure-Object -Property Length -Sum).Sum)
$removedOriginalBytes = [long]0
foreach ($record in $deleted) { $removedOriginalBytes += [long]$record['bytes'] }
$report = [ordered]@{
    completed_at = [DateTime]::UtcNow.ToString('o')
    policy = 'compact-v1'
    runtime_bytes = $installedRuntimeBytes
    candidate_budget_measurement_bytes = [long]$runtimeSize.runtime_bytes
    runtime_budget_bytes = [long]$runtimeSize.budget_bytes
    baseline_snapshot_bytes = [long]$baseline.total_bytes
    final_workspace_bytes = $workspaceBytes
    net_reduction_from_baseline_bytes = [long]$baseline.total_bytes - $workspaceBytes
    removed_original_files_bytes = $removedOriginalBytes
    removed_originals = $deleted.ToArray()
    transient_copies_counted_as_savings = $false
    acceptance_report = 'data/reports/compact-acceptance.json'
    basis = 'Logical file lengths; workspace total includes Python environment and project Git. Final report itself and later documentation add a small amount.'
}
$report | ConvertTo-Json -Depth 100 | Set-Content -LiteralPath $cleanupPath -Encoding utf8NoBOM
$runtimeMiB = [Math]::Round($report.runtime_bytes / 1MB, 2)
$savedGiB = [Math]::Round($report.net_reduction_from_baseline_bytes / 1GB, 3)
Write-Output "Installed runtime: $runtimeMiB MiB; net reduction from baseline: $savedGiB GiB"
