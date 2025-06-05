/**
 * File: app/static/js/script.js

 * What it does:
 *   - Controls frontend interactivity (opening/closing pop-up modals).
 
 * Why it’s here:
 *   - Keeps JavaScript separate from HTML so behavior is easy to update.
 */


// script.js



/**
 * Update the progress bar fill, text, and use a smooth green→red gradient.
 *
 * @param {number} booked - How many canoes have been booked.
 * @param {number} total  - Total available canoes.
 */
function updateProgress(booked, total) {
  // 1. Compute percent fill, clamped between 0 and 100.
  const percent = Math.min(100, Math.max(0, (booked / total) * 100));

  // 2. Define hue endpoints for the gradient (green to red).
  const startHue = 120;   // green at 120°
  const endHue   = 0;     // red at 0°

  // 3. Interpolate between startHue and endHue based on percent.
  const hue = startHue + (endHue - startHue) * (percent / 100);

  // 4. Build the HSL color string.
  const color = `hsl(${hue}, 100%, 50%)`;

  // 5. Find the progress-bar element by its ID.
  const bar = document.getElementById('progressBar');

  // 6. Set the bar’s width to match the booking percentage.
  bar.style.width = percent + '%';

  // 7. Update the bar’s background color to the computed HSL value.
  bar.style.backgroundColor = color;

  // 8. Update the centered text inside the bar.
  const text = document.getElementById('progressText');
  text.innerText = `${booked} / ${total} kanoter bokade`;
}

/**
 * Test function to demonstrate disabling the "Book" button
 * when booked reaches total. Call this with your desired values.
 */
function testBookingState(booked, total) {
  // 1. First, update the progress bar and its text.
  updateProgress(booked, total);

  // 2. Grab the booking button by its ID.
  const bookBtn = document.getElementById('bookBtn');

  // 3. If fully booked (booked >= total), disable and change text.
  if (booked >= total) {
    bookBtn.disabled = true;                   // Disable clicks
    bookBtn.innerText = 'Fullbokat';           // Change button label
    bookBtn.setAttribute('aria-disabled', 'true'); // Accessibility hint
  } else {
    // 4. Otherwise, ensure button is enabled with original text.
    bookBtn.disabled = false;
    bookBtn.innerText = 'Boka kanot';
    bookBtn.setAttribute('aria-disabled', 'false');
  }
}

// ===== Example test run =====
// When the DOM is loaded, run a test where 50 of 50 canoes are booked.
document.addEventListener('DOMContentLoaded', () => {
  testBookingState(49, 50);
});




// ===== Dummy test parameters =====
// 1. Set your event’s date & time here:
const eventDate = new Date('2025-06-13T10:00:00');

// 2. Placeholder forecast data (replace with real API response)
const dummyForecast = {
  icon: '☀️',        // could be an <img> URL or emoji
  temperature: 22,   // degrees Celsius
  rainChance: 10     // percent
};

/**
 * Updates the weather widget UI.
 * - Shows countdown until forecast opens (>14 days).
 * - Shows actual forecast when within 14 days.
 */
function updateWeather(eventDate, forecast) {
  const today    = new Date();                       // current date/time
  const msPerDay = 1000 * 60 * 60 * 24;              // ms in one day
  const diffMs   = eventDate - today;                // ms until event
  const diffDays = Math.ceil(diffMs / msPerDay);     // round up to whole days

  // 1. Update the event date in the title (e.g. “15 juni 2025”)
  document.getElementById('eventDateText').innerText =
    eventDate.toLocaleDateString('sv-SE', {
      day: 'numeric', month: 'long', year: 'numeric'
    });

  const statusEl   = document.getElementById('weatherStatus');
  const forecastEl = document.getElementById('widgetForecast');

  if (diffDays > 14) {
    // a) Too early: show “available in X days”
    const daysUntil = diffDays - 14;  // days left until forecast opens
    statusEl.innerHTML = `
      Prognos kommer vara tillgänglig om
      <span id="daysUntil">${daysUntil}</span> dagar
    `;
    forecastEl.style.display = 'none'; // hide forecast details
  } else {
    // b) Within 14 days: show forecast
    statusEl.style.display   = 'none';  // hide the countdown text
    forecastEl.style.display = 'block'; // reveal forecast

    // 2. Populate real forecast values
    document.getElementById('weatherIcon').innerText = forecast.icon;
    document.getElementById('temperature').innerText = forecast.temperature;
    document.getElementById('rainChance').innerText  = forecast.rainChance;
  }
}

