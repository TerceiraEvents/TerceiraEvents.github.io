---
layout: default
title: Special Events - Angra Events
---

## Special Events

<p class="section-intro">One-off concerts, parties, festivals, and special nights in Angra do Heroísmo.</p>

{% assign now_ts = "now" | date: "%s" | plus: 0 %}
{% assign today_date = "now" | date: "%Y-%m-%d" %}
{% assign sorted_events = site.data.special_events | sort: "date" %}

{% comment %}
  Calculate end of this week (Sunday).
  Jekyll/Liquid doesn't have great date arithmetic, so we use a 7-day window
  from today as "this week". We compare using epoch seconds.
  We add 6 days worth of seconds to cover through Sunday Apr 5 from Thu Apr 2.
  86400 seconds/day * 4 days = 345600 (Thu->Sun = 3 remaining days + today = 4 days window)
{% endcomment %}
{% assign end_of_week_ts = now_ts | plus: 345600 %}

{% comment %} Collect this week's events and upcoming events {% endcomment %}
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

### This Week

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

### Upcoming Events

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
