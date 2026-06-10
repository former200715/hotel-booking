/**
 * 酒店预订系统 - Three.js 丝绸涟漪背景动画
 * 5色系统: indigo / cyan / amber / violet / sky
 * 跨页面共享 (base.html, login.html, register.html)
 */
import * as THREE from 'three';

const canvas = document.getElementById('bg-canvas');
if (!canvas) throw new Error('Missing #bg-canvas element');

// 初始隐藏 canvas，等第一帧渲染后再淡入，避免黑屏闪烁
canvas.style.opacity = '0';
canvas.style.transition = 'opacity 0.8s ease';

const renderer = new THREE.WebGLRenderer({ canvas, antialias: true, alpha: true });
renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
renderer.setSize(window.innerWidth, window.innerHeight);

const scene = new THREE.Scene();
const camera = new THREE.PerspectiveCamera(60, window.innerWidth / window.innerHeight, 0.1, 100);
camera.position.z = 28;

const palette = [
    new THREE.Color('#818cf8'),  // indigo
    new THREE.Color('#22d3ee'),  // cyan
    new THREE.Color('#fbbf24'),  // amber
    new THREE.Color('#6366f1'),  // violet
    new THREE.Color('#38bdf8'),  // sky
];

// ---- Silk ripple plane ----
const planeW = 52, planeH = 36, segW = 56, segH = 42;
const planeGeo = new THREE.PlaneGeometry(planeW, planeH, segW, segH);
const vertCount = planeGeo.attributes.position.count;
const origPositions = new Float32Array(planeGeo.attributes.position.array);
const colorArr = new Float32Array(vertCount * 3);
const waveData = new Float32Array(vertCount * 3);

for (let i = 0; i < vertCount; i++) {
    const x = origPositions[i * 3], y = origPositions[i * 3 + 1];
    waveData[i * 3] = Math.random() * Math.PI * 2;
    waveData[i * 3 + 1] = Math.random() * Math.PI * 2;
    waveData[i * 3 + 2] = 0.3 + Math.random() * 0.7;
    const nx = x / planeW + 0.5, ny = y / planeH + 0.5;
    const idx = Math.floor((nx * 0.7 + ny * 0.3) * palette.length);
    const c = palette[Math.min(idx, palette.length - 1)].clone();
    const c2 = palette[Math.min((idx + 1) % palette.length, palette.length - 1)];
    c.lerp(c2, (nx * 0.7 + ny * 0.3) * palette.length - idx);
    const dapple = 0.85 + Math.random() * 0.15;
    colorArr[i * 3] = c.r * dapple;
    colorArr[i * 3 + 1] = c.g * dapple;
    colorArr[i * 3 + 2] = c.b * dapple;
}
planeGeo.setAttribute('color', new THREE.BufferAttribute(colorArr, 3));

const planeMat = new THREE.MeshBasicMaterial({
    vertexColors: true, transparent: true, opacity: 0.22,
    blending: THREE.AdditiveBlending, depthWrite: false, side: THREE.DoubleSide,
});
const silkPlane = new THREE.Mesh(planeGeo, planeMat);
silkPlane.position.z = -5;
scene.add(silkPlane);

// ---- Sparkle particles ----
const pCount = 600;
const pGeo = new THREE.BufferGeometry();
const pPos = new Float32Array(pCount * 3), pCol = new Float32Array(pCount * 3);
for (let i = 0; i < pCount; i++) {
    pPos[i * 3] = (Math.random() - 0.5) * 60;
    pPos[i * 3 + 1] = (Math.random() - 0.5) * 42;
    pPos[i * 3 + 2] = (Math.random() - 0.5) * 12 - 2;
    const c = palette[Math.floor(Math.random() * palette.length)];
    pCol[i * 3] = c.r; pCol[i * 3 + 1] = c.g; pCol[i * 3 + 2] = c.b;
}
pGeo.setAttribute('position', new THREE.BufferAttribute(pPos, 3));
pGeo.setAttribute('color', new THREE.BufferAttribute(pCol, 3));
const pMat = new THREE.PointsMaterial({
    size: 0.1, vertexColors: true, blending: THREE.AdditiveBlending,
    depthWrite: false, opacity: 0.5, transparent: true,
});
const particles = new THREE.Points(pGeo, pMat);
scene.add(particles);

