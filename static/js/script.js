// =================
// DARK THEME 
// =================
const darkSheet = document.getElementById("darkThemeStylesheet");
const themeToggle = document.getElementById("themeToggle");

// ===== LOAD SAVED THEME =====
const savedTheme = localStorage.getItem("theme");

if(savedTheme === "dark"){
    darkSheet.removeAttribute("disabled");
    themeToggle.checked = true;
}else{
    darkSheet.setAttribute("disabled","true");
    themeToggle.checked = false;
}

// ===== TOGGLE EVENT =====
themeToggle.addEventListener("change", function(){

    if(this.checked){
        darkSheet.removeAttribute("disabled");
        localStorage.setItem("theme","dark");
    }else{
        darkSheet.setAttribute("disabled","true");
        localStorage.setItem("theme","light");
    }

});
// ======================
// 3 DOT MENU (MULTIPLE SAFE)
// ======================

document.addEventListener("click", function (e) {

    // Close all menus if click outside
    document.querySelectorAll(".menu-dropdown").forEach(menu => {
        if (!menu.parentElement.contains(e.target)) {
            menu.style.display = "none";
        }
    });

});

// Toggle individual menu
document.querySelectorAll(".menu-btn").forEach(btn => {
    btn.addEventListener("click", function (e) {
        e.stopPropagation();

        const menu = this.nextElementSibling;

        // Close other open menus first
        document.querySelectorAll(".menu-dropdown").forEach(m => {
            if (m !== menu) m.style.display = "none";
        });

        // Toggle current menu
        menu.style.display =
            menu.style.display === "block" ? "none" : "block";
    });
});


