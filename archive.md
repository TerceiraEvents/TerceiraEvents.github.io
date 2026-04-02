---
layout: default
title: Event Archive - Angra Events
---

<h2>Event Archive</h2>

<p class="section-intro">Past concerts, parties, festivals, and special nights in Angra do Heroísmo.</p>

{% assign now_ts = "now" | date: "%s" | plus: 0 %}
{% assign one_month_ago_ts = now_ts | minus: 2592000 %}
{% assign sorted_events = site.data.special_events | sort: "date" | reverse %}

{% assign has_recent = false %}
{% assign has_older = false %}

{% for event in sorted_events %}
  {% assign event_ts = event.date | date: "%s" | plus: 0 %}
  {% if event_ts < now_ts and event_ts >= one_month_ago_ts %}
    {% assign has_recent = true %}
  {% elsif event_ts < one_month_ago_ts %}
    {% assign has_older = true %}
  {% endif %}
{% endfor %}

{% if has_recent %}
<div class="section">

<h3>Recent Events</h3>

{% for event in sorted_events %}
  {% assign event_ts = event.date | date: "%s" | plus: 0 %}
  {% if event_ts < now_ts and event_ts >= one_month_ago_ts %}
    {% include special_event_card.html event=event %}
  {% endif %}
{% endfor %}

</div>
{% endif %}

{% if has_older %}
<div class="section">

<h3>Older Events</h3>

<table class="archive-table">
  <thead>
    <tr>
      <th>Date</th>
      <th>Event</th>
      <th>Venue</th>
    </tr>
  </thead>
  <tbody>
    {% for event in sorted_events %}
      {% assign event_ts = event.date | date: "%s" | plus: 0 %}
      {% if event_ts < one_month_ago_ts %}
    <tr>
      <td class="archive-date">{{ event.date | date: "%b %d, %Y" }}</td>
      <td class="archive-name">{{ event.name }}{% if event.festival %} <span class="archive-festival">{{ event.festival }}</span>{% endif %}</td>
      <td class="archive-venue">{{ event.venue }}</td>
    </tr>
      {% endif %}
    {% endfor %}
  </tbody>
</table>

</div>
{% endif %}

<div class="archive-link-section">
  <a href="{{ '/special' | relative_url }}" class="view-all">Back to Special Events</a>
</div>
