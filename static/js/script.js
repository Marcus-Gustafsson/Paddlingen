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

const totalCanoesCurrentYear = eventSettings.available_canoes_total || 50;
const currentYearEventDate = new Date(
  eventSettings.datetime_local_iso || "2026-06-28T10:00:00"
);
const pricePerCanoeSek = eventSettings.price_per_canoe_sek || 1200;
const weatherForecastDaysBeforeEvent =
  eventSettings.weather_forecast_days_before_event || 7;

/**
 * Update the progress bar and its helper text.
 *
 * Args:
 *   booked: Number of currently confirmed canoe bookings.
 *   total: Total number of canoes available.
 */
function updateBookingProgress(booked, total) {
  const percent = Math.min(100, Math.max(0, (booked / total) * 100));
  const startHue = 120;
  const endHue = 0;
  const hue = startHue + (endHue - startHue) * (percent / 100);
  const color = `hsl(${hue}, 100%, 50%)`;

  const progressBar = document.getElementById("progressBar");
  const progressText = document.getElementById("progressText");
  const bookButton = document.getElementById("bookBtn");

  if (!progressBar || !progressText || !bookButton) {
    return;
  }

  progressBar.style.width = `${percent}%`;
  progressBar.style.backgroundColor = color;
  progressText.innerHTML = `
    <span class="progress-text-main">${booked} / ${total} kanoter bokade</span>
    <span class="progress-text-hint">Tryck för att se deltagare</span>
  `;

  if (booked >= total) {
    bookButton.disabled = true;
    bookButton.innerText = "Fullbokat";
    bookButton.setAttribute("aria-disabled", "true");
  } else {
    bookButton.disabled = false;
    bookButton.innerText = "Boka kanot";
    bookButton.setAttribute("aria-disabled", "false");
  }
}

/**
 * Fetch the current number of confirmed bookings from the backend.
 *
 * Returns:
 *   Promise<number>: Booking count, or 0 if the request fails.
 */
async function fetchBookingCount() {
  try {
    const response = await fetch("/api/booking-count");
    const data = await response.json();
    return data.count;
  } catch (error) {
    console.error("Failed to fetch booking count:", error);
    return 0;
  }
}

/**
 * Refresh the booking progress using live database data.
 */
async function updateProgressFromDatabase() {
  const currentBookings = await fetchBookingCount();
  updateBookingProgress(currentBookings, totalCanoesCurrentYear);
}

/**
 * Show a countdown or fetch the forecast when it becomes available.
 */
function fetchWeatherIfAvailable(eventDate) {
  const weatherStatus = document.getElementById("weatherStatus");
  const widgetForecast = document.getElementById("widgetForecast");

  if (!weatherStatus || !widgetForecast) {
    return;
  }

  const today = new Date();
  const millisecondsPerDay = 1000 * 60 * 60 * 24;
  const diffMilliseconds = eventDate - today;
  const diffDays = Math.ceil(diffMilliseconds / millisecondsPerDay);

  if (diffDays > weatherForecastDaysBeforeEvent) {
    const daysUntil = diffDays - weatherForecastDaysBeforeEvent;
    weatherStatus.innerHTML = `
      Prognos kommer vara tillgänglig om
      <span id="daysUntil">${daysUntil}</span> dagar
    `;
    widgetForecast.style.display = "none";
    return;
  }

  const formattedDate = eventDate.toISOString().split("T")[0];

  fetch(`/api/forecast?date=${formattedDate}`)
    .then((response) => response.json())
    .then((data) => {
      if (data.error) {
        throw new Error(data.error);
      }
      updateWeather(eventDate, data);
    })
    .catch((error) => {
      weatherStatus.innerText =
        `Tillgänglig ${weatherForecastDaysBeforeEvent} dagar innan`;
      console.error("Forecast error:", error);
    });
}

/**
 * Write forecast data into the weather widget.
 *
 * Args:
 *   eventDate: Date of the event.
 *   forecast: Forecast data returned by the backend.
 */
function updateWeather(eventDate, forecast) {
  const eventDateText = document.getElementById("eventDateText");
  const weatherStatus = document.getElementById("weatherStatus");
  const widgetForecast = document.getElementById("widgetForecast");
  const weatherIcon = document.getElementById("weatherIcon");
  const temperature = document.getElementById("temperature");
  const rainChance = document.getElementById("rainChance");

  if (
    !eventDateText ||
    !weatherStatus ||
    !widgetForecast ||
    !weatherIcon ||
    !temperature ||
    !rainChance
  ) {
    return;
  }

  eventDateText.innerText = eventDate.toLocaleDateString("sv-SE", {
    day: "numeric",
    month: "long",
    year: "numeric",
  });

  weatherStatus.style.display = "none";
  widgetForecast.style.display = "block";
  weatherIcon.innerText = forecast.icon;
  temperature.innerText = forecast.temperature;
  rainChance.innerText = forecast.rainChance;
}

/**
 * Open and close the shared modal components used on the homepage.
 */
function registerBasicModalTriggers() {
  const faqButton = document.getElementById("faqBtn");
  const contactButton = document.getElementById("contactBtn");
  const overviewTrigger = document.getElementById("overviewTrigger");
  const faqModal = document.getElementById("faqModal");
  const contactModal = document.getElementById("contactModal");
  const overviewModal = document.getElementById("overviewModal");
  const closeButtons = document.querySelectorAll(".modal-close");

  function openModal(modalElement) {
    if (modalElement) {
      modalElement.style.display = "flex";
    }
  }

  function closeModal(modalElement) {
    if (modalElement) {
      modalElement.style.display = "none";
    }
  }

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
      closeModal(button.closest(".modal"));
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

  if (faqModal) {
    const tabButtons = faqModal.querySelectorAll(".modal-tab");
    const tabPanels = faqModal.querySelectorAll(".modal-body");

    tabButtons.forEach((button) => {
      const targetPanelId = button.getAttribute("data-tab");
      const targetPanel = targetPanelId
        ? faqModal.querySelector(`#${targetPanelId}`)
        : null;

      if (targetPanel) {
        button.setAttribute("aria-controls", targetPanel.id);
      }
    });

    tabButtons.forEach((button) => {
      button.addEventListener("click", () => {
        const target = button.getAttribute("data-tab");

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

        const activePanel = faqModal.querySelector(`#${target}`);
        if (activePanel) {
          activePanel.classList.remove("modal-body--hidden");
          activePanel.hidden = false;
        }
      });
    });
  }
}

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
  await updateProgressFromDatabase();
  fetchWeatherIfAvailable(currentYearEventDate);
  registerBasicModalTriggers();
  registerGalleryModal();
  initializeGalleryRibbonMarquee();
  registerBookingModal();
  registerScrollAnimations();
});
