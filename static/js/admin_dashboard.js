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
});
