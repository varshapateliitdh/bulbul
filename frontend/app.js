/* ═══════════════════════════════════════════
   Bulbul — Application Logic
   ═══════════════════════════════════════════ */

const API_BASE = 'http://localhost:8000';

// ── DOM refs ──
const uploadScreen = document.getElementById('upload-screen');
const chatScreen = document.getElementById('chat-screen');
const uploadZone = document.getElementById('upload-zone');
const fileInput = document.getElementById('file-input');
const uploadStatus = document.getElementById('upload-status');
const statusText = document.getElementById('status-text');
const uploadError = document.getElementById('upload-error');
const errorText = document.getElementById('error-text');
const headerFile = document.getElementById('header-file');
const messagesContainer = document.getElementById('messages-container');
const messageInput = document.getElementById('message-input');
const sendBtn = document.getElementById('send-btn');
const micBtn = document.getElementById('mic-btn');
const micIcon = micBtn.querySelector('.mic-icon');
const stopIcon = micBtn.querySelector('.stop-icon');
const recordingIndicator = document.getElementById('recording-indicator');
const toastContainer = document.getElementById('toast-container');
const langSelect = document.getElementById('lang-select');

// ── State ──
let isRecording = false;
let audioContext = null;
let mediaStream = null;
let scriptNode = null;
let pcmChunks = [];
let sampleRate = 44100;
let docFilename = '';   // set after successful upload


/* ═══════════════════════════════════════════
   UPLOAD
   ═══════════════════════════════════════════ */

// Click to upload
uploadZone.addEventListener('click', () => fileInput.click());

fileInput.addEventListener('change', (e) => {
  if (e.target.files.length) handleUpload(e.target.files[0]);
});

// Drag & Drop
uploadZone.addEventListener('dragover', (e) => { e.preventDefault(); uploadZone.classList.add('drag-over'); });
uploadZone.addEventListener('dragleave', () => uploadZone.classList.remove('drag-over'));
uploadZone.addEventListener('drop', (e) => {
  e.preventDefault();
  uploadZone.classList.remove('drag-over');
  const file = e.dataTransfer.files[0];
  if (file) handleUpload(file);
});

async function handleUpload(file) {
  if (file.type !== 'application/pdf') {
    showUploadError('Please upload a PDF file.');
    return;
  }

  // Show loading
  uploadZone.style.display = 'none';
  uploadError.style.display = 'none';
  uploadStatus.style.display = 'flex';
  statusText.textContent = 'Processing your document…';

  const formData = new FormData();
  formData.append('file', file);

  const selectedLang = langSelect.value;

  try {
    const res = await fetch(`${API_BASE}/upload-file?language_code=${encodeURIComponent(selectedLang)}`, {
      method: 'POST',
      body: formData,
    });

    if (!res.ok) {
      const detail = await res.text();
      throw new Error(detail || 'Upload failed');
    }

    // Parse response and store the unique doc filename
    const data = await res.json();
    docFilename = data.doc_filename;

    // Success — switch to chat
    headerFile.textContent = file.name;
    switchToChat();
  } catch (err) {
    console.error('Upload error:', err);
    uploadStatus.style.display = 'none';
    uploadZone.style.display = 'block';
    showUploadError('Failed to process document. Please try again.');
  }
}

function showUploadError(msg) {
  errorText.textContent = msg;
  uploadError.style.display = 'block';
}

function switchToChat() {
  uploadScreen.classList.remove('active');
  setTimeout(() => chatScreen.classList.add('active'), 50);
}


/* ═══════════════════════════════════════════
   CHAT — TEXT
   ═══════════════════════════════════════════ */

// Auto-resize textarea
messageInput.addEventListener('input', () => {
  messageInput.style.height = 'auto';
  messageInput.style.height = Math.min(messageInput.scrollHeight, 140) + 'px';
});

// Enter to send (Shift+Enter for newline)
messageInput.addEventListener('keydown', (e) => {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault();
    sendTextMessage();
  }
});

sendBtn.addEventListener('click', sendTextMessage);

