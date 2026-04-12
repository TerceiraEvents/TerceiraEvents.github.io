---
layout: default
title: Special Events - Terceira Events
---

{% assign now_ts = "now" | date: "%s" | plus: 0 %}
{% assign sorted_events = site.data.special_events | sort: "date" %}
{% assign end_of_week_ts = now_ts | plus: 604800 %}

{% assign has_this_week = false %}

{% for event in sorted_events %}
  {% assign event_ts = event.date | date: "%s" | plus: 0 %}
  {% if event_ts >= now_ts and event_ts <= end_of_week_ts %}
    {% assign has_this_week = true %}
  {% endif %}
{% endfor %}

<div class="section">

<h2>This Week's Special Events</h2>

{% if has_this_week %}
<p class="section-intro">What's happening this week in Angra do Heroísmo.</p>

{% for event in sorted_events %}
  {% assign event_ts = event.date | date: "%s" | plus: 0 %}
  {% if event_ts >= now_ts and event_ts <= end_of_week_ts %}
    {% include special_event_card.html event=event %}
  {% endif %}
{% endfor %}

{% else %}
<p class="section-intro">No special events this week. Check the full calendar for what's coming up!</p>
{% endif %}

</div>

<div class="homepage-buttons" style="margin-top: 2rem;">
  <a href="{{ '/calendar' | relative_url }}" class="homepage-btn btn-special">
    <span class="btn-icon">&#128197;</span>
    <span class="btn-title">Full Events Calendar</span>
    <span class="btn-desc">All upcoming concerts, festivals, parties, and special events</span>
  </a>
  <a href="{{ '/archive' | relative_url }}" class="homepage-btn btn-venues">
    <span class="btn-icon">&#128218;</span>
    <span class="btn-title">Event Archive</span>
    <span class="btn-desc">Browse past events and what you might have missed</span>
  </a>
</div>
