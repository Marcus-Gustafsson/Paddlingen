/**
 * File: app/static/js/script.js
 *
 * What it does:
 *   - Controls public page interactivity such as modals, the booking form,
 *     the booking progress bar, the weather widget, and the image gallery.
 *
 * Why it is here:
 *   - Keeping JavaScript separate from HTML makes the public page easier to
 *     update as the design changes.
 */

const eventSettings = window.PADDLINGEN_EVENT_SETTINGS || {};
const previousYearGalleryImages = window.PADDLINGEN_PREVIOUS_YEAR_IMAGES || [];

const pricePerCanoeSek = eventSettings.price_per_canoe_sek || 1200;

/**
 * Register the previous-years gallery modal and its controls.
 */
function registerGalleryModal() {
  const modal = document.getElementById("galleryModal");
  const imageElement = modal ? modal.querySelector(".gallery-image") : null;
  const counterElement = modal ? modal.querySelector(".gallery-counter") : null;
  const closeButton = modal ? modal.querySelector(".gallery-close") : null;
  const previousButton = modal ? modal.querySelector(".gallery-prev") : null;
  const nextButton = modal ? modal.querySelector(".gallery-next") : null;
  const showGalleryButton = document.getElementById("showPreviousYearsGallery");

  if (
    !modal ||
    !imageElement ||
    !counterElement ||
    !closeButton ||
    !previousButton ||
    !nextButton
  ) {
    return;
  }

  let galleryImages = [];
  let currentIndex = 0;

  function updateGallery() {
    if (!galleryImages.length) {
      return;
    }

    imageElement.src = galleryImages[currentIndex];
    counterElement.innerText = `${currentIndex + 1} / ${galleryImages.length}`;
    previousButton.style.display = galleryImages.length > 1 ? "block" : "none";
    nextButton.style.display = galleryImages.length > 1 ? "block" : "none";
  }

  function openGallery(images, startIndex = 0) {
    if (!images.length) {
      return;
    }

    galleryImages = images;
    currentIndex = startIndex;
    updateGallery();
    modal.style.display = "flex";
  }

  function closeGallery() {
    modal.style.display = "none";
    galleryImages = [];
  }

  previousButton.addEventListener("click", () => {
    currentIndex = (currentIndex - 1 + galleryImages.length) % galleryImages.length;
    updateGallery();
  });

  nextButton.addEventListener("click", () => {
    currentIndex = (currentIndex + 1) % galleryImages.length;
    updateGallery();
  });

  closeButton.addEventListener("click", closeGallery);

  modal.addEventListener("click", (event) => {
    if (event.target === modal) {
      closeGallery();
    }
  });

  document.addEventListener("keydown", (event) => {
    if (modal.style.display !== "flex") {
      return;
    }

    if (event.key === "Escape") {
      closeGallery();
    }
    if (event.key === "ArrowLeft") {
      previousButton.click();
    }
    if (event.key === "ArrowRight") {
      nextButton.click();
    }
  });

  if (showGalleryButton) {
    showGalleryButton.addEventListener("click", () => {
      openGallery(previousYearGalleryImages, 0);
    });
  }
}

/**
 * Start the continuous previous-years ribbon animation.
 *
 * This uses `requestAnimationFrame` instead of a CSS keyframe loop so the
 * track can wrap based on its measured width without a visible jump.
 */
function initializeGalleryRibbonMarquee() {
  const ribbonTrack = document.getElementById("galleryRibbonTrack");

  if (!ribbonTrack) {
    return;
  }

  const ribbonGroups = ribbonTrack.querySelectorAll(".gallery-ribbon-group");

  if (ribbonGroups.length < 2) {
    return;
  }

  const firstRibbonGroup = ribbonGroups[0];
  const trackGap = parseFloat(window.getComputedStyle(ribbonTrack).gap || "0");
  const pixelsPerSecond = 28;

  let currentOffset = 0;
  let previousTimestamp = 0;

  function stepAnimation(timestamp) {
    if (previousTimestamp === 0) {
      previousTimestamp = timestamp;
    }

    const deltaSeconds = (timestamp - previousTimestamp) / 1000;
    previousTimestamp = timestamp;

    const ribbonLoopWidth =
      firstRibbonGroup.getBoundingClientRect().width + trackGap;

    if (ribbonLoopWidth <= 0) {
      requestAnimationFrame(stepAnimation);
      return;
    }

    currentOffset += pixelsPerSecond * deltaSeconds;

    if (currentOffset >= ribbonLoopWidth) {
      currentOffset -= ribbonLoopWidth;
    }

    ribbonTrack.style.transform = `translate3d(-${currentOffset}px, 0, 0)`;
    requestAnimationFrame(stepAnimation);
  }

  requestAnimationFrame(stepAnimation);
}

