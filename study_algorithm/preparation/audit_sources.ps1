param(
    [string]$Root = (Split-Path -Parent $PSScriptRoot)
)
$ErrorActionPreference = 'Stop'
$Root = [IO.Path]::GetFullPath($Root).TrimEnd('\', '/')
$utf8 = New-Object System.Text.UTF8Encoding($false)
function Read-Json([string]$RelativePath) {
    $parsed = [IO.File]::ReadAllText((Join-Path $Root $RelativePath), $utf8) | ConvertFrom-Json
    return $parsed
}
function Relative-Path([string]$FullPath) {
    $FullPath.Substring($Root.Length + 1).Replace('\', '/')
}
function Seconds([string]$Timestamp) {
    $parts = $Timestamp.Replace(',', ':').Split(':')
    return ([int]$parts[0] * 3600 + [int]$parts[1] * 60 + [int]$parts[2] + [int]$parts[3] / 1000.0)
}
$issues = New-Object 'System.Collections.Generic.List[string]'
$notes = New-Object 'System.Collections.Generic.List[object]'
$manifest = @(Read-Json 'preparation/source_manifest.json')
$coverage = Read-Json 'preparation/source_coverage.json'
$operations = Read-Json 'preparation/operational_rules.json'
$blueprint = Read-Json 'preparation/learning_assistant_blueprint.json'
$oldResults = @(Read-Json 'src/YouTube_2020_Noryangjin_subtitles/results.json')
$seasonInventory = @(Read-Json 'src/YouTube_Study_Season3_subtitles/inventory.json')
$seasonPrevious = @(Read-Json 'src/YouTube_Study_Season3_subtitles/verification.json')
$additionalResults = @()
foreach ($support in $coverage.supporting_files) {
    if ($support.path.EndsWith('/results.json') -and $support.path -ne 'src/YouTube_2020_Noryangjin_subtitles/results.json') {
        $additionalResults += @(Read-Json $support.path)
    }
}
$physicalManifest = @(foreach ($entry in $manifest) {
    $entry
    foreach ($copy in $entry.copies) {
        [pscustomobject]@{id=$entry.id;path=$copy.path;lines=$copy.lines;sha256=$copy.sha256;is_copy=$true}
    }
})
$byId = @{}
$ruleIds = @($operations.rules | ForEach-Object { $_.id })
foreach ($entry in $manifest) {
    if ($byId.ContainsKey($entry.id)) { $issues.Add("Duplicate manifest ID: $($entry.id)") }
    $byId[$entry.id] = $entry
}
if (@($ruleIds | Select-Object -Unique).Count -ne $ruleIds.Count) { $issues.Add('Duplicate rule ID') }
$sourceIds = @($coverage.sources | ForEach-Object { $_.id })
if (@($sourceIds | Select-Object -Unique).Count -ne $sourceIds.Count) { $issues.Add('Duplicate coverage source ID') }
foreach ($id in $sourceIds) {
    if (-not $byId.ContainsKey($id)) { $issues.Add("Unknown coverage source: $id") }
}
foreach ($rule in $operations.rules) {
    foreach ($field in @('when', 'assistant_actions', 'deliverable', 'check_or_next', 'limits', 'evidence')) {
        if (-not $rule.$field) { $issues.Add("Missing rule field: $($rule.id).$field") }
    }
    foreach ($ref in $rule.evidence) {
        if ($ref -notmatch '^([A-Za-z0-9_-]{11}):(\d+)-(\d+)$') {
            $issues.Add("Malformed evidence: $ref")
            continue
        }
        $id = $Matches[1]; $first = [int]$Matches[2]; $last = [int]$Matches[3]
        if (-not $byId.ContainsKey($id) -or $first -lt 1 -or $last -lt $first -or $last -gt $byId[$id].lines) {
            $issues.Add("Invalid evidence range: $ref")
        }
    }
}
$reports = New-Object 'System.Collections.Generic.List[object]'
$expectedPaths = New-Object 'System.Collections.Generic.List[string]'
$headerPattern = '(?m)^[ \t]*(?<number>\d+)[ \t]*\n[ \t]*(?<start>\d{2}:\d{2}:\d{2},\d{3})[ \t]*-->[ \t]*(?<end>\d{2}:\d{2}:\d{2},\d{3})[^\n]*\n?'
foreach ($entry in $physicalManifest) {
    $localIssues = New-Object 'System.Collections.Generic.List[string]'
    $txtPath = Join-Path $Root $entry.path
    $srtRelative = [IO.Path]::ChangeExtension($entry.path, '.srt').Replace('\', '/')
    $srtPath = Join-Path $Root $srtRelative
    $expectedPaths.Add($entry.path)
    $expectedPaths.Add($srtRelative)
    if (-not (Test-Path -LiteralPath $txtPath) -or -not (Test-Path -LiteralPath $srtPath)) {
        $issues.Add("Missing transcript pair: $($entry.id)")
        continue
    }
    $txtLines = [IO.File]::ReadAllLines($txtPath, $utf8)
    $hash = (Get-FileHash -LiteralPath $txtPath -Algorithm SHA256).Hash
    if ($hash -ne $entry.sha256) { $localIssues.Add('TXT differs from previous manifest') }
    if ($txtLines.Count -ne $entry.lines) { $localIssues.Add('TXT line count differs from manifest') }
    $raw = [IO.File]::ReadAllText($srtPath, $utf8).Replace("`r`n", "`n").Replace("`r", "`n").TrimStart([char]0xFEFF)
    $headers = [regex]::Matches($raw, $headerPattern)
    $allTimestampCount = [regex]::Matches($raw, '(?m)^\s*\d{2}:\d{2}:\d{2},\d{3}\s*-->').Count
    if ($allTimestampCount -ne $headers.Count) { $localIssues.Add('Unparsed SRT timestamp or missing cue ID') }
    if ($headers.Count -eq 0) { $localIssues.Add('No SRT cues found') }
    $deduped = New-Object 'System.Collections.Generic.List[string]'
    $gaps = New-Object 'System.Collections.Generic.List[object]'
    $lastText = $null
    $previousEnd = $null
    $previousStart = -1.0
    for ($i = 0; $i -lt $headers.Count; $i++) {
        $h = $headers[$i]
        if ([int]$h.Groups['number'].Value -ne $i + 1) { $localIssues.Add("Broken cue sequence at $i") }
        $start = Seconds $h.Groups['start'].Value
        $end = Seconds $h.Groups['end'].Value
        if ($start -lt $previousStart -or $end -lt $start) { $localIssues.Add("Invalid timestamp order at $i") }
        if ($null -ne $previousEnd -and $start - $previousEnd -gt 0.001) {
            $gaps.Add([ordered]@{ after_cue=$i; seconds=[math]::Round($start-$previousEnd,3) })
        }
        $previousStart = $start
        $previousEnd = $end
        $bodyStart = $h.Index + $h.Length
        $bodyEnd = $raw.Length
        if ($i + 1 -lt $headers.Count) { $bodyEnd = $headers[$i + 1].Index }
        foreach ($line in ($raw.Substring($bodyStart, $bodyEnd-$bodyStart) -split "`n")) {
            $clean = [regex]::Replace($line, '<[^>]+>', '').Trim()
            if ($clean.Length -gt 0 -and $clean -cne $lastText) {
                $deduped.Add($clean)
                $lastText = $clean
            }
        }
    }
    $exact = $deduped.Count -eq $txtLines.Count
    if ($exact) {
        for ($i = 0; $i -lt $txtLines.Count; $i++) {
            if ($txtLines[$i] -cne $deduped[$i]) { $exact = $false; break }
        }
    }
    if (-not $exact) { $localIssues.Add('SRT-to-TXT sequential deduplication mismatch') }
    $replacement = ($txtLines -join '').Contains([string][char]0xFFFD)
    if ($replacement) { $localIssues.Add('Replacement character in TXT') }
    $mapped = @($coverage.sources | Where-Object id -EQ $entry.id)
    $segments = @()
    $kinds = @{}
    $expectedStart = 1
    if ($mapped.Count -ne 1) {
        $localIssues.Add('Expected one coverage entry')
    } else {
        $segments = @($mapped[0].segments)
        foreach ($segment in $segments) {
            if ($segment.start -ne $expectedStart -or $segment.end -lt $segment.start -or $segment.end -gt $txtLines.Count) {
                $localIssues.Add("Coverage gap, overlap or invalid range at $($segment.start)")
            }
            $expectedStart = $segment.end + 1
            if (-not $segment.topic -or -not $segment.treatment) { $localIssues.Add('Unexplained coverage segment') }
            if ($segment.kind -notin @('method','example','claim','context','mixed')) { $localIssues.Add('Unknown segment kind') }
            if ($segment.kind -ne 'context' -and @($segment.rule_ids).Count -eq 0) { $localIssues.Add('Missing operational mapping') }
            foreach ($ruleId in $segment.rule_ids) {
                if ($ruleId -notin $ruleIds) { $localIssues.Add("Unknown rule reference: $ruleId") }
            }
            if (-not $kinds.ContainsKey($segment.kind)) { $kinds[$segment.kind] = 0 }
            $kinds[$segment.kind] += $segment.end - $segment.start + 1
        }
        if ($expectedStart -ne $txtLines.Count + 1) { $localIssues.Add('Coverage does not reach final TXT line') }
    }
    $catalog = @($blueprint.source_catalog | Where-Object id -EQ $entry.id)
    if ($catalog.Count -ne 1 -or $catalog[0].lines -ne $txtLines.Count) { $localIssues.Add('Blueprint catalog mismatch') }
    $old = @($oldResults | Where-Object id -EQ $entry.id)
    if ($old.Count -eq 0) { $old = @($additionalResults | Where-Object id -EQ $entry.id) }
    $past = @($seasonPrevious | Where-Object id -EQ $entry.id)
    $duration = $null
    if ($old.Count -eq 1) {
        $duration = $old[0].duration
        if ($old[0].cues -ne $headers.Count) {
            $notes.Add([ordered]@{ id=$entry.id; field='old_results.cues'; previous=$old[0].cues; current=$headers.Count; treatment='Original collection record retained; current SRT recount is authoritative for this audit.' })
        }
        if ($old[0].lines -ne $txtLines.Count) { $localIssues.Add('Old results line count mismatch') }
    } elseif ($past.Count -eq 1) {
        $duration = $past[0].durationSeconds
        if ($past[0].srtCues -ne $headers.Count -or $past[0].txtLines -ne $txtLines.Count) { $localIssues.Add('Previous season verification count mismatch') }
    } else { $localIssues.Add('Missing duration metadata') }
    $startSeconds = $null; $endSeconds = $null; $endDifference = $null
    if ($headers.Count -gt 0) {
        $startSeconds = Seconds $headers[0].Groups['start'].Value
        $endSeconds = Seconds $headers[$headers.Count-1].Groups['end'].Value
        if ($null -ne $duration) { $endDifference = [math]::Round($duration-$endSeconds,3) }
    }
    foreach ($issue in $localIssues) { $issues.Add("$($entry.id): $issue") }
    $reports.Add([pscustomobject][ordered]@{
        id=$entry.id; path=$entry.path; txt_lines=$txtLines.Count; sha256=$hash
        matches_manifest=($hash -eq $entry.sha256); srt_cues=$headers.Count
        srt_txt_exact_match=$exact; caption_start_seconds=$startSeconds; caption_end_seconds=$endSeconds
        duration_seconds=$duration; end_difference_seconds=$endDifference
        internal_timestamp_gaps=@($gaps.ToArray()); replacement_character=$replacement
        coverage_segments=$segments.Count; covered_lines=($expectedStart-1); lines_by_kind=$kinds
        issues=@($localIssues.ToArray())
    })
}
$csvFiles = @(Get-ChildItem -LiteralPath (Join-Path $Root 'src/YouTube_2020_Noryangjin_subtitles') -File -Filter '*.csv')
if ($csvFiles.Count -ne 1) { $issues.Add('Expected one old source CSV') }
$csvIds = @()
if ($csvFiles.Count -eq 1) {
    $csvRows = @(Import-Csv -LiteralPath $csvFiles[0].FullName -Encoding UTF8)
    $csvIds = @($csvRows | ForEach-Object { if ($_.url -match '[?&]v=([^&]+)') { $Matches[1] } })
}
$oldIds = @($oldResults | ForEach-Object { $_.id })
$seasonIds = @($seasonInventory | ForEach-Object { $_.id })
$urlIds = @([IO.File]::ReadAllLines((Join-Path $Root 'src/YouTube_Study_Season3_subtitles/urls.txt'), $utf8) | ForEach-Object {
    if ($_ -match '[?&]v=([^&]+)') { $Matches[1] }
})
function Same-Ids($LeftIds, $RightIds) {
    return (($LeftIds | Sort-Object) -join '|') -ceq (($RightIds | Sort-Object) -join '|')
}
if (-not (Same-Ids $csvIds $oldIds)) { $issues.Add('Old CSV IDs mismatch') }
if (-not (Same-Ids $urlIds $seasonIds)) { $issues.Add('Season URLs mismatch') }
if (-not (Same-Ids (@(@($oldIds) + @($seasonIds) + @($additionalResults.id)) | Select-Object -Unique) @($manifest | ForEach-Object { $_.id }))) { $issues.Add('Inventory does not equal manifest') }
foreach ($support in $coverage.supporting_files) {
    if ($support.path.EndsWith('.csv') -and -not $support.path.StartsWith('src/YouTube_2020_Noryangjin_subtitles/')) {
        $rows = @(Import-Csv -LiteralPath (Join-Path $Root $support.path) -Encoding UTF8)
        $ids = @($rows | ForEach-Object { if ($_.url -match '[?&]v=([^&]+)') { $Matches[1] } })
        if (-not (Same-Ids $ids @($additionalResults.id))) { $issues.Add('Additional CSV IDs mismatch') }
    }
}
foreach ($support in $coverage.supporting_files) { $expectedPaths.Add($support.path) }
$examManifestPath = Join-Path $Root 'preparation/target_analysis/target_manifest.json'
$examPaths = @()
if (Test-Path -LiteralPath $examManifestPath) {
    $examManifest = Read-Json 'preparation/target_analysis/target_manifest.json'
    $examPaths = @($examManifest.documents | ForEach-Object { $_.path })
    foreach ($examPath in $examPaths) { $expectedPaths.Add($examPath) }
}
$files = @(Get-ChildItem -LiteralPath (Join-Path $Root 'src') -Recurse -File -Force | Sort-Object FullName)
$inventory = @($files | ForEach-Object {
    $relative = Relative-Path $_.FullName
    $role = 'supporting_record'
    if ($_.Extension -eq '.txt' -and $relative -in @($physicalManifest.path)) { $role = 'transcript' }
    elseif ($_.Extension -eq '.srt') { $role = 'timed_transcript' }
    elseif ($relative -in $examPaths) { $role = 'exam_material_separate_analysis' }
    [pscustomobject][ordered]@{ path=$relative; role=$role; bytes=$_.Length; sha256=(Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash; accounted=($relative -in $expectedPaths) }
})
foreach ($file in $inventory) { if (-not $file.accounted) { $issues.Add("Unaccounted source file: $($file.path)") } }
foreach ($expected in $expectedPaths) {
    if (-not (Test-Path -LiteralPath (Join-Path $Root $expected))) { $issues.Add("Missing expected source file: $expected") }
}
foreach ($state in $blueprint.preparation_audit.state_rule_mapping.PSObject.Properties) {
    foreach ($ruleId in $state.Value) {
        if ($ruleId -notin $ruleIds) { $issues.Add("Unknown blueprint rule: $ruleId") }
    }
}
$report = [ordered]@{
    checked_at=(Get-Date).ToString('o')
    status=$(if ($issues.Count -eq 0) { 'passed' } else { 'failed' })
    meaning='File integrity, source accounting and design-reference validation. This is not proof of exhaustive semantic understanding, ten full rereads, original video fidelity or learning efficacy.'
    counts=[ordered]@{
        src_files=$files.Count; transcript_files=$physicalManifest.Count; unique_videos=$manifest.Count
        txt_lines=($reports | Measure-Object txt_lines -Sum).Sum; unique_txt_lines=($manifest | Measure-Object lines -Sum).Sum
        srt_cues=($reports | Measure-Object srt_cues -Sum).Sum; supporting_files=@($coverage.supporting_files).Count
        coverage_segments=@($coverage.sources.segments).Count; operational_rules=$ruleIds.Count
        matching_transcript_hashes=@($reports | Where-Object matches_manifest -EQ $true).Count
        srt_txt_exact_matches=@($reports | Where-Object srt_txt_exact_match -EQ $true).Count
        unaccounted_src_files=@($inventory | Where-Object accounted -EQ $false).Count
        errors=$issues.Count; historical_metadata_differences=$notes.Count
    }
    sources=@($reports.ToArray()); file_inventory=$inventory
    historical_metadata_differences=@($notes.ToArray()); errors=@($issues.ToArray())
    retained_limits=@('Literal ten full rereads not completed.', 'Original video audio and diagrams not checked.', 'Scientific claims not independently validated.', 'Operational assistant is a design, not an implemented or efficacy-tested program.')
}
$outputPath = Join-Path $Root 'preparation/coverage_verification.json'
[IO.File]::WriteAllText($outputPath, ($report | ConvertTo-Json -Depth 30), $utf8)
$report.counts | ConvertTo-Json
Write-Output ("Status: " + $report.status)
if ($issues.Count -gt 0) { throw ($issues -join [Environment]::NewLine) }
