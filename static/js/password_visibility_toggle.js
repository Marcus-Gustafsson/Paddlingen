/*
File: static/js/password_visibility_toggle.js

What it does:
  - Adds show/hide password behavior to any password field that uses the
    shared data-password-toggle markup.

Why it is separate:
  - The same interaction is used on both admin and public login-related pages.
  - Keeping it shared avoids duplicating the same toggle logic in multiple
    page-specific scripts.
*/

document.addEventListener("DOMContentLoaded", () => {
  const passwordToggleButtons = document.querySelectorAll("[data-password-toggle]");

  function applyPasswordVisibilityState(toggleButton, isPasswordVisible) {
    const hiddenPasswordIcon = toggleButton.querySelector(
      ".password-visibility-icon--password-hidden"
    );
    const visiblePasswordIcon = toggleButton.querySelector(
      ".password-visibility-icon--password-visible"
    );

    function setIconVisibility(iconElement, shouldShow) {
      if (!iconElement) {
        return;
      }

      iconElement.hidden = !shouldShow;
      iconElement.style.display = shouldShow ? "block" : "none";
    }

    setIconVisibility(hiddenPasswordIcon, !isPasswordVisible);
    setIconVisibility(visiblePasswordIcon, isPasswordVisible);

    toggleButton.setAttribute("aria-pressed", String(isPasswordVisible));
    toggleButton.setAttribute(
      "aria-label",
      isPasswordVisible
        ? toggleButton.dataset.hideLabel || "Dölj lösenord"
        : toggleButton.dataset.showLabel || "Visa lösenord"
    );
  }

  passwordToggleButtons.forEach((toggleButton) => {
    const inputShell = toggleButton.closest(".password-input-shell");
    const passwordInput = inputShell?.querySelector("input");
    if (!passwordInput) {
      return;
    }

    passwordInput.type = "password";
    applyPasswordVisibilityState(toggleButton, false);

    toggleButton.addEventListener("click", () => {
      const isCurrentlyHidden = passwordInput.type === "password";
      passwordInput.type = isCurrentlyHidden ? "text" : "password";
      applyPasswordVisibilityState(toggleButton, isCurrentlyHidden);
    });
  });
});
