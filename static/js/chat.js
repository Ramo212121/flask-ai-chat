document.addEventListener("DOMContentLoaded", () => {
    const form = document.getElementById("chat-form");
    const input = document.getElementById("chat-input");
    const messages = document.getElementById("chat-messages");
    const clearBtn = document.getElementById("clear-btn");

    // Load history when page opens
    async function loadHistory() {
        try {
            const response = await fetch("/history");
            const data = await response.json();

            if (data.history && data.history.length > 0) {
                messages.innerHTML = "";
                data.history.forEach(msg => {
                    const sender = msg.role === "user" ? "user" : "ai";
                    addMessage(msg.content, sender);
                });
            }
        } catch (err) {
            console.error("Failed to load history:", err);
        }
    }

    loadHistory();

    // Handle form submit
    form.addEventListener("submit", async (e) => {
        e.preventDefault();

        const text = input.value.trim();
        if (!text) return;

        addMessage(text, "user");
        input.value = "";
        input.disabled = true;

        // Create empty AI message bubble
        const aiDiv = document.createElement("div");
        aiDiv.className = "message ai-message";
        const aiContent = document.createElement("div");
        aiContent.className = "message-content";
        aiDiv.appendChild(aiContent);
        messages.appendChild(aiDiv);
        messages.scrollTop = messages.scrollHeight;

        try {
            const response = await fetch("/chat", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({ message: text })
            });

            if (!response.ok) {
                const data = await response.json();
                aiContent.textContent = `Error: ${data.error}`;
                return;
            }

            const reader = response.body.getReader();
            const decoder = new TextDecoder();

            while (true) {
                const { done, value } = await reader.read();
                if (done) break;

                const chunk = decoder.decode(value, { stream: true });
                aiContent.textContent += chunk;
                messages.scrollTop = messages.scrollHeight;
            }
        } catch (err) {
            aiContent.textContent = "Connection error. Try again.";
        } finally {
            input.disabled = false;
            input.focus();
        }
    });

    // Handle clear button
    clearBtn.addEventListener("click", async () => {
        try {
            await fetch("/history", { method: "DELETE" });
            messages.innerHTML = `
                <div class="message ai-message">
                    <div class="message-content">
                        Hello! 👋 I'm an AI assistant. Ask me anything!
                    </div>
                </div>
            `;
        } catch (err) {
            console.error("Failed to clear history:", err);
        }
    });

    // Add a message to the screen
    function addMessage(text, sender) {
        const div = document.createElement("div");
        div.className = `message ${sender}-message`;
        div.innerHTML = `<div class="message-content">${escapeHtml(text)}</div>`;
        messages.appendChild(div);
        messages.scrollTop = messages.scrollHeight;
    }

    // Escape HTML to prevent XSS
    function escapeHtml(text) {
        const div = document.createElement("div");
        div.textContent = text;
        return div.innerHTML;
    }
});