async function sendTextMessage() {
  const text = messageInput.value.trim();
  if (!text) return;

  addMessage('user', text);
  messageInput.value = '';
  messageInput.style.height = 'auto';

  const assistantEl = addMessage('assistant', '', true); // streaming placeholder

  try {
    const res = await fetch(`${API_BASE}/chat?user_message=${encodeURIComponent(text)}&doc_filename=${encodeURIComponent(docFilename)}`, {
      method: 'POST',
    });

    if (!res.ok) throw new Error('Chat request failed');

    await streamResponse(res, assistantEl);
  } catch (err) {
    console.error('Chat error:', err);
    setMessageText(assistantEl, 'Sorry, something went wrong. Please try again.');
    showToast('Failed to get response');
  }
}


/* ═══════════════════════════════════════════
   CHAT — VOICE (MIC)
   ═══════════════════════════════════════════ */

micBtn.addEventListener('click', toggleRecording);

async function toggleRecording() {
  if (isRecording) {
    stopRecording();
  } else {
    await startRecording();
  }
}

async function startRecording() {
  try {
    mediaStream = await navigator.mediaDevices.getUserMedia({ audio: true });
  } catch (err) {
    console.error('Mic access denied:', err);
    showToast('Microphone access denied');
    return;
  }

  isRecording = true;
  pcmChunks = [];

  audioContext = new (window.AudioContext || window.webkitAudioContext)();
  sampleRate = audioContext.sampleRate;

  const source = audioContext.createMediaStreamSource(mediaStream);

  // ScriptProcessorNode (widely supported, works for our use case)
  scriptNode = audioContext.createScriptProcessor(4096, 1, 1);
  scriptNode.onaudioprocess = (e) => {
    if (!isRecording) return;
    const data = e.inputBuffer.getChannelData(0);
    pcmChunks.push(new Float32Array(data));
  };

  source.connect(scriptNode);
  scriptNode.connect(audioContext.destination);

  // Update UI
  micBtn.classList.add('recording');
  micIcon.style.display = 'none';
  stopIcon.style.display = 'block';
  recordingIndicator.style.display = 'flex';
}

function stopRecording() {
  isRecording = false;

  // Stop everything
  if (scriptNode) { scriptNode.disconnect(); scriptNode = null; }
  if (audioContext) { audioContext.close(); audioContext = null; }
  if (mediaStream) { mediaStream.getTracks().forEach(t => t.stop()); mediaStream = null; }

  // Reset UI
  micBtn.classList.remove('recording');
  micIcon.style.display = 'block';
  stopIcon.style.display = 'none';
  recordingIndicator.style.display = 'none';

  // Encode to MP3 and send
  const mp3Blob = encodeMP3(pcmChunks, sampleRate);
  pcmChunks = [];
  sendVoiceMessage(mp3Blob);
}

function encodeMP3(chunks, rate) {
  // Merge all Float32 chunks
  let totalLength = 0;
  for (const c of chunks) totalLength += c.length;
  const merged = new Float32Array(totalLength);
  let offset = 0;
  for (const c of chunks) { merged.set(c, offset); offset += c.length; }

  // Float32 → Int16
  const samples = new Int16Array(merged.length);
  for (let i = 0; i < merged.length; i++) {
    const s = Math.max(-1, Math.min(1, merged[i]));
    samples[i] = s < 0 ? s * 0x8000 : s * 0x7FFF;
  }

  // Encode with lamejs
  const mp3Encoder = new lamejs.Mp3Encoder(1, rate, 128);
  const blockSize = 1152;
  const mp3Buffers = [];

  for (let i = 0; i < samples.length; i += blockSize) {
    const chunk = samples.subarray(i, i + blockSize);
    const buf = mp3Encoder.encodeBuffer(chunk);
    if (buf.length > 0) mp3Buffers.push(buf);
  }

  const flush = mp3Encoder.flush();
  if (flush.length > 0) mp3Buffers.push(flush);

  return new Blob(mp3Buffers, { type: 'audio/mp3' });
}

