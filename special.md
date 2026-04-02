---
layout: default
title: Special Events - Angra Events
---

{% assign now_ts = "now" | date: "%s" | plus: 0 %}
{% assign sorted_events = site.data.special_events | sort: "date" %}
{% assign end_of_week_ts = now_ts | plus: 345600 %}

{% assign has_this_week = false %}
{% assign has_upcoming = false %}

{% for event in sorted_events %}
  {% assign event_ts = event.date | date: "%s" | plus: 0 %}
  {% if event_ts >= now_ts and event_ts <= end_of_week_ts %}
    {% assign has_this_week = true %}
  {% elsif event_ts > end_of_week_ts %}
    {% assign has_upcoming = true %}
  {% endif %}
{% endfor %}

{% if has_this_week %}
<div class="section">

<h2>This Week's Special Events</h2>

<p class="section-intro">What's happening this week in Angra do Heroísmo.</p>

{% for event in sorted_events %}
  {% assign event_ts = event.date | date: "%s" | plus: 0 %}
  {% if event_ts >= now_ts and event_ts <= end_of_week_ts %}
    {% include special_event_card.html event=event %}
  {% endif %}
{% endfor %}

</div>
{% endif %}

{% if has_upcoming %}
<div class="section">

<h2>Full Special Events Calendar</h2>

<p class="section-intro">Concerts, festivals, parties, and one-off events coming up in Angra do Heroísmo.</p>

{% for event in sorted_events %}
  {% assign event_ts = event.date | date: "%s" | plus: 0 %}
  {% if event_ts > end_of_week_ts %}
    {% include special_event_card.html event=event %}
  {% endif %}
{% endfor %}

</div>
{% endif %}

<div class="archive-link-section">
  <a href="{{ '/archive' | relative_url }}" class="view-all">View Event Archive</a>
</div>
