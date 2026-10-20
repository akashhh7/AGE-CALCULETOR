const releases = [
    {
        version: 'v2.3.0', name: 'Changelog UI', date: 'Oct 2026', status: 'latest',
        summary: 'Changelog dial component!',
        changes: [
            { type: 'new', text: 'New changelog page' },
            { type: 'new', text: 'Dial based minimal component' },
        ],
    },
    {
        version: 'v2.2.0', name: 'Scientific calculator', date: 'Oct 2026', status: null,
        summary: 'new page for sci calc',
        changes: [
            { type: 'new', text: 'New ui for scientific calc page integrated with its python script' },
        ],
    },
    
    {
        version: 'v2.1.0', name: 'Whole website rewrite', date: 'Oct 2026', status: null,
        summary: 'A fresh look for the whole site',
        changes: [
            { type: 'new', text: 'new home page and shared navigation' },
            { type: 'new', text: 'redesigned age calculator ui' },
        ],
    },
    {
        version: 'v2.0.0', name: 'calc.py', date: 'Sep 2026', status: null,
        summary: 'new script',
        changes: [
            { type: 'new', text: 'scientific calc script with tons of features' },
        ],
    },
    {
        version: 'v1.0.0', name: 'Website', date: 'Sep 2026', status: null,
        summary: 'flask app',
        changes: [
            { type: 'new', text: 'flask app with ui using age calc script' },
        ],
    },
    {
        version: 'v0.1.0', name: 'Beginning', date: 'Sep 2026', status: 'first',
        summary: 'start',
        changes: [
            { type: 'new', text: 'age calculator script' },
        ],
    },
];

const tagStyle = {
    new: { label: 'New', color: '#4ade80', bg: 'rgba(74,222,128,0.08)', border: 'rgba(74,222,128,0.25)' },
    fix: { label: 'Fix', color: '#60a5fa', bg: 'rgba(96,165,250,0.08)', border: 'rgba(96,165,250,0.25)' },
    wip: { label: 'WIP', color: '#fbbf24', bg: 'rgba(251,191,36,0.08)', border: 'rgba(251,191,36,0.25)' },
};

const GAP = 108;
const VISIBLE_SPAN = 4.4;
const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

let panelEl, canvasEl, ctx, chipsLayer, indicatorEl, detailInner, counterEl, dpr;
let R = 640, cx = 0, cy = 0;
let pos = 0, vel = 0, dest = 0, cur = 0;
let pulsed = false;
let rafId = null;
let wheelAccum = 0, wheelTime = 0;
let touchStartY = null, touchAccum = 0;

function clamp(n, a, b) { return Math.max(a, Math.min(b, n)); }

function fit() {
    dpr = window.devicePixelRatio || 1;
    const rect = panelEl.getBoundingClientRect();
    canvasEl.width = rect.width * dpr;
    canvasEl.height = rect.height * dpr;
    canvasEl.style.width = rect.width + 'px';
    canvasEl.style.height = rect.height + 'px';
    ctx = canvasEl.getContext('2d');
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);



    R = Math.max(300, rect.width * 0.68);
    cx = rect.width + R - 100;
    cy = rect.height / 2;

    draw();
    updateChips();
}

function pointFor(i, step) {
    const ang = Math.PI + (pos - i) * step;
    return { x: cx + Math.cos(ang) * R, y: cy + Math.sin(ang) * R, ang };
}

