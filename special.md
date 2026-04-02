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
<div class="special-event">
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
    <div class="event-description">{{ event.description }}</div>
  </div>
</div>
{% endfor %}
