document.addEventListener("DOMContentLoaded", () => {
    const form = document.getElementById("chat-form");
    const input = document.getElementById("chat-input");
    const messages = document.getElementById("chat-messages");
    const clearBtn = document.getElementById("clear-btn");
    const chatList = document.getElementById("chat-list");
    const newChatBtn = document.getElementById("new-chat-btn");
    const menuToggle = document.getElementById("menu-toggle");
    const sidebar = document.getElementById("sidebar");

    // ===== Text-to-Speech (TTS) with gTTS =====
    let currentAudio = null;
    let speakingBtn = null;

    async function speakText(text, btn) {
        if (currentAudio && !currentAudio.paused) {
            currentAudio.pause();
            currentAudio.currentTime = 0;
            if (speakingBtn) {
                speakingBtn.classList.remove("speaking");
                if (speakingBtn === btn) {
                    speakingBtn = null;
                    return;
                }
                speakingBtn = null;
            }
        }

        btn.classList.add("speaking");
        speakingBtn = btn;

        try {
            const response = await fetch("/speak", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ text: text })
            });

            if (!response.ok) {
                throw new Error("TTS request failed");
            }

            const audioBlob = await response.blob();
            const audioUrl = URL.createObjectURL(audioBlob);

            currentAudio = new Audio(audioUrl);

            currentAudio.onended = () => {
                btn.classList.remove("speaking");
                if (speakingBtn === btn) speakingBtn = null;
                URL.revokeObjectURL(audioUrl);
            };

            currentAudio.onerror = () => {
                btn.classList.remove("speaking");
                if (speakingBtn === btn) speakingBtn = null;
                URL.revokeObjectURL(audioUrl);
            };

            await currentAudio.play();
        } catch (err) {
            console.error("TTS failed:", err);
            btn.classList.remove("speaking");
            if (speakingBtn === btn) speakingBtn = null;
        }
    }

    // ===== Microphone (Speech-to-Text) =====
    const micBtn = document.getElementById("mic-btn");
    let mediaRecorder = null;
    let audioChunks = [];
    let isRecording = false;

    if (micBtn) {
        micBtn.addEventListener("mousedown", startRecording);
        micBtn.addEventListener("touchstart", (e) => {
            e.preventDefault();
            startRecording();
        });

        micBtn.addEventListener("mouseup", stopRecording);
        micBtn.addEventListener("mouseleave", stopRecording);
        micBtn.addEventListener("touchend", (e) => {
            e.preventDefault();
            stopRecording();
        });
    }

    async function startRecording() {
        if (isRecording) return;

        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            mediaRecorder = new MediaRecorder(stream);
            audioChunks = [];

            mediaRecorder.ondataavailable = (event) => {
                if (event.data.size > 0) {
                    audioChunks.push(event.data);
                }
            };

            mediaRecorder.onstop = async () => {
                stream.getTracks().forEach(track => track.stop());

                if (audioChunks.length === 0) {
                    return;
                }

                const audioBlob = new Blob(audioChunks, { type: "audio/webm" });

                try {
                    const formData = new FormData();
                    formData.append("audio", audioBlob, "recording.webm");

                    const res = await fetch("/transcribe", {
                        method: "POST",
                        body: formData
                    });

                    const data = await res.json();

                    if (res.ok && data.text) {
                        input.value = (input.value + " " + data.text).trim();
                        input.focus();
                    } else {
                        console.error("Transcription error:", data.error);
                    }
                } catch (err) {
                    console.error("Transcribe request failed:", err);
                }
            };

            mediaRecorder.start();
            isRecording = true;
            micBtn.classList.add("recording");
        } catch (err) {
            console.error("Microphone access denied:", err);
            alert("Microphone access denied. Please allow in browser settings.");
        }
    }

    function stopRecording() {
        if (!isRecording || !mediaRecorder) return;

        mediaRecorder.stop();
        isRecording = false;
        micBtn.classList.remove("recording");
    }

    // Image elements
    const imageInput = document.getElementById("image-input");
    const imagePreview = document.getElementById("image-preview");
    const previewImg = document.getElementById("preview-img");
    const removeImageBtn = document.getElementById("remove-image-btn");

    // PDF elements
    const pdfInput = document.getElementById("pdf-input");
    const pdfPreview = document.getElementById("pdf-preview");
    const pdfName = document.getElementById("pdf-name");
    const removePdfBtn = document.getElementById("remove-pdf-btn");

    // Model selector
    const modelSelect = document.getElementById("model-select");
    let currentModel = "openai/gpt-oss-120b";

    // Emoji elements
    const emojiBtn = document.getElementById("emoji-btn");
    const emojiPicker = document.getElementById("emoji-picker");
    const emojiClose = document.getElementById("emoji-close");
    const emojiGrid = document.getElementById("emoji-grid");

    // State
    let currentChatId = null;
    let currentImageBase64 = null;
    let currentImageType = null;
    let currentPdfFile = null;
    let currentPdfName = "";

    // ===== Emoji Picker =====
    const EMOJIS = [
        "😀", "😃", "😄", "😁", "😆", "😅", "🤣", "😂",
        "🙂", "🙃", "😉", "😊", "😇", "🥰", "😍", "🤩",
        "😘", "😗", "😚", "😙", "🥲", "😋", "😛", "😜",
        "🤪", "😝", "🤑", "🤗", "🤭", "🤫", "🤔", "🤐",
        "🤨", "😐", "😑", "😶", "😏", "😒", "🙄", "😬",
        "😮", "😯", "😴", "🤤", "😪", "😵", "🤯", "🤠",
        "👋", "🤚", "🖐️", "✋", "🖖", "👌", "🤌", "🤏",
        "✌️", "🤞", "🤟", "🤘", "👈", "👉", "👆", "👇",
        "👍", "👎", "✊", "👊", "🤛", "🤜", "👏", "🙌",
        "🤝", "🙏", "💪", "🦾",
        "❤️", "🧡", "💛", "💚", "💙", "💜", "🖤", "🤍",
        "💔", "❣️", "💕", "💞", "💓", "💗", "💖", "💘",
        "✨", "⭐", "🌟", "💫", "⚡", "🔥", "💥", "💯",
        "🎉", "🎊", "🎈", "🎁", "🚀", "🎯", "🏆", "🥇",
        "🐶", "🐱", "🐭", "🐹", "🐰", "🦊", "🐻", "🐼",
        "🐨", "🐯", "🦁", "🐮", "🐷", "🐸", "🐵", "🦄",
    ];

    function initEmojiPicker() {
        if (!emojiGrid) return;
        emojiGrid.innerHTML = "";
        EMOJIS.forEach(emoji => {
            const btn = document.createElement("button");
            btn.type = "button";
            btn.className = "emoji-item";
            btn.textContent = emoji;
            btn.addEventListener("click", () => {
                input.value += emoji;
                input.focus();
            });
            emojiGrid.appendChild(btn);
        });
    }

    if (emojiBtn && emojiPicker) {
        initEmojiPicker();

        emojiBtn.addEventListener("click", (e) => {
            e.stopPropagation();
            emojiPicker.classList.toggle("open");
        });

        if (emojiClose) {
            emojiClose.addEventListener("click", () => {
                emojiPicker.classList.remove("open");
            });
        }

        document.addEventListener("click", (e) => {
            if (
                emojiPicker.classList.contains("open") &&
                !emojiPicker.contains(e.target) &&
                !emojiBtn.contains(e.target)
            ) {
                emojiPicker.classList.remove("open");
            }
        });
    }

    // ===== Model Selector =====
    if (modelSelect) {
        modelSelect.addEventListener("change", () => {
            currentModel = modelSelect.value;
        });
    }

    // ===== Add copy buttons + apply highlight =====
    function addCopyButtons(container) {
        if (!container) return;
        const pres = container.querySelectorAll ? container.querySelectorAll("pre") : [];
        pres.forEach(pre => {
            const codeEl = pre.querySelector("code");
            if (codeEl && typeof hljs !== "undefined" && !codeEl.dataset.highlighted) {
                hljs.highlightElement(codeEl);
                codeEl.dataset.highlighted = "yes";
            }

            if (pre.parentElement && pre.parentElement.classList.contains("code-block-wrapper")) return;

            const btn = document.createElement("button");
            btn.className = "copy-code-btn";
            btn.textContent = "Copy";
            btn.type = "button";

            btn.addEventListener("click", async (e) => {
                e.stopPropagation();
                const codeEl2 = pre.querySelector("code");
                const code = codeEl2 ? codeEl2.textContent : pre.textContent;
                try {
                    await navigator.clipboard.writeText(code);
                    btn.textContent = "Copied!";
                    btn.classList.add("copied");
                    setTimeout(() => {
                        btn.textContent = "Copy";
                        btn.classList.remove("copied");
                    }, 2000);
                } catch (err) {
                    console.error("Copy failed:", err);
                }
            });

            const wrapper = document.createElement("div");
            wrapper.className = "code-block-wrapper";
            pre.parentNode.insertBefore(wrapper, pre);
            wrapper.appendChild(pre);
            wrapper.appendChild(btn);
        });
    }

    // ===== Load chats =====
    async function loadChats() {
        try {
            const res = await fetch("/chats");
            const data = await res.json();

            chatList.innerHTML = "";

            if (!data.chats || data.chats.length === 0) {
                chatList.innerHTML = '<p class="empty-hint">No chats yet</p>';
                return;
            }

            data.chats.forEach(chat => {
                const item = document.createElement("div");
                item.className = "chat-item";
                if (chat.id === currentChatId) item.classList.add("active");

                item.innerHTML = `
                    <span class="chat-title">${escapeHtml(chat.title)}</span>
                    <button class="delete-chat-btn" title="Delete">×</button>
                `;

                item.addEventListener("click", (e) => {
                    if (e.target.classList.contains("delete-chat-btn")) return;
                    openChat(chat.id);
                });

                const delBtn = item.querySelector(".delete-chat-btn");
                delBtn.addEventListener("click", async (e) => {
                    e.stopPropagation();
                    if (!confirm("Delete this chat?")) return;

                    try {
                        await fetch(`/chats/${chat.id}`, { method: "DELETE" });
                        if (chat.id === currentChatId) {
                            currentChatId = null;
                            resetMessages();
                        }
                        loadChats();
                    } catch (err) {
                        console.error("Delete failed:", err);
                    }
                });

                chatList.appendChild(item);
            });
        } catch (err) {
            console.error("Failed to load chats:", err);
        }
    }

    // ===== Open a chat =====
    async function openChat(chatId) {
        currentChatId = chatId;
        resetMessages();

        try {
            const res = await fetch(`/history/${chatId}`);
            const data = await res.json();

            if (data.history && data.history.length > 0) {
                messages.innerHTML = "";
                data.history.forEach(msg => {
                    const sender = msg.role === "user" ? "user" : "ai";
                    addMessage(msg.content, sender);
                });
            }

            addCopyButtons(messages);

            document.querySelectorAll(".chat-item").forEach(el => {
                el.classList.remove("active");
            });
            loadChats();

            if (window.innerWidth <= 768) {
                sidebar.classList.remove("open");
            }
        } catch (err) {
            console.error("Failed to open chat:", err);
        }
    }

    // ===== Reset messages =====
    function resetMessages() {
        messages.innerHTML = `
            <div class="message ai-message">
                <div class="message-content">
                    Hello! 👋 I'm an AI assistant. Ask me anything!
                </div>
            </div>
        `;
    }

    // ===== New Chat =====
    newChatBtn.addEventListener("click", async () => {
        try {
            const res = await fetch("/chats", { method: "POST" });
            const data = await res.json();
            currentChatId = data.id;
            resetMessages();
            await loadChats();

            if (window.innerWidth <= 768) {
                sidebar.classList.remove("open");
            }

            input.focus();
        } catch (err) {
            console.error("Failed to create chat:", err);
        }
    });

    // ===== Image upload =====
    imageInput.addEventListener("change", (e) => {
        const file = e.target.files[0];
        if (!file) return;

        if (file.size > 5 * 1024 * 1024) {
            alert("Image too large. Max 5 MB.");
            imageInput.value = "";
            return;
        }

        currentImageType = file.type;

        const reader = new FileReader();
        reader.onload = (event) => {
            const dataUrl = event.target.result;
            currentImageBase64 = dataUrl.split(",")[1];
            previewImg.src = dataUrl;
            imagePreview.style.display = "inline-block";
        };
        reader.readAsDataURL(file);
    });

    removeImageBtn.addEventListener("click", () => {
        currentImageBase64 = null;
        currentImageType = null;
        imageInput.value = "";
        imagePreview.style.display = "none";
        previewImg.src = "";
    });

    // ===== PDF upload =====
    if (pdfInput) {
        pdfInput.addEventListener("change", (e) => {
            const file = e.target.files[0];
            if (!file) return;

            if (file.size > 10 * 1024 * 1024) {
                alert("PDF too large. Max 10 MB.");
                pdfInput.value = "";
                return;
            }

            currentPdfFile = file;
            currentPdfName = file.name;
            pdfName.textContent = file.name;
            pdfPreview.style.display = "inline-flex";
        });
    }

    if (removePdfBtn) {
        removePdfBtn.addEventListener("click", () => {
            currentPdfFile = null;
            currentPdfName = "";
            pdfInput.value = "";
            pdfPreview.style.display = "none";
        });
    }

    // ===== Form submit =====
    form.addEventListener("submit", async (e) => {
        e.preventDefault();

        const text = input.value.trim();
        if (!text && !currentImageBase64 && !currentPdfFile) return;

        const imageUrl = currentImageBase64
            ? `data:${currentImageType};base64,${currentImageBase64}`
            : null;
        addMessage(text, "user", imageUrl);

        input.value = "";
        input.disabled = true;

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

        const sentImageBase64 = currentImageBase64;
        const sentImageType = currentImageType;
        currentImageBase64 = null;
        currentImageType = null;
        imageInput.value = "";
        imagePreview.style.display = "none";
        previewImg.src = "";

        let pdfText = "";
        if (currentPdfFile) {
            try {
                const formData = new FormData();
                formData.append("pdf", currentPdfFile);

                const uploadRes = await fetch("/upload-pdf", {
                    method: "POST",
                    body: formData
                });

                const uploadData = await uploadRes.json();

                if (uploadRes.ok) {
                    pdfText = uploadData.text;
                } else {
                    aiContent.innerHTML = `<div style="color: #e74c3c;">PDF error: ${uploadData.error}</div>`;
                    input.disabled = false;
                    return;
                }
            } catch (err) {
                aiContent.innerHTML = `<div style="color: #e74c3c;">PDF upload failed</div>`;
                input.disabled = false;
                return;
            }

            currentPdfFile = null;
            currentPdfName = "";
            pdfInput.value = "";
            pdfPreview.style.display = "none";
        }

        let firstChunk = true;

        try {
            const response = await fetch("/chat", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    message: text,
                    chat_id: currentChatId,
                    image: sentImageBase64,
                    image_type: sentImageType,
                    model: currentModel,
                    pdf_text: pdfText
                })
            });

            if (!response.ok) {
                const data = await response.json();
                let errorMsg = data.error || `HTTP ${response.status}`;

                if (response.status === 429) {
                    errorMsg = "⏳ Too many requests. Please wait a moment.";
                } else if (response.status === 403) {
                    errorMsg = "🚫 Forbidden. You don't have access.";
                } else if (response.status === 401) {
                    errorMsg = "🔒 Please log in again.";
                    setTimeout(() => window.location.href = "/login", 1500);
                }

                aiContent.innerHTML = `<div style="color: #e74c3c;">${errorMsg}</div>`;
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

                if (firstChunk) {
                    aiContent.innerHTML = "";
                    firstChunk = false;
                }

                aiContent.innerHTML = marked.parse(fullText);
                messages.scrollTop = messages.scrollHeight;

                addCopyButtons(aiContent);
            }

            addCopyButtons(aiContent);

            if (aiContent.textContent.trim()) {
                const aiMsgDiv = aiContent.closest(".message");
                if (aiMsgDiv && !aiMsgDiv.querySelector(".copy-message-btn")) {
                    const msgActions = document.createElement("div");
                    msgActions.className = "message-actions";

                    const capturedText = aiContent.textContent;

                    const speakBtn = document.createElement("button");
                    speakBtn.className = "speak-btn";
                    speakBtn.type = "button";
                    speakBtn.textContent = "Speak";
                    speakBtn.title = "Read aloud";
                    speakBtn.addEventListener("click", (e) => {
                        e.stopPropagation();
                        speakText(capturedText, speakBtn);
                    });
                    msgActions.appendChild(speakBtn);

                    const fullCopyBtn = document.createElement("button");
                    fullCopyBtn.className = "copy-message-btn";
                    fullCopyBtn.type = "button";
                    fullCopyBtn.textContent = "Copy";
                    fullCopyBtn.addEventListener("click", async (e) => {
                        e.stopPropagation();
                        try {
                            await navigator.clipboard.writeText(capturedText);
                            fullCopyBtn.textContent = "Copied!";
                            fullCopyBtn.classList.add("copied");
                            setTimeout(() => {
                                fullCopyBtn.textContent = "Copy";
                                fullCopyBtn.classList.remove("copied");
                            }, 2000);
                        } catch (err) {
                            console.error("Copy failed:", err);
                        }
                    });
                    msgActions.appendChild(fullCopyBtn);

                    aiMsgDiv.appendChild(msgActions);
                }
            }

            await loadChats();
        } catch (err) {
            aiContent.textContent = "Connection error. Try again.";
        } finally {
            input.disabled = false;
            input.focus();
        }
    });

    // ===== Clear button =====
    clearBtn.addEventListener("click", async () => {
        if (!currentChatId) {
            resetMessages();
            return;
        }

        try {
            await fetch(`/history/${currentChatId}`, { method: "DELETE" });
            resetMessages();
        } catch (err) {
            console.error("Clear failed:", err);
        }
    });

    // ===== Add message =====
    function addMessage(text, sender, imageUrl = null) {
        const div = document.createElement("div");
        div.className = `message ${sender}-message`;

        const content = document.createElement("div");
        content.className = "message-content";

        if (imageUrl) {
            const img = document.createElement("img");
            img.src = imageUrl;
            img.className = "message-image";
            img.alt = "Uploaded image";
            content.appendChild(img);
        }

        if (text) {
            if (sender === "ai") {
                const textDiv = document.createElement("div");
                textDiv.innerHTML = marked.parse(text);
                content.appendChild(textDiv);
            } else {
                const textDiv = document.createElement("div");
                textDiv.textContent = text;
                content.appendChild(textDiv);
            }
        }

        const timestamp = document.createElement("div");
        timestamp.className = "message-timestamp";
        timestamp.textContent = new Date().toLocaleTimeString([], {
            hour: '2-digit',
            minute: '2-digit'
        });

        div.appendChild(content);
        div.appendChild(timestamp);

        if (sender === "ai" && text) {
            const msgActions = document.createElement("div");
            msgActions.className = "message-actions";

            const speakBtn = document.createElement("button");
            speakBtn.className = "speak-btn";
            speakBtn.type = "button";
            speakBtn.textContent = "Speak";
            speakBtn.title = "Read aloud";
            speakBtn.addEventListener("click", (e) => {
                e.stopPropagation();
                speakText(text, speakBtn);
            });
            msgActions.appendChild(speakBtn);

            const fullCopyBtn = document.createElement("button");
            fullCopyBtn.className = "copy-message-btn";
            fullCopyBtn.type = "button";
            fullCopyBtn.textContent = "Copy";
            fullCopyBtn.addEventListener("click", async (e) => {
                e.stopPropagation();
                try {
                    await navigator.clipboard.writeText(text);
                    fullCopyBtn.textContent = "Copied!";
                    fullCopyBtn.classList.add("copied");
                    setTimeout(() => {
                        fullCopyBtn.textContent = "Copy";
                        fullCopyBtn.classList.remove("copied");
                    }, 2000);
                } catch (err) {
                    console.error("Copy failed:", err);
                }
            });
            msgActions.appendChild(fullCopyBtn);

            div.appendChild(msgActions);
        }

        messages.appendChild(div);
        messages.scrollTop = messages.scrollHeight;

        addCopyButtons(content);
    }

    // ===== Escape HTML =====
    function escapeHtml(text) {
        const div = document.createElement("div");
        div.textContent = text;
        return div.innerHTML;
    }

    // ===== Sidebar toggle (mobile) =====
    if (menuToggle && sidebar) {
        menuToggle.addEventListener("click", () => {
            sidebar.classList.toggle("open");
        });

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

    // ===== Initial load =====
    loadChats();
});