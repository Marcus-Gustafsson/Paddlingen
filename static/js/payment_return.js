/**
 * File: static/js/payment_return.js
 *
 * What it does:
 *   - Polls the local booking state after Stripe redirects back.
 *   - Redirects to the final confirmed success page only after the local
 *     booking is marked as paid by the verified webhook.
 *
 * Why it is here:
 *   - Stripe-hosted Checkout controls when the browser leaves Stripe.
 *   - This page makes sure the visitor does not see the final success state
 *     until the app has confirmed the booking locally.
 */

(function registerPaymentReturnModule() {
  const paymentReturnCard = document.getElementById("paymentReturnCard");
  if (!paymentReturnCard) {
    return;
  }

  const paymentStatusUrl = paymentReturnCard.dataset.paymentStatusUrl || "";
  const confirmedReturnUrl =
    paymentReturnCard.dataset.confirmedReturnUrl || window.location.href;
  const homeUrl = paymentReturnCard.dataset.homeUrl || "/";
  const headingElement = document.getElementById("paymentReturnHeading");
  const messageElement = document.getElementById("paymentReturnMessage");
  const statusNoteElement = document.getElementById("paymentReturnStatusNote");
  const primaryLinkElement = document.getElementById("paymentReturnPrimaryLink");
  const spinnerElement = document.getElementById("paymentReturnSpinner");

  if (!paymentStatusUrl) {
    return;
  }

  let isFinished = false;
  let timedOut = false;
  const pollIntervalMs = 1500;
  const timeoutMs = 45000;

  function showPrimaryLink(label, url) {
    if (!primaryLinkElement) {
      return;
    }

    primaryLinkElement.textContent = label;
    primaryLinkElement.href = url;
    primaryLinkElement.classList.remove("is-hidden");
  }

  function hideSpinner() {
    if (spinnerElement) {
      spinnerElement.classList.add("is-hidden");
    }
  }

  function showErrorState(
    message,
    note,
    headingText = "Bokningen kunde inte slutföras automatiskt"
  ) {
    isFinished = true;
    hideSpinner();
    paymentReturnCard.classList.remove("payment-return-card--processing");

    if (headingElement) {
      headingElement.textContent = headingText;
    }

    if (messageElement) {
      messageElement.textContent = message;
    }

    if (statusNoteElement) {
      statusNoteElement.textContent = note;
      statusNoteElement.classList.remove("is-hidden");
    }

    showPrimaryLink("Tillbaka till hemsidan", homeUrl);
  }

  function showPayloadErrorState(payload, fallbackMessage, fallbackNote) {
    const headingText =
      payload && typeof payload.heading === "string"
        ? payload.heading
        : "Bokningen kunde inte slutföras automatiskt";
    const message =
      payload && typeof payload.message === "string"
        ? payload.message
        : fallbackMessage;
    const statusNote =
      payload && typeof payload.status_note === "string"
        ? payload.status_note
        : fallbackNote;

    showErrorState(message, statusNote, headingText);
  }

  function buildFailedConfirmationUrl() {
    const separator = paymentStatusUrl.includes("?") ? "&" : "?";
    return `${paymentStatusUrl}${separator}finalize_failed=1`;
  }

  async function pollBookingStatus() {
    if (isFinished || timedOut) {
      return;
    }

    try {
      const response = await fetch(paymentStatusUrl, {
        headers: {
          Accept: "application/json",
        },
        credentials: "same-origin",
        cache: "no-store",
      });

      if (!response.ok) {
        throw new Error(`Unexpected status ${response.status}`);
      }

      const payload = await response.json();
      const bookingStatus = payload.booking_status || "unknown";

      if (payload.reload_page) {
        isFinished = true;
        window.location.replace(payload.redirect_url || homeUrl);
        return;
      }

      if (bookingStatus === "paid") {
        isFinished = true;
        window.location.replace(confirmedReturnUrl);
        return;
      }

      if (bookingStatus === "pending") {
        window.setTimeout(pollBookingStatus, pollIntervalMs);
        return;
      }

      if (bookingStatus === "not_found") {
        showPayloadErrorState(
          payload,
          "Bokningen kunde inte hittas längre. Om betalningen drogs ska du inte betala igen.",
          "Kontakta arrangören och ange din bokningsreferens om du behöver hjälp."
        );
        return;
      }

      if (
        bookingStatus === "canceled" ||
        bookingStatus === "expired" ||
        bookingStatus === "payment_failed" ||
        bookingStatus === "session_mismatch"
      ) {
        showPayloadErrorState(
          payload,
          "Betalningen kunde inte kopplas till en aktiv bokning.",
          "Gå tillbaka till startsidan och börja om om du fortfarande vill boka en kanot."
        );
        return;
      }

      showPayloadErrorState(
        payload,
        "Bokningen kunde inte bekräftas automatiskt just nu.",
        "Vänta en stund och kontrollera bokningen igen om du redan har betalat."
      );
    } catch (error) {
      window.setTimeout(pollBookingStatus, pollIntervalMs);
    }
  }

  async function finalizeFailedConfirmation() {
    try {
      const response = await fetch(buildFailedConfirmationUrl(), {
        headers: {
          Accept: "application/json",
        },
        credentials: "same-origin",
        cache: "no-store",
      });

      if (!response.ok) {
        throw new Error(`Unexpected status ${response.status}`);
      }

      const payload = await response.json();
      const bookingStatus = payload.booking_status || "unknown";

      if (payload.reload_page) {
        isFinished = true;
        window.location.replace(payload.redirect_url || homeUrl);
        return;
      }

      if (bookingStatus === "paid") {
        isFinished = true;
        window.location.replace(confirmedReturnUrl);
        return;
      }

      if (bookingStatus === "pending") {
        showPayloadErrorState(
          payload,
          "Betalningen väntar fortfarande på bekräftelse.",
          "Boka inte samma kanoter igen just nu."
        );
        return;
      }

      showPayloadErrorState(
        payload,
        "Det tog för lång tid att bekräfta bokningen automatiskt.",
        "Gå tillbaka till startsidan och gör en ny bokning om du fortfarande vill boka en kanot."
      );
    } catch (error) {
      showErrorState(
        "Det tog för lång tid att bekräfta bokningen automatiskt.",
        "Vi kunde inte avgöra om reservationen skulle släppas. Vänta en stund och kontrollera bokningen igen om du redan har betalat."
      );
    }
  }

  window.setTimeout(async function handlePollingTimeout() {
    if (isFinished) {
      return;
    }

    timedOut = true;
    await finalizeFailedConfirmation();
  }, timeoutMs);

  pollBookingStatus();
})();
