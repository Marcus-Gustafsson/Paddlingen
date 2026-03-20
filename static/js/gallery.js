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
    const infoTriggerButton = modalElement
      ? modalElement.querySelector(".gallery-info-trigger")
      : null;
    const infoPanelElement = modalElement
      ? modalElement.querySelector(".gallery-info-panel")
      : null;
    const infoCloseButton = modalElement
      ? modalElement.querySelector(".gallery-info-close")
      : null;
    const infoImageIdElement = modalElement
      ? modalElement.querySelector(".gallery-info-image-id")
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
      !infoTriggerButton ||
      !infoPanelElement ||
      !infoCloseButton ||
      !infoImageIdElement ||
      !closeButton ||
      !previousButton ||
      !nextButton
    ) {
      return;
    }

    let galleryImages = [];
    let currentImageIndex = 0;
    const preloadedGalleryImageUrls = new Set();

    infoTriggerButton.setAttribute("aria-expanded", "false");

    function getImageUrlByIndex(imageIndex) {
      if (!galleryImages.length) {
        return null;
      }

      const normalizedIndex =
        (imageIndex + galleryImages.length) % galleryImages.length;
      const selectedImage = galleryImages[normalizedIndex];
      return typeof selectedImage === "string" ? selectedImage : selectedImage.url;
    }

    function preloadGalleryImageAtIndex(imageIndex) {
      const imageUrl = getImageUrlByIndex(imageIndex);
      if (!imageUrl || preloadedGalleryImageUrls.has(imageUrl)) {
        return;
      }

      const preloadedImage = new Image();
      preloadedImage.decoding = "async";
      preloadedImage.src = imageUrl;
      preloadedGalleryImageUrls.add(imageUrl);
    }

    function updateGalleryView() {
      if (!galleryImages.length) {
        return;
      }

      const currentImage = galleryImages[currentImageIndex];
      const imageUrl =
        typeof currentImage === "string" ? currentImage : currentImage.url;
      const imageId =
        typeof currentImage === "string"
          ? `IMG-${String(currentImageIndex + 1).padStart(4, "0")}`
          : currentImage.id;
      imageElement.src = imageUrl;
      imageElement.alt = `Galleri bild ${imageId}`;
      counterElement.textContent = `${currentImageIndex + 1} / ${galleryImages.length}`;
      infoImageIdElement.textContent = `ID: ${imageId}`;
      previousButton.style.display = galleryImages.length > 1 ? "block" : "none";
      nextButton.style.display = galleryImages.length > 1 ? "block" : "none";

      if (galleryImages.length > 1) {
        preloadGalleryImageAtIndex(currentImageIndex + 1);
        preloadGalleryImageAtIndex(currentImageIndex - 1);
      }
    }

    function openGalleryInfoPanel() {
      infoPanelElement.hidden = false;
      infoTriggerButton.setAttribute("aria-expanded", "true");
    }

    function closeGalleryInfoPanel() {
      infoPanelElement.hidden = true;
      infoTriggerButton.setAttribute("aria-expanded", "false");
    }

    function openGallery(images, startIndex = 0) {
      if (!images.length) {
        return;
      }

      galleryImages = images;
      currentImageIndex = startIndex;
      preloadedGalleryImageUrls.clear();
      closeGalleryInfoPanel();
      updateGalleryView();
      modalElement.style.display = "flex";
    }

    function closeGallery() {
      modalElement.style.display = "none";
      closeGalleryInfoPanel();
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
    infoTriggerButton.addEventListener("click", () => {
      if (infoPanelElement.hidden) {
        openGalleryInfoPanel();
        return;
      }

      closeGalleryInfoPanel();
    });
    infoCloseButton.addEventListener("click", closeGalleryInfoPanel);

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
        if (!infoPanelElement.hidden) {
          closeGalleryInfoPanel();
          return;
        }

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