function draw() {
    const w = canvasEl.width / dpr;
    const h = canvasEl.height / dpr;
    ctx.clearRect(0, 0, w, h);

    const step = GAP / R;
    const span = step * (VISIBLE_SPAN + 0.3);

    // lighting shade
    const sweepY = cy;

    function metalStroke(radius, baseAlpha, glintAlpha, lineWidth) {
        const y0 = cy - R, y1 = cy + R;
        const grad = ctx.createLinearGradient(0, Math.max(-50, y0), 0, Math.min(h + 50, y1));
        const t = clamp((sweepY - y0) / (y1 - y0), 0, 1);
        grad.addColorStop(Math.max(0, t - 0.22), `rgba(255,255,255,${baseAlpha})`);
        grad.addColorStop(t, `rgba(255,255,255,${glintAlpha})`);
        grad.addColorStop(Math.min(1, t + 0.22), `rgba(255,255,255,${baseAlpha})`);
        ctx.beginPath();
        ctx.arc(cx, cy, radius, Math.PI - span, Math.PI + span);
        ctx.strokeStyle = grad;
        ctx.lineWidth = lineWidth;
        ctx.stroke();
    }



    metalStroke(R + 27, 0.03, 0.06, 2);
    metalStroke(R + 22, 0.05, 0.24, 5);
    metalStroke(R + 18, 0.03, 0.11, 1);

    const knurl = 46;
    for (let k = 0; k <= knurl; k++) {
        const t = -span + (2 * span) * (k / knurl);
        const ang = Math.PI + t;
        const x1 = cx + Math.cos(ang) * (R + 15), y1 = cy + Math.sin(ang) * (R + 15);
        const x2 = cx + Math.cos(ang) * (R + 25), y2 = cy + Math.sin(ang) * (R + 25);
        const tickY = cy + Math.sin(ang) * R;
        const glint = Math.max(0, 1 - Math.abs(tickY - sweepY) / (h * 0.2));
        ctx.beginPath();
        ctx.moveTo(x1, y1);
        ctx.lineTo(x2, y2);
        ctx.strokeStyle = `rgba(255,255,255,${0.08 + glint * 0.5})`;
        ctx.lineWidth = 1;
        ctx.stroke();
    }



    metalStroke(R + 3, 0.04, 0.12, 1);
    metalStroke(R, 0.09, 0.55, 4);
    metalStroke(R - 3, 0.03, 0.14, 1);

    releases.forEach((r, i) => {
        const dist = Math.abs(pos - i);
        if (dist > VISIBLE_SPAN) return;
        const { x, y, ang } = pointFor(i, step);
        if (y < -20 || y > h + 20) return;

        const active = dist < 0.5;
        if (active) {
            const len = 28;
            const x1 = cx + Math.cos(ang) * (R - len), y1 = cy + Math.sin(ang) * (R - len);
            const x2 = cx + Math.cos(ang) * R, y2 = cy + Math.sin(ang) * R;

            ctx.beginPath();
            ctx.moveTo(x1, y1);
            ctx.lineTo(x2, y2);
            ctx.strokeStyle = 'rgba(240,196,86,0.95)';
            ctx.lineWidth = 2;
            ctx.stroke();
        }

        if (i < releases.length - 1) {
            const midAng = Math.PI + (pos - (i + 0.5)) * step;
            const mx1 = cx + Math.cos(midAng) * (R - 6), my1 = cy + Math.sin(midAng) * (R - 6);
            const mx2 = cx + Math.cos(midAng) * R, my2 = cy + Math.sin(midAng) * R;
            ctx.beginPath();
            ctx.moveTo(mx1, my1);
            ctx.lineTo(mx2, my2);
            ctx.strokeStyle = 'rgba(255,255,255,0.05)';
            ctx.lineWidth = 1;
            ctx.stroke();
        }
    });
}

function updateChips() {
    const step = GAP / R;
    const existing = new Map();
    chipsLayer.querySelectorAll('.chip').forEach((el) => existing.set(el.dataset.i, el));
    const used = new Set();

    releases.forEach((r, i) => {
        const dist = Math.abs(pos - i);
        if (dist > VISIBLE_SPAN) return;
        used.add(String(i));

        let chip = existing.get(String(i));
        if (!chip) {
            chip = document.createElement('div');
            chip.className = 'chip';
            chip.dataset.i = String(i);
            chip.innerHTML = `<span class="chip-leader"></span><span class="chip-label">${r.version}</span>`;
            chip.addEventListener('click', () => snapTo(i));
            chipsLayer.appendChild(chip);
        }

        const { x, y } = pointFor(i, step);
        const active = dist < 0.5;
        const scale = active ? 1 : Math.max(0.55, 1 - dist * 0.13);
        const opacity = active ? 1 : Math.max(0.1, 1 - dist * 0.23);

        chip.style.setProperty('--x', `${x - 60}px`);
        chip.style.setProperty('--y', `${y}px`);
        chip.style.setProperty('--scale', scale);
        chip.style.setProperty('--op', opacity);
        chip.classList.toggle('is-active', active);
    });

    existing.forEach((el, key) => { if (!used.has(key)) el.remove(); });
}

