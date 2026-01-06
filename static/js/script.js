// ======================
// CSRF TOKEN
// ======================
function getCookie(name) {
    let cookieValue = null;
    let cookies = document.cookie ? document.cookie.split(";") : [];
    for (let cookie of cookies) {
        cookie = cookie.trim();
        if (cookie.startsWith(name + "=")) {
            cookieValue = decodeURIComponent(cookie.slice(name.length + 1));
            break;
        }
    }
    return cookieValue;
}

// ======================
// AUTO SCROLL
// ======================
function autoScroll() {
    const chatBody = document.getElementById("chatBody");
    if (chatBody) chatBody.scrollTop = chatBody.scrollHeight;
}

// ======================
// LIMIT UI HANDLER
// ======================
function forceLimitReached(seconds = 0) {
    const input = document.getElementById("userInput");
    const sendBtn = document.getElementById("sendBtn");
    const chatBody = document.getElementById("chatBody");

    if (input) input.disabled = true;
    if (sendBtn) {
        sendBtn.disabled = true;
        sendBtn.style.opacity = "0.5";
    }

    if (!document.getElementById("limitMessage")) {
        const msg = document.createElement("div");
        msg.id = "limitMessage";
        msg.className = "message system-message";
        msg.innerHTML = `
            ⚠ Chat limit reached (10 messages / 24 hours)
            <div id="timeLeft"></div>
        `;
        chatBody.appendChild(msg);
        autoScroll();
    }

    if (seconds > 0) startCountdown(seconds);
}

// ======================
// COUNTDOWN TIMER
// ======================

document.addEventListener("DOMContentLoaded", () => {
    if (window.REMAINING_SECONDS > 0) {
        startCountdown(window.REMAINING_SECONDS);
    }
});

function startCountdown(seconds) {
    const el = document.getElementById("timeLeft");

    const timer = setInterval(() => {
        if (seconds <= 0) {
            clearInterval(timer);
            location.reload(); // auto unlock after expiry
            return;
        }

        const h = Math.floor(seconds / 3600);
        const m = Math.floor((seconds % 3600) / 60);
        const s = seconds % 60;

        if (el) el.textContent = `${h}h ${m}m ${s}s remaining`;
        seconds--;
    }, 1000);
}

// ====================
// MARKDOWN 
// ====================

document.addEventListener("DOMContentLoaded", function () {
    document.querySelectorAll(".markdown-content[data-markdown]").forEach(el => {
        const markdown = el.getAttribute("data-markdown");
        if (!markdown) return;

        const rawHtml = marked.parse(markdown);
        const safeHtml = DOMPurify.sanitize(rawHtml);

        el.innerHTML = safeHtml;
    });
});



// ======================
// SEND MESSAGE
// ======================
let isProcessing = false;
let selectedFile = null;
let streamStarted = false;


