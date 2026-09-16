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

        // Create empty AI message bubble with typing indicator
        const aiDiv = document.createElement("div");
        aiDiv.className = "message ai-message";
        const aiContent = document.createElement("div");
        aiContent.className = "message-content";
        aiContent.innerHTML = `
            <div class="typing-indicator">
                <span></span><span></span><span></span>
            </div>
        `;
        aiDiv.appendChild(aiContent);
        messages.appendChild(aiDiv);
        messages.scrollTop = messages.scrollHeight;

        // İlk token gelince typing indicator'ı temizle
        let firstChunk = true;

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
            let fullText = "";

            while (true) {
                const { done, value } = await reader.read();
                if (done) break;

                const chunk = decoder.decode(value, { stream: true });
                fullText += chunk;

                // İlk token geldiğinde typing indicator'ı kaldır
                if (firstChunk) {
                    aiContent.innerHTML = "";
                    firstChunk = false;
                }

                aiContent.innerHTML = marked.parse(fullText);
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

        const content = document.createElement("div");
        content.className = "message-content";

        if (sender === "ai") {
            content.innerHTML = marked.parse(text);
        } else {
            content.textContent = text;
        }

        // Timestamp
        const timestamp = document.createElement("div");
        timestamp.className = "message-timestamp";
        timestamp.textContent = new Date().toLocaleTimeString([], {
            hour: '2-digit',
            minute: '2-digit'
        });

        div.appendChild(content);
        div.appendChild(timestamp);
        messages.appendChild(div);
        messages.scrollTop = messages.scrollHeight;
    }

    // Escape HTML to prevent XSS
    function escapeHtml(text) {
        const div = document.createElement("div");
        div.textContent = text;
        return div.innerHTML;
    }

    // Sidebar toggle for mobile
    const menuToggle = document.getElementById("menu-toggle");
    const sidebar = document.getElementById("sidebar");

    if (menuToggle && sidebar) {
        menuToggle.addEventListener("click", () => {
            sidebar.classList.toggle("open");
        });

        // Sidebar dışına tıklayınca kapat
        document.addEventListener("click", (e) => {
            if (
                sidebar.classList.contains("open") &&
                !sidebar.contains(e.target) &&
                !menuToggle.contains(e.target)
            ) {
                sidebar.classList.remove("open");
            }
        });
    }

    // New Chat button (placeholder — Gün 10'da çalışacak)
    const newChatBtn = document.getElementById("new-chat-btn");
    if (newChatBtn) {
        newChatBtn.addEventListener("click", () => {
            console.log("New chat — will be functional on Day 10");
        });
    }
});