function pulseIndicator() {
    indicatorEl.classList.remove('is-settled');
    void indicatorEl.offsetWidth;
    indicatorEl.classList.add('is-settled');
}

function stepPhysics() {
    const force = (dest - pos) * 0.15;
    vel = (vel + force) * 0.72;
    pos += vel;
    draw();
    updateChips();

    if (!pulsed && Math.abs(dest - pos) < 0.12) {
        pulsed = true;
        pulseIndicator();
    }

    if (Math.abs(dest - pos) > 0.0012 || Math.abs(vel) > 0.0012) {
        rafId = requestAnimationFrame(stepPhysics);
    } else {
        pos = dest;
        vel = 0;
        draw();
        updateChips();
        rafId = null;
    }
}

function animateTo(n) {
    dest = n;
    pulsed = false;
    if (reduceMotion) {
        pos = n;
        vel = 0;
        draw();
        updateChips();
        pulseIndicator();
        return;
    }
    if (!rafId) rafId = requestAnimationFrame(stepPhysics);
}

function renderDetail(idx) {
    const entry = releases[idx];

    const badge =
        entry.status === 'latest' ? '<span class="badge badge--latest">Latest</span>'
            : entry.status === 'first' ? '<span class="badge badge--first">First release</span>'
                : '';

    const changesHtml = entry.changes.map((c) => {
        const t = tagStyle[c.type];
        return `<div class="change">
      <span class="change-tag" style="color:${t.color};background:${t.bg};border-color:${t.border}">${t.label}</span>
      <p>${c.text}</p>
    </div>`;
    }).join('');

    const prev = idx - 1, next = idx + 1;
    const prevBtn = prev >= 0
        ? `<button class="nav-btn" data-goto="${prev}"><svg viewBox="0 0 12 12" fill="none"><path d="M6 9V3M2.5 5.5 6 3l3.5 2.5" stroke="currentColor" stroke-width="1.3" stroke-linecap="round" stroke-linejoin="round"/></svg>${releases[prev].version}</button>`
        : '';
    const nextBtn = next < releases.length
        ? `<button class="nav-btn" data-goto="${next}"><svg viewBox="0 0 12 12" fill="none"><path d="M6 3v6M2.5 6.5 6 9l3.5-2.5" stroke="currentColor" stroke-width="1.3" stroke-linecap="round" stroke-linejoin="round"/></svg>${releases[next].version}</button>`
        : '';

    detailInner.classList.remove('is-visible');
    window.setTimeout(() => {
        detailInner.innerHTML = `
      <div class="badge-row">${badge}</div>
      <h1 class="detail-title">${entry.version} - ${entry.name}</h1>
      <p class="detail-date">${entry.date}</p>
      <p class="detail-summary">${entry.summary}</p>
      <div class="detail-divider"></div>
      <div class="changes">${changesHtml}</div>
      <div class="nav-row">${prevBtn}${nextBtn}</div>
    `;
        detailInner.querySelectorAll('[data-goto]').forEach((btn) => {
            btn.addEventListener('click', () => snapTo(Number(btn.dataset.goto)));
        });
        requestAnimationFrame(() => detailInner.classList.add('is-visible'));
    }, reduceMotion ? 0 : 130);

    counterEl.innerHTML = `<strong>${String(idx + 1).padStart(2, '0')}</strong> / ${String(releases.length).padStart(2, '0')}`;
}

