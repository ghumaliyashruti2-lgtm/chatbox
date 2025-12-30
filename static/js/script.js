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


/************************************************ CHAT MESSAGE LIMIT ***************************************/

// ======================
// CONFIG
// ======================
const MAX_MESSAGES = 10;
const CHAT_LIMIT_HOURS = 24;
let isProcessing = false;

// ======================
// CHAT LIMIT HELPERS
// ======================
function setChatStartTime() {
    localStorage.setItem("chatStartTime", Date.now());
    localStorage.setItem("messageCount", "0");
}

function isChatExpired() {
    const start = localStorage.getItem("chatStartTime");
    if (!start) return true;
    return (Date.now() - start) / (1000 * 60 * 60) >= CHAT_LIMIT_HOURS;
}

function resetChatLimit() {
    localStorage.removeItem("chatStartTime");
    localStorage.removeItem("messageCount");
}

function getUserMessageCount() {
    return parseInt(localStorage.getItem("messageCount") || "0", 10);
}

function incrementMessageCount() {
    localStorage.setItem("messageCount", getUserMessageCount() + 1);
}

// ======================
// LIMIT REACHED MESSAGE 
// ======================

document.addEventListener("DOMContentLoaded", () => {
    if (document.getElementById("limitMessage")) {
        const input = document.getElementById("userInput");
        const sendBtn = document.getElementById("sendBtn");

        if (input) input.disabled = true;
        if (sendBtn) {
            sendBtn.disabled = true;
            sendBtn.style.opacity = "0.5";
            sendBtn.style.cursor = "not-allowed";
        }
    }
});

// =========================================
// LIMIT REACHED REMMANING TIME MESSAGE SHOW 
// =========================================

let seconds = window.REMAINING_SECONDS || 0;

if (seconds > 0) {
    const el = document.getElementById("timeLeft");

    setInterval(() => {
        if (seconds <= 0) return;

        const h = Math.floor(seconds / 3600);
        const m = Math.floor((seconds % 3600) / 60);

        if (el) {
            el.textContent = `${h}h ${m}m remaining`;
        }

        seconds--;
    }, 1000);
}

// ======================
// FORCE NEW CHAT
// ======================
function forceNewChat() {
    const input = document.getElementById("userInput");
    const sendBtn = document.getElementById("sendBtn");
    const chatBody = document.getElementById("chatBody");

    if (!input || !sendBtn || !chatBody) return;

    input.disabled = true;
    sendBtn.disabled = true;
    sendBtn.style.opacity = "0.5";

    if (!document.getElementById("limitMessage")) {
        const msg = document.createElement("div");
        msg.id = "limitMessage";
        msg.className = "message system-message";
        msg.innerHTML = "⚠ Chat limit reached (10 messages / 24 hours). Start a new chat.";
        chatBody.appendChild(msg);
        autoScroll();
    }
}

// ======================
// SEND MESSAGE
// ======================
async function sendMessage(e) {
    if (e) e.preventDefault();
    if (isProcessing) return;

    const input = document.getElementById("userInput");
    const sendBtn = document.getElementById("sendBtn");
    const chatBody = document.getElementById("chatBody");
    const typing = document.getElementById("typingIndicator");

    if (!input || !sendBtn || !chatBody) return;

    const message = input.value.trim();
    if (!message) return;

    isProcessing = true;
    input.disabled = true;
    sendBtn.style.opacity = "0.6";

    chatBody.insertAdjacentHTML("beforeend", `
        <div class="chat-message user-message">
            <div class="message user">
                <div class="message-content">${message}</div>
                <div class="message-actions">
                    <i class="fa fa-copy copy-btn"></i>
                </div>
            </div>
        </div>
    `);

    input.value = "";
    autoScroll();

    if (typing) {
        typing.style.display = "flex";
        chatBody.appendChild(typing);
    }

    try {
        const res = await fetch("/chatbot/chatbot/", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": getCookie("csrftoken"),
                "X-Requested-With": "XMLHttpRequest"
            },
            body: JSON.stringify({ message })
        });

        if (typing) typing.style.display = "none";

        if (res.status === 403) {
            await res.json();
            forceNewChat();
            isProcessing = false;
            return;
        }

        if (!res.ok) {
            throw new Error("Server error");
        }

        const data = await res.json();

        incrementMessageCount(); // ✅ ONLY here

        chatBody.insertAdjacentHTML("beforeend", `
            <div class="chat-message bot-message">
                <div class="message bot">
                    <div class="message-content">${data.reply.replace(/\n/g, "<br>")}</div>
                    <div class="message-actions">
                        <i class="fa fa-copy copy-btn"></i>
                    </div>
                </div>
            </div>
        `);

        autoScroll();
    } catch (err) {
        console.error(err);
    }

    isProcessing = false;
    input.disabled = false;
    sendBtn.style.opacity = "1";
    input.focus();
}


// ======================
// COPY BUTTON
// ======================
document.addEventListener("click", e => {
    const btn = e.target.closest(".copy-btn");
    if (!btn) return;
    const msg = btn.closest(".message");
    if (!msg) return;

    const clone = msg.cloneNode(true);
    clone.querySelector(".message-actions")?.remove();

    navigator.clipboard.writeText(clone.innerText.trim()).then(() => {
        btn.classList.replace("fa-copy", "fa-check");
        setTimeout(() => btn.classList.replace("fa-check", "fa-copy"), 1000);
    });
});



/************************************INPUT FIED OPTIONS **********************************************/

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
// PAGE LOAD
// ======================
document.addEventListener("DOMContentLoaded", () => {
    autoScroll();
    if (!localStorage.getItem("chatStartTime")) setChatStartTime();
});


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

