const form = document.querySelector("#chat-form");
const input = document.querySelector("#message-input");
const sendButton = document.querySelector("#send-button");
const messageList = document.querySelector("#messages");
const welcome = document.querySelector("#welcome");
const historyKey = "nova-chat-history";
let conversation = loadConversation();

function loadConversation() {
  try {
    const saved = JSON.parse(localStorage.getItem(historyKey) || "[]");
    return Array.isArray(saved)
      ? saved.filter((item) => item && ["user", "assistant"].includes(item.role) && typeof item.content === "string").slice(-20)
      : [];
  } catch {
    return [];
  }
}

function saveConversation() {
  try {
    localStorage.setItem(historyKey, JSON.stringify(conversation.slice(-20)));
  } catch {
    showMessage("Your browser could not save chat history. You can still continue this conversation.", "assistant", true);
  }
}

function showMessage(content, role, isError = false) {
  welcome.hidden = true;
  const row = document.createElement("article");
  row.className = `message ${role}${isError ? " error" : ""}`;
  const avatar = document.createElement("div");
  avatar.className = "message-avatar";
  avatar.setAttribute("aria-hidden", "true");
  avatar.textContent = role === "user" ? "Y" : "✳";
  const text = document.createElement("div");
  text.className = "message-content";
  text.textContent = content;
  row.append(avatar, text);
  messageList.append(row);
  row.scrollIntoView({ behavior: "smooth", block: "nearest" });
}

function renderHistory() {
  messageList.replaceChildren();
  welcome.hidden = conversation.length > 0;
  for (const message of conversation) showMessage(message.content, message.role);
}

function showTyping() {
  const row = document.createElement("div");
  row.className = "message";
  row.id = "typing-indicator";
  row.setAttribute("aria-label", "Nova is thinking");
  const avatar = document.createElement("div");
  avatar.className = "message-avatar";
  avatar.textContent = "✳";
  const dots = document.createElement("div");
  dots.className = "typing";
  dots.innerHTML = "<span></span><span></span><span></span>";
  row.append(avatar, dots);
  messageList.append(row);
  row.scrollIntoView({ behavior: "smooth", block: "nearest" });
}

function setBusy(busy) {
  sendButton.disabled = busy;
  input.disabled = busy;
  sendButton.setAttribute("aria-label", busy ? "Sending message" : "Send message");
}

async function sendMessage(content) {
  const prompt = content.trim();
  if (!prompt || sendButton.disabled) return;
  conversation.push({ role: "user", content: prompt });
  conversation = conversation.slice(-20);
  saveConversation();
  showMessage(prompt, "user");
  input.value = "";
  input.style.height = "auto";
  setBusy(true);
  showTyping();

  try {
    const response = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ messages: conversation }),
    });
    const data = await response.json();
    document.querySelector("#typing-indicator")?.remove();
    if (!response.ok) throw new Error(data.error || "The assistant could not respond.");
    conversation.push({ role: "assistant", content: data.reply });
    conversation = conversation.slice(-20);
    saveConversation();
    showMessage(data.reply, "assistant");
  } catch (error) {
    document.querySelector("#typing-indicator")?.remove();
    showMessage(error.message || "Something went wrong. Please try again.", "assistant", true);
  } finally {
    setBusy(false);
    input.focus();
  }
}

function startNewChat() {
  conversation = [];
  try {
    localStorage.removeItem(historyKey);
  } catch {
    showMessage("The browser could not clear saved chat history.", "assistant", true);
  }
  messageList.replaceChildren();
  welcome.hidden = false;
  input.value = "";
  input.focus();
}

form.addEventListener("submit", (event) => {
  event.preventDefault();
  sendMessage(input.value);
});

input.addEventListener("input", () => {
  input.style.height = "auto";
  input.style.height = `${Math.min(input.scrollHeight, 180)}px`;
});

input.addEventListener("keydown", (event) => {
  if (event.key === "Enter" && !event.shiftKey) {
    event.preventDefault();
    form.requestSubmit();
  }
});

document.querySelectorAll("[data-prompt]").forEach((button) => {
  button.addEventListener("click", () => sendMessage(button.dataset.prompt));
});

document.querySelectorAll("#new-chat, #top-new-chat").forEach((button) => {
  button.addEventListener("click", startNewChat);
});

renderHistory();
