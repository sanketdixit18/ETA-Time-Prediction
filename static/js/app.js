(() => {
  "use strict";

  const $ = (id) => document.getElementById(id);
  const form = $("eta-form");
  const submitBtn = $("submit-btn");
  const resultBody = $("result-body");
  const distanceReadout = $("distance-readout");
  const prepHint = $("prep-hint");

  // illustrative routes (restaurant -> delivery) so the form can be tried in one click
  const SAMPLES = {
    mumbai:    [19.1136, 72.8697, 19.1176, 72.9047],
    bengaluru: [12.9716, 77.5946, 12.9352, 77.6245],
    pune:      [18.5204, 73.8567, 18.5590, 73.7868],
    delhi:     [28.6139, 77.2090, 28.5355, 77.2100],
    hyderabad: [17.4401, 78.3489, 17.4326, 78.4071],
  };
  const ROUTE_IDS = ["restaurant_latitude", "restaurant_longitude", "delivery_latitude", "delivery_longitude"];

  // ---------- helpers ----------
  const pad = (n) => String(n).padStart(2, "0");
  const toMinutes = (hhmm) => { const [h, m] = hhmm.split(":").map(Number); return h * 60 + m; };
  const fromMinutes = (total) => { const t = ((total % 1440) + 1440) % 1440; return `${pad(Math.floor(t / 60))}:${pad(t % 60)}`; };

  // same formula as the backend: absolute coordinates, haversine, earth radius 6371 km
  function haversineKm(lat1, lon1, lat2, lon2) {
    const rad = (d) => (Math.abs(d) * Math.PI) / 180;
    const dLat = rad(lat2) - rad(lat1);
    const dLon = rad(lon2) - rad(lon1);
    const a = Math.sin(dLat / 2) ** 2 + Math.cos(rad(lat1)) * Math.cos(rad(lat2)) * Math.sin(dLon / 2) ** 2;
    return 6371 * 2 * Math.asin(Math.sqrt(a));
  }

  // same bins the backend uses to create "distance_type"
  function distanceBand(km) {
    if (km < 5) return "short";
    if (km < 10) return "medium";
    if (km < 15) return "long";
    if (km < 25) return "very long";
    return null;
  }

  function routeDistance() {
    const v = ROUTE_IDS.map((id) => parseFloat($(id).value));
    return v.every(Number.isFinite) ? haversineKm(...v) : null;
  }

  // ---------- live hints ----------
  function updateDistance() {
    const km = routeDistance();
    distanceReadout.classList.remove("warn");
    if (km === null) { distanceReadout.textContent = ""; return; }
    const band = distanceBand(km);
    if (band) {
      distanceReadout.innerHTML = `Straight-line distance: <strong>${km.toFixed(1)} km</strong> (${band})`;
    } else {
      distanceReadout.textContent = `Straight-line distance: ${km.toFixed(1)} km. The model only supports routes under 25 km.`;
      distanceReadout.classList.add("warn");
    }
  }

  function prepMinutes() {
    if (!$("order_time").value || !$("pickup_time").value) return null;
    return (toMinutes($("pickup_time").value) - toMinutes($("order_time").value) + 1440) % 1440;
  }

  function updatePrepHint() {
    const m = prepMinutes();
    prepHint.textContent = m === null ? "" : `${m} min after the order was placed`;
  }

  // ---------- defaults ----------
  function applySample(key) {
    SAMPLES[key].forEach((value, i) => { $(ROUTE_IDS[i]).value = value; });
    updateDistance();
  }

  function setDefaults() {
    const now = new Date();
    const nowMin = now.getHours() * 60 + now.getMinutes();
    $("order_date").value = `${now.getFullYear()}-${pad(now.getMonth() + 1)}-${pad(now.getDate())}`;
    // keep the default order out of the 00:00-00:59 hour, which the model cannot score
    const orderMin = nowMin < 60 ? 60 : nowMin;
    $("order_time").value = fromMinutes(orderMin);
    $("pickup_time").value = fromMinutes(orderMin + 10);
    applySample("mumbai");
    updatePrepHint();
  }

  // ---------- validation ----------
  function validate() {
    const errors = {};
    const age = parseFloat($("age").value);
    const rating = parseFloat($("ratings").value);

    if (!$("order_date").value) errors.order_date = "Choose a date.";
    if (!$("order_time").value) errors.order_time = "Choose a time.";
    else if (toMinutes($("order_time").value) < 60) errors.order_time = "Orders placed between 00:00 and 00:59 are not supported.";
    if (!$("pickup_time").value) errors.pickup_time = "Choose a time.";
    else if (prepMinutes() > 120) errors.pickup_time = "Pickup is more than 2 hours after the order. Check AM/PM.";

    if (!Number.isFinite(age) || age < 18 || age > 70) errors.age = "Enter an age from 18 to 70.";
    if (!Number.isFinite(rating) || rating < 1 || rating > 5) errors.ratings = "Enter a rating from 1 to 5.";

    ROUTE_IDS.forEach((id) => {
      const n = parseFloat($(id).value);
      const limit = id.endsWith("latitude") ? 90 : 180;
      if (!Number.isFinite(n)) errors[id] = "Required.";
      else if (Math.abs(n) < 1 || Math.abs(n) > limit) errors[id] = `Enter a value between 1 and ${limit}.`;
    });

    if (!Object.keys(errors).some((k) => ROUTE_IDS.includes(k))) {
      const km = routeDistance();
      if (km !== null && km >= 25) errors.delivery_latitude = "The route must be under 25 km.";
    }
    return errors;
  }

  function showErrors(errors) {
    document.querySelectorAll(".field-error").forEach((el) => {
      const message = errors[el.dataset.for] || "";
      el.textContent = message;
      const input = $(el.dataset.for);
      if (message) input.setAttribute("aria-invalid", "true");
      else input.removeAttribute("aria-invalid");
    });
  }

  // ---------- request ----------
  function buildPayload() {
    const [y, m, d] = $("order_date").value.split("-");
    return {
      ID: `web-${Date.now()}`,
      Delivery_person_ID: "WEBRES00DEL00", // only used to derive a city name that the model drops
      Delivery_person_Age: String($("age").value),
      Delivery_person_Ratings: String($("ratings").value),
      Restaurant_latitude: parseFloat($("restaurant_latitude").value),
      Restaurant_longitude: parseFloat($("restaurant_longitude").value),
      Delivery_location_latitude: parseFloat($("delivery_latitude").value),
      Delivery_location_longitude: parseFloat($("delivery_longitude").value),
      Order_Date: `${d}-${m}-${y}`,
      Time_Orderd: `${$("order_time").value}:00`,
      Time_Order_picked: `${$("pickup_time").value}:00`,
      Weatherconditions: `conditions ${$("weather").value}`,
      Road_traffic_density: $("traffic").value,
      Vehicle_condition: parseInt($("vehicle_condition").value, 10),
      Type_of_order: $("type_of_order").value,
      Type_of_vehicle: $("type_of_vehicle").value,
      multiple_deliveries: $("multiple_deliveries").value,
      Festival: form.elements.festival.value,
      City: $("city").value,
    };
  }

  function errorMessage(body) {
    if (!body || !body.detail) return "The server could not process this request.";
    if (typeof body.detail === "string") return body.detail;
    return body.detail.map((e) => `${(e.loc || []).slice(-1)[0]}: ${e.msg}`).join("; ");
  }

  // ---------- rendering ----------
  function renderLoading() {
    resultBody.className = "result-body state-loading";
    resultBody.innerHTML = '<div class="spinner" role="status" aria-label="Predicting"></div>';
  }

  function renderError(message) {
    resultBody.className = "result-body state-error";
    const box = document.createElement("div");
    box.className = "error-box";
    box.textContent = message;
    resultBody.replaceChildren(box);
  }

  function renderResult(minutes) {
    const km = routeDistance();
    const rows = [
      ["Distance", km === null ? "-" : `${km.toFixed(1)} km`],
      ["Pickup after order", `${prepMinutes()} min`],
      ["Weather / traffic", `${$("weather").value} / ${$("traffic").value}`],
      ["Vehicle", $("type_of_vehicle").selectedOptions[0].textContent],
    ];
    resultBody.className = "result-body state-success";
    resultBody.innerHTML = `
      <div class="minutes"><span class="value">${minutes.toFixed(1)}</span><span class="unit">min</span></div>
      <p class="result-sub">Predicted delivery time</p>
      <dl class="summary">${rows.map(([k, v]) => `<dt>${k}</dt><dd>${v}</dd>`).join("")}</dl>`;
  }

  // ---------- events ----------
  async function onSubmit(event) {
    event.preventDefault();
    const errors = validate();
    showErrors(errors);
    if (Object.keys(errors).length) {
      renderError("Please fix the highlighted fields.");
      return;
    }

    submitBtn.disabled = true;
    renderLoading();
    try {
      const payload = buildPayload();
      const response = await fetch("/predict", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
    //   const body = await response.json().catch(() => null);
    //   if (!response.ok) { renderError(errorMessage(body)); return; }
    //   if (typeof body !== "number" || !Number.isFinite(body)) { renderError("The server returned an unexpected response."); return; }
    //   renderResult(body);
    
    const body = await response.json().catch(() => null);

    if (!response.ok) {
        renderError(errorMessage(body));
        return;
    }

    // Support both a plain numeric response and a JSON object.
    const prediction =
        typeof body === "number" ? body : body?.prediction;

    if (
        typeof prediction !== "number" ||
        !Number.isFinite(prediction)
    ) {
        renderError("The server returned an unexpected response.");
        return;
    }

    renderResult(prediction);

    } catch (err) {
      renderError("Could not reach the server. Check that the API is running and try again.");
    } finally {
      submitBtn.disabled = false;
    }
  }

  form.addEventListener("submit", onSubmit);
  form.addEventListener("reset", () => {
    // let the browser restore the HTML defaults first, then refill the dynamic ones
    setTimeout(() => {
      showErrors({});
      setDefaults();
      resultBody.className = "result-body state-empty";
      resultBody.innerHTML = '<p class="placeholder">Fill in the details and press <strong>Predict delivery time</strong>.</p>';
    }, 0);
  });
  document.querySelectorAll("[data-sample]").forEach((btn) =>
    btn.addEventListener("click", () => applySample(btn.dataset.sample)));
  ROUTE_IDS.forEach((id) => $(id).addEventListener("input", updateDistance));
  ["order_time", "pickup_time"].forEach((id) => $(id).addEventListener("input", updatePrepHint));

  setDefaults();
})();