/**
 * File: static/js/booking_progress.js
 *
 * What it does:
 *   - Handles the public booking progress bar.
 *   - Fetches the current unavailable canoe count and updates the progress display.
 *
 * Why it is separate:
 *   - The booking-progress feature is small and mostly independent.
 *   - Splitting it out first is a low-risk way to start the JavaScript
 *     refactor.
 */

(function registerBookingProgressModule() {
  const eventSettings = window.PADDLINGEN_EVENT_SETTINGS || {};
  const totalAvailableCanoes = eventSettings.available_canoes_total || 50;

  /**
   * Render the current booking progress into the homepage progress bar.
   *
   * Args:
   *   bookedCanoes: Number of canoes currently blocking availability.
   *   totalAvailableCanoesForEvent: Total number of canoes available.
   */
  function updateBookingProgress(
    bookedCanoes,
    totalAvailableCanoesForEvent
  ) {
    const bookingPercentage = Math.min(
      100,
      Math.max(0, (bookedCanoes / totalAvailableCanoesForEvent) * 100)
    );
    const startHue = 120;
    const endHue = 0;
    const progressHue =
      startHue + (endHue - startHue) * (bookingPercentage / 100);
    const progressColor = `hsl(${progressHue}, 100%, 50%)`;

    const progressBarElement = document.getElementById("progressBar");
    const progressTextElement = document.getElementById("progressText");
    const bookButtonElement = document.getElementById("bookBtn");

    if (!progressBarElement || !progressTextElement || !bookButtonElement) {
      return;
    }

    progressBarElement.style.width = `${bookingPercentage}%`;
    progressBarElement.style.backgroundColor = progressColor;
    progressTextElement.innerHTML = `
      <span class="progress-text-main">${bookedCanoes} / ${totalAvailableCanoesForEvent} kanoter bokade</span>
      <span class="progress-text-hint">Tryck för att se deltagare</span>
    `;

    if (bookedCanoes >= totalAvailableCanoesForEvent) {
      bookButtonElement.disabled = true;
      bookButtonElement.innerText = "Fullbokat";
      bookButtonElement.setAttribute("aria-disabled", "true");
      return;
    }

    bookButtonElement.disabled = false;
    bookButtonElement.innerText = "Boka kanot";
    bookButtonElement.setAttribute("aria-disabled", "false");
  }

  /**
   * Fetch the number of canoes currently blocking availability.
   *
   * Returns:
   *   Promise<number>: Current unavailable-canoe count, or 0 if the request fails.
   */
  async function fetchBookingCount() {
    try {
      const response = await fetch("/api/booking-count");
      const responseData = await response.json();
      return responseData.count;
    } catch (error) {
      console.error("Failed to fetch booking count:", error);
      return 0;
    }
  }

  /**
   * Refresh the booking progress bar using live booking data.
   *
   * Returns:
   *   Promise<void>: Resolves when the progress display has been updated.
   */
  async function updateProgressFromDatabase() {
    const bookedCanoeCount = await fetchBookingCount();
    updateBookingProgress(bookedCanoeCount, totalAvailableCanoes);
  }

  window.PaddlingenBookingProgress = {
    updateBookingProgress,
    updateProgressFromDatabase,
  };
})();