async function sendVoiceMessage(mp3Blob) {
  addMessage('user', '🎤 Voice message');

  const assistantEl = addMessage('assistant', '', true);

  const formData = new FormData();
  formData.append('file', mp3Blob, 'recording.mp3');

  try {
    const res = await fetch(`${API_BASE}/talk?doc_filename=${encodeURIComponent(docFilename)}`, {
      method: 'POST',
      body: formData,
    });

    if (!res.ok) throw new Error('Talk request failed');
    await streamResponse(res, assistantEl);
  } catch (err) {
    console.error('Talk error:', err);
    setMessageText(assistantEl, 'Sorry, something went wrong with the voice input.');
    showToast('Voice processing failed');
  }
}


/* ═══════════════════════════════════════════
   READ ALOUD
   ═══════════════════════════════════════════ */

async function readAloud(text, btn) {
  if (btn.classList.contains('playing')) return; // already playing

  btn.classList.add('playing');
  btn.querySelector('span').textContent = 'Playing…';

  try {
    const res = await fetch(`${API_BASE}/read_aloud?answer=${encodeURIComponent(text)}`, {
      method: 'POST',
    });

    if (!res.ok) throw new Error('Read aloud failed');

    const blob = await res.blob();
    const url = URL.createObjectURL(blob);
    const audio = new Audio(url);

    audio.onended = () => {
      btn.classList.remove('playing');
      btn.querySelector('span').textContent = 'Read Aloud';
      URL.revokeObjectURL(url);
    };

    audio.onerror = () => {
      btn.classList.remove('playing');
      btn.querySelector('span').textContent = 'Read Aloud';
      showToast('Audio playback failed');
    };

    audio.play();
  } catch (err) {
    console.error('Read aloud error:', err);
    btn.classList.remove('playing');
    btn.querySelector('span').textContent = 'Read Aloud';
    showToast('Read aloud failed');
  }
}


/* ═══════════════════════════════════════════
   STREAMING RESPONSE HELPER
   ═══════════════════════════════════════════ */

async function streamResponse(response, messageEl) {
  const bubble = messageEl.querySelector('.message-bubble');
  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let fullText = '';

  // Remove typing indicator
  const typingEl = bubble.querySelector('.typing-indicator');
  if (typingEl) typingEl.remove();

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    const chunk = decoder.decode(value, { stream: true });
    fullText += chunk;
    bubble.innerHTML = marked.parse(fullText);
    scrollToBottom();
  }

  // Add read-aloud button after streaming completes
  if (fullText.trim()) {
    addReadAloudButton(messageEl, fullText);
  }
}


/* ═══════════════════════════════════════════
   DOM HELPERS
   ═══════════════════════════════════════════ */

function addMessage(role, text, isStreaming = false) {
  // Remove welcome card if present
  const welcome = messagesContainer.querySelector('.welcome-card');
  if (welcome) welcome.remove();

  const wrapper = document.createElement('div');
  wrapper.className = `message ${role}`;

  const bubble = document.createElement('div');
  bubble.className = 'message-bubble';

  if (isStreaming) {
    // Show typing indicator
    bubble.innerHTML = `
      <div class="typing-indicator">
        <span></span><span></span><span></span>
      </div>`;
  } else {
    bubble.textContent = text;
  }

  wrapper.appendChild(bubble);
  messagesContainer.appendChild(wrapper);
  scrollToBottom();

  return wrapper;
}

function setMessageText(messageEl, text) {
  const bubble = messageEl.querySelector('.message-bubble');
  bubble.innerHTML = marked.parse(text);
}

function addReadAloudButton(messageEl, text) {
  const btn = document.createElement('button');
  btn.className = 'read-aloud-btn';
  btn.innerHTML = `
    <svg class="speaker-icon" width="14" height="14" viewBox="0 0 24 24" fill="none">
      <path d="M11 5L6 9H2v6h4l5 4V5z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
      <path d="M15.54 8.46a5 5 0 010 7.07" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
      <path d="M19.07 4.93a10 10 0 010 14.14" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
    </svg>
    <span>Read Aloud</span>`;

  btn.addEventListener('click', () => readAloud(text, btn));
  messageEl.appendChild(btn);
}

function scrollToBottom() {
  messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

function showToast(msg) {
  const toast = document.createElement('div');
  toast.className = 'toast';
  toast.textContent = msg;
  toastContainer.appendChild(toast);
  setTimeout(() => toast.remove(), 3000);
}
