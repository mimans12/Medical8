// === Backend base URL ===
const API_BASE = "http://localhost:8000";

// === Screen navigation ===
const screens = document.querySelectorAll('.screen');  

function showScreen(id) {
  screens.forEach(s => s.classList.remove('active'));
  const target = document.getElementById(id);
  if (target) target.classList.add('active');

  // bottom nav active state
  document.querySelectorAll('.nav-item').forEach(item => {
    item.classList.toggle('active', item.dataset.target === id);
  });
}

function navTo(el) {
  const target = el.dataset.target;
  showScreen(target);
}

// === Splash auto navigation ===
setTimeout(() => {
  showScreen('onboarding');
}, 2000);

// === Onboarding logic ===
let currentSlide = 0;
const slides = document.querySelectorAll('.onboarding-slide');
const dots = document.querySelectorAll('.dot');

function updateOnboarding() {    
  slides.forEach((slide, idx) => {
    slide.classList.toggle('active', idx === currentSlide);
    dots[idx].classList.toggle('active', idx === currentSlide);
  });
  const nextBtn = document.getElementById('nextSlideBtn');
  nextBtn.textContent = currentSlide === slides.length - 1 ? 'Skip' : 'Next';
}

document.getElementById('nextSlideBtn').addEventListener('click', () => {
  currentSlide = (currentSlide + 1) % slides.length;
  updateOnboarding();
});

document.getElementById('getStartedBtn').addEventListener('click', () => {
  showScreen('auth');
});

