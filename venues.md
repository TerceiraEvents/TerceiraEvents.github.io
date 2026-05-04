---
layout: default
title: Venues - Terceira Events
description: Bars, restaurants, cultural spaces, and other venues hosting events in Angra do Heroísmo, Terceira.
---

<h2>Venues</h2>

<p class="section-intro">Bars, restaurants, cultural spaces, and other venues hosting events in Angra do Heroísmo.</p>

{% for venue in site.data.venues %}
<div class="venue-card">
  <h3>{{ venue.name }}</h3>
  <div class="venue-address">{{ venue.address }}{% if venue.map_url %} · <a href="{{ venue.map_url }}">Map</a>{% endif %}</div>
  <div class="venue-regulars">
    {% if venue.description %}
    <p>{{ venue.description }}</p>
    {% endif %}
    {% if venue.weekly %}
    <p><strong>Weekly schedule:</strong></p>
    <ul>
      {% for entry in venue.weekly %}{% assign day_str = entry.day | strip %}{% assign day_len = day_str | size | minus: 1 %}{% assign day_last = day_str | slice: day_len, 1 %}
      <li><strong>{{ entry.day }}</strong>{% if day_last == ":" %} {{ entry.name }}{% else %} — {{ entry.name }}{% endif %}</li>
      {% endfor %}
    </ul>
    {% endif %}
    {% if venue.description_after_weekly %}
    <p>{{ venue.description_after_weekly }}</p>
    {% endif %}
    {% if venue.links or venue.reservation_phone %}
    <p>{% if venue.links %}{% for link in venue.links %}{% unless forloop.first %} · {% endunless %}<a href="{{ link.url }}">{{ link.label }}</a>{% endfor %}{% endif %}{% if venue.links and venue.reservation_phone %} · {% endif %}{% if venue.reservation_phone %}Reservations: {{ venue.reservation_phone }}{% endif %}</p>
    {% endif %}
    {% if venue.reservation_url %}
    <div class="event-reservations"><a href="{{ venue.reservation_url }}">{{ venue.reservation_label | default: "Make a dinner reservation" }}</a></div>
    {% endif %}
  </div>
</div>

{%- comment -%}
  JSON-LD `LocalBusiness` (or more specific subtype) per venue card.
  Address: parsed into `PostalAddress` when a Portuguese 9700-/9760-
  postal code is present; otherwise the raw address string becomes
  the `addressLocality`. `addressCountry` is always "PT".
  `sameAs` collects every URL from `links` (no mailto, etc.).
{%- endcomment -%}

{%- assign schema_type = venue.schema_type | default: "LocalBusiness" -%}
{%- comment -%}
  Build sameAs from venue.links, and pull out a "Website" link as the
  business's canonical URL if one exists. Liquid 4.0.4 lacks `push`
  so sameAs is built as a delimited string then split back. Trailing
  delimiter is fine — Liquid's `split` drops the empty trailing element.
{%- endcomment -%}
{%- assign sameas_buf = "" -%}
{%- assign business_url = "" -%}
{%- if venue.links -%}
  {%- for link in venue.links -%}
    {%- assign link_url = link.url | strip -%}
    {%- unless link_url contains "mailto:" or link_url == "" -%}
      {%- assign sameas_buf = sameas_buf | append: link_url | append: "|||" -%}
      {%- comment -%} First "Website" link wins. {%- endcomment -%}
      {%- if business_url == "" and link.label == "Website" -%}
        {%- assign business_url = link_url -%}
      {%- endif -%}
    {%- endunless -%}
  {%- endfor -%}
{%- endif -%}
{%- assign sameas = sameas_buf | split: "|||" -%}
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": {{ schema_type | jsonify }},
  "name": {{ venue.name | jsonify }},
  "address": {% include postal_address.html address=venue.address %}{% if business_url != "" %},
  "url": {{ business_url | jsonify }}{% endif %}{% if venue.map_url %},
  "hasMap": {{ venue.map_url | jsonify }}{% endif %}{% if venue.telephone %},
  "telephone": {{ venue.telephone | jsonify }}{% endif %}{% if sameas.size > 0 %},
  "sameAs": {{ sameas | jsonify }}{% endif %}
}
</script>
{% endfor %}