// ======================
// PASSWORD SHOW 
// ======================
function togglePassword(inputId, icon) {
  const input = document.getElementById(inputId);
  const iconElement = icon.querySelector("i");

  if (input.type === "password") {
    input.type = "text";
    iconElement.classList.remove("fa-eye");
    iconElement.classList.add("fa-eye-slash");
  } else {
    input.type = "password";
    iconElement.classList.remove("fa-eye-slash");
    iconElement.classList.add("fa-eye");
  }
}


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
    // Start countdown if there is remaining_seconds
    if (window.REMAINING_SECONDS > 0) {
        startCountdown(window.REMAINING_SECONDS);
    }

    // 🔴 BLOCK USER INPUT if limit reached
    if (window.REMAINING_MESSAGES <= 0) {
        forceLimitReached(window.REMAINING_SECONDS);
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
// MOBILE MODE STREAMING 
// ======================
document.addEventListener("DOMContentLoaded", () => {

    const desktopToggle = document.getElementById("desktopStreamToggle");
    const mobileToggle  = document.getElementById("mobileStreamToggle");

    // If none exist
    if (!desktopToggle && !mobileToggle) return;

    // 🔹 Load saved state
    const savedState = localStorage.getItem("streamingEnabled") === "true";

    if (desktopToggle) desktopToggle.checked = savedState;
    if (mobileToggle)  mobileToggle.checked  = savedState;

    // 🔹 Sync function
    function syncToggles(value) {
        localStorage.setItem("streamingEnabled", value);
        if (desktopToggle) desktopToggle.checked = value;
        if (mobileToggle)  mobileToggle.checked  = value;
    }

    // Desktop → Mobile
    if (desktopToggle) {
        desktopToggle.addEventListener("change", () => {
            syncToggles(desktopToggle.checked);
        });
    }

    // Mobile → Desktop
    if (mobileToggle) {
        mobileToggle.addEventListener("change", () => {
            syncToggles(mobileToggle.checked);
        });
    }

});

let editingMessageElement = null;

// ======================
// COPY EDIT BUTTON
// ======================

document.addEventListener("click", function (e) {

    const copyBtn = e.target.closest(".copy-btn");
    const editBtn = e.target.closest(".edit-btn");

    /* ================= COPY ================= */
    if (copyBtn) {
        const msg = copyBtn.closest(".chat-message");
        if (!msg) return;

        const textDiv = msg.querySelector(".message-content");
        if (!textDiv) return;

        navigator.clipboard.writeText(textDiv.innerText.trim());

        copyBtn.innerHTML = "<i class='fas fa-check-square'></i>";
        setTimeout(() => {
            copyBtn.innerHTML = '<i class="fa fa-copy"></i>';
        }, 800);
    }

    /* ================= EDIT ================= */
    if (editBtn) {
        const msg = editBtn.closest(".chat-message");
        if (!msg || !msg.classList.contains("user-message")) return;

        const textDiv = msg.querySelector(".message-content");
        if (!textDiv) return;

        // prevent multiple edits
        if (msg.querySelector("textarea")) return;

        editingMessageElement = msg;

        const textarea = document.createElement("textarea");
        textarea.className = "edit-textarea";
        textarea.value = textDiv.innerText.trim();

        textDiv.replaceWith(textarea);
        textarea.focus();

        textarea.addEventListener("keydown", function (ev) {
            if (ev.key === "Enter" && !ev.shiftKey) {
                ev.preventDefault();

                document.getElementById("userInput").value = textarea.value;
                document.getElementById("chatForm")
                    .dispatchEvent(new Event("submit"));
            }
        });
    }

});




// ======================
// SEND MESSAGE
// ======================
let isProcessing = false;
let selectedFile = null;
let streamStarted = false;
let serverError = false;  

async function sendMessage(e) {
    if (e) e.preventDefault();
    if (isProcessing) return;

    streamStarted = false;

    const input = document.getElementById("userInput");
    const sendBtn = document.getElementById("sendBtn");
    const chatBody = document.getElementById("chatBody");
    const typing = document.getElementById("typingIndicator");
    const modelSelect = document.getElementById("modelSelect");
    const isStreaming = localStorage.getItem("streamingEnabled") === "true";

    const message = input.value.trim();
    if (!message && !selectedFile) return;

    if (window.REMAINING_MESSAGES <= 0) {
        forceLimitReached(window.REMAINING_SECONDS);
        return;
    }

    isProcessing = true;
    input.disabled = true;
    sendBtn.style.opacity = "0.6";

    const formData = new FormData();
    formData.append("message", message);
    formData.append("chat_id", String(window.CHAT_ID));
    formData.append("model", modelSelect.value);

    if (selectedFile) formData.append("file", selectedFile);

    try {

        // ✅ 1. SEND REQUEST FIRST (check legal)
        const res = await fetch(isStreaming ? "/chatbot/stream/" : "/chatbot/", {
            method: "POST",
            headers: {
                "X-CSRFToken": getCookie("csrftoken"),
                "X-Requested-With": "XMLHttpRequest"
            },
            body: formData
        });

        // 🚫 2. ILLEGAL → popup only
        if (res.status === 403) {
            alert("Don't share illegal content or personal info");

            isProcessing = false;
            input.disabled = false;
            sendBtn.style.opacity = "1";
            return;
        }

        // ✅ 3. SHOW USER MESSAGE
        chatBody.insertAdjacentHTML("beforeend", `
            <div class="chat-message user-message">
                <div class="message user">
                    <div class="message-content message-text">${message}</div>
                </div>
            </div>
        `);

        // ✅ 4. SHOW TYPING
        if (typing) {
            typing.style.display = "flex";
            chatBody.appendChild(typing);
        }

        autoScroll();

        // ======================
        // NON STREAM
        // ======================
        if (!isStreaming) {
            const data = await res.json();

            if (typing) typing.style.display = "none";

            const botWrapper = document.createElement("div");
            botWrapper.className = "chat-message bot-message";

            const botMsg = document.createElement("div");
            botMsg.className = "message bot";

            const botContent = document.createElement("div");
            botContent.className = "message-content markdown-content message-text";
            botContent.innerHTML = DOMPurify.sanitize(marked.parse(data.reply || ""));

            botMsg.appendChild(botContent);
            botWrapper.appendChild(botMsg);
            chatBody.appendChild(botWrapper);

            autoScroll();
        }

        // ======================
        // STREAM
        // ======================
        if (isStreaming) {
            const reader = res.body.getReader();
            const decoder = new TextDecoder();

            const botWrapper = document.createElement("div");
            botWrapper.className = "chat-message bot-message";

            const botMsg = document.createElement("div");
            botMsg.className = "message bot";

            const botContent = document.createElement("div");
            botContent.className = "message-content markdown-content message-text";

            botMsg.appendChild(botContent);
            botWrapper.appendChild(botMsg);
            chatBody.appendChild(botWrapper);

            let fullMarkdown = "";

            while (true) {
                const { value, done } = await reader.read();
                if (done) break;

                const chunk = decoder.decode(value, { stream: true });

                if (!streamStarted && chunk.trim()) {
                    streamStarted = true;
                    if (typing) typing.style.display = "none";
                }

                fullMarkdown += chunk;
                botContent.innerHTML = DOMPurify.sanitize(marked.parse(fullMarkdown));
                autoScroll();
            }
        }

        window.REMAINING_MESSAGES--;

    } catch (err) {
        if (typing) typing.style.display = "none";
    }

    // RESET
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

document.addEventListener("DOMContentLoaded", () => {
    const chatBody = document.getElementById("chatBody");
    if (chatBody) {
        chatBody.scrollTop = chatBody.scrollHeight;
    }
});

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
// ARCHIVE HISTORY LOGIC
// ======================


function archiveChat(chatId){

    fetch(`/archive/${chatId}/`,{
        method:"POST",
        headers:{
            "X-CSRFToken": getCookie("csrftoken")
        }
    })
    .then(res=>res.json())
    .then(data=>{

        const row = document.querySelector(`[data-chat="${chatId}"]`);
        if(!row) return;

        const group = row.closest(".history-group");

        row.style.opacity="0";
        row.style.transform="translateX(40px)";

        setTimeout(()=>{

            row.remove();

            if(group && group.querySelectorAll(".history-row").length === 0){
                group.remove();
            }

        },250);

    });
}

// ======================
// UNARCHIVE HISTORY LOGIC
// ======================


function unarchiveChat(chatId){

    fetch(`/unarchive/${chatId}/`,{
        method:"POST",
        headers:{
            "X-CSRFToken": getCookie("csrftoken")
        }
    })
    .then(res=>res.json())
    .then(data=>{

        const row = document.querySelector(`[data-chat="${chatId}"]`);
        if(!row) return;

        const group = row.closest(".history-group");

        row.style.opacity="0";
        row.style.transform="translateX(40px)";

        setTimeout(()=>{

            row.remove();

            if(group && group.querySelectorAll(".history-row").length === 0){
                group.remove();
            }

        },250);

    });
    

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


