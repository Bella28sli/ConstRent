(() => {
    const themes = {
        light: {
            background: "#F0F0F0",
            accent: "#143EE6",
            text_primary: "#3C337E",
            surface: "#85AECF",
            error_text: "#D30D0A",
            on_surface: "#FFFFFF",
        },
        dark: {
            background: "#121212",
            accent: "#4C6DFF",
            text_primary: "#D2D0FF",
            surface: "#1E2A35",
            error_text: "#FF6B6B",
            on_surface: "#FFFFFF",
        },
    };

    const applyTheme = (mode) => {
        const palette = themes[mode] || themes.light;
        const root = document.documentElement;
        root.setAttribute("data-theme", mode);
        root.style.setProperty("--background", palette.background);
        root.style.setProperty("--accent", palette.accent);
        root.style.setProperty("--text-primary", palette.text_primary);
        root.style.setProperty("--surface", palette.surface);
        root.style.setProperty("--error-text", palette.error_text);
        root.style.setProperty("--on-surface", palette.on_surface);
    };

    const saved = localStorage.getItem("theme_mode") || "light";
    applyTheme(saved);

    // Можно добавить переключатель темы по кнопке, если появится на странице
    window.applyTheme = applyTheme;
    window.switchTheme = () => {
        const current = document.documentElement.getAttribute("data-theme") || "light";
        const next = current === "light" ? "dark" : "light";
        localStorage.setItem("theme_mode", next);
        applyTheme(next);
    };
})();
