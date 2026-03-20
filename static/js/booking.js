/**
 * File: app/static/js/booking.js
 *
 * What it does:
 *   - Controls the public booking modal.
 *   - Handles the two-step booking flow, participant field generation, and
 *     the booking summary shown before submission.
 *
 * Why it is here:
 *   - Keeping the booking flow in its own file makes the public JavaScript
 *     easier to understand and keeps the most stateful homepage feature
 *     isolated from the other UI modules.
 */

(function registerBookingModule() {
  const eventSettings = window.PADDLINGEN_EVENT_SETTINGS || {};
  const pricePerCanoeSek = eventSettings.price_per_canoe_sek || 1200;

  /**
   * Create the empty-state row shown before any canoes are selected.
   *
   * Returns:
   *   A list item element that explains how the booking summary works.
   */
  function buildEmptySummaryItem() {
    const emptySummaryItem = document.createElement("li");
    emptySummaryItem.className = "booking-summary-empty";
    emptySummaryItem.textContent =
      "Välj antal kanoter för att se översikten.";
    return emptySummaryItem;
  }

  /**
   * Register the booking modal and participant field generation.
   */
  function registerBookingModal() {
    const openButton = document.getElementById("bookBtn");
    const modalElement = document.getElementById("bookingModal");
    const formElement = document.getElementById("bookingForm");
    const canoeCountInput = document.getElementById("canoeCount");
    const quantityOptionButtons = document.querySelectorAll(".quantity-option");
    const bookingStepOneElement = document.getElementById("bookingStepOne");
    const bookingStepTwoElement = document.getElementById("bookingStepTwo");
    const bookingStepLabelElement = document.getElementById("bookingStepLabel");
    const nameFieldsContainer = document.getElementById("nameFieldsContainer");
    const priceInfoElement = document.getElementById("priceInfo");
    const bookingSummaryListElement = document.getElementById("bookingSummaryList");
    const summaryCanoeCountElement = document.getElementById("summaryCanoeCount");
    const bookingPaymentNoteElement = document.getElementById("bookingPaymentNote");
    const cancelButton = document.getElementById("cancelBooking");
    const submitButton = document.getElementById("confirmBooking");

    if (
      !openButton ||
      !modalElement ||
      !formElement ||
      !canoeCountInput ||
      !bookingStepOneElement ||
      !bookingStepTwoElement ||
      !bookingStepLabelElement ||
      !nameFieldsContainer ||
      !priceInfoElement ||
      !bookingSummaryListElement ||
      !summaryCanoeCountElement ||
      !bookingPaymentNoteElement ||
      !cancelButton ||
      !submitButton
    ) {
      return;
    }

    let currentBookingStep = 1;
    let selectedCanoeCount = 0;

    function updateStepVisibility() {
      const isStepOneActive = currentBookingStep === 1;
      bookingStepOneElement.hidden = !isStepOneActive;
      bookingStepTwoElement.hidden = isStepOneActive;
      bookingPaymentNoteElement.hidden = isStepOneActive;
      bookingStepOneElement.classList.toggle(
        "booking-step--active",
        isStepOneActive
      );
      bookingStepTwoElement.classList.toggle(
        "booking-step--active",
        !isStepOneActive
      );

      if (isStepOneActive) {
        bookingStepLabelElement.textContent = "Steg 1 av 2";
        cancelButton.textContent = "Avbryt";
        submitButton.textContent = "Fortsätt";
        submitButton.disabled = selectedCanoeCount === 0;
        return;
      }

      bookingStepLabelElement.textContent = "Steg 2 av 2";
      cancelButton.textContent = "Tillbaka";
      submitButton.textContent = "Fortsätt till betalning";
      validateParticipantForm();
    }

    function resetQuantitySelection() {
      quantityOptionButtons.forEach((button) => {
        button.classList.remove("is-selected");
        button.setAttribute("aria-pressed", "false");
      });
    }

    function buildParticipantFields(canoeCount) {
      nameFieldsContainer.innerHTML = "";

      for (let canoeNumber = 1; canoeNumber <= canoeCount; canoeNumber += 1) {
        const fieldWrapper = document.createElement("section");
        fieldWrapper.className = "canoe-field";

        const canoeLabel = document.createElement("label");
        canoeLabel.setAttribute("for", `canoe${canoeNumber}_fname`);
        canoeLabel.textContent = `Kanot ${canoeNumber}`;
        fieldWrapper.appendChild(canoeLabel);

        const inputsContainer = document.createElement("div");
        inputsContainer.className = "inputs";

        const firstNameInput = document.createElement("input");
        firstNameInput.type = "text";
        firstNameInput.id = `canoe${canoeNumber}_fname`;
        firstNameInput.name = `canoe${canoeNumber}_fname`;
        firstNameInput.placeholder = "Förnamn";
        firstNameInput.maxLength = 15;
        firstNameInput.required = true;

        const lastNameInput = document.createElement("input");
        lastNameInput.type = "text";
        lastNameInput.id = `canoe${canoeNumber}_lname`;
        lastNameInput.name = `canoe${canoeNumber}_lname`;
        lastNameInput.placeholder = "Efternamn";
        lastNameInput.maxLength = 18;
        lastNameInput.required = true;

        inputsContainer.appendChild(firstNameInput);
        inputsContainer.appendChild(lastNameInput);
        fieldWrapper.appendChild(inputsContainer);
        nameFieldsContainer.appendChild(fieldWrapper);
      }
    }

    function updateBookingSummary() {
      bookingSummaryListElement.innerHTML = "";

      if (selectedCanoeCount === 0) {
        bookingSummaryListElement.appendChild(buildEmptySummaryItem());
        summaryCanoeCountElement.textContent = "0";
        priceInfoElement.textContent = "0 kr";
        return;
      }

      summaryCanoeCountElement.textContent = String(selectedCanoeCount);
      priceInfoElement.textContent = `${selectedCanoeCount * pricePerCanoeSek} kr`;

      for (let canoeNumber = 1; canoeNumber <= selectedCanoeCount; canoeNumber += 1) {
        const firstNameInput = document.getElementById(`canoe${canoeNumber}_fname`);
        const lastNameInput = document.getElementById(`canoe${canoeNumber}_lname`);
        const firstName = firstNameInput ? firstNameInput.value.trim() : "";
        const lastName = lastNameInput ? lastNameInput.value.trim() : "";

        const summaryItem = document.createElement("li");
        summaryItem.className = "booking-summary-item";

        const titleElement = document.createElement("span");
        titleElement.className = "booking-summary-item-title";
        titleElement.textContent = `Kanot ${canoeNumber}`;

        const valueElement = document.createElement("span");
        valueElement.className = "booking-summary-item-value";
        valueElement.textContent =
          firstName || lastName
            ? `${firstName} ${lastName}`.trim()
            : "Namn saknas";

        summaryItem.appendChild(titleElement);
        summaryItem.appendChild(valueElement);
        bookingSummaryListElement.appendChild(summaryItem);
      }
    }

    function validateParticipantForm() {
      if (currentBookingStep !== 2) {
        return;
      }

      const participantInputs = nameFieldsContainer.querySelectorAll("input");
      const allInputsAreFilled = Array.from(participantInputs).every(
        (inputField) => inputField.value.trim() !== ""
      );

      submitButton.disabled = !allInputsAreFilled;
      updateBookingSummary();
    }

    function handleQuantitySelection(canoeCount) {
      selectedCanoeCount = canoeCount;
      canoeCountInput.value = String(canoeCount);
      buildParticipantFields(canoeCount);
      updateBookingSummary();
      updateStepVisibility();

      const participantInputs = nameFieldsContainer.querySelectorAll("input");
      participantInputs.forEach((inputField) => {
        inputField.addEventListener("input", validateParticipantForm);
      });
    }

    function resetBookingModalState() {
      currentBookingStep = 1;
      selectedCanoeCount = 0;
      formElement.reset();
      canoeCountInput.value = "";
      nameFieldsContainer.innerHTML = "";
      bookingSummaryListElement.innerHTML = "";
      bookingSummaryListElement.appendChild(buildEmptySummaryItem());
      summaryCanoeCountElement.textContent = "0";
      priceInfoElement.textContent = "0 kr";
      resetQuantitySelection();
      updateStepVisibility();
    }

    function closeModal() {
      modalElement.style.display = "none";
    }

    openButton.addEventListener("click", () => {
      modalElement.style.display = "flex";
      resetBookingModalState();
      cancelButton.disabled = false;
    });

    modalElement.addEventListener("click", (event) => {
      if (event.target === modalElement) {
        closeModal();
      }
    });

    document.addEventListener("keydown", (event) => {
      if (event.key === "Escape" && modalElement.style.display === "flex") {
        closeModal();
      }
    });

    quantityOptionButtons.forEach((button) => {
      button.addEventListener("click", () => {
        resetQuantitySelection();
        button.classList.add("is-selected");
        button.setAttribute("aria-pressed", "true");
        handleQuantitySelection(parseInt(button.dataset.canoeCount, 10));
      });
    });

    cancelButton.addEventListener("click", () => {
      if (currentBookingStep === 1) {
        closeModal();
        return;
      }

      currentBookingStep = 1;
      updateStepVisibility();
    });

    submitButton.addEventListener("click", () => {
      if (currentBookingStep === 1) {
        if (selectedCanoeCount === 0) {
          return;
        }

        currentBookingStep = 2;
        updateBookingSummary();
        updateStepVisibility();

        const firstParticipantInput = nameFieldsContainer.querySelector("input");
        if (firstParticipantInput) {
          firstParticipantInput.focus();
        }
        return;
      }

      if (!submitButton.disabled) {
        formElement.requestSubmit();
      }
    });
  }

  window.PaddlingenBooking = {
    registerBookingModal,
  };
})();
