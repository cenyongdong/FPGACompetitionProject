// 纯回放时序；与DOM、Three.js、TCP和SDK均无依赖。
export function segmentsFor(manifest) {
    if (manifest.segments?.length) return manifest.segments;
    return [{ id: 'archive', start: 0, end: manifest.frames.length - 1, frames: manifest.frames.length }];
}
export function longestSegment(manifest) {
    const segments = segmentsFor(manifest);
    return segments.find(s => s.id === manifest.default_segment) || segments.reduce((a,b) => b.end - b.start > a.end - a.start ? b : a);
}
export function nextIndex(index, segment, loop) {
    return index < segment.end ? index + 1 : loop ? segment.start : null;
}
export function clampIndex(index, segment) {
    return Math.max(segment.start, Math.min(segment.end, index));
}
export function elapsedMs(manifest, index, segment) {
    const current = manifest.frames[index].playback_ms;
    const origin = manifest.frames[segment.start].playback_ms;
    return Number.isFinite(current) && Number.isFinite(origin) ? current - origin : (index - segment.start) * 1000 / manifest.default_playback_hz;
}
export function intervalMs(manifest, index, segment, speed) {
    if (!(speed > 0)) throw new Error('Invalid playback speed');
    const duration = index < segment.end ? elapsedMs(manifest, index + 1, segment) - elapsedMs(manifest, index, segment) : 1000 / manifest.default_playback_hz;
    if (!(duration > 0) || !Number.isFinite(duration)) throw new Error('Invalid archived timing');
    return duration / speed;
}
export function formatTime(ms) {
    return `${Math.floor(ms / 60000).toString().padStart(2, '0')}:${(ms / 1000 % 60).toFixed(1).padStart(4, '0')}`;
}
