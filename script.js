// === Backend base URL ===
const API_BASE = "https://medical8.onrender.com";

// === Screen navigation ===
const screens = document.querySelectorAll(".screen");

function showScreen(id) {
  screens.forEach((s) => s.classList.remove("active"));

  const target = document.getElementById(id);
  if (target) target.classList.add("active");

  // bottom nav active state
  document.querySelectorAll(".nav-item").forEach((item) => {
    item.classList.toggle("active", item.dataset.target === id);
  });
}

function navTo(el) {
  const target = el.dataset.target;
  showScreen(target);
}

// === Splash auto navigation ===
setTimeout(() => {
  showScreen("onboarding");
}, 2000);

// === Onboarding logic ===
let currentSlide = 0;
const slides = document.querySelectorAll(".onboarding-slide");
const dots = document.querySelectorAll(".dot");

function updateOnboarding() {
  slides.forEach((slide, idx) => {
    slide.classList.toggle("active", idx === currentSlide);

    if (dots[idx]) {
      dots[idx].classList.toggle(
        "active",
        idx === currentSlide
      );
    }
  });

  const nextBtn =
    document.getElementById("nextSlideBtn");

  if (nextBtn) {
    nextBtn.textContent =
      currentSlide === slides.length - 1
        ? "Skip"
        : "Next";
  }
}

document
  .getElementById("nextSlideBtn")
  ?.addEventListener("click", () => {
    currentSlide =
      (currentSlide + 1) % slides.length;
    updateOnboarding();
  });

document
  .getElementById("getStartedBtn")
  ?.addEventListener("click", () => {
    showScreen("auth");
  });

// === AUTH LOGIN ===
document
  .getElementById("authForm")
  ?.addEventListener("submit", async (e) => {
    e.preventDefault();

    const phone = document
      .getElementById("phone")
      .value.trim();

    const otp = document
      .getElementById("otp")
      .value.trim();

    if (!phone || !otp) {
      alert(
        "Please enter mobile number and OTP."
      );
      return;
    }

    try {
      const res = await fetch(
        `${API_BASE}/api/login`,
        {
          method: "POST",
          headers: {
            "Content-Type":
              "application/json",
          },
          body: JSON.stringify({
            phone,
            otp,
          }),
        }
      );

      const data = await res.json();

      if (!res.ok) {
        alert(
          data.error || "Login failed"
        );
        return;
      }

      localStorage.setItem(
        "user_phone",
        data.user.phone || phone
      );

      alert("Login successful!");
      showScreen("home");
    } catch (err) {
      console.error(err);
      alert(
        "Network error while logging in."
      );
    }
  });

// === Emergency Symptom chips ===
document
  .querySelectorAll(
    "#emergencySymptomList .symptom-chip"
  )
  .forEach((chip) => {
    chip.addEventListener("click", () => {
      chip.classList.toggle("active");

      const input =
        document.getElementById(
          "emergencyDescribe"
        );

      const active = Array.from(
        document.querySelectorAll(
          "#emergencySymptomList .symptom-chip.active"
        )
      ).map((c) =>
        c.textContent.trim()
      );

      if (input) {
        input.value = active.join(", ");
      }
    });
  });

function nearestDoctor() {
  alert(
    "Connecting you to nearest emergency doctor..."
  );
}

// === Symptom Checker ===
async function runSymptomChecker(
  inputId,
  resultId
) {
  const text = document
    .getElementById(inputId)
    ?.value.toLowerCase();

  const box =
    document.getElementById(resultId);

  if (!text?.trim()) {
    box.classList.remove("hide");
    box.innerHTML =
      "Please describe at least one symptom.";
    return;
  }

  try {
    const res = await fetch(
      `${API_BASE}/api/symptom-checker`,
      {
        method: "POST",
        headers: {
          "Content-Type":
            "application/json",
        },
        body: JSON.stringify({
          description: text,
        }),
      }
    );

    const data = await res.json();

    box.classList.remove("hide");

    if (!res.ok) {
      box.innerHTML =
        data.error ||
        "Error checking symptoms.";
      return;
    }

    box.innerHTML = `
      <div><strong>Possible problem:</strong> ${data.possible_problem}</div>
      <div><strong>Severity:</strong> ${data.severity.toUpperCase()}</div>
      <div><strong>Urgency:</strong> ${data.urgency.toUpperCase()}</div>
      <div><strong>Recommendation:</strong> ${data.recommendation}</div>
    `;
  } catch (err) {
    console.error(err);
    box.classList.remove("hide");
    box.innerHTML =
      "Network error while checking symptoms.";
  }
}