// Run on page load (or call again after fetching real API)
document.addEventListener('DOMContentLoaded', () => {
  updateWeather(eventDate, dummyForecast);
  // Later, you can fetch real data:
  // fetch('/api/forecast?date=2025-06-15')
  //   .then(r => r.json())
  //   .then(data => updateWeather(eventDate, data));
});



document.addEventListener('DOMContentLoaded', () => {
  // 1. Grab all year sections and sidebar links
  const sections = document.querySelectorAll('.year-section');
  const sidebarLinks = document.querySelectorAll('.year-sidebar a');

  // 2. Build a map from section ID → sidebar <a>
  const linkMap = {};
  sidebarLinks.forEach(link => {
    const target = link.getAttribute('href').slice(1); // "year-2024"
    linkMap[target] = link;
  });

  // 3. IntersectionObserver callback
  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      const id = entry.target.id;       // e.g. "year-2024"
      const link = linkMap[id];
      if (entry.isIntersecting) {
        // a) Section is in view → mark its link active
        link.classList.add('active');
      } else {
        // b) Section is out of view → remove active
        link.classList.remove('active');
      }
    });
  }, {
    root: null,                        // viewport
    threshold: 0.5                     // 50% of section must be visible
  });

  // 4. Observe each section
  sections.forEach(section => observer.observe(section));
});



// ===== SCROLL-TRIGGERED ANIMATIONS =====
document.addEventListener('DOMContentLoaded', () => {
  // 1. Select all elements marked for scroll animation
  const animatables = document.querySelectorAll('.scroll-animate');

  // 2. Create an IntersectionObserver
  const animObserver = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        // a) Entered viewport: add .in-view to trigger CSS animation
        entry.target.classList.add('in-view');
      } else {
        // b) Left viewport: remove if you want to re-animate on re-entry
        entry.target.classList.remove('in-view');
      }
    });
  }, {
    root: null,        // Use the browser viewport
    threshold: 0.25     // Fire when 20% of the element is visible
  });

  // 3. Observe each target element
  animatables.forEach(el => animObserver.observe(el));
});



document.addEventListener("DOMContentLoaded", () => {
  const overviewBtn = document.getElementById("mobileOverviewBtn");
  const overviewDiv = document.getElementById("overviewPanel");

  if (overviewBtn && overviewDiv) {
    // Show overview on “Översikt” click
    overviewBtn.addEventListener("click", () => {
      overviewDiv.classList.add("scrolled");
    });

    // Hide when tapping outside the table (backdrop)
    overviewDiv.addEventListener("click", e => {
      if (e.target === overviewDiv) {
        overviewDiv.classList.remove("scrolled");
      }
    });

    // ===== OUR NEW CLOSE-BUTTON =====
    const closeBtn = overviewDiv.querySelector(".overview-close");
    if (closeBtn) {
      closeBtn.addEventListener("click", () => {
        overviewDiv.classList.remove("scrolled");
      });
    }

    // Hide on Escape key
    document.addEventListener("keydown", e => {
      if (e.key === "Escape" && overviewDiv.classList.contains("scrolled")) {
        overviewDiv.classList.remove("scrolled");
      }
    });
  }
});


