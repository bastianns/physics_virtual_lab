// Selecting necessary elements
const body = document.querySelector("body"),
    sidebar = body.querySelector(".sidebar"),
    toggle = body.querySelector(".toggle"),  // Unified the toggle selector
    searchBtn = body.querySelector(".search-box"),
    modeSwitch = body.querySelector(".toggle-switch"),
    modeText = body.querySelector(".mode-text");

// Sidebar toggle function
toggle.addEventListener("click", () => {
    sidebar.classList.toggle("close");
});

// Dark mode switch function
modeSwitch.addEventListener("click", () => {
    body.classList.toggle("dark");
});

