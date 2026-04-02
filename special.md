---
layout: default
title: Special Events - Angra Events
---

## Special Events

<p class="section-intro">One-off concerts, parties, festivals, and special nights in Angra do Heroísmo.</p>

{% assign sorted_events = site.data.special_events | sort: "date" | reverse %}
{% for event in sorted_events %}
{% assign date_parts = event.date | split: "-" %}
{% assign months = "Jan,Feb,Mar,Apr,May,Jun,Jul,Aug,Sep,Oct,Nov,Dec" | split: "," %}
{% assign month_index = date_parts[1] | plus: 0 | minus: 1 %}
<div class="special-event {% if event.image %}has-image{% endif %}">
  <div class="event-date-badge">
    <div class="month">{{ months[month_index] }}</div>
    <div class="day">{{ date_parts[2] | plus: 0 }}</div>
    <div class="year">{{ date_parts[0] }}</div>
  </div>
  <div class="event-details">
    <div class="event-name">{{ event.name }}</div>
    <div class="event-venue">{{ event.venue }}</div>
    {% if event.address %}
    <div class="event-address">{{ event.address }}</div>
    {% endif %}
    {% if event.time %}
    <div class="event-time-info">Doors: {{ event.time }}</div>
    {% endif %}
    <div class="event-description">{{ event.description }}</div>
    {% if event.organizer %}
    <div class="event-organizer">Organized by: {{ event.organizer }}</div>
    {% endif %}
    {% if event.features %}
    <ul class="event-features">
      {% for feature in event.features %}
      <li>{{ feature }}</li>
      {% endfor %}
    </ul>
    {% endif %}
  </div>
  {% if event.image %}
  <div class="event-image">
    <img src="{{ event.image | relative_url }}" alt="{{ event.name }} flyer" data-lightbox>
  </div>
  {% endif %}
</div>
{% endfor %}
