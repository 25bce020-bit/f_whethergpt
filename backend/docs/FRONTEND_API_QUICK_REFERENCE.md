# WeatherGPT Frontend API Quick Reference

WeatherGPT is guest-first. Generate and persist an opaque guest `session_id`; do not share the default `"default"` session between users. Login is optional and uses an HttpOnly cookie, so the frontend does not store an auth token in localStorage. For cross-origin browser calls, use credentials and configure the backend's `CORS_ALLOWED_ORIGINS` in production.

## Optional authentication

`POST /auth/signup` with `{ "name":"Ava", "email":"ava@example.com", "password":"WeatherPass123" }` returns `201` and `{ "user": { "id":1,"name":"Ava","email":"ava@example.com","created_at":"…" } }`, setting the auth cookie.

`POST /auth/login` accepts `{ "email":"ava@example.com", "password":"WeatherPass123" }` and returns the same user shape. Invalid credentials return `401` without identifying which field was wrong. Duplicate signup returns `409`; malformed requests return `422`.

`GET /auth/me` returns the signed-in user or `401` for a guest. `POST /auth/logout` clears the cookie and invalidates its server session. Authentication is never required for weather or chat.

## Current weather

`GET /weather/current?latitude=18.5204&longitude=73.8567`

```json
{"latitude":18.5204,"longitude":73.8567,"weather":{"time":"2026-09-15T10:00","temperature_c":29.2,"feels_like_c":31.4,"humidity_percent":66,"precipitation_mm":0,"weather_code":2,"condition":"Partly cloudy","wind_speed_kmh":12.1,"wind_direction_degrees":260,"timezone":"Asia/Kolkata"}}
```

## Forecast

`GET /weather/forecast-by-location?name=Pune`

```json
{"location":{"name":"Pune","country":"India","state":"Maharashtra","latitude":18.52,"longitude":73.86},"forecast":[{"date":"2026-09-15","condition":"Partly cloudy","weather_code":2,"temperature_max_c":30,"temperature_min_c":22,"precipitation_mm":1.2,"wind_speed_max_kmh":18}]}
```

Unresolved location is legacy HTTP `200`: `{"error":"Could not find a location for '…'"}`.

## Chat

`POST /chat`

```json
{"message":"Will it rain tomorrow in Pune?","session_id":"guest-123","selected_mode":"normal","language":"en"}
```

```json
{"session_id":"guest-123","selected_mode":"normal","active_mode":"normal","display_mode":"normal","message":"Will it rain tomorrow in Pune?","understanding":{"intent":"forecast","location":"Pune","time":"tomorrow","activity":null,"language":"en"},"tool":{"tool":"forecast","reason":"…"},"location":{"name":"Pune","country":"India","state":"Maharashtra"},"forecast":[{"date":"2026-09-16","condition":"Light rain","weather_code":61,"temperature_max_c":29,"temperature_min_c":22,"precipitation_mm":5,"wind_speed_max_kmh":18}],"response":"…"}
```

`response` is always text, but chat is polymorphic. Every branch echoes the submitted `session_id`; feature-detect `weather`, `forecast`, `hourly_forecast`, `farmer_advisory`, `traveller_advisory`, `nwp`, `model_comparison`, `official_warnings`, `alerts`, and `advisories`.

## Farmer

Use chat with `selected_mode:"farmer"`; automatic farmer routing may instead return `selected_mode:"normal", active_mode:"farmer", display_mode:"normal"`.

```json
{"message":"Can I spray cotton in Pune tomorrow?","session_id":"guest-123","selected_mode":"farmer"}
```

Look for `farmer_advisory` with `crop`, `growth_stage`, `weather_summary`, decisions for `irrigation`/`spraying`/`sowing`/`harvesting`, `today_advisory`, `imd_warning_status`, `imd_actions`, `agromet_advisory` (official IMD Agromet / GKMS advisories with `crop`, `title`, `recommendation`, `recommendation_regional`, `valid_until`, and source attribution), `agromet_status`, and `limitations`. When present, top-level `official_agromet` contains the full normalized Agromet payload.

