/*
File: static/js/admin_dashboard.js

What it does:
  - Opens and closes the admin booking and event panels.
  - Restores the requested panel after a server-side redirect.

Why it is separate:
  - Keeps the admin interaction logic away from the public-site scripts.
*/

document.addEventListener("DOMContentLoaded", () => {
  const pageBody = document.body;
  const panelOverlays = Array.from(document.querySelectorAll(".admin-panel-overlay"));
  const openPanelButtons = document.querySelectorAll(
    ".admin-action-card[data-open-admin-panel], " +
      ".admin-support-card[data-open-admin-panel], " +
      ".admin-session-link[data-open-admin-panel]"
  );
  const closePanelButtons = document.querySelectorAll("[data-close-admin-panel]");
  const passwordToggleButtons = document.querySelectorAll("[data-password-toggle]");
  const validatedInputs = Array.from(
    document.querySelectorAll(
      ".admin-form input, .admin-form textarea, .admin-form select"
    )
  );

  const panelNameToId = {
    bookings: "bookingsPanel",
    bookingsPanel: "bookingsPanel",
    events: "eventsPanel",
    eventsPanel: "eventsPanel",
    publicSitePassword: "publicSitePasswordPanel",
    publicSitePasswordPanel: "publicSitePasswordPanel",
    checklist: "checklistPanel",
    checklistPanel: "checklistPanel",
    adminAccountPassword: "adminAccountPasswordPanel",
    adminAccountPasswordPanel: "adminAccountPasswordPanel",
  };

  function closeAllPanels() {
    panelOverlays.forEach((panelOverlay) => {
      panelOverlay.hidden = true;
    });
    pageBody.dataset.openAdminPanel = "";
  }

  function openPanel(panelNameOrId) {
    closeAllPanels();
    const targetPanelId = panelNameToId[panelNameOrId];
    if (!targetPanelId) {
      return;
    }

    const targetPanel = document.getElementById(targetPanelId);
    if (!targetPanel) {
      return;
    }

    targetPanel.hidden = false;
    pageBody.dataset.openAdminPanel = targetPanelId;
  }

  openPanelButtons.forEach((openButton) => {
    openButton.addEventListener("click", () => {
      openPanel(openButton.dataset.openAdminPanel);
    });
  });

  closePanelButtons.forEach((closeButton) => {
    closeButton.addEventListener("click", () => {
      closeAllPanels();
    });
  });

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
    if (passwordInput) {
      passwordInput.type = "password";
    }

    applyPasswordVisibilityState(toggleButton, false);

    toggleButton.addEventListener("click", () => {
      const buttonInputShell = toggleButton.closest(".password-input-shell");
      const passwordInput = buttonInputShell?.querySelector("input");
      if (!passwordInput) {
        return;
      }

      const isCurrentlyHidden = passwordInput.type === "password";
      passwordInput.type = isCurrentlyHidden ? "text" : "password";
      applyPasswordVisibilityState(toggleButton, isCurrentlyHidden);
    });
  });

  panelOverlays.forEach((panelOverlay) => {
    panelOverlay.addEventListener("click", (event) => {
      if (event.target === panelOverlay) {
        closeAllPanels();
      }
    });
  });

  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape") {
      closeAllPanels();
    }
  });

  const panelToOpenOnLoad = pageBody.dataset.openAdminPanel;
  closeAllPanels();
  if (panelToOpenOnLoad) {
    openPanel(panelToOpenOnLoad);
  }

  function isValidIsoDate(value) {
    const isoDateMatch = /^(\d{4})-(\d{2})-(\d{2})$/.exec(value);
    if (!isoDateMatch) {
      return false;
    }

    const year = Number(isoDateMatch[1]);
    const month = Number(isoDateMatch[2]);
    const day = Number(isoDateMatch[3]);
    const candidateDate = new Date(Date.UTC(year, month - 1, day));

    return (
      candidateDate.getUTCFullYear() === year &&
      candidateDate.getUTCMonth() === month - 1 &&
      candidateDate.getUTCDate() === day
    );
  }

  function isValidTwentyFourHourTime(value) {
    const timeMatch = /^(\d{2}):(\d{2})$/.exec(value);
    if (!timeMatch) {
      return false;
    }

    const hours = Number(timeMatch[1]);
    const minutes = Number(timeMatch[2]);
    return hours >= 0 && hours <= 23 && minutes >= 0 && minutes <= 59;
  }

  function isStrongSharedPassword(value) {
    return (
      value.length >= 8 &&
      /[A-ZÅÄÖ]/.test(value) &&
      /\d/.test(value) &&
      /[^A-Za-z0-9ÅÄÖåäö]/.test(value)
    );
  }

  function getCustomValidationMessage(inputElement) {
    const trimmedValue = inputElement.value.trim();
    if (!trimmedValue) {
      if (inputElement.required) {
        return (
          inputElement.dataset.requiredMessage || "Det här fältet måste fyllas i."
        );
      }

      return "";
    }

    if (inputElement.type === "email" && inputElement.validity.typeMismatch) {
      return "Ange en giltig e-postadress.";
    }

    if (inputElement.type === "url" && inputElement.validity.typeMismatch) {
      return "Ange en giltig webbadress.";
    }

    if (inputElement.type === "number") {
      const numericValue = Number(trimmedValue);
      if (Number.isNaN(numericValue)) {
        return "Ange ett giltigt tal.";
      }

      if (inputElement.min && numericValue < Number(inputElement.min)) {
        return `Värdet måste vara minst ${inputElement.min}.`;
      }
    }

    if (inputElement.dataset.validationType === "date") {
      return isValidIsoDate(trimmedValue)
        ? ""
        : inputElement.dataset.formatMessage ||
            "Ange datum i formatet ÅÅÅÅ-MM-DD.";
    }

    if (inputElement.dataset.validationType === "time") {
      return isValidTwentyFourHourTime(trimmedValue)
        ? ""
        : inputElement.dataset.formatMessage ||
            "Ange tid i 24-timmarsformatet TT:MM.";
    }

    if (inputElement.dataset.validationType === "password-strength") {
      return isStrongSharedPassword(trimmedValue)
        ? ""
        : "Ange minst 8 tecken, minst en versal, en siffra och ett specialtecken.";
    }

    if (inputElement.dataset.validationType === "password-confirmation") {
      const matchingFieldName = inputElement.dataset.matchField;
      const matchingInput = matchingFieldName
        ? inputElement.form?.querySelector(`[name="${matchingFieldName}"]`)
        : null;

      return matchingInput && trimmedValue !== matchingInput.value.trim()
        ? "Bekräftelsen måste matcha det nya lösenordet."
        : "";
    }

    if (
      inputElement.dataset.minLengthMessage &&
      inputElement.minLength > 0 &&
      trimmedValue.length < inputElement.minLength
    ) {
      return inputElement.dataset.minLengthMessage;
    }

    return "";
  }

  validatedInputs.forEach((inputElement) => {
    const applyValidationMessage = () => {
      inputElement.setCustomValidity(getCustomValidationMessage(inputElement));
    };

    inputElement.addEventListener("input", applyValidationMessage);
    inputElement.addEventListener("invalid", applyValidationMessage);
  });

  document
    .querySelectorAll("[data-password-rotation-form]")
    .forEach((passwordForm) => {
      passwordForm.addEventListener("submit", (event) => {
        const passwordInputs = Array.from(
          passwordForm.querySelectorAll("input")
        );

        passwordInputs.forEach((inputElement) => {
          inputElement.setCustomValidity(getCustomValidationMessage(inputElement));
        });

        if (!passwordForm.checkValidity()) {
          event.preventDefault();
          passwordForm.reportValidity();
        }
      });
    });
});
