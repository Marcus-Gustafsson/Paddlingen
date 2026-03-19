/**
 * File: app/static/js/weather.js
 *
 * What it does:
 *   - Controls the homepage weather widget.
 *   - Shows either a countdown until the forecast is available or the
 *     forecast itself when the backend can return it.
 *
 * Why it is here:
 *   - Keeping weather logic in its own file makes the public JavaScript
 *     easier to understand and test one feature at a time.
 */

(function registerWeatherModule() {
  const eventSettings = window.PADDLINGEN_EVENT_SETTINGS || {};

  const eventDate = new Date(
    eventSettings.datetime_local_iso || new Date().toISOString()
  );
  const forecastDaysBeforeEvent =
    eventSettings.weather_forecast_days_before_event || 7;

  /**
   * Write the returned forecast data into the weather widget.
   *
   * Args:
   *   forecastData: Forecast data returned by the backend API.
   */
  function updateWeatherWidget(forecastData) {
    const eventDateTextElement = document.getElementById("eventDateText");
    const weatherStatusElement = document.getElementById("weatherStatus");
    const widgetForecastElement = document.getElementById("widgetForecast");
    const weatherIconElement = document.getElementById("weatherIcon");
    const temperatureElement = document.getElementById("temperature");
    const rainChanceElement = document.getElementById("rainChance");

    if (
      !eventDateTextElement ||
      !weatherStatusElement ||
      !widgetForecastElement ||
      !weatherIconElement ||
      !temperatureElement ||
      !rainChanceElement
    ) {
      return;
    }

    eventDateTextElement.textContent = eventDate.toLocaleDateString("sv-SE", {
      day: "numeric",
      month: "long",
      year: "numeric",
    });

    weatherStatusElement.style.display = "none";
    widgetForecastElement.style.display = "block";
    weatherIconElement.textContent = forecastData.icon;
    temperatureElement.textContent = forecastData.temperature;
    rainChanceElement.textContent = forecastData.rainChance;
  }

  /**
   * Fetch the weather forecast from the backend for the configured event date.
   */
  async function fetchWeatherForecast() {
    const formattedDate = eventDate.toISOString().split("T")[0];
    const response = await fetch(`/api/forecast?date=${formattedDate}`);
    const forecastData = await response.json();

    if (forecastData.error) {
      throw new Error(forecastData.error);
    }

    updateWeatherWidget(forecastData);
  }

  /**
   * Show a countdown or load the weather forecast when it becomes available.
   */
  async function initializeWeatherWidget() {
    const weatherStatusElement = document.getElementById("weatherStatus");
    const widgetForecastElement = document.getElementById("widgetForecast");

    if (!weatherStatusElement || !widgetForecastElement) {
      return;
    }

    const currentDate = new Date();
    const millisecondsPerDay = 1000 * 60 * 60 * 24;
    const differenceInMilliseconds = eventDate - currentDate;
    const differenceInDays = Math.ceil(
      differenceInMilliseconds / millisecondsPerDay
    );

    if (differenceInDays > forecastDaysBeforeEvent) {
      const daysUntilForecast = differenceInDays - forecastDaysBeforeEvent;
      weatherStatusElement.textContent =
        `Prognos kommer vara tillgänglig om ${daysUntilForecast} dagar`;
      widgetForecastElement.style.display = "none";
      return;
    }

    try {
      await fetchWeatherForecast();
    } catch (error) {
      weatherStatusElement.textContent =
        `Tillgänglig ${forecastDaysBeforeEvent} dagar innan`;
      console.error("Forecast error:", error);
    }
  }

  window.PaddlingenWeather = {
    initializeWeatherWidget,
  };
})();
