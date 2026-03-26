/**
 * File: app/static/js/main.js
 *
 * What it does:
 *   - Controls the remaining public page interactivity after the JavaScript
 *     feature split.
 *   - Right now this mainly means the homepage scroll animations and the
 *     shared page initialization sequence.
 *
 * Why it is here:
 *   - This file stays small on purpose so the public page can still be loaded
 *     with plain browser scripts and no build step.
 */

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
    bookingProgressModule.updateProgressFromDatabase();
  }

  const weatherModule = window.PaddlingenWeather;
  if (weatherModule) {
    await weatherModule.initializeWeatherWidget();
  }

  const modalModule = window.PaddlingenModals;
  if (modalModule) {
    modalModule.registerPublicModals();
  }

  const galleryModule = window.PaddlingenGallery;
  if (galleryModule) {
    galleryModule.registerGalleryModal();
    galleryModule.initializeGalleryRibbonMarquee();
  }

  const bookingModule = window.PaddlingenBooking;
  if (bookingModule) {
    bookingModule.registerBookingModal();
  }

  registerScrollAnimations();
});
