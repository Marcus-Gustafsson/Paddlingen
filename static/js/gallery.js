/**
 * File: app/static/js/gallery.js
 *
 * What it does:
 *   - Controls the previous-years gallery modal.
 *   - Controls the continuously moving previous-years ribbon.
 *
 * Why it is here:
 *   - Keeping gallery behavior in one file makes the homepage JavaScript
 *     easier to understand and keeps the ribbon and lightbox logic together.
 */

(function registerGalleryModule() {
  const previousYearGalleryImages =
    window.PADDLINGEN_PREVIOUS_YEAR_IMAGES || [];

  /**
   * Register the previous-years gallery modal and its controls.
   */
  function registerGalleryModal() {
    const modalElement = document.getElementById("galleryModal");
    const imageElement = modalElement
      ? modalElement.querySelector(".gallery-image")
      : null;
    const counterElement = modalElement
      ? modalElement.querySelector(".gallery-counter")
      : null;
    const closeButton = modalElement
      ? modalElement.querySelector(".gallery-close")
      : null;
    const previousButton = modalElement
      ? modalElement.querySelector(".gallery-prev")
      : null;
    const nextButton = modalElement
      ? modalElement.querySelector(".gallery-next")
      : null;
    const showGalleryButton = document.getElementById(
      "showPreviousYearsGallery"
    );

    if (
      !modalElement ||
      !imageElement ||
      !counterElement ||
      !closeButton ||
      !previousButton ||
      !nextButton
    ) {
      return;
    }

    let galleryImages = [];
    let currentImageIndex = 0;

    function updateGalleryView() {
      if (!galleryImages.length) {
        return;
      }

      imageElement.src = galleryImages[currentImageIndex];
      counterElement.textContent = `${currentImageIndex + 1} / ${galleryImages.length}`;
      previousButton.style.display = galleryImages.length > 1 ? "block" : "none";
      nextButton.style.display = galleryImages.length > 1 ? "block" : "none";
    }

    function openGallery(images, startIndex = 0) {
      if (!images.length) {
        return;
      }

      galleryImages = images;
      currentImageIndex = startIndex;
      updateGalleryView();
      modalElement.style.display = "flex";
    }

    function closeGallery() {
      modalElement.style.display = "none";
      galleryImages = [];
    }

    previousButton.addEventListener("click", () => {
      currentImageIndex =
        (currentImageIndex - 1 + galleryImages.length) % galleryImages.length;
      updateGalleryView();
    });

    nextButton.addEventListener("click", () => {
      currentImageIndex = (currentImageIndex + 1) % galleryImages.length;
      updateGalleryView();
    });

    closeButton.addEventListener("click", closeGallery);

    modalElement.addEventListener("click", (event) => {
      if (event.target === modalElement) {
        closeGallery();
      }
    });

    document.addEventListener("keydown", (event) => {
      if (modalElement.style.display !== "flex") {
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

  window.PaddlingenGallery = {
    initializeGalleryRibbonMarquee,
    registerGalleryModal,
  };
})();
