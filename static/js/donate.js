let categorySelected = false;
let quantitySelected = false;
let locationSelected = false;

// Function to send user message
function sendMessage() {
  const input = document.getElementById("userInput");
  const msg = input.value.trim();
  if (!msg) return;

  addMessage("user", msg);
  input.value = "";

  setTimeout(() => {
    botReply(handleUserInput(msg));
  }, 800);
}

// Function to add messages to chat
function addMessage(type, text) {
  const chatBox = document.getElementById("chatboxBody");
  const msgDiv = document.createElement("div");
  msgDiv.className = `message ${type}`;
  msgDiv.textContent = text;
  chatBox.appendChild(msgDiv);
  chatBox.scrollTop = chatBox.scrollHeight;
}

// Function for bot's responses
function botReply(text) {
  addMessage("bot", text);
}

// Handle user input
function handleUserInput(msg) {
  msg = msg.toLowerCase();
  
  if (!categorySelected) {
    categorySelected = true;
    return askCategory();
  }

  if (!quantitySelected && (msg.includes("clothes") || msg.includes("books") || msg.includes("accessory"))) {
    return askQuantity();
  }

  if (!quantitySelected && !isNaN(msg)) {
    quantitySelected = true;
    return askLocation();
  }

  if (!locationSelected) {
    locationSelected = true;
    return showLocationOptions();
  }

  return "I didn't quite understand. Could you please clarify?";
}

// Ask for category selection
function askCategory() {
  return "Please select the category of your donation: \n1. Clothes \n2. Books \n3. Accessories";
}

// Ask for quantity
function askQuantity() {
  return "How many items would you like to donate? Please enter a number (e.g., 10).";
}

// Ask for location options
function showLocationOptions() {
  return `Please select your city to find nearby NGOs:
          1. Bhopal
          2. Indore
          3. Gwalior
          4. Jabalpur`;
}

// Get user's city selection
function handleLocationSelection(city) {
  const cityMapping = {
    "bhopal": "Bhopal",
    "indore": "Indore",
    "gwalior": "Gwalior",
    "jabalpur": "Jabalpur",
  };

  if (cityMapping[city]) {
    return `Thanks for selecting ${cityMapping[city]}. I will now show you nearby NGOs for donation.`;
  } else {
    return "I didn't recognize your city. Please select one of the listed cities.";
  }
}
