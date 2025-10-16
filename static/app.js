const messagesEl = document.getElementById('messages');
const inputEl = document.getElementById('text');
const sendBtn = document.getElementById('send');
const micBtn = document.getElementById('mic');
const personaEl = document.getElementById('persona');
const enableSearchEl = document.getElementById('enableSearch');
const histqEl = document.getElementById('histq');
const histbtnEl = document.getElementById('histbtn');
let conversationId = null;

function appendMessage(role, text) {
  const div = document.createElement('div');
  div.className = `msg ${role}`;
  div.textContent = `${role === 'user' ? '我' : '助手'}: ${text}`;
  messagesEl.appendChild(div);
  messagesEl.scrollTop = messagesEl.scrollHeight;
}

async function sendMessage() {
  const message = inputEl.value.trim();
  if (!message) return;
  appendMessage('user', message);
  inputEl.value = '';
  const body = {
    message,
    persona: personaEl.value || null,
    conversation_id: conversationId,
    enable_search: enableSearchEl.checked,
  };
  const res = await fetch('/api/chat', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  const data = await res.json();
  conversationId = data.conversation_id;
  appendMessage('assistant', data.reply);
  if (window.speechSynthesis) {
    const utter = new SpeechSynthesisUtterance(data.reply);
    utter.lang = 'zh-CN';
    window.speechSynthesis.speak(utter);
  }
}

sendBtn.addEventListener('click', sendMessage);
inputEl.addEventListener('keydown', (e) => {
  if (e.key === 'Enter') sendMessage();
});

// Simple mic button toggles Web Speech API (if available)
let recognizing = false;
let recognition;
if ('webkitSpeechRecognition' in window) {
  recognition = new webkitSpeechRecognition();
  recognition.lang = 'zh-CN';
  recognition.continuous = false;
  recognition.interimResults = false;
  recognition.onresult = (event) => {
    const transcript = event.results[0][0].transcript;
    inputEl.value = transcript;
    sendMessage();
  };
  recognition.onend = () => recognizing = false;
}

micBtn.addEventListener('click', () => {
  if (!recognition) {
    alert('当前浏览器不支持语音识别，请手动输入');
    return;
  }
  if (!recognizing) {
    recognizing = true;
    recognition.start();
  } else {
    recognition.stop();
    recognizing = false;
  }
});

// History search
histbtnEl.addEventListener('click', async () => {
  const q = histqEl.value.trim();
  if (!q) return;
  const res = await fetch(`/api/history/search?q=${encodeURIComponent(q)}`);
  const data = await res.json();
  const list = data.results || [];
  const container = document.getElementById('histres');
  container.innerHTML = '';
  list.forEach((r) => {
    const item = document.createElement('div');
    item.className = 'hist-item';
    item.textContent = `${r.created_at} [${r.role}] ${r.content}`;
    container.appendChild(item);
  });
});
