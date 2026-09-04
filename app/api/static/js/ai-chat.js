const socket = new WebSocket("ws://localhost:8000/ws/ai");

const messages = document.getElementById("messages");
const input = document.getElementById("chat-input");
const form = document.getElementById("chat-form");

// =========================================================
// WEBSOCKET
// =========================================================

socket.onopen = () => {
  console.log("AI connected");
};

socket.onmessage = (event) => {
  const data = JSON.parse(event.data);

  // -----------------------------------------------------
  // NORMAL AI MESSAGE
  // -----------------------------------------------------

  if (data.type === "message") {
    addMessage("assistant", data.content);
  }

  // -----------------------------------------------------
  // HTML FILE
  // -----------------------------------------------------
  else if (data.type === "html_file") {
    addHtmlFile(data);
  }

  // -----------------------------------------------------
  // ERROR
  // -----------------------------------------------------
  else if (data.type === "error") {
    addMessage("assistant", "Error: " + data.message);
  }
};

socket.onerror = (error) => {
  console.error("WebSocket error:", error);
};

socket.onclose = () => {
  console.log("AI disconnected");
};

// =========================================================
// SEND MESSAGE
// =========================================================

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

// =========================================================
// NORMAL MESSAGE
// =========================================================

function addMessage(role, message) {
  const messageElement = document.createElement("div");

  messageElement.classList.add("message", role);

  const bubble = document.createElement("div");

  bubble.classList.add("bubble");

  bubble.textContent = message;

  messageElement.appendChild(bubble);

  messages.appendChild(messageElement);

  messages.scrollTop = messages.scrollHeight;
}

// =========================================================
// HTML FILE
// =========================================================

function addHtmlFile(data) {
  const messageElement = document.createElement("div");

  messageElement.classList.add("message", "assistant");

  messageElement.innerHTML = `

        <div class="file-card">

            <div class="file-info">

                <div class="file-icon">
                    HTML
                </div>

                <div>

                    <div class="file-name">
                        ${escapeHtml(data.filename)}
                    </div>

                    <div class="file-type">
                        HTML document
                    </div>

                </div>

            </div>

            <button
                type="button"
                class="download-button"
            >
                Download
            </button>

        </div>

    `;

  messages.appendChild(messageElement);

  const downloadButton = messageElement.querySelector(".download-button");

  downloadButton.addEventListener("click", () => {
    downloadHtml(data.filename, data.content);
  });

  messages.scrollTop = messages.scrollHeight;
}

// =========================================================
// DOWNLOAD HTML
// =========================================================

function downloadHtml(filename, content) {
  const blob = new Blob([content], {
    type: "text/html;charset=utf-8",
  });

  const url = URL.createObjectURL(blob);

  const link = document.createElement("a");

  link.href = url;

  link.download = filename;

  document.body.appendChild(link);

  link.click();

  link.remove();

  setTimeout(() => {
    URL.revokeObjectURL(url);
  }, 100);
}

// =========================================================
// ESCAPE HTML
// =========================================================

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")

    .replaceAll("<", "&lt;")

    .replaceAll(">", "&gt;")

    .replaceAll('"', "&quot;")

    .replaceAll("'", "&#039;");
}
