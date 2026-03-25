/**
 * File: app/static/js/modals.js
 *
 * What it does:
 *   - Controls the shared public popups used on the homepage.
 *   - Handles opening and closing the FAQ, contact, and participant overview
 *     modals.
 *   - Handles FAQ tab switching inside the FAQ modal.
 *
 * Why it is here:
 *   - Keeping modal behavior in its own file makes the remaining public-page
 *     JavaScript easier to read and maintain.
 */

(function registerModalModule() {
  /**
   * Show a modal element.
   *
   * Args:
   *   modalElement: The modal container to show.
   */
  function openModal(modalElement) {
    if (!modalElement) {
      return;
    }

    modalElement.style.display = "flex";
  }

  /**
   * Hide a modal element.
   *
   * Args:
   *   modalElement: The modal container to hide.
   */
  function closeModal(modalElement) {
    if (!modalElement) {
      return;
    }

    modalElement.style.display = "none";
  }

  /**
   * Add FAQ tab switching inside the FAQ modal.
   *
   * Args:
   *   faqModalElement: The FAQ modal container.
   */
  function registerFaqTabs(faqModalElement) {
    if (!faqModalElement) {
      return;
    }

    const tabButtons = faqModalElement.querySelectorAll(".modal-tab");
    const tabPanels = faqModalElement.querySelectorAll(".modal-body");

    tabButtons.forEach((button) => {
      const targetPanelId = button.getAttribute("data-tab");
      const targetPanel = targetPanelId
        ? faqModalElement.querySelector(`#${targetPanelId}`)
        : null;

      if (targetPanel) {
        button.setAttribute("aria-controls", targetPanel.id);
      }
    });

    tabButtons.forEach((button) => {
      button.addEventListener("click", () => {
        const targetPanelId = button.getAttribute("data-tab");

        tabButtons.forEach((tabButton) => {
          tabButton.classList.remove("modal-tab--active");
          tabButton.setAttribute("aria-selected", "false");
        });

        tabPanels.forEach((panel) => {
          panel.classList.add("modal-body--hidden");
          panel.hidden = true;
        });

        button.classList.add("modal-tab--active");
        button.setAttribute("aria-selected", "true");

        const activePanel = targetPanelId
          ? faqModalElement.querySelector(`#${targetPanelId}`)
          : null;

        if (activePanel) {
          activePanel.classList.remove("modal-body--hidden");
          activePanel.hidden = false;
        }
      });
    });
  }

  /**
   * Register expandable grouped rows that reveal hidden canoe details.
   *
   * Args:
   *   rootElement: Container where grouped-row buttons should be found.
   */
  function registerGroupedDetailToggles(rootElement) {
    if (!rootElement) {
      return;
    }

    const toggleButtons = rootElement.querySelectorAll("[data-toggle-grouped-details]");
    toggleButtons.forEach((toggleButton) => {
      const detailsId = toggleButton.getAttribute("aria-controls");
      const detailsElement = detailsId
        ? rootElement.querySelector(`#${detailsId}`)
        : null;

      if (!detailsElement) {
        return;
      }

      toggleButton.addEventListener("click", () => {
        const shouldExpand = toggleButton.getAttribute("aria-expanded") !== "true";
        toggleButton.setAttribute("aria-expanded", String(shouldExpand));
        detailsElement.hidden = !shouldExpand;
        toggleButton
          .closest(".participant-overview-group")
          ?.classList.toggle("participant-overview-group--expanded", shouldExpand);
      });
    });
  }

  /**
   * Register the shared public modals used on the homepage.
   */
  function registerPublicModals() {
    const faqButton = document.getElementById("faqBtn");
    const contactButton = document.getElementById("contactBtn");
    const overviewTrigger = document.getElementById("overviewTrigger");
    const faqModal = document.getElementById("faqModal");
    const contactModal = document.getElementById("contactModal");
    const overviewModal = document.getElementById("overviewModal");
    const closeButtons = document.querySelectorAll(".modal-close");

    if (faqButton && faqModal) {
      faqButton.addEventListener("click", () => openModal(faqModal));
    }

    if (contactButton && contactModal) {
      contactButton.addEventListener("click", () => openModal(contactModal));
    }

    if (overviewTrigger && overviewModal) {
      overviewTrigger.addEventListener("click", () => openModal(overviewModal));
      overviewTrigger.addEventListener("keydown", (event) => {
        if (event.key === "Enter" || event.key === " ") {
          event.preventDefault();
          openModal(overviewModal);
        }
      });
    }

    closeButtons.forEach((button) => {
      button.addEventListener("click", () => {
        const parentModal = button.closest(".modal");
        if (parentModal && parentModal.id === "bookingModal") {
          return;
        }
        closeModal(parentModal);
      });
    });

    [faqModal, contactModal, overviewModal].forEach((modalElement) => {
      if (!modalElement) {
        return;
      }

      modalElement.addEventListener("click", (event) => {
        if (event.target === modalElement) {
          closeModal(modalElement);
        }
      });
    });

    document.addEventListener("keydown", (event) => {
      if (event.key === "Escape") {
        [faqModal, contactModal, overviewModal].forEach(closeModal);
      }
    });

    registerFaqTabs(faqModal);
    registerGroupedDetailToggles(overviewModal);
  }

  window.PaddlingenModals = {
    registerPublicModals,
  };
})();
