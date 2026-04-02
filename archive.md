---
layout: default
title: Event Archive - Angra Events
---

## Event Archive

<p class="section-intro">Past concerts, parties, festivals, and special nights in Angra do Heroísmo.</p>

{% assign now_ts = "now" | date: "%s" | plus: 0 %}
{% assign sorted_events = site.data.special_events | sort: "date" | reverse %}

{% assign has_past = false %}
{% for event in sorted_events %}
  {% assign event_ts = event.date | date: "%s" | plus: 0 %}
  {% if event_ts < now_ts %}
    {% assign has_past = true %}
  {% endif %}
{% endfor %}

{% if has_past %}
{% for event in sorted_events %}
  {% assign event_ts = event.date | date: "%s" | plus: 0 %}
  {% if event_ts < now_ts %}
    {% include special_event_card.html event=event %}
  {% endif %}
{% endfor %}
{% else %}
<p>No past events yet.</p>
{% endif %}

<div class="archive-link-section">
  <a href="{{ '/special' | relative_url }}" class="view-all">Back to Special Events</a>
</div>
