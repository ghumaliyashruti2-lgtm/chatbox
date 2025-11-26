function sendQuick(text){
  sendToChat(text);
  botReply(text);
}

function sendMessage() {
  let input = document.getElementById("userInput");
  if (input.value.trim() == "") return;
  sendToChat(input.value);
  botReply(input.value);
  input.value = "";
}

function sendToChat(text){
  let chatBody = document.getElementById("chatBody");
  let userMsg = document.createElement("div");
  userMsg.classList.add("user-message");
  userMsg.innerText = text;
  chatBody.appendChild(userMsg);
  chatBody.scrollTop = chatBody.scrollHeight;
}

// ----------------------
// BOT REPLY LOGIC
// ----------------------

function botReply(text){
  let lower = text.toLowerCase();

  if(lower.includes("course")){
    showCourseButtons();
  }
  else {
    let reply = "";

    if(lower.includes("fees"))
      reply = "Course fees start from ₹4,999 to ₹24,999 depending on module.";
    else if(lower.includes("duration"))
      reply = "Course duration varies 4–12 weeks.";
    else if(lower.includes("location") || lower.includes("contact"))
      reply = "Nana Varachha, Surat • +91 87805 62404";
    else if(lower.includes("job"))
      reply = "We provide placement support after course completion.";
    else
      reply = "Thank you! Our team will assist you shortly 😊";

    showBotMessage(reply);
  }
}

// ----------------------
// SHOW NORMAL BOT TEXT
// ----------------------

function showBotMessage(text){
  setTimeout(()=>{
    let chatBody = document.getElementById("chatBody");
    let botMsg = document.createElement("div");
    botMsg.classList.add("bot-message");
    botMsg.innerText = text;
    chatBody.appendChild(botMsg);
    chatBody.scrollTop = chatBody.scrollHeight;
  }, 400);
}

// ----------------------
// SHOW COURSE BUTTONS
// ----------------------

function showCourseButtons(){
  setTimeout(()=>{
    let chatBody = document.getElementById("chatBody");

    const courses = [
      "Python",
      "Java",
      "Full Stack",
      "Web Development",
      "More"
    ];

    let box = document.createElement("div");
    box.classList.add("course-options-box");

    courses.forEach(course => {
      let btn = document.createElement("button");
      btn.classList.add("smart-option-btn");
      btn.innerText = course;

      btn.addEventListener("click", () => {
        sendToChat(course);
        botReply(course);
      });

      box.appendChild(btn);
    });

    chatBody.appendChild(box);
    chatBody.scrollTop = chatBody.scrollHeight;

  }, 400);
}


