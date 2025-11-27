// Горячие клавиши (Alt+буква) на e.code, чтобы работать на любой раскладке
(function () {
  const actionsByCode = {
    AltKeyH: { type: "nav", url: "/" },
    AltKeyE: { type: "nav", url: "/equipment/list/" },
    AltKeyR: { type: "nav", url: "/rents/create/" },
    AltKeyL: { type: "nav", url: "/rents/" },
    AltKeyP: { type: "nav", url: "/rents/payments/" },
    AltKeyC: { type: "nav", url: "/clients/" },
    AltKeyD: { type: "nav", url: "/debts/monetary/" },
    AltKeyS: { type: "nav", url: "/account/settings/" },
    AltKeyT: { type: "toggleTheme" },
    AltKeyU: { type: "nav", url: "/maintenance/required/" },
    AltKeyB: { type: "nav", url: "/debts/equipment/" },
    AltKeyO: { type: "nav", url: "/csv/" },
    AltKeyM: { type: "nav", url: "/maintenance/" },
    AltKeyK: { type: "nav", url: "/clients/history/" },
    AltKeyF: { type: "focus", selector: "input[type='search'], input[type='text']:not([type='password']), textarea" },
  };

  function isTypingTarget(el) {
    return el && (["INPUT", "TEXTAREA", "SELECT"].includes(el.tagName) || el.isContentEditable);
  }

  function toggleTheme() {
    const html = document.documentElement;
    const current = html.getAttribute("data-theme") || "light";
    const next = current === "dark" ? "light" : "dark";
    if (window.applyTheme) {
      window.applyTheme(next);
    } else {
      html.setAttribute("data-theme", next);
      try {
        localStorage.setItem("theme", next);
      } catch (e) { /* ignore */ }
    }
  }

  function focusFirst(selector) {
    const el = document.querySelector(selector);
    if (el) el.focus();
  }

  document.addEventListener("keydown", (e) => {
    if (e.repeat) return;
    if (!e.altKey) return;
    if (isTypingTarget(document.activeElement)) return;
    const key = `Alt${e.code}`;
    const action = actionsByCode[key];
    if (!action) return;
    e.preventDefault();
    switch (action.type) {
      case "nav":
        window.location.href = action.url;
        break;
      case "toggleTheme":
        toggleTheme();
        break;
      case "focus":
        focusFirst(action.selector);
        break;
      default:
        break;
    }
  });
})();