async function sendMessage(e) {
    if (e) e.preventDefault();
    if (isProcessing) return;

    streamStarted = false;

    const input = document.getElementById("userInput");
    const sendBtn = document.getElementById("sendBtn");
    const chatBody = document.getElementById("chatBody");
    const typing = document.getElementById("typingIndicator");
    const modelSelect = document.getElementById("modelSelect");


    const message = input.value.trim();
    if (!message && !selectedFile) return;

    // 🚫 HARD LIMIT CHECK
    if (window.REMAINING_MESSAGES <= 0) {
        forceLimitReached(window.REMAINING_SECONDS);
        return;
    }

    // ✅ USER MESSAGE
    chatBody.insertAdjacentHTML("beforeend", `
        <div class="chat-message user-message">
           ${selectedFile && selectedFile.type.startsWith("image/")
            ? `<img src="${URL.createObjectURL(selectedFile)}" class="chat-image" />`
            : `<span class="chat-text">${message}</span>`}
            <div class="message user">
                <div class="message-content">
                    ${message || "📎 " + selectedFile.name}
                    <div class="message-actions">
                        <i class="fa fa-edit edit-btn"></i>
                        <i class="fa fa-copy copy-btn"></i>
                    </div>
                </div>
            </div>
        </div>
    `);
    autoScroll();

    // 🔵 TYPING INDICATOR
    if (typing) {
        typing.style.display = "flex";
        chatBody.appendChild(typing);
        autoScroll();
    }

    isProcessing = true;
    input.disabled = true;
    sendBtn.style.opacity = "0.6";

    const formData = new FormData();
    formData.append("message", message);
    formData.append("chat_id", window.CHAT_ID);
    formData.append("model", modelSelect.value);


    // 🔥 IMAGE SUPPORT FOR STREAMING
    if (selectedFile && selectedFile.type.startsWith("image/")) {
        const base64Image = await fileToBase64(selectedFile);
        formData.append("image_base64", base64Image);
        formData.append("file", selectedFile);
    }


    try {
            const res = await fetch("/chatbot/stream/", {
            method: "POST",
            headers: {
                "X-CSRFToken": getCookie("csrftoken")
            },
            body: formData
            });

            if (!res.ok) {
                throw new Error("Server error " + res.status);
            }


            // ✅ CREATE BOT MESSAGE BOX ONCE
            const reader = res.body.getReader();
            const decoder = new TextDecoder();

            const botWrapper = document.createElement("div");
            botWrapper.className = "chat-message bot-message";

            const botMsg = document.createElement("div");
            botMsg.className = "message bot";

            const botContent = document.createElement("div");
            botContent.className = "message-content markdown-content";

            botMsg.appendChild(botContent);
            botWrapper.appendChild(botMsg);
            chatBody.appendChild(botWrapper);
            autoScroll();

            let fullMarkdown = "";
          while (true) {
                const { value, done } = await reader.read();
                if (done) break;

                const chunk = decoder.decode(value, { stream: true });

                // 🔥 Hide typing only when real text arrives
                if (!streamStarted && chunk.trim() !== "") {
                    streamStarted = true;
                    if (typing) typing.style.display = "none";
                }

                // 1️⃣ Accumulate RAW markdown
                fullMarkdown += chunk;

                // 2️⃣ Convert markdown → HTML
                const rawHtml = marked.parse(fullMarkdown);

                // 3️⃣ Sanitize HTML
                const safeHtml = DOMPurify.sanitize(rawHtml);

                // 4️⃣ Render
                botContent.innerHTML = safeHtml;

                autoScroll();
            }

            window.REMAINING_MESSAGES--;

        } catch (err) {
            console.error("Streaming error:", err);
            if (typing) typing.style.display = "none";
        }


    // 🔄 RESET
    isProcessing = false;
    input.disabled = false;
    sendBtn.style.opacity = "1";
    input.value = "";
    selectedFile = null;
    streamStarted = false;
    document.getElementById("fileInput").value = "";
}

// ======================
// FILE UPLOAD
// ======================
function fileToBase64(file) {
    return new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.onload = () => {
            const base64 = reader.result.split(",")[1];
            resolve(base64);
        };
        reader.onerror = reject;
        reader.readAsDataURL(file);
    });
}

function uploadFile() {
    const fileInput = document.getElementById("fileInput");
    const userInput = document.getElementById("userInput");

    if (!fileInput.files.length) return;

    selectedFile = fileInput.files[0];
    userInput.value = `📎 ${selectedFile.name}`;
}


// ======================
// EMOJI ATTACH 
// ======================


let emojiPickerLoaded = false;

function toggleEmojiPicker() {
    const pickerDiv = document.getElementById("emojiPicker");

    if (!emojiPickerLoaded) {
        const picker = new window.EmojiMart.Picker({
            onEmojiSelect: (emoji) => {
                document.getElementById("userInput").value += emoji.native;
                
            }
        });

        pickerDiv.appendChild(picker);
        emojiPickerLoaded = true;
    }

    pickerDiv.style.display =
        pickerDiv.style.display === "block" ? "none" : "block";
}

document.addEventListener("DOMContentLoaded", () => {
    const emojiBtn = document.getElementById("emojiBtn");
    const picker = document.getElementById("emojiPicker");

    if (!emojiBtn || !picker) return;

    emojiBtn.addEventListener("click", e => e.stopPropagation());
    picker.addEventListener("click", e => e.stopPropagation());

    document.addEventListener("click", () => {
        picker.style.display = "none";
    });
});



// ======================
// MOBILE NAV
// ======================
document.addEventListener("DOMContentLoaded", () => {
    const menuBtn = document.querySelector('.mobile-menu-btn');
    const mobileNav = document.querySelector('.mobile-navbar');
    const mobileLinks = document.querySelectorAll('.mobile-link');

    if (menuBtn && mobileNav) {
        menuBtn.addEventListener("click", () => mobileNav.classList.toggle("active"));
        mobileLinks.forEach(link => link.addEventListener("click", () => mobileNav.classList.remove("active")));
    }
});


