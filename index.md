---
layout: default
title: Angra Events - What's Happening in Angra do Heroísmo
---

<div class="section">

## Weekly Events

<p class="section-intro">Recurring events happening every week around Angra do Heroísmo.</p>

{% for day in site.data.weekly %}
<div class="day-section">
  <div class="day-header">{{ day.day }}</div>
  <div class="day-events">
    {% for event in day.events %}
    <div class="event-card">
      <div class="event-name">{{ event.name }}</div>
      <div class="event-venue">{{ event.venue }}</div>
      <div class="event-time">{{ event.time }}</div>
      <div class="event-description">{{ event.description }}</div>
    </div>
    {% endfor %}
  </div>
</div>
{% endfor %}

</div>

<div class="section">

## Special Events

<p class="section-intro">One-off concerts, parties, and special nights.</p>

{% assign sorted_events = site.data.special_events | sort: "date" | reverse %}
{% for event in sorted_events limit: 5 %}
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
    <div class="event-description">{{ event.description }}</div>
  </div>
</div>
{% endfor %}

<p><a href="{{ '/special' | relative_url }}">View all special events &rarr;</a></p>

</div>
