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
   * Return one trimmed full name or a fallback when both parts are empty.
   */
  function buildFullName(firstName, lastName, emptyFallback = "") {
    const combinedName = `${firstName || ""} ${lastName || ""}`.trim();
    return combinedName || emptyFallback;
  }

  /**
   * Return whether the visible rider-pair fields are filled correctly.
   */
  function areNamePairFieldsValid(firstInput, lastInput, isRequired = false) {
    const firstValue = firstInput ? firstInput.value.trim() : "";
    const lastValue = lastInput ? lastInput.value.trim() : "";

    if (isRequired) {
      return firstValue !== "" && lastValue !== "";
    }

    if (firstInput && firstInput.closest("[hidden]")) {
      return true;
    }

    return (
      (firstValue === "" && lastValue === "") ||
      (firstValue !== "" && lastValue !== "")
    );
  }

  /**
   * Build one reusable rider input row inside a canoe card.
   */
  function buildRiderFieldRow({
    canoeNumber,
    riderNumber,
    title,
    description,
    firstNameFieldName,
    lastNameFieldName,
    required = false,
    initiallyHidden = false,
  }) {
    const riderField = document.createElement("div");
    riderField.className = "canoe-rider-field";
    riderField.dataset.riderNumber = String(riderNumber);
    riderField.hidden = initiallyHidden;

    const riderHeading = document.createElement("div");
    riderHeading.className = "canoe-rider-field-header";

    const riderTitle = document.createElement("strong");
    riderTitle.textContent = title;

    const riderDescription = document.createElement("span");
    riderDescription.textContent = description;

    riderHeading.appendChild(riderTitle);
    riderHeading.appendChild(riderDescription);
    riderField.appendChild(riderHeading);

    const inputsContainer = document.createElement("div");
    inputsContainer.className = "inputs";

    const firstNameInput = document.createElement("input");
    firstNameInput.type = "text";
    firstNameInput.id = `canoe${canoeNumber}_${firstNameFieldName}`;
    firstNameInput.name = `canoe${canoeNumber}_${firstNameFieldName}`;
    firstNameInput.placeholder = "Förnamn";
    firstNameInput.maxLength = 20;
    firstNameInput.required = required;

    const lastNameInput = document.createElement("input");
    lastNameInput.type = "text";
    lastNameInput.id = `canoe${canoeNumber}_${lastNameFieldName}`;
    lastNameInput.name = `canoe${canoeNumber}_${lastNameFieldName}`;
    lastNameInput.placeholder = "Efternamn";
    lastNameInput.maxLength = 20;
    lastNameInput.required = required;

    inputsContainer.appendChild(firstNameInput);
    inputsContainer.appendChild(lastNameInput);
    riderField.appendChild(inputsContainer);

    return {
      riderField,
      firstNameInput,
      lastNameInput,
    };
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

        const canoeHeader = document.createElement("div");
        canoeHeader.className = "canoe-field-header";

        const canoeLabel = document.createElement("label");
        canoeLabel.setAttribute("for", `canoe${canoeNumber}_fname`);
        canoeLabel.textContent = `Kanot ${canoeNumber}`;

        const canoeHint = document.createElement("p");
        canoeHint.className = "canoe-field-hint";
          canoeHint.textContent = ''
          canoeHeader.appendChild(canoeLabel);
        canoeHeader.appendChild(canoeHint);
        fieldWrapper.appendChild(canoeHeader);

        const pickupPersonFields = buildRiderFieldRow({
          canoeNumber,
          riderNumber: 1,
          title: "Ansvarig vid uthämtning",
          description: "Detta namn måste anges.",
          firstNameFieldName: "fname",
          lastNameFieldName: "lname",
          required: true,
        });
        fieldWrapper.appendChild(pickupPersonFields.riderField);

        const secondRiderFields = buildRiderFieldRow({
          canoeNumber,
          riderNumber: 2,
          title: "Person 2",
          description: "",
          firstNameFieldName: "passenger2_fname",
          lastNameFieldName: "passenger2_lname",
          initiallyHidden: true,
        });
        secondRiderFields.riderField.id = `canoe${canoeNumber}_second_rider`;
        const removeSecondPersonButton = document.createElement("button");
        removeSecondPersonButton.type = "button";
        removeSecondPersonButton.className = "booking-inline-link";
        removeSecondPersonButton.textContent = "Ta bort person 2";
        removeSecondPersonButton.hidden = true;
        secondRiderFields.riderField.appendChild(removeSecondPersonButton);
        fieldWrapper.appendChild(secondRiderFields.riderField);

        const thirdRiderFields = buildRiderFieldRow({
          canoeNumber,
          riderNumber: 3,
          title: "Person 3",
          description: "",
          firstNameFieldName: "passenger3_fname",
          lastNameFieldName: "passenger3_lname",
          initiallyHidden: true,
        });
        const removeThirdPersonButton = document.createElement("button");
        removeThirdPersonButton.type = "button";
        removeThirdPersonButton.className = "booking-inline-link";
        removeThirdPersonButton.textContent = "Ta bort person 3";
        removeThirdPersonButton.hidden = true;
        thirdRiderFields.riderField.appendChild(removeThirdPersonButton);
        fieldWrapper.appendChild(thirdRiderFields.riderField);

        const addSecondPersonButton = document.createElement("button");
        addSecondPersonButton.type = "button";
        addSecondPersonButton.className = "booking-inline-link";
        addSecondPersonButton.textContent = "Lägg till person";
        addSecondPersonButton.setAttribute("aria-expanded", "false");
        addSecondPersonButton.setAttribute(
          "aria-controls",
          secondRiderFields.riderField.id
        );

        const addThirdPersonButton = document.createElement("button");
        addThirdPersonButton.type = "button";
        addThirdPersonButton.className = "booking-inline-link";
        addThirdPersonButton.textContent = "Lägg till person";
        addThirdPersonButton.setAttribute("aria-expanded", "false");
        addThirdPersonButton.hidden = true;
        thirdRiderFields.riderField.id = `canoe${canoeNumber}_third_rider`;
        addThirdPersonButton.setAttribute(
          "aria-controls",
          thirdRiderFields.riderField.id
        );

        addSecondPersonButton.addEventListener("click", () => {
          secondRiderFields.riderField.hidden = false;
          addSecondPersonButton.hidden = true;
          addThirdPersonButton.hidden = false;
          removeSecondPersonButton.hidden = false;
          validateParticipantForm();
        });

        addThirdPersonButton.addEventListener("click", () => {
          thirdRiderFields.riderField.hidden = false;
          addThirdPersonButton.hidden = true;
          removeThirdPersonButton.hidden = false;
          validateParticipantForm();
        });

        removeThirdPersonButton.addEventListener("click", () => {
          thirdRiderFields.riderField.hidden = true;
          thirdRiderFields.firstNameInput.value = "";
          thirdRiderFields.lastNameInput.value = "";
          removeThirdPersonButton.hidden = true;
          addThirdPersonButton.hidden = false;
          validateParticipantForm();
        });

        removeSecondPersonButton.addEventListener("click", () => {
          const thirdRiderVisible = !thirdRiderFields.riderField.hidden;

          if (thirdRiderVisible) {
            secondRiderFields.firstNameInput.value = thirdRiderFields.firstNameInput.value;
            secondRiderFields.lastNameInput.value = thirdRiderFields.lastNameInput.value;
            thirdRiderFields.firstNameInput.value = "";
            thirdRiderFields.lastNameInput.value = "";
            thirdRiderFields.riderField.hidden = true;
            removeThirdPersonButton.hidden = true;
            addThirdPersonButton.hidden = false;
            validateParticipantForm();
            return;
          }

          secondRiderFields.firstNameInput.value = "";
          secondRiderFields.lastNameInput.value = "";
          secondRiderFields.riderField.hidden = true;
          removeSecondPersonButton.hidden = true;
          addSecondPersonButton.hidden = false;
          addThirdPersonButton.hidden = true;
          validateParticipantForm();
        });

        const optionalActionRow = document.createElement("div");
        optionalActionRow.className = "booking-inline-actions";
        optionalActionRow.appendChild(addSecondPersonButton);
        optionalActionRow.appendChild(addThirdPersonButton);

        fieldWrapper.appendChild(optionalActionRow);
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
        const passengerTwoFirstNameInput = document.getElementById(
          `canoe${canoeNumber}_passenger2_fname`
        );
        const passengerTwoLastNameInput = document.getElementById(
          `canoe${canoeNumber}_passenger2_lname`
        );
        const passengerTwoField = document.getElementById(
          `canoe${canoeNumber}_second_rider`
        );
        const passengerThreeField = document.getElementById(
          `canoe${canoeNumber}_third_rider`
        );
        const passengerThreeFirstNameInput = document.getElementById(
          `canoe${canoeNumber}_passenger3_fname`
        );
        const passengerThreeLastNameInput = document.getElementById(
          `canoe${canoeNumber}_passenger3_lname`
        );
        const firstName = firstNameInput ? firstNameInput.value.trim() : "";
        const lastName = lastNameInput ? lastNameInput.value.trim() : "";
        const secondRiderName = buildFullName(
          passengerTwoFirstNameInput ? passengerTwoFirstNameInput.value.trim() : "",
          passengerTwoLastNameInput ? passengerTwoLastNameInput.value.trim() : "",
          "Namn saknas"
        );
        const secondRiderIsVisible = passengerTwoField
          ? !passengerTwoField.hidden
          : false;
        const thirdRiderIsVisible = passengerThreeField
          ? !passengerThreeField.hidden
          : false;
        const thirdRiderName = buildFullName(
          passengerThreeFirstNameInput
            ? passengerThreeFirstNameInput.value.trim()
            : "",
          passengerThreeLastNameInput ? passengerThreeLastNameInput.value.trim() : "",
          "Namn saknas"
        );

        const summaryItem = document.createElement("li");
        summaryItem.className = "booking-summary-item";

        const titleElement = document.createElement("span");
        titleElement.className = "booking-summary-item-title";
        titleElement.textContent = `Kanot ${canoeNumber}`;

        const riderLinesElement = document.createElement("div");
        riderLinesElement.className = "booking-summary-item-lines";

        const pickupPersonElement = document.createElement("span");
        pickupPersonElement.className = "booking-summary-item-line";
        pickupPersonElement.textContent = buildFullName(
          firstName,
          lastName,
          "Namn saknas"
        );
        riderLinesElement.appendChild(pickupPersonElement);

        if (secondRiderIsVisible) {
          const secondRiderElement = document.createElement("span");
          secondRiderElement.className = "booking-summary-item-line";
          secondRiderElement.textContent = secondRiderName;
          riderLinesElement.appendChild(secondRiderElement);
        }

        if (thirdRiderIsVisible) {
          const thirdRiderElement = document.createElement("span");
          thirdRiderElement.className = "booking-summary-item-line";
          thirdRiderElement.textContent = thirdRiderName;
          riderLinesElement.appendChild(thirdRiderElement);
        }

        summaryItem.appendChild(titleElement);
        summaryItem.appendChild(riderLinesElement);
        bookingSummaryListElement.appendChild(summaryItem);
      }
    }

    function validateParticipantForm() {
      if (currentBookingStep !== 2) {
        return;
      }

      let isFormValid = true;

      for (let canoeNumber = 1; canoeNumber <= selectedCanoeCount; canoeNumber += 1) {
        const pickupFirstNameInput = document.getElementById(`canoe${canoeNumber}_fname`);
        const pickupLastNameInput = document.getElementById(`canoe${canoeNumber}_lname`);
        const secondRiderFirstNameInput = document.getElementById(
          `canoe${canoeNumber}_passenger2_fname`
        );
        const secondRiderLastNameInput = document.getElementById(
          `canoe${canoeNumber}_passenger2_lname`
        );
        const thirdRiderFirstNameInput = document.getElementById(
          `canoe${canoeNumber}_passenger3_fname`
        );
        const thirdRiderLastNameInput = document.getElementById(
          `canoe${canoeNumber}_passenger3_lname`
        );

        if (
          !areNamePairFieldsValid(pickupFirstNameInput, pickupLastNameInput, true) ||
          !areNamePairFieldsValid(
            secondRiderFirstNameInput,
            secondRiderLastNameInput
          ) ||
          !areNamePairFieldsValid(thirdRiderFirstNameInput, thirdRiderLastNameInput)
        ) {
          isFormValid = false;
          break;
        }
      }

      submitButton.disabled = !isFormValid;
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
