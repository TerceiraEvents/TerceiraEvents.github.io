---
layout: default
title: "Suggest an Event - Terceira Events"
---

<h2>Suggest an Event</h2>

<p class="section-intro">Got an event you think should be on here? Fill out the form below. We'll review it and add it to the site &mdash; usually within a day or two.</p>

<form id="suggest-form" class="suggest-form">
  <div class="form-field">
    <label for="name">Event Name <span class="required">*</span></label>
    <input type="text" id="name" name="name" required maxlength="200" placeholder="e.g. Concert at Teatro Angrense">
  </div>

  <div class="form-field">
    <label for="date">Date <span class="required">*</span></label>
    <input type="date" id="date" name="date" required>
  </div>

  <div class="form-field">
    <label for="time">Time</label>
    <input type="time" id="time" name="time" placeholder="e.g. 21:30">
    <small>Optional &mdash; leave blank if unknown</small>
  </div>

  <div class="form-field">
    <label for="venue">Venue <span class="required">*</span></label>
    <input type="text" id="venue" name="venue" required maxlength="200" placeholder="e.g. Teatro Angrense">
  </div>

  <div class="form-field">
    <label for="address">Address</label>
    <input type="text" id="address" name="address" maxlength="300" placeholder="e.g. Rua da Esperança 48-52, Angra do Heroísmo">
  </div>

  <div class="form-field">
    <label for="description">Description</label>
    <textarea id="description" name="description" rows="4" maxlength="2000" placeholder="What's the event about? Ticket info, guests, anything else people should know."></textarea>
  </div>

  <div class="form-field">
    <label for="instagram">Instagram Link</label>
    <input type="url" id="instagram" name="instagram" maxlength="500" placeholder="https://www.instagram.com/p/...">
    <small>Link to an Instagram post or account with event details</small>
  </div>

  <div class="form-field">
    <label for="image">Flyer / Poster Image URL</label>
    <input type="url" id="image" name="image" maxlength="500" placeholder="https://...">
    <small>Link to a flyer or poster image (e.g. from Instagram or any public URL). Please include whenever possible!</small>
  </div>

  <div class="form-field form-checkbox">
    <label for="kid_friendly">
      <input type="checkbox" id="kid_friendly" name="kid_friendly" value="true">
      <span>👶 Kid Friendly &mdash; suitable for children/families</span>
    </label>
    <small>Check this if the event is appropriate for kids (family screenings, parades, daytime shows, etc.)</small>
  </div>

  <div class="form-field">
    <label for="submitterName">Your Name</label>
    <input type="text" id="submitterName" name="submitterName" maxlength="100" placeholder="Optional &mdash; for credit">
  </div>

  <!-- Honeypot field: hidden from users, bots fill it in -->
  <div style="position:absolute; left:-9999px; opacity:0; pointer-events:none;" aria-hidden="true">
    <label for="website">Website (leave blank)</label>
    <input type="text" id="website" name="website" tabindex="-1" autocomplete="off">
  </div>

  <button type="submit" id="submit-btn" class="form-submit">Submit Event</button>

  <div id="form-message" class="form-message" style="display:none;"></div>
</form>

<div class="venue-card" style="margin-top:2rem;">
  <div class="venue-regulars">
    <p><strong>Other ways to suggest events:</strong></p>
    <ul>
      <li>Open the <strong>Terceira Events</strong> mobile app and tap "Suggest Event"</li>
      <li>Submit a pull request on <a href="https://github.com/TerceiraEvents/Angraevents.github.io">GitHub</a> if you're technical</li>
      <li>DM <a href="https://www.instagram.com/chrisrackauckas/">@chrisrackauckas</a> on Instagram</li>
    </ul>
  </div>
</div>

<style>
.suggest-form {
  max-width: 640px;
  margin: 1.5rem 0 2rem;
}
.form-field {
  margin-bottom: 1.25rem;
}
.form-field label {
  display: block;
  font-weight: 600;
  color: var(--primary, #2d5016);
  margin-bottom: 0.4rem;
  font-size: 0.95rem;
}
.form-field .required {
  color: #c0392b;
}
.form-field input,
.form-field textarea {
  width: 100%;
  padding: 0.65rem 0.85rem;
  border: 1px solid #d8d4c4;
  border-radius: 6px;
  font-family: inherit;
  font-size: 1rem;
  background: #fff;
  box-sizing: border-box;
  color: #2c2c2c;
}
.form-field input:focus,
.form-field textarea:focus {
  outline: none;
  border-color: var(--primary, #2d5016);
  box-shadow: 0 0 0 3px rgba(45, 80, 22, 0.1);
}
.form-field textarea {
  resize: vertical;
  min-height: 90px;
}
.form-field.form-checkbox label {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  cursor: pointer;
  font-weight: 600;
}
.form-field.form-checkbox input[type="checkbox"] {
  width: auto;
  margin: 0;
  accent-color: #f5a623;
  transform: scale(1.2);
}
.form-field small {
  display: block;
  margin-top: 0.3rem;
  color: #777;
  font-size: 0.85rem;
}
.form-submit {
  background: var(--primary, #2d5016);
  color: #fff;
  border: none;
  padding: 0.85rem 1.75rem;
  border-radius: 6px;
  font-family: inherit;
  font-size: 1rem;
  font-weight: 700;
  cursor: pointer;
  transition: background 0.15s;
}
.form-submit:hover:not(:disabled) {
  background: #1a3009;
}
.form-submit:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}
.form-message {
  margin-top: 1rem;
  padding: 0.85rem 1rem;
  border-radius: 6px;
  font-size: 0.95rem;
}
.form-message.success {
  background: #e8f5e0;
  border-left: 3px solid var(--primary, #2d5016);
  color: #1a3009;
}
.form-message.error {
  background: #fbeaea;
  border-left: 3px solid #c0392b;
  color: #8a1e1e;
}
</style>

<script>
(function() {
  var SUBMIT_URL = 'https://event-submit-worker.terceriaevents.workers.dev/submit-event';
  var form = document.getElementById('suggest-form');
  var btn = document.getElementById('submit-btn');
  var msgBox = document.getElementById('form-message');

  function showMessage(text, type) {
    msgBox.textContent = text;
    msgBox.className = 'form-message ' + type;
    msgBox.style.display = 'block';
  }

  form.addEventListener('submit', async function(e) {
    e.preventDefault();
    msgBox.style.display = 'none';

    var data = {};
    new FormData(form).forEach(function(value, key) {
      var trimmed = String(value).trim();
      if (trimmed) data[key] = trimmed;
    });

    // Honeypot check — silently pretend success to not tip off bots
    if (data.website) {
      showMessage('Thank you! Your event has been submitted for review.', 'success');
      form.reset();
      return;
    }

    // Client-side required-field check
    if (!data.name || !data.date || !data.venue) {
      showMessage('Please fill in event name, date, and venue.', 'error');
      return;
    }

    btn.disabled = true;
    btn.textContent = 'Submitting...';

    try {
      var response = await fetch(SUBMIT_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
      });
      var result = await response.json().catch(function() { return {}; });

      if (response.ok && result.success) {
        showMessage('Thank you! Your event has been submitted for review.', 'success');
        form.reset();
      } else {
        var errMsg = result.error || 'Something went wrong. Please try again later.';
        showMessage(errMsg, 'error');
      }
    } catch (err) {
      showMessage('Network error. Please check your connection and try again.', 'error');
    } finally {
      btn.disabled = false;
      btn.textContent = 'Submit Event';
    }
  });
})();
</script>