// === Voice demo ===
function simulateVoiceInput() {
  const input =
    document.getElementById(
      "symptomInput"
    );

  input.value =
    "chest pain + sweating + shortness of breath";

  runSymptomChecker(
    "symptomInput",
    "symptomResult"
  );
}

// === Ambulance Booking ===
async function bookAmbulance() {
  const inputs =
    document.querySelectorAll(
      '#ambulance .field input[type="text"]'
    );

  const pickup =
    inputs[0]?.value.trim();

  const destination =
    inputs[1]?.value.trim();

  const phone =
    localStorage.getItem(
      "user_phone"
    ) || "";

  if (!pickup) {
    alert(
      "Please enter pickup location."
    );
    return;
  }

  try {
    const res = await fetch(
      `${API_BASE}/api/ambulance/book`,
      {
        method: "POST",
        headers: {
          "Content-Type":
            "application/json",
        },
        body: JSON.stringify({
          phone,
          pickup_location:
            pickup,
          destination,
        }),
      }
    );

    const data = await res.json();

    if (!res.ok) {
      alert(
        data.error ||
          "Failed to book ambulance"
      );
      return;
    }

    alert(
      `Ambulance booked! ETA: ${data.eta_minutes} min`
    );

    const etaLabel =
      document.getElementById(
        "etaLabel"
      );

    if (etaLabel) {
      etaLabel.textContent = `ETA: ${data.eta_minutes} min`;
    }
  } catch (err) {
    console.error(err);
    alert(
      "Network error while booking ambulance."
    );
  }
}

// === Blood Availability ===
async function checkBloodAvailability() {
  const group =
    document.getElementById(
      "bloodGroup"
    ).value;

  const box =
    document.getElementById(
      "bloodResult"
    );

  try {
    const res = await fetch(
      `${API_BASE}/api/blood/check`,
      {
        method: "POST",
        headers: {
          "Content-Type":
            "application/json",
        },
        body: JSON.stringify({
          blood_group:
            group,
        }),
      }
    );

    const data = await res.json();

    box.classList.remove("hide");

    if (!res.ok) {
      box.innerHTML =
        data.error ||
        "Error checking blood availability";
      return;
    }

    if (
      !data.banks ||
      data.banks.length === 0
    ) {
      box.innerHTML = `
        <div>No blood found for ${data.blood_group}</div>
      `;
      return;
    }

    const listHtml =
      data.banks
        .map(
          (b) => `
      <div>
        ${b.name} —
        ${b.units_available} units
        (${b.distance_km} km)
      </div>
    `
        )
        .join("");

    box.innerHTML = `
      <div><strong>Blood group:</strong> ${data.blood_group}</div>
      <div>${listHtml}</div>
    `;
  } catch (err) {
    console.error(err);
    box.classList.remove("hide");
    box.innerHTML =
      "Network error while checking blood availability.";
  }
}

// === Dark Mode ===
function toggleDarkMode() {
  const toggle =
    document.getElementById(
      "darkToggle"
    );

  toggle?.classList.toggle("on");

  document.body.classList.toggle(
    "dark-theme"
  );
}

// === SOS ===
function triggerSOS() {
  alert(
    "SOS Activated!\n\n" +
      "- Ambulance booking initiated\n" +
      "- Family notified\n" +
      "- Hospital alerted"
  );

  showScreen("emergency");
}
