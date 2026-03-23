/*
File: static/js/toasts.js

What it does:
  - Adds dismiss behavior for shared toast messages.
  - Supports click-to-close and automatic fade-out after a short delay.
  - Pauses the auto-dismiss timer while the user hovers or focuses a toast.

Why it is separate:
  - The same toast behavior is used on the public, login, and admin pages.
*/

document.addEventListener("DOMContentLoaded", () => {
  const toastElements = document.querySelectorAll(
    ".home-toast, .login-toast, .admin-toast"
  );

  function dismissToast(toastElement) {
    if (
      !toastElement ||
      toastElement.classList.contains("toast-is-hiding") ||
      !toastElement.isConnected
    ) {
      return;
    }

    toastElement.classList.add("toast-is-hiding");
    window.setTimeout(() => {
      toastElement.remove();
    }, 260);
  }

  toastElements.forEach((toastElement) => {
    let hideTimerId = 0;
    const autoDismissDelayMs = toastElement.className.includes("-error")
      ? 7000
      : 5000;

    function startHideTimer() {
      window.clearTimeout(hideTimerId);
      hideTimerId = window.setTimeout(() => {
        dismissToast(toastElement);
      }, autoDismissDelayMs);
    }

    function stopHideTimer() {
      window.clearTimeout(hideTimerId);
    }

    toastElement.tabIndex = 0;
    toastElement.setAttribute("role", "button");
    toastElement.setAttribute(
      "aria-label",
      "Meddelande. Klicka eller tryck Enter för att stänga."
    );

    toastElement.addEventListener("click", () => {
      dismissToast(toastElement);
    });

    toastElement.addEventListener("keydown", (event) => {
      if (event.key === "Enter" || event.key === " ") {
        event.preventDefault();
        dismissToast(toastElement);
      }
    });

    toastElement.addEventListener("mouseenter", stopHideTimer);
    toastElement.addEventListener("mouseleave", startHideTimer);
    toastElement.addEventListener("focus", stopHideTimer);
    toastElement.addEventListener("blur", startHideTimer);

    startHideTimer();
  });
});
