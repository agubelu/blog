"use strict";

let toggle = null;
let darkMode = false;

// Main function that will run when the page is ready
function main() {
    toggle = document.getElementById("dark-mode-toggle");

    // On initial load, check if we have a stored preference
    let stored = localStorage.getItem("theme");
    if (stored !== null) {
        setDarkMode(stored === "dark");
        // Otherwise, apply the dark theme if it's the user's preferred theme
        // on their system, but without remembering the preference
    } else if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
        setDarkMode(true);
        // If there is no stored preference and the system's theme is not "dark" or
        // it's not available for querying, default to the light theme
    } else {
        setDarkMode(false);
    }

    // Set the event handler for when the user changes the theme manually
    toggle.onchange = () => setDarkMode(!toggle.checked, true);
}

function setDarkMode(switchOn, remember = false) {
    darkMode = switchOn;
    toggle.checked = !darkMode;

    if (switchOn) {
        document.documentElement.setAttribute("data-theme", 'dark');
    } else {
        document.documentElement.removeAttribute("data-theme");
    }

    if (remember) {
        localStorage.setItem("theme", darkMode ? "dark" : "light");
    }
}

document.addEventListener("DOMContentLoaded", main);