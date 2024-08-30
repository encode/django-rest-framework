// import "../../node_modules/bootstrap/js/dist/alert";
import "../../node_modules/bootstrap/js/dist/button";
// import "../../node_modules/bootstrap/js/dist/carousel";
import "../../node_modules/bootstrap/js/dist/collapse";
import "../../node_modules/bootstrap/js/dist/dropdown";
import "../../node_modules/bootstrap/js/dist//modal";
// import "../../node_modules/bootstrap/js/dist/offcanvas";
// import "../../node_modules/bootstrap/js/dist/popover";
// import "../../node_modules/bootstrap/js/dist/scrollspy";
// import "../../node_modules/bootstrap/js/dist/tab";
// import "../../node_modules/bootstrap/js/dist/toast";
// import "../../node_modules/bootstrap/js/dist/tooltip";

import "./prettify-1.0.js";

import "../scss/main.scss";

function setupPrettify() {
  const codeBlocks = document.querySelectorAll("pre code");
  codeBlocks.forEach((block) => {
    block.parentElement.classList.add("prettyprint", "well");
  });
}

setupPrettify();

const getStoredTheme = () => localStorage.getItem("theme");
const setStoredTheme = (theme) => localStorage.setItem("theme", theme);

const getPreferredTheme = () => {
  const storedTheme = getStoredTheme();
  if (storedTheme) {
    return storedTheme;
  }

  return window.matchMedia("(prefers-color-scheme: dark)").matches
    ? "dark"
    : "light";
};

const setTheme = (theme) => {
  if (theme === "auto") {
    document.documentElement.setAttribute(
      "data-bs-theme",
      window.matchMedia("(prefers-color-scheme: dark)").matches
        ? "dark"
        : "light"
    );
  } else {
    document.documentElement.setAttribute("data-bs-theme", theme);
  }
};

setTheme(getPreferredTheme());

const showActiveTheme = (theme, focus = false) => {
  const themeSwitcher = document.querySelector("#bd-theme");

  if (!themeSwitcher) {
    return;
  }

  const activeThemeIcon = document.querySelector(".theme-icon-active");
  const btnToActive = document.querySelector(
    `[data-bs-theme-value="${theme}"]`
  );
  const svgOfActiveBtn = btnToActive.querySelector("svg").cloneNode(true);

  document.querySelectorAll("[data-bs-theme-value]").forEach((element) => {
    element.classList.remove("active");
    element.setAttribute("aria-pressed", "false");
  });

  btnToActive.classList.add("active");
  btnToActive.setAttribute("aria-pressed", "true");
  activeThemeIcon.innerHTML = null;
  activeThemeIcon.appendChild(svgOfActiveBtn);
  const themeSwitcherLabel = `Toggle Theme (${btnToActive.dataset.bsThemeValue})`;
  themeSwitcher.setAttribute("aria-label", themeSwitcherLabel);

  if (focus) {
    themeSwitcher.focus();
  }
};

window
  .matchMedia("(prefers-color-scheme: dark)")
  .addEventListener("change", () => {
    const storedTheme = getStoredTheme();
    if (storedTheme !== "light" && storedTheme !== "dark") {
      setTheme(getPreferredTheme());
    }
  });

window.addEventListener("DOMContentLoaded", () => {
  showActiveTheme(getPreferredTheme());

  document.querySelectorAll("[data-bs-theme-value]").forEach((toggle) => {
    toggle.addEventListener("click", () => {
      const theme = toggle.getAttribute("data-bs-theme-value");
      setStoredTheme(theme);
      setTheme(theme);
      showActiveTheme(theme, true);
    });
  });
});