/**
 * Register the booking modal and participant field generation.
 */
function registerBookingModal() {
  const openButton = document.getElementById("bookBtn");
  const modal = document.getElementById("bookingModal");
  const form = document.getElementById("bookingForm");
  const canoeCountInput = document.getElementById("canoeCount");
  const quantityOptionButtons = document.querySelectorAll(".quantity-option");
  const bookingStepOne = document.getElementById("bookingStepOne");
  const bookingStepTwo = document.getElementById("bookingStepTwo");
  const bookingStepLabel = document.getElementById("bookingStepLabel");
  const nameFieldsContainer = document.getElementById("nameFieldsContainer");
  const priceInfo = document.getElementById("priceInfo");
  const bookingSummaryList = document.getElementById("bookingSummaryList");
  const summaryCanoeCount = document.getElementById("summaryCanoeCount");
  const bookingPaymentNote = document.getElementById("bookingPaymentNote");
  const cancelButton = document.getElementById("cancelBooking");
  const submitButton = document.getElementById("confirmBooking");

  if (
    !openButton ||
    !modal ||
    !form ||
    !canoeCountInput ||
    !bookingStepOne ||
    !bookingStepTwo ||
    !bookingStepLabel ||
    !nameFieldsContainer ||
    !priceInfo ||
    !bookingSummaryList ||
    !summaryCanoeCount ||
    !bookingPaymentNote ||
    !cancelButton ||
    !submitButton
  ) {
    return;
  }

  let currentBookingStep = 1;
  let selectedCanoeCount = 0;

  function updateStepVisibility() {
    const isStepOneActive = currentBookingStep === 1;
    bookingStepOne.hidden = !isStepOneActive;
    bookingStepTwo.hidden = isStepOneActive;
    bookingPaymentNote.hidden = isStepOneActive;
    bookingStepOne.classList.toggle("booking-step--active", isStepOneActive);
    bookingStepTwo.classList.toggle("booking-step--active", !isStepOneActive);

    if (isStepOneActive) {
      bookingStepLabel.innerText = "Steg 1 av 2";
      cancelButton.innerText = "Avbryt";
      submitButton.innerText = "Fortsätt";
      submitButton.disabled = selectedCanoeCount === 0;
    } else {
      bookingStepLabel.innerText = "Steg 2 av 2";
      cancelButton.innerText = "Tillbaka";
      submitButton.innerText = "Fortsätt till betalning";
      validateParticipantForm();
    }
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
      const wrapper = document.createElement("section");
      wrapper.className = "canoe-field";

      const label = document.createElement("label");
      label.setAttribute("for", `canoe${canoeNumber}_fname`);
      label.innerText = `Kanot ${canoeNumber}`;
      wrapper.appendChild(label);

      const inputsContainer = document.createElement("div");
      inputsContainer.className = "inputs";

      const firstNameInput = document.createElement("input");
      firstNameInput.type = "text";
      firstNameInput.id = `canoe${canoeNumber}_fname`;
      firstNameInput.name = `canoe${canoeNumber}_fname`;
      firstNameInput.placeholder = "Förnamn";
      firstNameInput.required = true;

      const lastNameInput = document.createElement("input");
      lastNameInput.type = "text";
      lastNameInput.id = `canoe${canoeNumber}_lname`;
      lastNameInput.name = `canoe${canoeNumber}_lname`;
      lastNameInput.placeholder = "Efternamn";
      lastNameInput.required = true;

      inputsContainer.appendChild(firstNameInput);
      inputsContainer.appendChild(lastNameInput);
      wrapper.appendChild(inputsContainer);
      nameFieldsContainer.appendChild(wrapper);
    }
  }

  function updateBookingSummary() {
    bookingSummaryList.innerHTML = "";

    if (selectedCanoeCount === 0) {
      bookingSummaryList.innerHTML =
        '<li class="booking-summary-empty">Välj antal kanoter för att se översikten.</li>';
      summaryCanoeCount.innerText = "0";
      priceInfo.innerText = "0 kr";
      return;
    }

    summaryCanoeCount.innerText = String(selectedCanoeCount);
    priceInfo.innerText = `${selectedCanoeCount * pricePerCanoeSek} kr`;

    for (let canoeNumber = 1; canoeNumber <= selectedCanoeCount; canoeNumber += 1) {
      const firstNameInput = document.getElementById(`canoe${canoeNumber}_fname`);
      const lastNameInput = document.getElementById(`canoe${canoeNumber}_lname`);
      const firstName = firstNameInput ? firstNameInput.value.trim() : "";
      const lastName = lastNameInput ? lastNameInput.value.trim() : "";
      const summaryItem = document.createElement("li");
      summaryItem.className = "booking-summary-item";

      const title = document.createElement("span");
      title.className = "booking-summary-item-title";
      title.innerText = `Kanot ${canoeNumber}`;

      const value = document.createElement("span");
      value.className = "booking-summary-item-value";
      value.innerText = firstName || lastName ? `${firstName} ${lastName}`.trim() : "Namn saknas";

      summaryItem.appendChild(title);
      summaryItem.appendChild(value);
      bookingSummaryList.appendChild(summaryItem);
    }
  }

  function validateParticipantForm() {
    if (currentBookingStep !== 2) {
      return;
    }

    const allInputs = nameFieldsContainer.querySelectorAll("input");
    const allFilled = Array.from(allInputs).every((inputField) => {
      return inputField.value.trim() !== "";
    });
    submitButton.disabled = !allFilled;
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
    form.reset();
    canoeCountInput.value = "";
    nameFieldsContainer.innerHTML = "";
    bookingSummaryList.innerHTML =
      '<li class="booking-summary-empty">Välj antal kanoter för att se översikten.</li>';
    summaryCanoeCount.innerText = "0";
    priceInfo.innerText = "0 kr";
    resetQuantitySelection();
    updateStepVisibility();
  }

  function closeModal() {
    modal.style.display = "none";
  }

  openButton.addEventListener("click", () => {
    modal.style.display = "flex";
    resetBookingModalState();
    cancelButton.disabled = false;
  });

  modal.addEventListener("click", (event) => {
    if (event.target === modal) {
      closeModal();
    }
  });

  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape" && modal.style.display === "flex") {
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
      form.requestSubmit();
    }
  });
}

/**
 * Register the scroll-based reveal animation used on the homepage.
 */
function registerScrollAnimations() {
  const animatedElements = document.querySelectorAll(".scroll-animate");

  if (!animatedElements.length) {
    return;
  }

  const animationObserver = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          entry.target.classList.add("in-view");
        } else {
          entry.target.classList.remove("in-view");
        }
      });
    },
    {
      root: null,
      threshold: 0.2,
    }
  );

  animatedElements.forEach((element) => {
    animationObserver.observe(element);
  });
}

document.addEventListener("DOMContentLoaded", async () => {
  const bookingProgressModule = window.PaddlingenBookingProgress;
  if (bookingProgressModule) {
    await bookingProgressModule.updateProgressFromDatabase();
  }

  const weatherModule = window.PaddlingenWeather;
  if (weatherModule) {
    await weatherModule.initializeWeatherWidget();
  }

  const modalModule = window.PaddlingenModals;
  if (modalModule) {
    modalModule.registerPublicModals();
  }

  registerGalleryModal();
  initializeGalleryRibbonMarquee();
  registerBookingModal();
  registerScrollAnimations();
});
