/**
 * ThemeSwitcher.js
 * A Micro-Interaction Component (equivalent to a VanJS component for simplicity)
 * Handles persistence and switching of dark/light mode for the entire application.
 * Must be loaded in the <head> or at the beginning of <body> of base_skeleton.html
 */

document.addEventListener('DOMContentLoaded', () => {
    const themeToggle = document.getElementById('theme-toggle');
    const htmlEl = document.documentElement;
    const sunIcon = document.getElementById('sun-icon');
    const moonIcon = document.getElementById('moon-icon');

    if (!themeToggle || !htmlEl || !sunIcon || !moonIcon) {
        console.warn("Theme toggle elements not found. Skipping theme initialization.");
        return;
    }

    /**
     * Reads the preferred theme from localStorage or system preference.
     * @returns {string} 'dark' or 'light'.
     */
    function getStoredTheme() {
        if (localStorage.getItem('theme')) {
            return localStorage.getItem('theme');
        }
        // Fallback to system preference if no explicit choice is stored
        return window.matchMedia('(prefers-color-scheme: light)').matches ? 'light' : 'dark';
    }

    /**
     * Applies the theme to the HTML element and updates the icon.
     * @param {string} themeName 
     */
    function applyTheme(themeName) {
        if (themeName === 'dark') {
            htmlEl.classList.add('dark');
            sunIcon.classList.remove('hidden');
            moonIcon.classList.add('hidden');
        } else {
            htmlEl.classList.remove('dark');
            sunIcon.classList.add('hidden');
            moonIcon.classList.remove('hidden');
        }
        localStorage.setItem('theme', themeName);
    }

    // Initialize theme on load
    applyTheme(getStoredTheme());

    // Toggle logic
    themeToggle.addEventListener('click', () => {
        const currentTheme = htmlEl.classList.contains('dark') ? 'dark' : 'light';
        const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
        applyTheme(newTheme);
    });

    console.log("ThemeSwitcher initialized.");
});