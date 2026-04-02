---
layout: default
title: Weekly Events - Angra Events
---

## Weekly Events

<p class="section-intro">These events happen every week at venues around Angra do Heroísmo. Check with venues for holiday schedules and changes.</p>

{% for day in site.data.weekly %}
<div class="day-section">
  <div class="day-header">{{ day.day }}</div>
  <div class="day-events">
    {% for event in day.events %}
    <div class="event-card">
      <div class="event-info">
        <div class="event-name">{{ event.name }}</div>
        <div class="event-venue">{{ event.venue }}</div>
        <div class="event-description">{{ event.description }}</div>
        {% if event.address %}
        <div class="event-address">{{ event.address }}</div>
        {% endif %}
        {% if event.reservations %}
        <div class="event-reservations"><a href="{{ event.reservations }}">Make a reservation</a></div>
        {% endif %}
      </div>
      <div class="event-time">{{ event.time }}</div>
    </div>
    {% endfor %}
  </div>
</div>
{% endfor %}
