param([Parameter(Mandatory=$true)][string]$Directory)
$ErrorActionPreference='Stop'
$guideRoot=(Resolve-Path -LiteralPath $Directory).Path
$guidePhases=@(
    '双脚与肩同宽，双臂略微离开身体，自然站立。',
    '缓慢将双臂侧平举，保持T字形。',
    '左臂保持侧平举，右臂自然放下。',
    '右臂侧平举，左臂自然放下。',
    '双肘弯曲，双手放在肩旁，不要挡住脸。',
    '双臂略微张开，向左移动小半步，然后站稳。',
    '向右移动小半步，回到中间，然后站稳。',
    '缓慢将双臂侧平举，保持T字形。',
    '双肘弯曲，双手放在肩旁，不要挡住脸。',
    '双臂略微离开身体，自然站立。'
)
$guideVoice=$null;$guideComplete=$false;$guideError=$null
$guideEvents=[System.IO.StreamWriter]::new((Join-Path $guideRoot 'protocol-events.jsonl'),$false,[System.Text.UTF8Encoding]::new($false))
function Write-GuideEvent($guideValue){$guideEvents.WriteLine(($guideValue|ConvertTo-Json -Compress -Depth 8));$guideEvents.Flush()}
try {
    Add-Type -AssemblyName System.Speech
    $guideVoice=[System.Speech.Synthesis.SpeechSynthesizer]::new()
    $guideVoice.SelectVoiceByHints([System.Speech.Synthesis.VoiceGender]::NotSet,[System.Speech.Synthesis.VoiceAge]::NotSet,0,[System.Globalization.CultureInfo]::GetCultureInfo('zh-CN'))
    $guideVoice.Rate=0;$guideVoice.Volume=100
    $guideDeadline=[System.Diagnostics.Stopwatch]::StartNew()
    $guideSeen=$false
    while($guideDeadline.Elapsed.TotalSeconds -lt 25 -and !$guideSeen){
        if(Test-Path -LiteralPath (Join-Path $guideRoot 'guide-stop.request')){throw 'Camera ended before protocol start'}
        $guideFile=Join-Path $guideRoot 'kinect/bodies.jsonl'
        if(Test-Path -LiteralPath $guideFile){
            $guideLines=@(Get-Content -LiteralPath $guideFile -Tail 8 -ErrorAction SilentlyContinue)
            foreach($guideLine in $guideLines){
                try{$guideFrame=$guideLine|ConvertFrom-Json -ErrorAction Stop;if($guideFrame.body_count -eq 1){$guideSeen=$true;break}}catch{}
            }
        }
        if(!$guideSeen){Start-Sleep -Milliseconds 150}
    }
    if(!$guideSeen){throw 'No single tracked person before bounded preparation deadline'}
    $guideVoice.Speak('已经识别到一人。请全身入镜，正对镜头。五秒后正式开始。')
    for($guideCountdown=5;$guideCountdown -ge 1;$guideCountdown--){$guideVoice.Speak([string]$guideCountdown);Start-Sleep -Milliseconds 450}
    $guideStart=[System.Diagnostics.Stopwatch]::GetTimestamp();$guideFrequency=[System.Diagnostics.Stopwatch]::Frequency
    Write-GuideEvent @{event='start';host_qpc=$guideStart;qpc_frequency_hz=$guideFrequency;duration_seconds=300;time_basis='PC prompt scheduling; not RF exposure synchronization'}
    for($guideIndex=0;$guideIndex -lt $guidePhases.Count;$guideIndex++){
        while(([System.Diagnostics.Stopwatch]::GetTimestamp()-$guideStart)/$guideFrequency -lt $guideIndex*30){
            if(Test-Path -LiteralPath (Join-Path $guideRoot 'guide-stop.request')){throw 'Camera ended during protocol'}
            Start-Sleep -Milliseconds 50
        }
        $guideCueQpc=[System.Diagnostics.Stopwatch]::GetTimestamp()
        Write-GuideEvent @{event='phase';phase=$guideIndex;nominal_seconds=$guideIndex*30;host_qpc=$guideCueQpc;instruction=$guidePhases[$guideIndex]}
        $guideVoice.Speak($(if($guideIndex -eq 0){'正式开始。'}else{'切换动作。'})+$guidePhases[$guideIndex]+' 保持到下一次提示。')
        Write-GuideEvent @{event='speech_finished';phase=$guideIndex;host_qpc=[System.Diagnostics.Stopwatch]::GetTimestamp()}
    }
    while(([System.Diagnostics.Stopwatch]::GetTimestamp()-$guideStart)/$guideFrequency -lt 300){
        if(Test-Path -LiteralPath (Join-Path $guideRoot 'guide-stop.request')){throw 'Camera ended before the final hold'}
        Start-Sleep -Milliseconds 50
    }
    Write-GuideEvent @{event='end';host_qpc=[System.Diagnostics.Stopwatch]::GetTimestamp();completed=$true}
    $guideComplete=$true
    $guideVoice.Speak('五分钟动作采集已完成，可以休息了。')
}catch{$guideError=$_.Exception.Message;Write-GuideEvent @{event='error';message=$guideError;host_qpc=[System.Diagnostics.Stopwatch]::GetTimestamp()};if($guideVoice){$guideVoice.Speak('本次动作采集已停止，请查看电脑提示。')}}
finally{
    'Guided protocol ended.'|Set-Content -LiteralPath (Join-Path $guideRoot 'kinect-stop.request')
    if($guideVoice){$guideVoice.Dispose()};$guideEvents.Dispose()
    @{completed=$guideComplete;error=$guideError;training_started=$false}|ConvertTo-Json|Set-Content -LiteralPath (Join-Path $guideRoot 'protocol-result.json') -Encoding UTF8
}
if(!$guideComplete){exit 1}