document.addEventListener("DOMContentLoaded", () => {
  // 1. Grab our buttons and modals
  const faqBtn      = document.getElementById("faqBtn");
  const contactBtn  = document.getElementById("contactBtn");
  const faqModal    = document.getElementById("faqModal");
  const contactModal= document.getElementById("contactModal");
  const closeBtns   = document.querySelectorAll(".modal-close");
  const tabButtons = faqModal.querySelectorAll(".modal-tab");
  const tabPanels  = faqModal.querySelectorAll(".modal-body");

  // 2. Utility to open a modal
  function openModal(modal) {
    modal.style.display = "flex";
  }

  // 3. Utility to close a modal
  function closeModal(modal) {
    modal.style.display = "none";
  }

  // 4. Hook up button clicks to open
  faqBtn.addEventListener("click",   () => openModal(faqModal));
  contactBtn.addEventListener("click", () => openModal(contactModal));

  // 5. Hook up each “×” close button
  closeBtns.forEach(btn => {
    btn.addEventListener("click", () => {
      const modal = btn.closest(".modal");
      closeModal(modal);
    });
  });

  // 6. Click outside content box to close
  [faqModal, contactModal].forEach(modal => {
    modal.addEventListener("click", e => {
      if (e.target === modal) {         // only if we click the backdrop
        closeModal(modal);
      }
    });
  });

  // 7. Press Escape to close any open modal
  document.addEventListener("keydown", e => {
    if (e.key === "Escape") {
      [faqModal, contactModal].forEach(closeModal);
    }
  });


  tabButtons.forEach(btn => {
    btn.addEventListener("click", () => {
      const target = btn.getAttribute("data-tab");  // "questions" or "rules"

      // a) Remove active class from all tabs
      tabButtons.forEach(t => t.classList.remove("modal-tab--active"));
      // b) Hide all panels
      tabPanels.forEach(p => p.classList.add("modal-body--hidden"));

      // c) Activate clicked tab
      btn.classList.add("modal-tab--active");
      // d) Show the matching panel
      faqModal.querySelector(`#${target}`).classList.remove("modal-body--hidden");
    });
  });
});




// ===== IMAGE GALLERY (LIGHTBOX) =====
document.addEventListener("DOMContentLoaded", () => {
  // 1) Grab modal elements
  const modal       = document.getElementById("galleryModal");
  const imgEl       = modal.querySelector(".gallery-image");
  const counterEl   = modal.querySelector(".gallery-counter");
  const btnClose    = modal.querySelector(".gallery-close");
  const btnPrev     = modal.querySelector(".gallery-prev");
  const btnNext     = modal.querySelector(".gallery-next");

  // 2) State: current image list and index
  let galleryImages = [];
  let currentIndex  = 0;

  // 3) Utility: show modal
  function openGallery(images, startIndex = 0) {
    galleryImages = images;         // store URLs
    currentIndex  = startIndex;     // start on chosen image
    updateGallery();                // show image & caption
    modal.style.display = "flex";   // reveal the modal
  }

  // 4) Utility: hide modal
  function closeGallery() {
    modal.style.display = "none";
    galleryImages = [];
  }

  // 5) Utility: refresh the <img> and caption
  function updateGallery() {
    const url = galleryImages[currentIndex];
    imgEl.src = url;                          // update image
    counterEl.innerText = `${currentIndex+1} / ${galleryImages.length}`;
    // Show or hide arrows if only one image
    btnPrev.style.display = galleryImages.length > 1 ? "block" : "none";
    btnNext.style.display = galleryImages.length > 1 ? "block" : "none";
  }

  // 6) Wire up Prev/Next buttons
  btnPrev.addEventListener("click", () => {
    currentIndex = (currentIndex - 1 + galleryImages.length) % galleryImages.length;
    updateGallery();
  });
  btnNext.addEventListener("click", () => {
    currentIndex = (currentIndex + 1) % galleryImages.length;
    updateGallery();
  });

  // 7) Close by × or backdrop click
  btnClose.addEventListener("click", closeGallery);
  modal.addEventListener("click", e => {
    if (e.target === modal) closeGallery();
  });

  // 8) Close on Escape, Left/Right arrows for navigation
  document.addEventListener("keydown", e => {
    if (modal.style.display !== "flex") return; // only if open
    if (e.key === "Escape")      closeGallery();
    if (e.key === "ArrowLeft")   btnPrev.click();
    if (e.key === "ArrowRight")  btnNext.click();
  });

  // 9) Hook up each "Visa bilder" button
  //    Buttons have IDs like "showPhotos2024" in each .year-section
  const galleryButtons = document.querySelectorAll("button[id^='showPhotos']");
  galleryButtons.forEach(btn => {
    btn.addEventListener("click", () => {
      // a) Find this button's section
      const section = btn.closest(".year-section");
      // b) Collect all .grid-cell background-image URLs
      const cells   = section.querySelectorAll(".photo-grid-bg .grid-cell");
      const urls    = Array.from(cells).map(cell => {
        // cell.style.backgroundImage is like 'url("…/img.jpg")'
        const bg = cell.style.backgroundImage;
        // remove url("…") wrapper:
        return bg.slice(5, -2);
      });
      // c) Open gallery starting at the first image
      openGallery(urls, 0);
    });
  });
});