/********************************* EDIT AND DELETE PROFILE FRAME **************************************/

// ======================
// POPUPS
// ======================
function openeditPopup(url) {
    const overlay = document.getElementById("popupOverlay");
    const frame = document.getElementById("popupFrame");
    if (!overlay || !frame) return;

    frame.src = url;
    overlay.classList.add("active");
}

function opendeletePopup(url) {
    openeditPopup(url);
}

window.addEventListener("message", function (event) {
    if (event.data !== "closeProfilePopup") return;

    const overlay = document.getElementById("popupOverlay");
    const frame = document.getElementById("popupFrame");
    if (!overlay || !frame) return;

    overlay.classList.remove("active");
    frame.src = "";

    location.reload();
});

function closePopup() {
    window.parent.postMessage("closeProfilePopup", "*");
}

function previewImage(event) {
    const img = document.getElementById("previewImg");
    if (!img) return;
    img.src = URL.createObjectURL(event.target.files[0]);
}


/***************************************************** HISTORY PAGE LOGIC **************************************/

// ======================
// SEARCH & HIGHLIGHT
// ======================
function searchHistory() {
    const input = document.getElementById("searchInput");
    if (!input) return;

    const val = input.value.trim().toLowerCase();
    const rows = document.querySelectorAll(".history-wrapper");

    rows.forEach(row => {
        const blocks = row.querySelectorAll(".history-msg");
        let matchFound = false;

        blocks.forEach(block => {
            let original = block.getAttribute("data-original");
            if (!original) {
                block.setAttribute("data-original", block.innerHTML);
                original = block.innerHTML;
            }

            if (val === "") {
                block.innerHTML = original;
                matchFound = true;
                return;
            }

            if (original.toLowerCase().includes(val)) matchFound = true;

            const regex = new RegExp(`(${val})`, "gi");
            block.innerHTML = original.replace(regex, `<mark>$1</mark>`);
        });

        row.style.display = matchFound ? "flex" : "none";
    });
}

// -------------------------
// 🌟 SORT HISTORY
// -------------------------
function sortHistory() {
    let sort = document.getElementById("sortSelect").value;
    window.location.href = "?sort=" + sort;
}

/********** HISTORY CLEAN MENU  **********/

// ======================
// SAFE MENU CLOSE (FIXED)
// ======================
document.addEventListener("click", event => {
    const menu = document.getElementById("dotsMenu");
    const dots = document.querySelector(".dots");
    const submenu = document.getElementById("submenu");

    if (!menu || !dots) return;

    if (!menu.contains(event.target) && !dots.contains(event.target)) {
        menu.classList.remove("show");
        submenu?.classList.remove("show");
    }
});

// ======================
// MENU TOGGLES
// ======================
function toggleMenu() {
    document.getElementById("dotsMenu")?.classList.toggle("show");
}

function toggleSubmenu(e) {
    e.stopPropagation();
    document.getElementById("submenu")?.classList.toggle("show");
}



// ======================
// HISTORY PAGE DELETE LOGIC
// ======================

function openCleanPopup(value) {
    const popup = document.getElementById("cleanPopup");
    const input = document.getElementById("cleanRange");

    if (!popup || !input) return;

    popup.style.display = "flex";
    input.value = value;   // can be chat_id OR day/week/month/all
}

function closeCleanPopup() {
    const popup = document.getElementById("cleanPopup");
    const input = document.getElementById("cleanRange");

    if (popup) popup.style.display = "none";
    if (input) input.value = "";
}

function confirmCleanHistory() {
    const value = document.getElementById("cleanRange").value;
    const csrftoken = getCookie("csrftoken");

    if (!value) return;

    // 🔹 RANGE DELETE
    if (["day", "week", "month", "all"].includes(value)) {
        fetch("/clean-history/", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": csrftoken
            },
            body: JSON.stringify({ range_type: value })
        })
        .then(() => location.reload());
    }
    // 🔹 SINGLE CHAT DELETE
    else {
        fetch(`/delete-history/${value}/`, {
            method: "POST",
            headers: {
                "X-CSRFToken": csrftoken
            }
        })
        .then(() => location.reload());
    }
}