## Researcher

Use chat with `selected_mode:"researcher"`.

```json
{"message":"Analyze the historical weather in Pune last week","session_id":"guest-123","selected_mode":"researcher"}
```

The normal chat envelope is retained. Read branch evidence such as `historical_weather`, `forecast`, `weather`, `nwp`, `model_comparison`, and `official_warnings`; there is no public `researcher_analysis` field.

## Traveller

Use chat with `selected_mode:"traveller"`.

```json
{"message":"Is Goa suitable for travel tomorrow?","session_id":"guest-123","selected_mode":"traveller"}
```

`traveller_advisory.suitability.status` is `GOOD`, `CAUTION`, `UNFAVORABLE`, or `UNAVAILABLE`. Also render `reasons`, nullable `best_outdoor_window`, `packing`, and official warning information separately.

## GFS

`GET /weather/gfs?latitude=18.5204&longitude=73.8567`

```json
{"latitude":18.5204,"longitude":73.8567,"model":"NCEP GFS","provider":"NOAA","hourly":[{"time":"2026-09-15T10:00","temperature_c":29.2,"humidity_percent":66,"apparent_temperature_c":31.4,"precipitation_mm":0,"rain_mm":0,"weather_code":2,"wind_speed_kmh":12,"wind_gusts_kmh":20,"wind_direction_degrees":260,"cloud_cover_percent":45,"surface_pressure_hpa":1008}],"daily":[{"date":"2026-09-15","temperature_max_c":30,"temperature_min_c":22,"precipitation_mm":1.2,"wind_speed_max_kmh":18,"wind_gusts_max_kmh":30,"weather_code":2}]}
```

GFS numeric fields can be `null`.

## Model comparison and warnings

`GET /weather/model-comparison?latitude=18.5204&longitude=73.8567` returns a `comparison` array of `{date,temperature,precipitation,wind,confidence,explanation}`.

`GET /weather/official-warnings?latitude=18.5204&longitude=73.8567` returns `{source,official,latitude,longitude,total_alerts,location_alerts,warnings}`. Warning objects are CAP-derived and dynamic; tolerate absent/null values.

## GIS

- `GET /gis/location?query=Pune` → `{latitude,longitude,name,country,state}`
- `GET /gis/weather/current?name=Pune` → location/weather/map/marker/GeoJSON
- `GET /gis/weather/forecast?latitude=18.52&longitude=73.86` → location/forecast/map
- `GET /gis/weather/hourly?name=Pune` → location/hourly/map
- `GET /gis/warnings` → map-safe IMD alert points; `location` is nullable when no CAP circle exists.

GIS requires either `name` or both coordinates. Invalid/missing pairs return `422`; unresolved names return `404`.

## Voice

`POST /voice/transcribe` multipart fields: `audio` required; `session_id` and `language` optional.

```json
{"success":true,"transcript":"Weather in Pune","language":"en","session_id":"guest-123"}
```

`POST /voice/chat` takes the same form and returns `{success,transcript,language,session_id,response,chat,tts}`. `chat` is the full polymorphic chat payload; `tts` is browser SpeechSynthesis metadata, not generated audio.

Supported files: WAV, MP3, WebM, OGG, MP4, M4A; default limit 10 MB. Errors are `400`, `413`, `415`, or `503` with `{"detail":"…"}`.

## Operational routes

Existing but not normal end-user UI APIs: `/realtime/status`, `/realtime/refresh/{location_name}`, `/realtime/location/{location_name}`, `/realtime/imd`, `/realtime/refresh`, `/realtime/cache`, `/database/status`, `/database/summary`, `/performance/cache`. They are currently public and should be treated as admin/diagnostic-only.

For the full inventory, exact conditional chat variants, error behavior, and contract findings, see `docs/API_CONTRACT.md`.