// ===== BOOKING MODAL & FORM LOGIC =====
document.addEventListener("DOMContentLoaded", () => {
  // 0) CONSTANTS
  const PRICE_PER_CANOE = 900;   // cost per canoe in SEK

  // 1) GRAB ALL THE ELEMENTS WE’LL NEED
  const openBtn    = document.getElementById("bookBtn");           // “Boka kanot” button
  const modal      = document.getElementById("bookingModal");      // The whole modal overlay
  const form       = document.getElementById("bookingForm");       // The <form> inside the modal
  const select     = document.getElementById("canoeCount");        // <select> for number of canoes
  const namesWrap  = document.getElementById("nameFieldsContainer"); // Where we inject name inputs
  const priceInfo  = document.getElementById("priceInfo");         // Shows “Totalt: … kr”
  const cancelBtn  = document.getElementById("cancelBooking");     // “Avbryt” button
  const submitBtn  = document.getElementById("confirmBooking");    // “Betala” button

  // 2) OPEN THE MODAL
  openBtn.addEventListener("click", () => {
    // a) Show the modal
    modal.style.display = "flex";

    // b) Reset any previous state
    form.reset();                   // clear select + inputs
    namesWrap.innerHTML = "";       // remove old name fields
    priceInfo.textContent = 
      `Totalt: 0 kr (${PRICE_PER_CANOE} kr per kanot)`;
    submitBtn.disabled = true;      // disable “Betala” until ready
    cancelBtn.disabled = false;     // ensure “Avbryt” is clickable
  });

  // 3) CLOSE HELPER FUNCTION
  function closeModal() {
    modal.style.display = "none";
  }
  // a) Clicking “Avbryt”
  cancelBtn.addEventListener("click", closeModal);
  // b) Clicking outside the content box (the backdrop)
  modal.addEventListener("click", e => {
    if (e.target === modal) closeModal();
  });
  // c) Pressing Escape
  document.addEventListener("keydown", e => {
    if (e.key === "Escape" && modal.style.display === "flex") {
      closeModal();
    }
  });

  // 4) WHEN USER CHOOSES NUMBER OF CANOES
  select.addEventListener("change", () => {
    const count = parseInt(select.value, 10); // how many canoes
    namesWrap.innerHTML = "";                 // clear old fields

    // a) Build one pair of inputs (first + last name) per canoe
    for (let i = 1; i <= count; i++) {
      const wrapper = document.createElement("div");
      wrapper.className = "canoe-field";

      // Label above the inputs
      const lbl = document.createElement("label");
      lbl.setAttribute("for", `canoe${i}_fname`);
      lbl.innerText = 
        `Kanot ${i}: \n (Ange namn på den som hämtar ut kanoten)`;
      wrapper.appendChild(lbl);

      // Container for two side-by-side inputs
      const inputsDiv = document.createElement("div");
      inputsDiv.className = "inputs";

      // First name input
      const first = document.createElement("input");
      first.type        = "text";
      first.id          = `canoe${i}_fname`;
      first.name        = `canoe${i}_fname`;
      first.placeholder = "Förnamn";
      first.required    = true;

      // Last name input
      const last = document.createElement("input");
      last.type         = "text";
      last.id           = `canoe${i}_lname`;
      last.name         = `canoe${i}_lname`;
      last.placeholder  = "Efternamn";
      last.required     = true;

      // Assemble the two inputs
      inputsDiv.appendChild(first);
      inputsDiv.appendChild(last);
      wrapper.appendChild(inputsDiv);
      namesWrap.appendChild(wrapper);
    }

    // b) Update the total price display
    priceInfo.textContent = 
      `Totalt: ${count * PRICE_PER_CANOE} kr (${PRICE_PER_CANOE} kr per kanot)`;

    // c) Form validation: only enable “Betala” when ALL inputs are non-empty
    const allInputs = namesWrap.querySelectorAll("input");
    function validate() {
      // Check every input has some non-whitespace text
      const allFilled = Array.from(allInputs)
        .every(inp => inp.value.trim() !== "");
      submitBtn.disabled = !allFilled;
    }
    // Attach an ‘input’ listener to each field
    allInputs.forEach(i => i.addEventListener("input", validate));
    validate(); // run once in case there’s only one canoe
  });

  // 5) HANDLE FORM SUBMISSION (BETALA)
 
  
});