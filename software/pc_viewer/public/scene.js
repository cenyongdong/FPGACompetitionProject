import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';

// 唯一展示坐标变换，与既有固定投影的-C2竖直方向一致。无auto-fit/逐帧居中。
const toScene = (raw, i) => new THREE.Vector3(raw[i*3] - 1.75, 4.2 - raw[i*3+2], -(raw[i*3+1] - 1.75));
export function createScene(container, bones, onFps) {
    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.setClearColor(0x0b111b, 0);
    renderer.outputColorSpace = THREE.SRGBColorSpace;
    renderer.toneMapping = THREE.ACESFilmicToneMapping;
    renderer.toneMappingExposure = 1.25;
    renderer.shadowMap.enabled = true;
    renderer.shadowMap.type = THREE.PCFShadowMap;
    container.append(renderer.domElement);
    const scene = new THREE.Scene();
    scene.fog = new THREE.FogExp2(0x0b111b, 0.075);
    const camera = new THREE.PerspectiveCamera(36, 1, 0.05, 50);
    const controls = new OrbitControls(camera, renderer.domElement);
    controls.enableDamping = true;
    controls.dampingFactor = 0.09;
    controls.minDistance = 1.2; controls.maxDistance = 13;
    controls.maxPolarAngle = Math.PI * 0.95;
    // 固定观察点，仅相机取景；三帧均保持同一世界位置与尺度。
    const target = new THREE.Vector3(-1, 0.82, 0.4);
    function view(mode) {
        const positions = { perspective: [1.5,0.85,2.4], front: [0,0.05,3.1], side: [3.1,0.05,0], top: [0,3.2,0.001] };
        camera.up.set(0,1,0);
        camera.position.fromArray(positions[mode] || positions.perspective).add(target);
        controls.target.copy(target); controls.update();
    }
    view('perspective');
    scene.add(new THREE.HemisphereLight(0xc8e8ff, 0x17282f, 2.5));
    const key = new THREE.DirectionalLight(0xdefffa, 3.2);
    key.position.set(2.5,5,3); key.castShadow = true;
    key.shadow.mapSize.set(1024,1024);
    Object.assign(key.shadow.camera, { left:-3,right:3,top:3,bottom:-3,near:0.1,far:12 });
    key.shadow.bias = -0.001; scene.add(key);
    const rim = new THREE.PointLight(0x63b9ee, 9, 9);
    rim.position.set(-2,2,-2); scene.add(rim);
    const floor = new THREE.Mesh(new THREE.PlaneGeometry(16,16), new THREE.MeshStandardMaterial({ color:0x0e1925, roughness:0.95, metalness:0.12 }));
    floor.rotation.x = -Math.PI/2; floor.position.y = -0.013; floor.receiveShadow = true; scene.add(floor);
    const grid = new THREE.GridHelper(9,18,0x314954,0x1e303e);
    grid.material.transparent = true; grid.material.opacity = 0.6; scene.add(grid);
    const ring = new THREE.Mesh(new THREE.RingGeometry(1.35,1.357,100), new THREE.MeshBasicMaterial({ color:0x6baea7,transparent:true,opacity:0.28,side:THREE.DoubleSide }));
    ring.rotation.x=-Math.PI/2; ring.position.set(-1,0.002,0.4);scene.add(ring);
    const axis = new THREE.Group();
    for (const [to,color] of [[[0.45,0.006,0],0xb37b68],[[0,0.45,0],0x81e1d5],[[0,0.006,-0.45],0x668ab3]]) {
        axis.add(new THREE.Line(new THREE.BufferGeometry().setFromPoints([new THREE.Vector3(0,0.006,0),new THREE.Vector3(...to)]),new THREE.LineBasicMaterial({color,transparent:true,opacity:0.7})));
    }
    axis.position.set(-1.6,0,1.6);scene.add(axis);
    const figure = new THREE.Group(); scene.add(figure); figure.visible=false;
    const jointGeo = new THREE.SphereGeometry(0.038,24,16);
    const jointMat = new THREE.MeshStandardMaterial({ color:0xf3cd8c, roughness:0.25, metalness:0.3,emissive:0xa07731,emissiveIntensity:0.16 });
    const boneGeo = new THREE.CylinderGeometry(0.019,0.019,1,14);
    const boneMat = new THREE.MeshStandardMaterial({color:0x8ee5d7,roughness:0.28,metalness:0.35,emissive:0x327b74,emissiveIntensity:0.15});
    const joints = Array.from({length:14},() => { const m=new THREE.Mesh(jointGeo,jointMat);m.castShadow=true;figure.add(m);return m; });
    const links = bones.map(() => { const m=new THREE.Mesh(boneGeo,boneMat);m.castShadow=true;figure.add(m);return m; });
    const labelGroup = new THREE.Group(); figure.add(labelGroup);labelGroup.visible=false;
    const labels = joints.map((_,i) => {
        const c=document.createElement('canvas');c.width=64;c.height=64;
        const ctx=c.getContext('2d');ctx.font='500 30px Segoe UI';ctx.textAlign='center';ctx.fillStyle='#e6f4f0';ctx.fillText(String(i),32,43);
        const material=new THREE.SpriteMaterial({map:new THREE.CanvasTexture(c),depthTest:false,transparent:true});
        const sprite=new THREE.Sprite(material);sprite.scale.set(0.13,0.13,1);labelGroup.add(sprite);return sprite;
    });
    const yAxis=new THREE.Vector3(0,1,0);
    function setPose(frame) {
        if (frame.joints.length!==42 || !frame.joints.every(Number.isFinite)) throw new Error('Invalid 3D input');
        const points=joints.map((m,i)=> { const p=toScene(frame.joints,i);m.position.copy(p);labels[i].position.copy(p).add(new THREE.Vector3(0.08,0.05,0));return p; });
        bones.forEach(([a,b],i)=> { const delta=new THREE.Vector3().subVectors(points[b],points[a]);const length=delta.length();links[i].visible=length>0;links[i].position.copy(points[a]).add(points[b]).multiplyScalar(0.5);links[i].scale.set(1,length,1);if(length)links[i].quaternion.setFromUnitVectors(yAxis,delta.divideScalar(length)); });
        figure.visible=true;
        renderer.domElement.dataset.frame=frame.frame;
        renderer.domElement.dataset.joints='14';
    }
    const resize=new ResizeObserver(()=> {const w=container.clientWidth,h=container.clientHeight;renderer.setSize(w,h);camera.aspect=w/h;camera.updateProjectionMatrix();});resize.observe(container);
    let last=performance.now(),count=0,raf;
    function render(now) {controls.update();renderer.render(scene,camera);++count;if(now-last>=1000){onFps(Math.round(count*1000/(now-last)));count=0;last=now;}raf=requestAnimationFrame(render);}
    raf=requestAnimationFrame(render);
    function dispose(){cancelAnimationFrame(raf);resize.disconnect();controls.dispose();scene.traverse(o=>{o.geometry?.dispose();if(o.material){const materials=Array.isArray(o.material)?o.material:[o.material];for(const m of materials){m.map?.dispose();m.dispose();}}});renderer.dispose();}
    return {setPose,view,labels:enabled=>{labelGroup.visible=enabled;},dispose};
}
