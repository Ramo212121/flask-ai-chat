document.addEventListener("DOMContentLoaded", () => {
    const form = document.getElementById("chat-form");
    const input = document.getElementById("chat-input");
    const messages = document.getElementById("chat-messages");
    const clearBtn = document.getElementById("clear-btn");

    form.addEventListener("submit", async (e) => {
        e.preventDefault();

        const text = input.value.trim();
        if (!text) return;

        addMessage(text, "user");
        input.value = "";
        input.disabled = true;

        try {
            const response = await fetch("/chat", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({ message: text })
            });

            const data = await response.json();

            if (response.ok) {
                addMessage(data.reply, "ai");
            } else {
                addMessage(`Error: ${data.error}`, "ai");
            }
        } catch (err) {
            addMessage("Connection error. Try again.", "ai");
        } finally {
            input.disabled = false;
            input.focus();
        }
    });

    clearBtn.addEventListener("click", () => {
        messages.innerHTML = `
            <div class="message ai-message">
                <div class="message-content">
                    Hello! 👋 I'm an AI assistant. Ask me anything!
                </div>
            </div>
        `;
    });

    function addMessage(text, sender) {
        const div = document.createElement("div");
        div.className = `message ${sender}-message`;
        div.innerHTML = `<div class="message-content">${escapeHtml(text)}</div>`;
        messages.appendChild(div);
        messages.scrollTop = messages.scrollHeight;
    }

    function escapeHtml(text) {
        const div = document.createElement("div");
        div.textContent = text;
        return div.innerHTML;
    }
});