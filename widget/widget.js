(function () {
  const currentScript = document.currentScript;
  const apiUrl = (currentScript && currentScript.dataset.apiUrl) || window.location.origin;
  const tenantSlug = (currentScript && currentScript.dataset.tenantSlug) || "demo";
  const storageKey = `ai-assistant-session:${tenantSlug}`;
  let sessionId = window.localStorage.getItem(storageKey);
  let isOpen = false;

  const style = document.createElement("style");
  style.textContent = `
    .aiw-button {
      position: fixed; right: 22px; bottom: 22px; z-index: 9999;
      width: 62px; height: 62px; border: 0; border-radius: 24px;
      color: #fff; background: linear-gradient(135deg, #111827, #2563eb);
      box-shadow: 0 18px 45px rgba(15, 23, 42, .28); cursor: pointer;
      font: 700 22px/1 system-ui, sans-serif;
    }
    .aiw-panel {
      position: fixed; right: 22px; bottom: 98px; z-index: 9999;
      width: min(390px, calc(100vw - 28px)); height: min(620px, calc(100vh - 124px));
      display: none; grid-template-rows: auto 1fr auto; overflow: hidden;
      border: 1px solid rgba(148, 163, 184, .35); border-radius: 28px;
      background: rgba(255,255,255,.96); box-shadow: 0 28px 80px rgba(15, 23, 42, .22);
      backdrop-filter: blur(18px);
    }
    .aiw-panel[data-open="true"] { display: grid; }
    .aiw-header { padding: 18px 18px 14px; color: #fff; background: #111827; }
    .aiw-title { margin: 0; font: 700 16px/1.2 system-ui, sans-serif; }
    .aiw-subtitle { margin: 5px 0 0; color: #cbd5e1; font: 400 13px/1.35 system-ui, sans-serif; }
    .aiw-messages { display: flex; flex-direction: column; gap: 10px; padding: 16px; overflow-y: auto; }
    .aiw-message { max-width: 86%; padding: 11px 13px; border-radius: 17px; font: 400 14px/1.45 system-ui, sans-serif; white-space: pre-wrap; }
    .aiw-message-user { align-self: flex-end; color: #fff; background: #2563eb; border-bottom-right-radius: 6px; }
    .aiw-message-bot { align-self: flex-start; color: #172033; background: #eef2ff; border-bottom-left-radius: 6px; }
    .aiw-form { display: grid; grid-template-columns: 1fr auto; gap: 8px; padding: 14px; border-top: 1px solid #e2e8f0; }
    .aiw-input { min-width: 0; padding: 13px 14px; border: 1px solid #cbd5e1; border-radius: 16px; font: 400 14px/1.2 system-ui, sans-serif; }
    .aiw-send { padding: 0 16px; border: 0; border-radius: 16px; color: #fff; background: #111827; font: 700 14px/1 system-ui, sans-serif; cursor: pointer; }
    .aiw-send:disabled { cursor: wait; opacity: .65; }
    @media (max-width: 520px) { .aiw-panel { right: 14px; bottom: 88px; } .aiw-button { right: 14px; bottom: 14px; } }
  `;
  document.head.appendChild(style);

  const panel = document.createElement("section");
  panel.className = "aiw-panel";
  panel.innerHTML = `
    <header class="aiw-header">
      <h2 class="aiw-title">AI-ассистент</h2>
      <p class="aiw-subtitle">Отвечает по demo-каталогу и помогает подобрать продукт.</p>
    </header>
    <div class="aiw-messages" aria-live="polite"></div>
    <form class="aiw-form">
      <input class="aiw-input" name="message" autocomplete="off" placeholder="Спросите про тарифы..." />
      <button class="aiw-send" type="submit">Отправить</button>
    </form>
  `;

  const button = document.createElement("button");
  button.className = "aiw-button";
  button.type = "button";
  button.textContent = "AI";
  button.setAttribute("aria-label", "Открыть AI-ассистента");

  document.body.appendChild(panel);
  document.body.appendChild(button);

  const messages = panel.querySelector(".aiw-messages");
  const form = panel.querySelector(".aiw-form");
  const input = panel.querySelector(".aiw-input");
  const send = panel.querySelector(".aiw-send");

  function addMessage(text, author) {
    const item = document.createElement("div");
    item.className = `aiw-message aiw-message-${author}`;
    item.textContent = text;
    messages.appendChild(item);
    messages.scrollTop = messages.scrollHeight;
    return item;
  }

  button.addEventListener("click", () => {
    isOpen = !isOpen;
    panel.dataset.open = String(isOpen);
    if (isOpen && messages.childElementCount === 0) {
      addMessage("Здравствуйте. Спросите меня про продукты, тарифы или интеграцию.", "bot");
      input.focus();
    }
  });

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const text = input.value.trim();
    if (!text) return;

    addMessage(text, "user");
    input.value = "";
    send.disabled = true;
    const pending = addMessage("Пишу ответ...", "bot");

    try {
      const response = await fetch(`${apiUrl}/api/chat/message`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: text, tenant_slug: tenantSlug, session_id: sessionId, channel: "WIDGET" }),
      });
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      const payload = await response.json();
      sessionId = payload.session_id;
      window.localStorage.setItem(storageKey, sessionId);
      pending.textContent = payload.answer;
    } catch (error) {
      pending.textContent = "Не удалось получить ответ. Проверьте, что backend запущен и каталог импортирован.";
      console.error(error);
    } finally {
      send.disabled = false;
      input.focus();
    }
  });
})();
