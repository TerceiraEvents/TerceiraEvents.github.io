---
layout: default
title: Weekly Events - Terceira Events
---

## Weekly Events

<p class="section-intro">These events happen every week at venues around Angra do Heroísmo. Check with venues for holiday schedules and changes.</p>

{% for day in site.data.weekly %}
<div class="day-section">
  <div class="day-header">{{ day.day }}</div>
  <div class="day-events">
    {% for event in day.events %}
    {%- comment -%}
      Build a Google Maps link, falling back map_url > address > venue.
      Same logic as `_includes/special_event_card.html` so weekly and
      special events present location identically.
    {%- endcomment -%}
    {% assign map_link = "" %}
    {% if event.map_url %}
      {% assign map_link = event.map_url %}
    {% elsif event.address %}
      {% assign map_query = event.address | url_encode %}
      {% assign map_link = "https://www.google.com/maps/search/?api=1&query=" | append: map_query %}
    {% elsif event.venue %}
      {% assign map_query = event.venue | url_encode %}
      {% assign map_link = "https://www.google.com/maps/search/?api=1&query=" | append: map_query %}
    {% endif %}
    <div class="event-card">
      <div class="event-info">
        <div class="event-name">{{ event.name }}</div>
        <div class="event-venue">{{ event.venue }}</div>
        <div class="event-description">{{ event.description }}</div>
        {% if event.note %}
        <div class="event-note">{{ event.note }}</div>
        {% endif %}
        {% if event.address %}
        <div class="event-address">{{ event.address }}</div>
        {% endif %}
        {% if map_link != "" %}
        <a class="event-map-link" href="{{ map_link }}" target="_blank" rel="noopener">📍 Open in Maps</a>
        {% endif %}
        {% if event.instagram %}
        <a class="event-source" href="{{ event.instagram }}" target="_blank" rel="noopener">📸 View on Instagram</a>
        {% endif %}
        {% if event.url %}
        <a class="event-source" href="{{ event.url }}" target="_blank" rel="noopener">🌐 Website</a>
        {% endif %}
        <button type="button" class="event-flag-btn"
          data-event-name="{{ event.name | escape }}"
          data-event-date="{{ day.day }} (weekly)"
          data-event-venue="{{ event.venue | escape }}">
          🚩 Suggest an edit
        </button>
      </div>
      <div class="event-time">{{ event.time }}</div>
    </div>
    {% endfor %}
  </div>
</div>
{% endfor %}
