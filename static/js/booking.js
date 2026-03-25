/**
 * File: app/static/js/booking.js
 *
 * What it does:
 *   - Controls the public booking modal.
 *   - Handles the three-step booking flow, participant field generation, and
 *     the booking summary shown before submission and payment.
 *
 * Why it is here:
 *   - Keeping the booking flow in its own file makes the public JavaScript
 *     easier to understand and keeps the most stateful homepage feature
 *     isolated from the other UI modules.
 */

(function registerBookingModule() {
  const eventSettings = window.PADDLINGEN_EVENT_SETTINGS || {};
  let pendingBooking = window.PADDLINGEN_PENDING_BOOKING || null;
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
    const closeButton = modalElement.querySelector(".modal-close");
    const formElement = document.getElementById("bookingForm");
    const canoeCountInput = document.getElementById("canoeCount");
    const quantityOptionButtons = document.querySelectorAll(".quantity-option");
    const bookingStepOneElement = document.getElementById("bookingStepOne");
    const bookingStepTwoElement = document.getElementById("bookingStepTwo");
    const bookingStepThreeElement = document.getElementById("bookingStepThree");
    const bookingStepLabelElement = document.getElementById("bookingStepLabel");
    const nameFieldsContainer = document.getElementById("nameFieldsContainer");
    const priceInfoElement = document.getElementById("priceInfo");
    const bookingSummaryListElement = document.getElementById("bookingSummaryList");
    const summaryCanoeCountElement = document.getElementById("summaryCanoeCount");
    const bookingPaymentNoteElement = document.getElementById("bookingPaymentNote");
    const bookingActionButtonsElement = modalElement.querySelector(
      ".booking-buttons--modal"
    );
    const cancelButton = document.getElementById("cancelBooking");
    const submitButton = document.getElementById("confirmBooking");
    const pendingBookingCancelForm = document.getElementById(
      "pendingBookingCancelForm"
    );
    const pendingBookingCancelReasonInput = document.getElementById(
      "pendingBookingCancelReason"
    );
    const pendingBookingReferenceElement = document.getElementById(
      "pendingBookingReference"
    );
    const pendingBookingCanoeCountElement = document.getElementById(
      "pendingBookingCanoeCount"
    );
    const pendingBookingTotalAmountElement = document.getElementById(
      "pendingBookingTotalAmount"
    );
    const pendingBookingSummaryListElement = document.getElementById(
      "pendingBookingSummaryList"
    );
    const bookingReservationTimerElement = document.getElementById(
      "bookingReservationTimer"
    );
    const bookingReservationTimerValueElement = document.getElementById(
      "bookingReservationTimerValue"
    );
    const continueToStripePaymentLink = document.getElementById(
      "continueToStripePayment"
    );

    if (
      !openButton ||
      !modalElement ||
      !closeButton ||
      !formElement ||
      !canoeCountInput ||
      !bookingStepOneElement ||
      !bookingStepTwoElement ||
      !bookingStepThreeElement ||
      !bookingStepLabelElement ||
      !nameFieldsContainer ||
      !priceInfoElement ||
      !bookingSummaryListElement ||
      !summaryCanoeCountElement ||
      !bookingPaymentNoteElement ||
      !bookingActionButtonsElement ||
      !cancelButton ||
      !submitButton ||
      !pendingBookingCancelForm ||
      !pendingBookingCancelReasonInput ||
      !pendingBookingReferenceElement ||
      !pendingBookingCanoeCountElement ||
      !pendingBookingTotalAmountElement ||
      !pendingBookingSummaryListElement ||
      !bookingReservationTimerElement ||
      !bookingReservationTimerValueElement ||
      !continueToStripePaymentLink
    ) {
      return;
    }

    let currentBookingStep = 1;
    let selectedCanoeCount = 0;
    let countdownIntervalId = 0;
    let isSubmittingReservation = false;

    function hasActivePendingBooking() {
      return Boolean(
        pendingBooking &&
          typeof pendingBooking.public_booking_reference === "string" &&
          pendingBooking.public_booking_reference
      );
    }

    function showBookingToast(message) {
      if (!message) {
        return;
      }

      let toastStackElement = document.querySelector(".home-toast-stack");
      if (!toastStackElement) {
        toastStackElement = document.createElement("div");
        toastStackElement.className = "home-toast-stack";
        toastStackElement.setAttribute("aria-live", "polite");
        document.body.appendChild(toastStackElement);
      }

      const toastElement = document.createElement("div");
      toastElement.className = "home-toast home-toast-error";
      toastElement.textContent = message;
      toastStackElement.appendChild(toastElement);

      window.setTimeout(() => {
        toastElement.remove();
        if (!toastStackElement.children.length) {
          toastStackElement.remove();
        }
      }, 7000);
    }

    function clearReservationCountdown() {
      window.clearInterval(countdownIntervalId);
      countdownIntervalId = 0;
    }

    function closeModal() {
      clearReservationCountdown();
      modalElement.style.display = "none";
    }

    function buildPendingBookingSummaryItem(canoeNumber, participantNames) {
      const summaryItem = document.createElement("li");
      summaryItem.className = "booking-summary-item";

      const titleElement = document.createElement("span");
      titleElement.className = "booking-summary-item-title";
      titleElement.textContent = `Kanot ${canoeNumber}`;

      const riderLinesElement = document.createElement("div");
      riderLinesElement.className = "booking-summary-item-lines";

      const safeParticipantNames = Array.isArray(participantNames)
        ? participantNames.filter((participantName) => typeof participantName === "string")
        : [];

      if (!safeParticipantNames.length) {
        const riderElement = document.createElement("span");
        riderElement.className = "booking-summary-item-line";
        riderElement.textContent = "Namn saknas";
        riderLinesElement.appendChild(riderElement);
      } else {
        safeParticipantNames.forEach((participantName) => {
          const riderElement = document.createElement("span");
          riderElement.className = "booking-summary-item-line";
          riderElement.textContent = participantName;
          riderLinesElement.appendChild(riderElement);
        });
      }

      summaryItem.appendChild(titleElement);
      summaryItem.appendChild(riderLinesElement);
      return summaryItem;
    }

    function renderPendingBookingStep() {
      const hasPendingBooking = hasActivePendingBooking();
      bookingReservationTimerElement.setAttribute(
        "data-expires-at",
        hasPendingBooking ? pendingBooking.countdown_expires_at_iso || "" : ""
      );
      pendingBookingReferenceElement.textContent = hasPendingBooking
        ? pendingBooking.public_booking_reference
        : "Ingen aktiv reservation";
      pendingBookingCanoeCountElement.textContent = hasPendingBooking
        ? String(pendingBooking.canoe_count || 0)
        : "0";
      pendingBookingTotalAmountElement.textContent = hasPendingBooking
        ? pendingBooking.formatted_total_amount || "0 kr"
        : "0 kr";

      pendingBookingSummaryListElement.innerHTML = "";
      const canoeSummaries =
        hasPendingBooking && Array.isArray(pendingBooking.canoe_summaries)
          ? pendingBooking.canoe_summaries
          : [];

      if (!canoeSummaries.length) {
        const emptyPendingSummaryItem = document.createElement("li");
        emptyPendingSummaryItem.className = "booking-summary-empty";
        emptyPendingSummaryItem.textContent = "Ingen aktiv reservation just nu.";
        pendingBookingSummaryListElement.appendChild(emptyPendingSummaryItem);
      } else {
        canoeSummaries.forEach((canoeSummary, index) => {
          const canoeNumber = Number.isInteger(canoeSummary.canoe_number)
            ? canoeSummary.canoe_number
            : index + 1;
          const participantNames = Array.isArray(canoeSummary.participant_names)
            ? canoeSummary.participant_names
            : [];
          pendingBookingSummaryListElement.appendChild(
            buildPendingBookingSummaryItem(canoeNumber, participantNames)
          );
        });
      }

      continueToStripePaymentLink.href =
        hasPendingBooking && pendingBooking.pay_now_url
          ? pendingBooking.pay_now_url
          : "#";
      continueToStripePaymentLink.classList.toggle(
        "button-primary-link--disabled",
        !hasPendingBooking
      );
      continueToStripePaymentLink.setAttribute(
        "aria-disabled",
        hasPendingBooking ? "false" : "true"
      );

      pendingBookingCancelForm.action =
        hasPendingBooking && pendingBooking.cancel_order_url
          ? pendingBooking.cancel_order_url
          : "#";
    }

    function submitPendingBookingCancellation(reason = "manual") {
      if (!hasActivePendingBooking()) {
        closeModal();
        return;
      }

      pendingBookingCancelReasonInput.value = reason;
      pendingBookingCancelForm.submit();
    }

    function requestModalClose() {
      if (currentBookingStep === 3 && hasActivePendingBooking()) {
        submitPendingBookingCancellation("manual");
        return;
      }

      closeModal();
    }

    function formatCountdownValue(remainingMilliseconds) {
      const remainingTotalSeconds = Math.max(
        0,
        Math.floor(remainingMilliseconds / 1000)
      );
      const remainingMinutes = Math.floor(remainingTotalSeconds / 60);
      const remainingSeconds = remainingTotalSeconds % 60;
      return `${String(remainingMinutes).padStart(2, "0")}:${String(
        remainingSeconds
      ).padStart(2, "0")}`;
    }

    function startReservationCountdown() {
      clearReservationCountdown();

      if (currentBookingStep !== 3 || !hasActivePendingBooking()) {
        return;
      }

      const expiresAtValue = bookingReservationTimerElement.getAttribute(
        "data-expires-at"
      );
      if (!expiresAtValue) {
        bookingReservationTimerValueElement.textContent = "--:--";
        return;
      }

      const expiresAtTimestamp = Date.parse(expiresAtValue);
      if (Number.isNaN(expiresAtTimestamp)) {
        bookingReservationTimerValueElement.textContent = "--:--";
        return;
      }

      const updateCountdown = () => {
        const remainingMilliseconds = expiresAtTimestamp - Date.now();
        bookingReservationTimerValueElement.textContent = formatCountdownValue(
          remainingMilliseconds
        );

        if (remainingMilliseconds <= 0) {
          clearReservationCountdown();
          submitPendingBookingCancellation("expired");
        }
      };

      updateCountdown();
      countdownIntervalId = window.setInterval(updateCountdown, 1000);
    }

    function updateStepVisibility() {
      const isStepOneActive = currentBookingStep === 1;
      const isStepTwoActive = currentBookingStep === 2;
      const isStepThreeActive = currentBookingStep === 3;

      bookingStepOneElement.hidden = !isStepOneActive;
      bookingStepTwoElement.hidden = !isStepTwoActive;
      bookingStepThreeElement.hidden = !isStepThreeActive;
      bookingPaymentNoteElement.hidden = !isStepTwoActive;
      bookingActionButtonsElement.hidden = isStepThreeActive;
      bookingStepOneElement.classList.toggle(
        "booking-step--active",
        isStepOneActive
      );
      bookingStepTwoElement.classList.toggle(
        "booking-step--active",
        isStepTwoActive
      );
      bookingStepThreeElement.classList.toggle(
        "booking-step--active",
        isStepThreeActive
      );
      modalElement.classList.toggle("booking-modal-step-three", isStepThreeActive);

      if (isStepOneActive) {
        clearReservationCountdown();
        bookingStepLabelElement.textContent = "Steg 1 av 3";
        cancelButton.textContent = "Avbryt";
        submitButton.textContent = "Fortsätt";
        submitButton.disabled = selectedCanoeCount === 0;
        return;
      }

      if (isStepTwoActive) {
        clearReservationCountdown();
        bookingStepLabelElement.textContent = "Steg 2 av 3";
        cancelButton.textContent = "Tillbaka";
        submitButton.textContent = "Reservera kanoter";
        submitButton.disabled = isSubmittingReservation;
        validateParticipantForm();
        return;
      }

      bookingStepLabelElement.textContent = "Steg 3 av 3";
      cancelButton.textContent = "Avbryt";
      submitButton.textContent = "Reservera kanoter";
      submitButton.disabled = false;
      renderPendingBookingStep();
      startReservationCountdown();
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
        canoeHint.textContent = "";
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

      submitButton.disabled = !isFormValid || isSubmittingReservation;
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
      clearReservationCountdown();
      currentBookingStep = 1;
      selectedCanoeCount = 0;
      pendingBooking = null;
      isSubmittingReservation = false;
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

    openButton.addEventListener("click", () => {
      modalElement.style.display = "flex";
      if (hasActivePendingBooking()) {
        currentBookingStep = 3;
        updateStepVisibility();
      } else {
        resetBookingModalState();
      }
      cancelButton.disabled = false;
    });

    closeButton.addEventListener("click", () => {
      requestModalClose();
    });

    formElement.addEventListener("submit", (event) => {
      if (currentBookingStep !== 3) {
        event.preventDefault();
      }
    });

    modalElement.addEventListener("click", (event) => {
      if (event.target === modalElement) {
        requestModalClose();
      }
    });

    document.addEventListener("keydown", (event) => {
      if (event.key === "Escape" && modalElement.style.display === "flex") {
        requestModalClose();
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
        requestModalClose();
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

      if (!submitButton.disabled && !isSubmittingReservation) {
        isSubmittingReservation = true;
        submitButton.disabled = true;
        submitButton.textContent = "Reserverar...";

        window
          .fetch(formElement.action, {
            method: "POST",
            body: new FormData(formElement),
            headers: {
              "X-Requested-With": "XMLHttpRequest",
            },
          })
          .then(async (response) => {
            const responseData = await response.json();
            if (!response.ok || !responseData.ok) {
              const reservationError = new Error(
                responseData.message ||
                  "Det gick inte att reservera kanoterna just nu."
              );
              reservationError.reloadPage = Boolean(responseData.reload_page);
              reservationError.redirectUrl =
                responseData.redirect_url || window.location.pathname;
              throw reservationError;
            }

            pendingBooking = responseData.pending_booking || null;
            currentBookingStep = 3;
            updateStepVisibility();

            const bookingProgressModule = window.PaddlingenBookingProgress;
            if (
              bookingProgressModule &&
              typeof bookingProgressModule.updateProgressFromDatabase === "function"
            ) {
              bookingProgressModule.updateProgressFromDatabase();
            }
          })
          .catch((error) => {
            if (error.reloadPage) {
              window.location.assign(error.redirectUrl || window.location.pathname);
              return;
            }

            showBookingToast(error.message);
            submitButton.textContent = "Reservera kanoter";
            isSubmittingReservation = false;
            validateParticipantForm();
          })
          .finally(() => {
            if (currentBookingStep === 3) {
              isSubmittingReservation = false;
            }
          });
      }
    });

    continueToStripePaymentLink.addEventListener("click", (event) => {
      if (
        continueToStripePaymentLink.getAttribute("aria-disabled") === "true" ||
        !hasActivePendingBooking()
      ) {
        event.preventDefault();
      }
    });

    if (hasActivePendingBooking() && pendingBooking.open_on_load) {
      modalElement.style.display = "flex";
      currentBookingStep = 3;
      updateStepVisibility();
    }
  }

  window.PaddlingenBooking = {
    registerBookingModal,
  };
})();