// ---- Glowing orbs ----
const orbGroup = new THREE.Group();
for (let i = 0; i < 5; i++) {
    const orbGeo = new THREE.SphereGeometry(0.16 + Math.random() * 0.3, 16, 16);
    const c = palette[Math.floor(Math.random() * palette.length)];
    const orbMat = new THREE.MeshBasicMaterial({
        color: c, transparent: true, opacity: 0.05 + Math.random() * 0.05,
        blending: THREE.AdditiveBlending, depthWrite: false,
    });
    const orb = new THREE.Mesh(orbGeo, orbMat);
    orb.position.set((Math.random() - 0.5) * 38, (Math.random() - 0.5) * 24, (Math.random() - 0.5) * 8 - 3);
    orb.userData = {
        baseX: orb.position.x, baseY: orb.position.y,
        speedX: (Math.random() - 0.5) * 0.002, phase: Math.random() * Math.PI * 2,
        amplitude: 0.3 + Math.random() * 0.9,
    };
    orbGroup.add(orb);
}
scene.add(orbGroup);

// ---- Mouse parallax ----
let mouseX = 0, mouseY = 0, targetMX = 0, targetMY = 0;
document.addEventListener('mousemove', (e) => {
    targetMX = (e.clientX / window.innerWidth - 0.5) * 2;
    targetMY = (e.clientY / window.innerHeight - 0.5) * 2;
});
document.addEventListener('touchmove', (e) => {
    if (e.touches.length) {
        targetMX = (e.touches[0].clientX / window.innerWidth - 0.5) * 2;
        targetMY = (e.touches[0].clientY / window.innerHeight - 0.5) * 2;
    }
}, { passive: true });

// ---- Animation loop ----
let firstFrame = true;
function animate(time) {
    requestAnimationFrame(animate);
    if (firstFrame) {
        firstFrame = false;
        requestAnimationFrame(() => { canvas.style.opacity = '1'; });
    }
    const t = time * 0.001;
    mouseX += (targetMX - mouseX) * 0.02;
    mouseY += (targetMY - mouseY) * 0.02;

    const posArr = silkPlane.geometry.attributes.position.array;
    for (let i = 0; i < vertCount; i++) {
        const ox = origPositions[i * 3], oy = origPositions[i * 3 + 1];
        const p0 = waveData[i * 3], p1 = waveData[i * 3 + 1], amp = waveData[i * 3 + 2];
        const d = Math.sqrt(ox * ox + oy * oy) * 0.15;
        posArr[i * 3 + 2] =
            Math.sin(ox * 0.4 + t * 0.3 + p0) * 0.8 * amp +
            Math.cos(oy * 0.5 + t * 0.25 + p1) * 0.6 * amp +
            Math.sin(d + t * 0.35) * 1.0 * amp +
            Math.cos(ox * 0.25 - oy * 0.3 + t * 0.2) * 0.5 * amp;
    }
    silkPlane.geometry.attributes.position.needsUpdate = true;

    particles.rotation.y += 0.0002;
    particles.rotation.x += 0.00008;

    orbGroup.children.forEach(orb => {
        const d = orb.userData;
        orb.position.x = d.baseX + Math.sin(t * 0.4 + d.phase) * d.amplitude;
        orb.position.y = d.baseY + Math.cos(t * 0.35 + d.phase) * d.amplitude * 0.7;
        orb.position.x += d.speedX;
        if (Math.abs(orb.position.x - d.baseX) > 6) d.speedX *= -1;
    });

    camera.position.x += (mouseX * 3.0 - camera.position.x) * 0.025;
    camera.position.y += (-mouseY * 1.6 - camera.position.y) * 0.025;
    camera.lookAt(scene.position);
    renderer.render(scene, camera);
}
requestAnimationFrame(animate);

// ---- Resize ----
window.addEventListener('resize', () => {
    camera.aspect = window.innerWidth / window.innerHeight;
    camera.updateProjectionMatrix();
    renderer.setSize(window.innerWidth, window.innerHeight);
});
