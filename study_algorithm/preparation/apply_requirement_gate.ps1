$ErrorActionPreference = 'Stop'
$base = $PSScriptRoot
$blueprintPath = Join-Path $base 'learning_assistant_blueprint.json'
$rulesPath = Join-Path $base 'operational_rules.json'
$blueprint = Get-Content -LiteralPath $blueprintPath -Raw -Encoding UTF8 | ConvertFrom-Json
$rules = Get-Content -LiteralPath $rulesPath -Raw -Encoding UTF8 | ConvertFrom-Json
$contract = Get-Content -LiteralPath (Join-Path $base 'exam_requirement_contract.json') -Raw -Encoding UTF8 | ConvertFrom-Json
$gate = [pscustomobject]@{
    state = 'calibrate_requirements'
    assistant_does = 'When an exam goal exists, establish its evidence-backed demand profile before choosing explanation depth, memory scope or assessment. Use exam_requirement_contract.json. Reuse known context; mark unsupported requirements provisional.'
    next = 'orient; missing evidence permits provisional teaching but never unsupported scope exclusion or exam-readiness claims.'
}
$gate | Add-Member -NotePropertyName status -NotePropertyValue $contract.status -Force
if (-not $contract.activation.enabled) {
    $gate.assistant_does = $contract.activation.while_deferred
    $gate.next = 'orient with provisional concept teaching. Do not collect or analyze exam papers, or finalize exam requirements, while the user-requested deferral remains active.'
}
$blueprint.version = '0.4-exam-requirements-deferred'
if ($contract.activation.enabled) { $blueprint.version = '0.4-exam-requirements-under-analysis' }
$blueprint | Add-Member -NotePropertyName exam_requirement_contract -NotePropertyValue 'exam_requirement_contract.json' -Force
$blueprint | Add-Member -NotePropertyName exam_requirement_activation -NotePropertyValue $contract.activation -Force
$blueprint.teaching_loop = @($gate) + @($blueprint.teaching_loop | Where-Object { $_.state -ne 'calibrate_requirements' })
$blueprint.intake | Add-Member -NotePropertyName exam_goal_policy -NotePropertyValue $contract.activation -Force
$blueprint.concept_record.fields = @($blueprint.concept_record.fields | Where-Object { $_ -ne 'exam_requirement_profile' }) + @('exam_requirement_profile')
$blueprint.mastery_evidence | Add-Member -NotePropertyName goal_alignment -NotePropertyValue $contract.completion_and_revision.criterion -Force
$blueprint.preparation_audit.state_rule_mapping | Add-Member -NotePropertyName calibrate_requirements -NotePropertyValue @('R01', 'R04', 'R02') -Force
$blueprint.preparation_audit.artifacts | Add-Member -NotePropertyName exam_requirements -NotePropertyValue 'preparation/exam_requirement_contract.json' -Force
$blueprint.preparation_audit.artifacts | Add-Member -NotePropertyName full_reread -NotePropertyValue 'preparation/full_reread_01.json' -Force
$blueprint | Add-Member -NotePropertyName stage_selection -NotePropertyValue $contract.stage_selection -Force
foreach ($stage in $blueprint.teaching_loop) {
    $binding = $contract.stage_bindings.PSObject.Properties[$stage.state]
    if ($null -ne $binding) {
        $stage | Add-Member -NotePropertyName requirement_binding -NotePropertyValue ([pscustomobject]@{enabled=$contract.activation.enabled; draft=$binding.Value}) -Force
    }
}
$blueprint.implementation_readiness | Add-Member -NotePropertyName exam_requirements_prepared -NotePropertyValue @('Evidence-backed demand profile before lesson design', 'Explanation, memory, practice and completion bound to the profile', 'Combined demands, provisional evidence and scope guards', 'Worked example under three assumed exam demands') -Force
$blueprint.implementation_readiness.next_build_unit = 'Current: concept -> learner state -> actual explanation and examples -> short understanding check -> targeted repair -> memory/application. Exam-specific calibration is deferred by user until past-paper analysis resumes.'
if ($contract.activation.enabled) {
    $blueprint.implementation_readiness.next_build_unit = 'Analyze all supplied exam questions by chapter -> evidence-backed requirements -> learner state -> explanation/examples -> check/repair -> memory/application. Unconfirmed exam demands remain unknown.'
}
$rules.version = $blueprint.version
$rules.dispatch_protocol[0] = 'FIRST: R01 identifies the goal. For exam goals, R04 gathers demand evidence and R02 calibrates the requirement profile using exam_requirement_contract.json BEFORE explanation depth, memory scope and completion criteria are chosen.'
if (-not $contract.activation.enabled) {
    $rules.dispatch_protocol[0] = 'R01 records the known exam goal. Exam-specific R04 evidence collection and R02 calibration are DEFERRED by user; see exam_requirement_contract.json activation. Continue concept teaching with exam requirements unknown. Do not infer exam scope, memory volume or readiness.'
}
$r02 = $rules.rules | Where-Object { $_.id -eq 'R02' }
$r02.when = $contract.priority
$r02 | Add-Member -NotePropertyName activation -NotePropertyValue $contract.activation -Force
$r02 | Add-Member -NotePropertyName requirement_contract -NotePropertyValue 'exam_requirement_contract.json' -Force
$r02 | Add-Member -NotePropertyName profile_schema -NotePropertyValue $contract.requirement_profile -Force
$r02 | Add-Member -NotePropertyName routing -NotePropertyValue $contract.routing -Force
$r02 | Add-Member -NotePropertyName routing_policy -NotePropertyValue $contract.routing_policy -Force
$r04 = $rules.rules | Where-Object { $_.id -eq 'R04' }
$r04 | Add-Member -NotePropertyName exam_analysis_activation -NotePropertyValue $contract.activation -Force
$r04 | Add-Member -NotePropertyName scope_guard -NotePropertyValue $contract.requirement_profile.scope_guard -Force
$r24 = $rules.rules | Where-Object { $_.id -eq 'R24' }
$r24 | Add-Member -NotePropertyName calibrated_delivery -NotePropertyValue $contract.lesson_delivery -Force
$r14 = $rules.rules | Where-Object { $_.id -eq 'R14' }
$r14 | Add-Member -NotePropertyName depth_guard -NotePropertyValue $contract.lesson_delivery.understanding_floor -Force
$r14.deliverable = 'Worked steps with reasons and targeted checks; formula derivation when required by the exam or needed to understand the method. Optional extensions are separate.'
$rules.lesson_packet_contract | Add-Member -NotePropertyName exam_requirement_profile -NotePropertyValue 'Unknown while exam analysis is deferred by the user. The draft schema is for future past-paper analysis; no exam-specific scope, memory volume or readiness may be finalized now.' -Force
if ($contract.activation.enabled) {
    $rules.lesson_packet_contract.exam_requirement_profile = 'Use reviewed question evidence from target_analysis. Separate textbook drills, mock questions and authenticated past papers. Unknown requirements remain unknown; material frequency is not actual exam probability.'
}
$blueprint | ConvertTo-Json -Depth 60 | Set-Content -LiteralPath $blueprintPath -Encoding UTF8
$rules | ConvertTo-Json -Depth 60 | Set-Content -LiteralPath $rulesPath -Encoding UTF8
Write-Output ('Exam requirement state: ' + $contract.status)
