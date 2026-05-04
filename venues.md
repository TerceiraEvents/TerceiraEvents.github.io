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
{%- assign addr = venue.address -%}
{%- assign has_postal = false -%}
{%- assign postal_prefix = "" -%}
{%- if addr contains "9700-" -%}
  {%- assign has_postal = true -%}
  {%- assign postal_prefix = "9700-" -%}
{%- elsif addr contains "9760-" -%}
  {%- assign has_postal = true -%}
  {%- assign postal_prefix = "9760-" -%}
{%- endif -%}
{%- if has_postal -%}
  {%- assign addr_parts = addr | split: postal_prefix -%}
  {%- comment -%} Strip the trailing ", " between street and postal code. {%- endcomment -%}
  {%- assign street_raw = addr_parts[0] | strip -%}
  {%- assign street_len = street_raw | size | minus: 1 -%}
  {%- assign last_char = street_raw | slice: street_len, 1 -%}
  {%- if last_char == "," -%}
    {%- assign street_address = street_raw | slice: 0, street_len -%}
  {%- else -%}
    {%- assign street_address = street_raw -%}
  {%- endif -%}
  {%- assign tail = addr_parts[1] | strip -%}
  {%- assign code_digits = tail | slice: 0, 3 -%}
  {%- assign locality = tail | slice: 3, 1000 | strip -%}
  {%- assign postal_code = postal_prefix | append: code_digits -%}
{%- endif -%}
{%- comment -%}
  Build sameAs as a delimited string (Liquid 4.0.4 lacks the `push`
  filter). Filter out mailto: links, then split back to an array for
  jsonify. A trailing delimiter is fine — Liquid's `split` drops the
  empty trailing element.
{%- endcomment -%}
{%- assign sameas_buf = "" -%}
{%- if venue.links -%}
  {%- for link in venue.links -%}
    {%- assign url = link.url | strip -%}
    {%- unless url contains "mailto:" or url == "" -%}
      {%- assign sameas_buf = sameas_buf | append: url | append: "|||" -%}
    {%- endunless -%}
  {%- endfor -%}
{%- endif -%}
{%- assign sameas = sameas_buf | split: "|||" -%}
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": {{ schema_type | jsonify }},
  "name": {{ venue.name | jsonify }},
  "address": {
    "@type": "PostalAddress",{% if has_postal %}
    "streetAddress": {{ street_address | jsonify }},
    "postalCode": {{ postal_code | jsonify }},
    "addressLocality": {{ locality | jsonify }},{% else %}
    "addressLocality": {{ addr | jsonify }},{% endif %}
    "addressCountry": "PT"
  },
  "url": "{{ site.url }}{{ site.baseurl }}/venues/"{% if venue.map_url %},
  "hasMap": {{ venue.map_url | jsonify }}{% endif %}{% if venue.telephone %},
  "telephone": {{ venue.telephone | jsonify }}{% endif %}{% if sameas.size > 0 %},
  "sameAs": {{ sameas | jsonify }}{% endif %}
}
</script>
{% endfor %}
