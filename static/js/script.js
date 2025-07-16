/**
 * File: app/static/js/script.js

 * What it does:
 *   - Controls frontend interactivity (opening/closing pop-up modals).
 
 * Why it’s here:
 *   - Keeps JavaScript separate from HTML so behavior is easy to update.
 */


// script.js

//////// CONSTANTS ////////

// How many canoes are available
const TOTAL_CANOES_CURRENT_YEAR = 50; 

// Set event’s date & time here:
const currentYearEventDate = new Date('2025-06-14T10:00:00');

const PRICE_PER_CANOE = 1200;   // in SEK

////////////////////



/**
 * PROGRESS BAR FUNCTIONALITY
 * 
 * This section handles the visual progress bar that shows how many canoes are booked.
 * Think of it like a gas gauge in a car - it shows how "full" the bookings are.
 */

/**
 * Updates the visual progress bar to show booking status.
 * 
 * How it works:
 * - Calculates what percentage of canoes are booked
 * - Changes color from green (few bookings) to red (almost full)
 * - Updates the text to show "X / Y kanoter bokade"
 * 
 * @param {number} booked - How many canoes have been booked so far
 * @param {number} total - Maximum number of canoes available
 * 
 * Example: updateBookingProgress(25, 50) means 25 out of 50 canoes are booked
 */
function updateBookingProgress(booked, total) {
  // Step 1: Calculate percentage (0-100)
  // Math.min() ensures we never go above 100%
  // Math.max() ensures we never go below 0%
  // This protects against weird data (like 60 bookings out of 50 total)
  const percent = Math.min(100, Math.max(0, (booked / total) * 100));

  // Step 2: Set up colors using the HSL color system
  // HSL = Hue, Saturation, Lightness
  // Hue is like a color wheel: 0° = red, 120° = green, 240° = blue
  const startHue = 120;   // Green (like grass) when few bookings
  const endHue   = 0;     // Red (like a stop sign) when almost full

  // Step 3: Calculate the current color based on how full we are
  // When percent = 0%, hue = 120 (green)
  // When percent = 100%, hue = 0 (red)
  // Everything in between is a smooth gradient
  const hue = startHue + (endHue - startHue) * (percent / 100);

  // Step 4: Create the color string that CSS understands
  // hsl(60, 100%, 50%) would be yellow
  // The 100% means "fully saturated" (vivid color)
  // The 50% means "normal brightness" (not too dark or light)
  const color = `hsl(${hue}, 100%, 50%)`;

  // Step 5: Find the progress bar element in your HTML
  // This looks for an element with id="progressBar"
  const bar = document.getElementById('progressBar');

  // Step 6: Update the bar's width to match the percentage
  // If 60% are booked, the bar fills 60% of its container
  bar.style.width = percent + '%';

  // Step 7: Apply the calculated color
  bar.style.backgroundColor = color;

  // Step 8: Update the text display
  // This shows something like "25 / 50 kanoter bokade"
  const text = document.getElementById('progressText');
  text.innerText = `${booked} / ${total} kanoter bokade`;


  // Step 2: Find the booking button in the HTML
  const bookBtn = document.getElementById('bookBtn');

  // Step 3: Check if we're at capacity
  if (booked >= total) {
    // We're full! Disable booking
    bookBtn.disabled = true;                      // Makes button unclickable
    bookBtn.innerText = 'Fullbokat';             // Changes button text
    bookBtn.setAttribute('aria-disabled', 'true'); // Helps screen readers
  } else {
    // Still room! Enable booking
    bookBtn.disabled = false;                      // Makes button clickable
    bookBtn.innerText = 'Boka kanot';              // Normal button text
    bookBtn.setAttribute('aria-disabled', 'false'); // Helps screen readers
  }
}



/**
 * Fetches the current number of bookings from your Flask server.
 * 
 * This function:
 * 1. Sends a request to your Python backend
 * 2. Gets the count of bookings in the database
 * 3. Returns that number
 * 
 * @returns {Promise<number>} The number of bookings (or 0 if error)
 */
async function fetchBookingCount() {
  try {
    // Send HTTP request to your Flask server
    // The '/api/booking-count' endpoint needs to be created in your Python code
    const response = await fetch('/api/booking-count');
    
    // Convert the response to JSON format
    const data = await response.json();
    
    // Expected response format: {count: 25}
    return data.count;
  } catch (error) {
    // If something goes wrong (network error, server down, etc.)
    console.error('Failed to fetch booking count:', error);
    return 0;  // Return 0 as a safe default
  }
}

/**
 * Updates the progress bar with real data from the database.
 * This is the main function that connects everything together.
 */
async function updateProgressFromDatabase() {
  // Step 1: Get the actual number of bookings from the server
  const currentBookings = await fetchBookingCount();
  
  // Step 2: Update the progress bar and button with real data
  updateBookingProgress(currentBookings, TOTAL_CANOES_CURRENT_YEAR);
}

// This runs once when the page loads (including after payment redirect)
document.addEventListener('DOMContentLoaded', async () => {
  // Get real booking data and update the progress bar
  await updateProgressFromDatabase();
});



// ===== Event Weather Forecast Widget =====

// 2. Fetch weather data from backend if within 14 days
function fetchWeatherIfAvailable(currentYearEventDate) {
  const today = new Date();
  const msPerDay = 1000 * 60 * 60 * 24;
  const diffMs = currentYearEventDate - today;
  const diffDays = Math.ceil(diffMs / msPerDay);

  // Show countdown or fetch forecast
  if (diffDays > 7) {
    const daysUntil = diffDays - 7;
    document.getElementById('weatherStatus').innerHTML = `
      Prognos kommer vara tillgänglig om
      <span id="daysUntil">${daysUntil}</span> dagar
    `;
    document.getElementById('widgetForecast').style.display = 'none';
  } else {
    // Format date to YYYY-MM-DD
    const formattedDate = currentYearEventDate.toISOString().split('T')[0];

    fetch(`/api/forecast?date=${formattedDate}`)
      .then(r => r.json())
      .then(data => {
        if (data.error) throw new Error(data.error);
        updateWeather(currentYearEventDate, data);
      })
      .catch(err => {
        document.getElementById('weatherStatus').innerText = "Tillgänglig 7 dagar innan";
        console.error("Forecast error:", err);
      });
  }
}

/**
 * Updates the weather widget with real forecast data.
 * @param {Date} currentYearEventDate - The date/time of your event
 * @param {Object} forecast - Contains temperature, rainChance and icon
 */
function updateWeather(currentYearEventDate, forecast) {
  // Format and display event date (e.g. “13 juni 2025”)
  document.getElementById('eventDateText').innerText =
    currentYearEventDate.toLocaleDateString('sv-SE', {
      day: 'numeric', month: 'long', year: 'numeric'
    });

  // Update UI elements with fetched forecast
  document.getElementById('weatherStatus').style.display = 'none';
  document.getElementById('widgetForecast').style.display = 'block';
  document.getElementById('weatherIcon').innerText = forecast.icon;
  document.getElementById('temperature').innerText = forecast.temperature;
  document.getElementById('rainChance').innerText = forecast.rainChance;
}

// Run on page load
document.addEventListener('DOMContentLoaded', () => {
  fetchWeatherIfAvailable(currentYearEventDate);
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
    threshold: 0.25                     // 50% of section must be visible
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
    threshold: 0.25     // Fire when X-% of the element is visible
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
});