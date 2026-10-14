param([string]$Root = (Split-Path -Parent $PSScriptRoot))
$ErrorActionPreference = 'Stop'
$Root = [IO.Path]::GetFullPath($Root)
$utf8 = New-Object System.Text.UTF8Encoding($false)
function Read-Json([string]$Path) {
    $v = [IO.File]::ReadAllText((Join-Path $Root $Path), $utf8) | ConvertFrom-Json
    return $v
}
function Save-Json([string]$Path, $Value) {
    [IO.File]::WriteAllText((Join-Path $Root $Path), (ConvertTo-Json -InputObject $Value -Depth 50), $utf8)
}
function Put($Obj, [string]$Key, $Value) {
    $Obj | Add-Member -MemberType NoteProperty -Name $Key -Value $Value -Force
}
$manifest = @(Read-Json 'preparation/source_manifest.json')
$coverage = Read-Json 'preparation/source_coverage.json'
$operations = Read-Json 'preparation/operational_rules.json'
$blueprint = Read-Json 'preparation/learning_assistant_blueprint.json'
$review = Read-Json 'preparation/additional_source_review.json'
$update = Read-Json 'preparation/source_audit_update.json'
$sourceRoot = Join-Path $Root 'src'
$third = @(Get-ChildItem -LiteralPath $sourceRoot -Directory -Force | Where-Object { $_.Name -like 'YouTube_*' -and $_.Name -notin @('YouTube_2020_Noryangjin_subtitles','YouTube_Study_Season3_subtitles') })
if ($third.Count -ne 1) { throw 'Expected exactly one additional YouTube source directory.' }
$thirdDir = $third[0]
$thirdPrefix = 'src/' + $thirdDir.Name + '/'
$results = @(Read-Json ($thirdPrefix + 'results.json'))
$transcriptFiles = @(Get-ChildItem -LiteralPath $thirdDir.FullName -File -Force -Filter '*.txt')
foreach ($entry in $results) {
    if ($entry.status -ne 'ok') { throw "Unresolved source collection status: $($entry.id)" }
    $matches = @($transcriptFiles | Where-Object { $_.Name.Contains($entry.id) })
    if ($matches.Count -ne 1) { throw "Expected one TXT for $($entry.id)" }
    $file = $matches[0]
    $record = [pscustomobject][ordered]@{
        id=$entry.id; path=($thirdPrefix + $file.Name)
        lines=[IO.File]::ReadAllLines($file.FullName, $utf8).Count
        sha256=(Get-FileHash -LiteralPath $file.FullName -Algorithm SHA256).Hash
    }
    $existing = @($manifest | Where-Object id -EQ $entry.id)
    if ($existing.Count -eq 1) {
        if ($existing[0].sha256 -ne $record.sha256) { throw "Same video has different TXT; review required: $($entry.id)" }
        if ($existing[0].path -ne $record.path) {
            Put $existing[0] 'copies' @([pscustomobject]@{path=$record.path;lines=$record.lines;sha256=$record.sha256})
        }
    } else {
        $read = @($review.sources | Where-Object id -EQ $entry.id)
        if ($read.Count -ne 1 -or -not $read[0].read_complete -or $read[0].lines -ne $record.lines) {
            throw "Missing full-text reading record: $($entry.id)"
        }
        $manifest += $record
    }
}
foreach ($source in $review.sources) {
    if ($source.id -notin @($coverage.sources.id)) {
        $start = 1
        $segments = foreach ($s in $source.segments) {
            [pscustomobject][ordered]@{
                start=$start;end=[int]$s[0];kind=$s[1];topic=$s[2]
                rule_ids=@($s[3]);treatment=$source.notes
            }
            $start = [int]$s[0] + 1
        }
        if ($start -ne $source.lines + 1) { throw "Incomplete semantic coverage: $($source.id)" }
        $coverage.sources += [pscustomobject]@{id=$source.id;segments=@($segments)}
    }
    if ($source.id -notin @($blueprint.source_catalog.id)) {
        $metadata = $results | Where-Object id -EQ $source.id
        $blueprint.source_catalog += [pscustomobject][ordered]@{
            id=$source.id;series=$thirdDir.Name;episode=$metadata.index;title=$metadata.title
            lines=$source.lines;reading='Full text read in this audit'
            meaning=(@($source.segments | ForEach-Object { $_[2] }) -join ' / ')
            interpretation_limits=$source.notes
        }
    }
}
foreach ($r in $update.new_rules) {
    if ($r.id -notin @($operations.rules.id)) { $operations.rules += $r }
}
foreach ($change in $update.enhancements) {
    $r = $operations.rules | Where-Object id -EQ $change.id
    if ($change.text -notin @($r.($change.field))) { $r.($change.field) = @($r.($change.field)) + $change.text }
}
foreach ($prop in $update.new_evidence_for_existing_rules.PSObject.Properties) {
    $r = $operations.rules | Where-Object id -EQ $prop.Name
    foreach ($ref in $prop.Value) { if ($ref -notin @($r.evidence)) { $r.evidence += $ref } }
}
$operations.version = $update.version
Put $operations 'additional_dispatch' @(
    'Use R26 for actual title-question-answer reconstruction and R27 for verified memory cues.',
    'Use R28 to keep source material, notes and assistant-generated cards linked.',
    'Use R29 for general-principle versus concrete-case reasoning.',
    'Use R30 only when timed multiple-choice performance is a goal.',
    'Use R31 to choose reading stages, manageable units and return paths.'
)
foreach ($file in @(Get-ChildItem -LiteralPath $thirdDir.FullName -File -Force | Where-Object { $_.Extension -in @('.json','.csv') })) {
    $relative = $thirdPrefix + $file.Name
    if ($relative -notin @($coverage.supporting_files.path)) {
        $coverage.supporting_files += [pscustomobject]@{
            path=$relative;purpose='Additional source collection inventory'
            treatment='Compare IDs, filenames, line counts and collection status against current transcript files.'
        }
    }
}
$uniqueLines = ($manifest | Measure-Object lines -Sum).Sum
$copyRecords = @($manifest | ForEach-Object { if ($_.copies) { $_.copies } })
$copyLines = ($copyRecords | Measure-Object lines -Sum).Sum
$segmentCount = @($coverage.sources.segments).Count
$physicalCount = $manifest.Count + $copyRecords.Count
$summary = "Three source groups; $physicalCount transcript files; $($manifest.Count) unique videos; $uniqueLines unique TXT lines; $($uniqueLines+$copyLines) physical TXT lines; $segmentCount semantic segments; $(@($operations.rules).Count) operational rules."
$coverage.version = $update.version
$coverage.scope = $summary
Put $coverage 'audit_correction' $update.correction
Put $coverage 'duplicate_policy' 'Identical duplicate TXT uses the same semantic coverage and reading record. Both physical TXT/SRT copies are validated.'
Put $coverage 'source_groups' @(
    [pscustomobject]@{directory='src/YouTube_2020_Noryangjin_subtitles';transcript_files=6},
    [pscustomobject]@{directory='src/YouTube_Study_Season3_subtitles';transcript_files=10},
    [pscustomobject]@{directory=('src/'+$thirdDir.Name);transcript_files=$results.Count}
)
$blueprint.version = $update.version
$blueprint.preparation_audit.before = $update.correction
$blueprint.preparation_audit.after = $summary
$blueprint.preparation_audit.reading_boundary = 'All 41 unique transcript texts have been read across the previous work and this audit. This does not mean ten complete rereads. Original video diagrams/audio and scientific claims have not been independently verified.'
Put $blueprint.preparation_audit 'full_source_correction' $update.correction
Put $blueprint.preparation_audit.artifacts 'additional_reading' 'preparation/additional_source_review.json'
Put $blueprint.preparation_audit.artifacts 'audit_update' 'preparation/source_audit_update.json'
Put $blueprint 'additional_source_tensions' $update.conflicts
$blueprint.review_provenance.corpus = ($coverage.source_groups.directory -join ' + ')
$blueprint.review_provenance.transcripts = $manifest.Count
$blueprint.review_provenance.lines = $uniqueLines
$blueprint.review_provenance.current_work = $update.correction
Put $blueprint.review_provenance 'ten_review_lenses_scope' 'The original ten thematic review lenses covered the first 16 videos. They are not ten exhaustive rereads of either the old corpus or the expanded 41-video corpus.'
Put $blueprint.review_provenance 'physical_transcript_files' $physicalCount
Put $blueprint.review_provenance 'additional_full_text_read' @($review.sources.id)
Put $blueprint.review_provenance 'duplicate_copies' $copyRecords
$links = @{
    orient=@('R26');prerequisite=@('R31');explain=@('R26','R27','R29','R31')
    check_understanding=@('R26','R29');repair=@('R26','R31');memory=@('R27','R28')
    guided_application=@('R29');independent_application=@('R29');training=@('R30')
    wrap_up=@('R28','R31');planning_when_needed=@('R31')
}
foreach ($key in $links.Keys) {
    $blueprint.preparation_audit.state_rule_mapping.$key = @(@($blueprint.preparation_audit.state_rule_mapping.$key) + @($links[$key]) | Select-Object -Unique)
}
Put $blueprint.implementation_readiness 'three_source_audit' $summary
$review.status = 'integrated_into_blueprint_rules_and_coverage'
Save-Json 'preparation/source_manifest.json' @($manifest)
Save-Json 'preparation/source_coverage.json' $coverage
Save-Json 'preparation/operational_rules.json' $operations
Save-Json 'preparation/learning_assistant_blueprint.json' $blueprint
Save-Json 'preparation/additional_source_review.json' $review
Write-Output $summary

