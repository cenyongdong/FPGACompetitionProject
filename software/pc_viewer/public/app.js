import { createScene } from './scene.js';

const $ = id => document.getElementById(id);
let clip = [], manifest = null, scene = null, index = 0;
let playing = false, timer = null, speed = 1;

function stop() {
    playing = false;
    clearTimeout(timer);
    $('play').textContent = '▶';
    $('play').setAttribute('aria-label', '播放回放');
    $('play-state').textContent = '已暂停';
}

function choose(i) {
    if (!clip.length) return;
    index = Math.max(0, Math.min(clip.length - 1, i));
    const f = clip[index];
    scene?.setPose(f);
    $('case').textContent = f.case;
    $('frame-id').textContent = f.frame;
    $('candidate').textContent = String(f.candidate).padStart(2, '0');
    $('score').textContent = f.score.toFixed(6);
    $('score-bar').style.width = `${Math.max(0, Math.min(1, f.score)) * 100}%`;
    $('position').textContent = `${index + 1} / ${clip.length}`;
    $('scrubber').value = index;
    $('source-detail').textContent = `${f.case} · 原始帧 ${f.frame} · 调用 ${f.invocation}\n${manifest.frames[index].source_directory}`;
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
        if (index === clip.length - 1) {
            stop();
            $('play-state').textContent = '回放结束';
            return;
        }
        choose(index + 1);
        schedule();
    }, 1000 / (manifest.default_playback_hz * speed));
}

function play() {
    if (!clip.length) return;
    if (playing) { stop(); return; }
    if (index === clip.length - 1) choose(0);
    playing = true;
    $('play').textContent = 'Ⅱ';
    $('play').setAttribute('aria-label', '暂停回放');
    $('play-state').textContent = '播放中';
    schedule();
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
    if (s.errors.length) { stop(); error(s.errors.join('\n')); }
}

function updateClip() {
    if (!clip.length) return;
    $('scrubber').max = clip.length - 1;
    $('scrubber').disabled = false;
    $('play').disabled = false;
    choose(index);
    if (!playing) $('play-state').textContent = '已就绪 · 单次播放';
}

$('play').addEventListener('click', play);
$('previous').addEventListener('click', () => { stop(); choose(index - 1); });
$('next').addEventListener('click', () => { stop(); choose(index + 1); });
$('scrubber').addEventListener('input', e => { stop(); choose(Number(e.target.value)); });
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
            updateClip();
            showStatus(data.status);
        } else if (data.type === 'frame') {
            if (!manifest || clip.length >= manifest.frames.length) throw new Error('Unexpected extra frame');
            clip.push(data.frame);
            updateClip();
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
