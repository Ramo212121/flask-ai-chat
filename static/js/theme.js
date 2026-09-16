document.addEventListener("DOMContentLoaded", () => {
    const themeToggle = document.getElementById("theme-toggle");
    const hljsLight = document.getElementById("hljs-light");
    const hljsDark = document.getElementById("hljs-dark");

    function applyHighlightTheme(theme) {
        if (!hljsLight || !hljsDark) return;
        if (theme === "dark") {
            hljsLight.disabled = true;
            hljsDark.disabled = false;
        } else {
            hljsLight.disabled = false;
            hljsDark.disabled = true;
        }
    }

    // Set initial icon + highlight theme
    const currentTheme = document.documentElement.getAttribute("data-theme") || "light";
    applyHighlightTheme(currentTheme);

    if (themeToggle) {
        themeToggle.textContent = currentTheme === "dark" ? "☀️" : "🌙";

        themeToggle.addEventListener("click", () => {
            const current = document.documentElement.getAttribute("data-theme") || "light";
            const next = current === "dark" ? "light" : "dark";

            document.documentElement.setAttribute("data-theme", next);
            localStorage.setItem("theme", next);

            themeToggle.textContent = next === "dark" ? "☀️" : "🌙";
            applyHighlightTheme(next);
        });
    }
});