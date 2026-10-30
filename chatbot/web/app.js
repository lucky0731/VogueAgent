const ESCAPES = { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' };
const escapeHtml = (v) => String(v ?? '').replace(/[&<>"']/g, (ch) => ESCAPES[ch]);
const formatPrice = (n) => '₹' + Number(n || 0).toLocaleString('en-IN', { maximumFractionDigits: 2 });

const messagesEl = document.getElementById('messages');
const formEl = document.getElementById('form');
const inputEl = document.getElementById('input');
const sendEl = document.getElementById('send');
const micEl = document.getElementById('micBtn');
const photoBtn = document.getElementById('photoBtn');
const photoInput = document.getElementById('photoInput');
const statusEl = document.getElementById('status');

let storeUrl = 'http://localhost:8000';
fetch('/config').then(r => r.json()).then(c => { if (c.store_url) { storeUrl = c.store_url; render(); } }).catch(() => {});
const productUrl = (p) => `${storeUrl}/#/product/${encodeURIComponent(p.id)}`;

const HINTS = ["Men's shirts under 2000", 'Summer dresses', 'Kids pyjamas', 'Black jackets'];
const messages = [];
let loading = false;

/* ---------------- rendering ---------------- */

function render() {
    const hints = messages.length === 0
        ? `<div class="hints">${HINTS.map(h => `<button type="button" class="hint">${escapeHtml(h)}</button>`).join('')}</div>
           <div class="message message-bot"><p class="bubble">Hi! I can find clothes for you. Type what you're after, tap the mic to say it, or share a photo to see lookalikes.</p></div>`
        : '';
    messagesEl.innerHTML = hints + messages.map(renderMessage).join('') +
        (loading ? `<p class="typing">${escapeHtml(loading)}</p>` : '');
    messagesEl.querySelectorAll('.hint').forEach(b => b.addEventListener('click', () => sendText(b.textContent)));
    messagesEl.scrollTop = messagesEl.scrollHeight;
    [sendEl, micEl, photoBtn].forEach(b => { if (b !== micEl || !recorder) b.disabled = Boolean(loading); });
}

function renderMessage(msg) {
    if (msg.sender === 'user') {
        const body = msg.image
            ? `<img class="upload-thumb" src="${msg.image}" alt="Your photo" />`
            : `<p class="bubble">${escapeHtml(msg.text)}</p>`;
        const via = msg.via ? `<span class="via">${escapeHtml(msg.via)}</span>` : '';
        return `<div class="message message-user">${body}${via}</div>`;
    }
    const text = msg.message ? `<p class="bubble">${escapeHtml(msg.message)}</p>` : '';
    if (msg.type === 'products') {
        const items = msg.data || [];
        const list = items.length === 0 ? '' : `<div class="products">${items.map(p => `
          <a class="product" href="${escapeHtml(productUrl(p))}" target="_blank" rel="noopener" title="View ${escapeHtml(p.name)} in the store">
            <img src="${escapeHtml(p.image)}" alt="${escapeHtml(p.name)}" loading="lazy" />
            <div><p>${escapeHtml(p.name)}</p><p class="price">${formatPrice(p.price)}</p><p class="view">View in store →</p></div>
          </a>`).join('')}</div>`;
        return `<div class="message message-bot">${text}${list}</div>`;
    }
    return `<div class="message message-bot">${text}</div>`;
}

function showStatus(text) {
    statusEl.textContent = text || '';
}

/* ---------------- requests ---------------- */

async function call(url, options, waitingText) {
    loading = waitingText;
    render();
    try {
        const res = await fetch(url, options);
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        return await res.json();
    } catch {
        return { type: 'text', message: 'Sorry, something went wrong. Please try again.' };
    } finally {
        loading = false;
    }
}

async function sendText(text) {
    messages.push({ sender: 'user', text });
    const data = await call('/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: text }),
    }, 'Finding styles…');
    messages.push({ sender: 'bot', ...data });
    render();
}

formEl.addEventListener('submit', (e) => {
    e.preventDefault();
    const text = inputEl.value.trim();
    if (!text || loading) return;
    inputEl.value = '';
    sendText(text);
});

/* ---------------- photo search ---------------- */

photoBtn.addEventListener('click', () => photoInput.click());

photoInput.addEventListener('change', async () => {
    const file = photoInput.files?.[0];
    photoInput.value = '';
    if (!file) return;
    if (file.size > 8 * 1024 * 1024) {
        showStatus('That photo is larger than 8 MB. Please choose a smaller one.');
        return;
    }
    showStatus('');
    messages.push({ sender: 'user', image: URL.createObjectURL(file), via: 'Find lookalikes' });
    const form = new FormData();
    form.append('image', file);
    const data = await call('/image-search', { method: 'POST', body: form }, 'Looking for similar styles…');
    messages.push({ sender: 'bot', ...data });
    render();
});

/* ---------------- voice input ---------------- */

let recorder = null;
let chunks = [];
let stopTimer = null;
const MAX_SECONDS = 30;

function pickMimeType() {
    const types = ['audio/webm;codecs=opus', 'audio/webm', 'audio/ogg;codecs=opus', 'audio/mp4'];
    return types.find(t => window.MediaRecorder?.isTypeSupported?.(t)) || '';
}

async function startRecording() {
    if (!navigator.mediaDevices?.getUserMedia || !window.MediaRecorder) {
        showStatus("Voice input isn't supported in this browser. Try Chrome, Edge or Firefox.");
        return;
    }
    let stream;
    try {
        stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    } catch {
        showStatus('Microphone access was blocked. Allow it in the browser’s address bar and try again.');
        return;
    }
    const mimeType = pickMimeType();
    recorder = new MediaRecorder(stream, mimeType ? { mimeType } : undefined);
    chunks = [];
    recorder.ondataavailable = (e) => { if (e.data.size) chunks.push(e.data); };
    recorder.onstop = async () => {
        stream.getTracks().forEach(t => t.stop());
        const type = recorder.mimeType || mimeType || 'audio/webm';
        const blob = new Blob(chunks, { type });
        recorder = null;
        setMicUi(false);
        if (blob.size < 1200) {
            showStatus("That was very short. Tap the mic, speak, then tap again to send.");
            render();
            return;
        }
        await sendVoice(blob, type);
    };
    recorder.start();
    setMicUi(true);
    stopTimer = setTimeout(stopRecording, MAX_SECONDS * 1000);
}

function stopRecording() {
    clearTimeout(stopTimer);
    if (recorder && recorder.state !== 'inactive') recorder.stop();
}

function setMicUi(on) {
    micEl.classList.toggle('recording', on);
    micEl.setAttribute('aria-pressed', String(on));
    micEl.setAttribute('aria-label', on ? 'Stop and send voice message' : 'Start voice input');
    showStatus(on ? 'Listening… tap the mic again when you’re done.' : '');
    [sendEl, photoBtn].forEach(b => { b.disabled = on; });
}

async function sendVoice(blob, type) {
    const ext = type.includes('ogg') ? 'ogg' : type.includes('mp4') ? 'm4a' : 'webm';
    const form = new FormData();
    form.append('audio', blob, `voice.${ext}`);
    const pending = { sender: 'user', text: '…', via: 'Voice' };
    messages.push(pending);
    const data = await call('/voice', { method: 'POST', body: form }, 'Listening back…');
    if (data.transcript) {
        pending.text = data.transcript;
    } else {
        messages.splice(messages.indexOf(pending), 1);
    }
    messages.push({ sender: 'bot', ...data });
    render();
}

micEl.addEventListener('click', () => (recorder ? stopRecording() : startRecording()));

render();