function snapTo(n) {
    n = clamp(n, 0, releases.length - 1);
    if (n === cur) return;
    cur = n;
    animateTo(n);
    renderDetail(n);
}

function onWheel(e) {
    e.preventDefault();
    const now = Date.now();
    if (now - wheelTime < 85) { wheelAccum += e.deltaY; return; }
    wheelAccum += e.deltaY;
    if (Math.abs(wheelAccum) < 22) return;
    const d = wheelAccum > 0 ? 1 : -1;
    wheelAccum = 0;
    wheelTime = now;
    snapTo(cur + d);
}

function onTouchStart(e) {
    touchStartY = e.touches[0].clientY;
    touchAccum = 0;
}

function onTouchMove(e) {
    if (touchStartY === null) return;
    const y = e.touches[0].clientY;
    touchAccum += touchStartY - y;
    touchStartY = y;
    if (Math.abs(touchAccum) > 40) {
        const d = touchAccum > 0 ? 1 : -1;
        touchAccum = 0;
        snapTo(cur + d);
    }
}

function onKeydown(e) {
    if (e.key === 'ArrowDown') { e.preventDefault(); snapTo(cur + 1); }
    else if (e.key === 'ArrowUp') { e.preventDefault(); snapTo(cur - 1); }
}

export function initDial() {
    panelEl = document.getElementById('dialPanel');
    canvasEl = document.getElementById('dialCanvas');
    chipsLayer = document.getElementById('chipsLayer');
    indicatorEl = document.getElementById('dialIndicator');
    detailInner = document.getElementById('detailInner');
    counterEl = document.getElementById('dialCounter');

    // top bar
    const releaseCountEl = document.getElementById('releaseCount');
    const commitCountEl = document.getElementById('commitCount');
    const closeButton = document.getElementById('btnClose');

    releaseCountEl.textContent =
        `${releases.length} ${releases.length === 1 ? 'release' : 'releases'}`;

    async function loadCommitCount() {
        const [owner, repo] = document.querySelector('.changelog').dataset.repo.split('/');
        commitCountEl.href = `https://github.com/${owner}/${repo}`;

        try {
            const response = await fetch(
                `https://api.github.com/repos/${owner}/${repo}/commits?per_page=100`
            );

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.message || 'GitHub API error');
            }

            const link = response.headers.get('Link');

            let commitCount;

            if (!link) {
                commitCount = data.length;
            } else {
                const lastPageMatch = link.match(
                    /<[^>]*[?&]page=(\d+)[^>]*>;\s*rel="last"/
                );

                if (lastPageMatch) {
                    const lastPage = Number(lastPageMatch[1]);

                    const lastResponse = await fetch(
                        `https://api.github.com/repos/${owner}/${repo}/commits?per_page=100&page=${lastPage}`
                    );

                    const lastData = await lastResponse.json();

                    if (!lastResponse.ok) {
                        throw new Error(lastData.message || 'GitHub API error');
                    }

                    commitCount = (lastPage - 1) * 100 + lastData.length;
                } else {
                    commitCount = data.length;
                }
            }

            commitCountEl.textContent =
                `(${commitCount.toLocaleString()} COMMITS ↗)`;
        } catch (error) {
            console.error('GitHub commit count error:', error);
            commitCountEl.textContent = '';
        }
    }

    loadCommitCount();

    //close btn
    closeButton.addEventListener('click', () => {
        window.location.href = closeButton.dataset.href || '/';
    });


    fit();
    renderDetail(cur);
    requestAnimationFrame(() => detailInner.classList.add('is-visible'));


    window.addEventListener('resize', fit);
    panelEl.addEventListener('wheel', onWheel, { passive: false });
    panelEl.addEventListener('touchstart', onTouchStart, { passive: true });
    panelEl.addEventListener('touchmove', onTouchMove, { passive: true });
    window.addEventListener('keydown', onKeydown);
}