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
    ".admin-action-card[data-open-admin-panel]"
  );
  const closePanelButtons = document.querySelectorAll("[data-close-admin-panel]");
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
  };

  function closeAllPanels() {
    panelOverlays.forEach((panelOverlay) => {
      panelOverlay.hidden = true;
    });
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

  closeAllPanels();

  const panelToOpenOnLoad = pageBody.dataset.openAdminPanel;
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

    return "";
  }

  validatedInputs.forEach((inputElement) => {
    const applyValidationMessage = () => {
      inputElement.setCustomValidity(getCustomValidationMessage(inputElement));
    };

    inputElement.addEventListener("input", applyValidationMessage);
    inputElement.addEventListener("invalid", applyValidationMessage);
  });
});
