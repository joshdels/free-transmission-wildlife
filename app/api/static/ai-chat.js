const socket = new WebSocket("ws://localhost:8000/ws/ai");

const messages = document.getElementById("messages");
const input = document.getElementById("chat-input");
const form = document.getElementById("chat-form");

socket.onopen = () => {
  console.log("AI connected");
};

socket.onmessage = (event) => {
  addMessage("assistant", event.data);
};

socket.onerror = (error) => {
  console.error("WebSocket error:", error);
};

socket.onclose = () => {
  console.log("AI disconnected");
};

form.addEventListener("submit", (event) => {
  event.preventDefault();

  const message = input.value.trim();

  if (!message) {
    return;
  }

  addMessage("user", message);

  socket.send(message);

  input.value = "";
});

function addMessage(role, message) {
  const messageElement = document.createElement("div");

  messageElement.classList.add("message", role);

  messageElement.textContent = message;

  messages.appendChild(messageElement);

  messages.scrollTop = messages.scrollHeight;
}
