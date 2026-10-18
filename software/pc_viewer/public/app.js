import { createScene } from './scene.js';
import { segmentsFor, longestSegment, nextIndex, clampIndex, elapsedMs, intervalMs, formatTime } from './playback.js';

const $ = id => document.getElementById(id);
let clip = [], manifest = null, scene = null, index = 0, segment = null;
const launch = new URLSearchParams(location.search);
let playing = false, timer = null, speed = 1, loop = launch.get('loop') === '1', autoStarted = false;
$('loop').setAttribute('aria-pressed', String(loop));

function stop() {
    playing = false;
    clearTimeout(timer);
    $('play').textContent = '▶';
    $('play').setAttribute('aria-label', '播放回放');
    $('play-state').textContent = '已暂停';
}
function choose(i) {
    if (!segment || clip.length <= segment.start) return;
    index = Math.min(clip.length - 1, clampIndex(i, segment));
    const f = clip[index];
    scene?.setPose(f);
    $('case').textContent = f.case;
    $('frame-id').textContent = f.frame;
    $('candidate').textContent = String(f.candidate).padStart(2, '0');
    $('score').textContent = f.score.toFixed(6);
    $('score-bar').style.width = `${Math.max(0, Math.min(1, f.score)) * 100}%`;
    $('position').textContent = `${index - segment.start + 1} / ${segment.end - segment.start + 1}`;
    $('scrubber').value = index - segment.start;
    $('timecode').textContent = `${formatTime(elapsedMs(manifest, index, segment))} / ${formatTime(elapsedMs(manifest, segment.end, segment))}`;
    const source = manifest.frames[index];
    $('source-detail').textContent = `${f.case} · 原始帧 ${f.frame} · 调用 ${f.invocation}\n${source.source_record || source.source_directory}`;
    const tbody = $('coordinates');
    tbody.replaceChildren();
    for (let joint = 0; joint < 14; ++joint) {
        const tr = document.createElement('tr');
        for (const text of [String(joint), ...f.joints.slice(joint * 3, joint * 3 + 3).map(x => x.toFixed(7))]) {
            const td = document.createElement('td');
            td.textContent = text;
            tr.append(td);
        }
        tbody.append(tr);
    }
}
function schedule() {
    if (!playing) return;
    timer = setTimeout(() => {
        const next = nextIndex(index, segment, loop);
        if (next === null) { stop(); $('play-state').textContent = '片段结束'; return; }
        choose(next);
        schedule();
    }, intervalMs(manifest, index, segment, speed));
}
function play() {
    if (!clip.length || !segment || clip.length <= segment.end) return;
    if (playing) { stop(); return; }
    if (index === segment.end) choose(segment.start);
    playing = true;
    $('play').textContent = 'Ⅱ';
    $('play').setAttribute('aria-label', '暂停回放');
    $('play-state').textContent = loop ? '循环播放 · 历史结果' : '播放中';
    schedule();
}
function selectSegment(id) {
    stop();
    segment = segmentsFor(manifest).find(s => s.id === id);
    if (!segment) throw new Error('Unknown source segment');
    $('segment').value = segment.id;
    const length = segment.end - segment.start + 1;
    $('scrubber').max = length - 1;
    $('clip-summary').textContent = `/ ${length}帧 · 共${manifest.frames.length}个真实结果`;
    const samples = [segment.start, Math.floor((segment.start + segment.end) / 2), segment.end];
    ['sample-first', 'sample-middle', 'sample-last'].forEach((name, n) => {
        const f = manifest.frames[samples[n]];
        $(name).textContent = f.sample ?? f.case.split('_').at(-1);
    });
    index = segment.start;
    choose(index);
}
function error(message) {
    const box = $('render-error');
    box.hidden = false;
    box.textContent = message;
}
function showStatus(s) {
    $('received').textContent = `${s.received} / ${s.expected}`;
    $('input-state').textContent = s.errors.length ? '错误' : s.complete ? '接收完成' : '接收中';
    $('integrity').textContent = s.errors.length ? '接收校验失败' : s.complete ? '原始字节核对通过' : '等待完整记录';
    $('integrity-mark').textContent = s.complete ? '✓' : '○';
    const ready = segment && clip.length > segment.end;
    $('play').disabled = !ready;
    $('scrubber').disabled = !ready;
    if (s.errors.length) { stop(); error(s.errors.join('\n')); }
    else if (ready && !autoStarted && launch.get('play') === '1') { autoStarted = true; play(); }
}
$('play').addEventListener('click', play);
$('previous').addEventListener('click', () => { stop(); choose(index - 1); });
$('next').addEventListener('click', () => { stop(); choose(index + 1); });
$('scrubber').addEventListener('input', e => { stop(); choose(segment.start + Number(e.target.value)); });
$('segment').addEventListener('change', e => selectSegment(e.target.value));
$('loop').addEventListener('click', () => {
    loop = !loop;
    $('loop').setAttribute('aria-pressed', String(loop));
    if (playing) $('play-state').textContent = loop ? '循环播放 · 历史结果' : '播放中';
});
$('speed').addEventListener('change', e => {
    speed = Number(e.target.value);
    $('pose-hz').textContent = (manifest.default_playback_hz * speed).toFixed(1);
    clearTimeout(timer);
    schedule();
});
const viewButtons = document.querySelectorAll('[data-view]');
function setView(mode) {
    scene?.view(mode);
    viewButtons.forEach(button => {
        const selected = button.dataset.view === mode;
        button.classList.toggle('selected', selected);
        button.setAttribute('aria-pressed', String(selected));
    });
}
viewButtons.forEach(button => button.addEventListener('click', () => setView(button.dataset.view)));
$('reset').addEventListener('click', () => setView('perspective'));
$('labels').addEventListener('click', () => {
    const enabled = $('labels').getAttribute('aria-pressed') !== 'true';
    $('labels').setAttribute('aria-pressed', String(enabled));
    scene?.labels(enabled);
});
$('detail-toggle').addEventListener('click', e => { e.preventDefault(); $('details').showModal(); });
$('close-details').addEventListener('click', () => $('details').close());
const ws = new WebSocket(`ws://${location.host}/updates`);
ws.addEventListener('open', () => { $('connection').textContent = '本地服务已连接'; });
ws.addEventListener('message', e => {
    try {
        const data = JSON.parse(e.data);
        if (data.type === 'clip') {
            manifest = data.manifest;
            clip = data.frames;
            scene = createScene($('viewport'), manifest.bones, fps => { $('render-fps').textContent = fps; });
            $('model-info').textContent = manifest.model_label || manifest.model;
            $('segment').replaceChildren(...segmentsFor(manifest).map(s => {
                const option = document.createElement('option');
                option.value = s.id;
                option.textContent = `${s.id} · ${s.end - s.start + 1}帧`;
                return option;
            }));
            selectSegment(longestSegment(manifest).id);
            showStatus(data.status);
        } else if (data.type === 'frame') {
            if (!manifest || clip.length >= manifest.frames.length) throw new Error('Unexpected extra frame');
            clip.push(data.frame);
            if (index === clip.length - 1) choose(index);
        } else if (data.type === 'status') {
            showStatus(data);
        }
    } catch (e) { stop(); error(e.message); console.error(e); }
});
ws.addEventListener('close', () => {
    stop();
    $('connection').textContent = '本地服务已断开';
    $('connection').classList.add('offline');
    $('input-state').textContent = '已断开';
    $('play-state').textContent = '已断开 · 已接收结果保留';
});
ws.addEventListener('error', () => { $('connection').textContent = '连接错误'; });
window.addEventListener('pagehide', () => { stop(); ws.close(); scene?.dispose(); });
