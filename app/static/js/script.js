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
  // ── 1) MOBILE SIDEBAR TOGGLE ─────────────────────────────────────────────
  const toggleBtn = document.getElementById("sidebarToggle");
  const sidebar  = document.querySelector(".year-sidebar");

  if (toggleBtn && sidebar) {
    toggleBtn.addEventListener("click", () => {
      // Check computed style so we respect media-query hiding/showing
      const currentDisplay = window.getComputedStyle(sidebar).display;
      if (currentDisplay === "none") {
        sidebar.style.display = "block";
      } else {
        sidebar.style.display = "none";
      }
    });
  }

  // ── 2) MOBILE ÖVERSIKT (OVERVIEW) POP-UP TOGGLE ─────────────────────────
  const overviewBtn  = document.getElementById("mobileOverviewBtn");
  const overviewDiv  = document.getElementById("overviewPanel");

  if (overviewBtn && overviewDiv) {
    // Show the overlay
    overviewBtn.addEventListener("click", () => {
      overviewDiv.classList.add("scrolled");
    });

    // Hide when tapping the “✕” in the top-right
    overviewDiv.addEventListener("click", (e) => {
      // If the user clicks anywhere on the overlay background or the “X” pseudo-element,
      // close the overview. (We can detect clicks outside the table easily.)
      // We check if the click target is exactly the outer overlay, not inside the table.
      if (e.target === overviewDiv) {
        overviewDiv.classList.remove("scrolled");
      }
    });
  }

  // ── 3) OPTIONAL: Close “Översikt” when pressing “Escape” on mobile/desktop ─
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape" && overviewDiv.classList.contains("scrolled")) {
      overviewDiv.classList.remove("scrolled");
    }
  });
});




