// 仅下载package.json中固定的两个运行依赖；核对registry提供的SHA512并复用锁。
import fs from 'node:fs';
import path from 'node:path';
import { createHash } from 'node:crypto';
import { HERE, WORK } from '../paths.mjs';
const pkg = JSON.parse(fs.readFileSync(path.join(HERE, 'package.json')));
const lockPath = path.join(HERE, 'dependencies.lock.json');
const previous = fs.existsSync(lockPath) ? JSON.parse(fs.readFileSync(lockPath)) : {};
const lock = {};
fs.mkdirSync(path.join(WORK, 'dependencies'), { recursive: true });
for (const [name, version] of Object.entries(pkg.dependencies)) {
    const response = await fetch(`https://registry.npmjs.org/${name}/${version}`);
    if (!response.ok) throw new Error('Registry error ' + response.status);
    const metadata = await response.json();
    const entry = { version, tarball: metadata.dist.tarball, integrity: metadata.dist.integrity, license: metadata.license };
    if (previous[name] && JSON.stringify(previous[name]) !== JSON.stringify(entry)) throw new Error('Locked dependency changed: ' + name);
    if (!entry.tarball.startsWith('https://registry.npmjs.org/') || !entry.integrity.startsWith('sha512-')) throw new Error('Unexpected dependency origin or integrity');
    const file = path.join(WORK, 'dependencies', `${name}-${version}.tgz`);
    const bytes = fs.existsSync(file) ? fs.readFileSync(file) : Buffer.from(await (await fetch(entry.tarball)).arrayBuffer());
    if ('sha512-' + createHash('sha512').update(bytes).digest('base64') !== entry.integrity) throw new Error('Dependency integrity mismatch');
    fs.writeFileSync(file, bytes); lock[name] = entry;
    console.log(JSON.stringify({ name, version, file, integrity_checked: true }));
}
fs.writeFileSync(lockPath, JSON.stringify(lock, null, 2) + '\n');
