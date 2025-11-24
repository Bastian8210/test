const WS_URL = "ws://localhost:8765";
const reconnectDelay = 2000;

const statusText = document.getElementById("status-text");
const statusDot = document.getElementById("status-dot");
const sendButton = document.getElementById("send");
const messageInput = document.getElementById("message");
const log = document.getElementById("log");

let socket;
let reconnectTimer;

function setStatus(state, color, glow) {
  statusText.textContent = state;
  statusDot.style.background = color;
  statusDot.style.boxShadow = glow;
  sendButton.disabled = state !== "Connected";
}

function addEntry(role, payload) {
  const entry = document.createElement("div");
  entry.className = `entry ${role}`;

  const badge = document.createElement("span");
  badge.className = "role";
  badge.textContent = role === "outbound" ? "Sent" : "Received";

  const text = document.createElement("div");
  text.className = "payload";
  text.textContent = payload;

  entry.appendChild(badge);
  entry.appendChild(text);
  log.appendChild(entry);
  log.scrollTop = log.scrollHeight;
}

function connect() {
  clearTimeout(reconnectTimer);
  setStatus("Connecting…", "var(--warning)", "0 0 12px rgba(246, 197, 96, 0.8)");

  socket = new WebSocket(WS_URL);

  socket.addEventListener("open", () => {
    setStatus("Connected", "var(--success)", "0 0 14px rgba(111, 240, 168, 0.9)");
  });

  socket.addEventListener("message", (event) => {
    addEntry("inbound", event.data);
  });

  socket.addEventListener("close", () => {
    setStatus("Disconnected", "var(--danger)", "0 0 12px rgba(255, 123, 123, 0.9)");
    reconnectTimer = setTimeout(connect, reconnectDelay);
  });

  socket.addEventListener("error", () => {
    setStatus("Error", "var(--danger)", "0 0 12px rgba(255, 123, 123, 0.9)");
    socket.close();
  });
}

sendButton.addEventListener("click", () => {
  const payload = messageInput.value.trim();
  if (!payload || !socket || socket.readyState !== WebSocket.OPEN) {
    return;
  }
  socket.send(payload);
  addEntry("outbound", payload);
  messageInput.value = "";
  messageInput.focus();
});

messageInput.addEventListener("keydown", (event) => {
  if (event.key === "Enter") {
    sendButton.click();
  }
});

document.addEventListener("visibilitychange", () => {
  if (document.visibilityState === "visible" && (!socket || socket.readyState === WebSocket.CLOSED)) {
    connect();
  }
});

connect();