// === AUTH: login/signup with backend ===
document.getElementById('authForm').addEventListener('submit', async e => {
  e.preventDefault();
  const phone = document.getElementById('phone').value.trim();
  const otp = document.getElementById('otp').value.trim();

  if (!phone || !otp) {
    alert('Please enter mobile number & OTP.');
    return;
  }

  try {
    const res = await fetch(`${API_BASE}/api/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ phone, otp })
    });

    const data = await res.json();

    if (!res.ok) {
      alert(data.error || "Login failed");
      return;
    }

    // user info ko store kar lo (ambulance booking me kaam aayega)
    localStorage.setItem("user_phone", data.user.phone || phone);

    showScreen('home');
  } catch (err) {
    console.error(err);
    alert("Network error while logging in.");
  }
});

// === Emergency Symptom chips ===
document.querySelectorAll('#emergencySymptomList .symptom-chip').forEach(chip => {
  chip.addEventListener('click', () => {
    chip.classList.toggle('active');
    const input = document.getElementById('emergencyDescribe');
    const active = Array.from(document.querySelectorAll('#emergencySymptomList .symptom-chip.active'))
      .map(c => c.textContent.trim());
    input.value = active.join(', ');
  });
});
                                                                             
function nearestDoctor() {
  alert('Connecting you to nearest emergency doctor (demo)…');
}

// === AI Symptom Checker (backend) ===
async function runSymptomChecker(inputId, resultId) {
  const text = document.getElementById(inputId).value.toLowerCase();
  const box = document.getElementById(resultId);

  if (!text.trim()) { 
    box.classList.remove('hide');
    box.innerHTML = 'Please describe at least one symptom.';
    return;
  }

  try {
    const res = await fetch(`${API_BASE}/api/symptom-checker`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ description: text })
    });

    const data = await res.json();

    if (!res.ok) {
      box.classList.remove('hide');
      box.innerHTML = data.error || "Error while checking symptoms.";
      return;
    }

    box.classList.remove('hide');
    box.innerHTML = `
      <div><strong>Possible problem:</strong> ${data.possible_problem}</div>
      <div><strong>Severity:</strong> ${data.severity.toUpperCase()}</div>
      <div><strong>Urgency:</strong> ${data.urgency.toUpperCase()}</div>
      <div style="margin-top:4px;"><strong>Recommended action:</strong> ${data.recommendation}</div>
      <div style="margin-top:4px;">If in doubt, treat as emergency & use SOS / ambulance booking.</div>
    `;
  } catch (err) {
    console.error(err);
    box.classList.remove('hide');
    box.innerHTML = "Network error while checking symptoms.";
  }
}

function simulateVoiceInput() {
  const input = document.getElementById('symptomInput');
  input.value = 'chest pain + sweating + shortness of breath';
  runSymptomChecker('symptomInput', 'symptomResult');
}

// === Night doctors filter (still frontend demo) ===
function filterDoctors() {
  const value = document.getElementById('specialityFilter').value;
  document.querySelectorAll('#nightDoctorList .doc-card').forEach(card => {
    const spec = card.dataset.spec;
    card.style.display = (value === 'all' || spec === value) ? 'block' : 'none';
  });
}

// === Doctor profile navigation ===
function openDoctorProfile(name) {
  const nameEl = document.getElementById('docFullName');
  const initialsEl = document.getElementById('docInitials');
  const profileNameEl = document.getElementById('docProfileName');

  nameEl.textContent = name;
  profileNameEl.textContent = name;
  const initials = name.split(' ')
    .filter(Boolean)
    .map(n => n[0].toUpperCase())
    .join('');
  initialsEl.textContent = initials.slice(0,2);

  showScreen('doctorProfile');
}

function goToBookingSummary() {
  const docName = document.getElementById('docFullName').textContent;
  const slot = document.querySelector('#slotRow .radio-chip.active')?.textContent || 'Within 15 min';
  const mode = document.querySelector('#modeRow .radio-chip.active')?.textContent || 'Video';
  const info = document.getElementById('summaryInfo');
  info.innerHTML = `
    <div class="small-label">Doctor</div>
    <div class="doc-name">${docName}</div>
    <div class="doc-meta">Night emergency specialist</div>
    <div class="small-label" style="margin-top:8px;">Appointment</div>
    <div class="doc-meta">Slot: ${slot}</div>
    <div class="doc-meta">Mode: ${mode}</div>
    <div class="small-label" style="margin-top:8px;">Charges</div>
    <div class="doc-meta">Consultation: ₹ 599</div>
    <div class="doc-meta">Night emergency fee: ₹ 100</div>
    <div class="doc-meta">Total: <strong>₹ 699</strong></div>
  `;
  showScreen('bookingSummary');
}

// === Radio chips selection (mode/slot/payment) ===
document.querySelectorAll('.radio-row').forEach(row => {
  row.addEventListener('click', e => {
    const chip = e.target.closest('.radio-chip');
    if (!chip) return;
    row.querySelectorAll('.radio-chip').forEach(c => c.classList.remove('active'));
    chip.classList.add('active');
  });
});

// === Payment ===
function completePayment() {
  alert('Payment successful! Your consultation is confirmed (demo).');
  showScreen('home');
}

// === Ambulance animation on home & ambulance screen ===
let progress = 0;
function animateAmbulance() {
  const ambHome = document.getElementById('homeAmbulance');
  const amb = document.getElementById('ambAmbulance');
  if (!ambHome || !amb) return;
  progress = (progress + 1) % 100;
  const x = 8 + progress * 0.6;
  ambHome.style.left = x + '%';
  amb.style.left = (10 + progress * 0.6) + '%';
}
setInterval(animateAmbulance, 200);                 

// === Ambulance booking (backend) ===
async function bookAmbulance() {
  const inputs = document.querySelectorAll('#ambulance .field input[type="text"]');
  const pickup = inputs[0].value.trim();
  const destination = inputs[1].value.trim();
  const phone = localStorage.getItem("user_phone") || "";

  if (!pickup) {
    alert("Please enter pickup location.");
    return;
  }

  try {
    const res = await fetch(`${API_BASE}/api/ambulance/book`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        phone,
        pickup_location: pickup,
        destination
      })
    });

    const data = await res.json();

    if (!res.ok) {
      alert(data.error || "Failed to book ambulance");
      return;
    }

    alert(`Ambulance booked! Booking ID: ${data.booking_id}, ETA: ${data.eta_minutes} min (demo)`);

    const etaLabel = document.getElementById('etaLabel');
    if (etaLabel) {
      etaLabel.textContent = `ETA: ${data.eta_minutes} min (en route)`;
    }
  } catch (err) {
    console.error(err);
    alert("Network error while booking ambulance.");
  }
}

// === Blood availability (backend) ===
async function checkBloodAvailability() {
  const group = document.getElementById('bloodGroup').value;
  const box = document.getElementById('bloodResult');

  try {
    const res = await fetch(`${API_BASE}/api/blood/check`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ blood_group: group })
    });

    const data = await res.json();

    if (!res.ok) {
      box.classList.remove('hide');
      box.innerHTML = data.error || "Error checking blood availability";
      return; 
    }                           

    box.classList.remove('hide');         
   

    if (!data.banks || data.banks.length === 0) {
      box.innerHTML = `
        <div>No blood found for group ${data.blood_group} in nearby banks (demo).</div>
        <div>You may raise an emergency request.</div>
      `;
      return;
    }          

    const listHtml = data.banks.map(b => `  
      <div>${b.name} – units: ${b.units_available} (${b.distance_km} km)</div>
    `).join("");

    box.innerHTML = `
      <div><strong>Blood group:</strong> ${data.blood_group}</div>
      <div><strong>Nearby blood banks:</strong></div>
      ${listHtml}
    `;
  } catch (err) {  
    console.error(err);
    box.classList.remove('hide');
    box.innerHTML = "Network error while checking blood availability.";
  }
}  

// === Video consult (demo only) ===
function simulateVideoConnect() {
  const box = document.getElementById('videoStatus');
  box.innerHTML = `
    <div><strong>Doctor found:</strong> Dr. Online Emergency</div>
    <div>Connecting secure video call in &lt; 30 seconds…</div>
    <div style="margin-top:4px;">Please keep your reports & medications nearby.</div>
  `;
}

// === Dark mode toggle ===  
function toggleDarkMode() {
  const toggle = document.getElementById('darkToggle');
  toggle.classList.toggle('on');
  document.body.classList.toggle('dark-theme');
}

// === SOS ===
function triggerSOS() {
  alert(
    'SOS activated! (demo)\n\n' +
    '- Auto-booking nearest ambulance\n' +
    '- Live location shared with family\n' +
    '- Nearest hospital alerted\n' +
    '- Dialling 112 / local emergency'
  );
  showScreen('emergency');
}