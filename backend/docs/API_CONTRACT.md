# WeatherGPT API Contract

## Base URL

The backend does not configure a public host or path prefix. Use the deployed server origin as the base URL (for local development, commonly `http://<host>:<port>`). All paths below are absolute.

## Authentication Model

WeatherGPT is guest-first: normal weather and chat functionality never require login. Optional account sessions use the HttpOnly `weathergpt_auth` cookie. The cookie contains a random opaque token; the server stores only its SHA-256 digest and validates a 14-day expiry. Set `AUTH_COOKIE_SECURE=true` in TLS production deployments; the non-secure default is only for local HTTP development.

The persistence model is `User` (`id`, nullable `name`, unique nullable `email`, nullable `password_hash`, `created_at`), `AuthSession` (`user_id`, token digest, expiry), one-to-one `UserPreference` (`language`, `units`, `theme`), `SavedLocation`, `Conversation` (nullable `user_id`, `session_id`, `title`, `created_at`), and `ChatMessage` (`role`, `content`, nullable `tool_used`, `created_at`). Guest chat creates a conversation with `user_id:null`; authenticated chat uses the authenticated user's id. `session_id` remains a separate conversation/context key in both cases.

Passwords use salted Python `hashlib.scrypt` hashes (Argon2id was not an installed dependency). Password hashes and session tokens are never returned. Production CORS origins must be supplied in comma-separated `CORS_ALLOWED_ORIGINS`; development defaults are explicit localhost ports and never a wildcard with credentials.

## Guest Access

Guest chat is supported through an opaque client-supplied `session_id`; it defaults to `"default"`. In-memory context is keyed by that value and persists only for the running process. Chat messages are also persisted under a database conversation with that `session_id`. Frontends should generate a unique session ID per guest browser/session and retain it locally. Do not use `"default"` in a multi-user client.

## Common Conventions

- Requests and responses are JSON except the two `multipart/form-data` voice endpoints.
- No endpoint declares FastAPI `response_model`; payloads below are the implementation’s actual shapes, not a normalized target schema.
- Coordinates are decimal numbers. Only GIS coordinate paths validate geographic ranges explicitly.
- Date fields are `YYYY-MM-DD`; weather times are provider strings (usually ISO-like local time without a documented offset). Cache timestamps are ISO 8601 UTC strings. Database timestamps are not exposed by public routes.
- `null` is possible where noted, especially optional geocoder fields and GFS values missing from the upstream provider.
- All endpoints currently return normal JSON with status `200` on success unless FastAPI validation or an explicit exception applies.

## Error Format

FastAPI request/parameter validation returns `422` with its standard shape:

```json
{"detail": [{"loc": ["query", "latitude"], "msg": "Field required", "type": "missing"}]}
```

Explicit GIS errors use `{"detail":"..."}`: `404` for an unresolved location, `422` for invalid/incomplete coordinates or bounds, and `502` if a geocoded result has invalid coordinates. Voice upload validation returns `{"detail":"..."}` with `400`, `413`, or `415`; transcription-provider failure returns `503`.

Many other upstream/network/database errors are not translated and can surface as `500`. Three location-name weather routes and `/realtime/location/{location_name}` instead return an **HTTP 200** payload containing `error`; see the endpoint tables.

### Reusable payload shapes

| Name | Actual fields |
|---|---|
| `Location` | `name: string`, `country: string|null`, `state: string|null`, `latitude?: number`, `longitude?: number`. `/locations/search` returns raw Open-Meteo geocoder objects, so additional provider fields may occur. |
| `CurrentWeather` | `time`, `temperature_c`, `feels_like_c`, `humidity_percent`, `precipitation_mm`, `weather_code`, `condition`, `wind_speed_kmh`, `wind_direction_degrees`, `timezone`. |
| `DailyForecast[]` | Each item: `date`, `condition`, `weather_code`, `temperature_max_c`, `temperature_min_c`, `precipitation_mm`, `wind_speed_max_kmh`. |
| `HourlyForecast[]` | Each item: `time`, `temperature_c`, `humidity_percent`, `rain_probability_percent`, `precipitation_mm`, `condition`, `weather_code`, `wind_speed_kmh`. |
| `GfsDaily[]` | Each item: `date`, `temperature_max_c|null`, `temperature_min_c|null`, `precipitation_mm|null`, `wind_speed_max_kmh|null`, `wind_gusts_max_kmh|null`, `weather_code|null`. |
| `GfsHourly[]` | Each item: `time`, `temperature_c|null`, `humidity_percent|null`, `apparent_temperature_c|null`, `precipitation_mm|null`, `rain_mm|null`, `weather_code|null`, `wind_speed_kmh|null`, `wind_gusts_kmh|null`, `wind_direction_degrees|null`, `cloud_cover_percent|null`, `surface_pressure_hpa|null`. |
| `Advisory[]` | `{type: "RAIN"|"HEAVY_RAIN"|"THUNDERSTORM"|"HEAT"|"WIND"|"HUMIDITY", severity: "HIGH"|"MODERATE", message, evidence: object}`. Evidence field depends on advisory type. |
| `DerivedAlert[]` | `{date, type, severity, title, message}`; these are WeatherGPT threshold-derived risks, not official warnings. |
| `OfficialWarning[]` | Dynamic normalized CAP data. Stable observed keys include `identifier`, `sent`, `status`, `msg_type`, `scope`, `event`, `urgency`, `severity`, `certainty`, `effective`, `onset`, `expires`, `headline`, `description`, `instruction`, `web`, `contact`, `sender_name`, `areas`, `source`, `official`. Values from CAP, including nested `areas` / `polygons` / `circles`, can be null or absent. |

## Core APIs

| Method / path | Request | Actual success response | Errors / auth / priority |
|---|---|---|---|
| `GET /` | None | `{message: "Welcome to WeatherGPT", status: "Backend is running"}` | `200`; guest; P2 (health/banner only). |
| `GET /locations/search` | Query `name` required string, min 2 chars | `{query, results: OpenMeteoGeocoderResult[]}`. Raw results commonly include `id`, `name`, `latitude`, `longitude`, `elevation`, `feature_code`, `country_code`, `admin1_id`, `admin2_id`, `timezone`, `population`, `postcodes`, `country`, `admin1`, `admin2`. | `422`, upstream `500`; guest; P0. |
| `DELETE /chat/session/{session_id}` | Path `session_id` | `{message: "Conversation cleared", session_id}`. Clears only in-memory context; it does not delete persisted database messages/conversation. | `200`; guest; P1. |

## Location APIs

The location-name weather APIs resolve only the first geocoder result and retain only `name`, `country`, `state`, `latitude`, and `longitude` as applicable.

| Method / path | Request | Actual success response | Errors / auth / priority |
|---|---|---|---|
| `GET /weather/current-by-location` | `name` required, min 2 | `{location: Location, weather: CurrentWeather}` | `200` even when unresolved: `{error: "Could not find a location for '…'"}`; `422`, upstream `500`; guest; P0. |
| `GET /weather/forecast-by-location` | `name` required, min 2 | `{location: Location, forecast: DailyForecast[]}` | Same `200` error payload behavior; guest; P0. |
| `GET /weather/hourly-by-location` | `name` required, min 2 | `{location: Location, hourly_forecast: HourlyForecast[]}` | Same `200` error payload behavior; guest; P1. |
| `GET /weather/advisory-by-location` | `name` required, min 2 | `{location: {name,country,state}, advisories: Advisory[], forecast_used: HourlyForecast[]}`. `forecast_used` is the first six returned hours. | Same `200` error payload behavior; guest; P1. |

## Weather APIs

| Method / path | Request | Actual success response | Errors / auth / priority |
|---|---|---|---|
| `GET /weather/current` | Required query `latitude: number`, `longitude: number` | `{latitude, longitude, weather: CurrentWeather}` | `422`; upstream `500`; guest; P0. |
| `GET /weather/gfs` | Required query `latitude`, `longitude` | `{latitude, longitude, model: "NCEP GFS", provider: "NOAA", hourly: GfsHourly[], daily: GfsDaily[]}` | `422`; upstream `500`; guest; P1. |
| `GET /weather/model-comparison` | Required query `latitude`, `longitude` | `{latitude, longitude, base_forecast_model: "Open-Meteo", nwp_model: "NCEP GFS", nwp_provider: "NOAA", comparison: ModelComparison[]}` | `422`; upstream `500`; guest; P1. |
| `GET /weather/official-warnings` | Required query `latitude`, `longitude` | `{source: "India Meteorological Department", official: true, latitude, longitude, total_alerts, location_alerts, warnings: OfficialWarning[]}` | `422`; upstream `500`; guest; P1. |

`ModelComparison[]` items contain `{date, temperature, precipitation, wind, confidence, explanation}`. Temperature is either `{base_model_c, gfs_c, difference_c, agreement}` or `{difference_c: null, agreement: "unknown"}`; precipitation and wind follow the same pattern with `_mm`/`_kmh`. `agreement` and aggregate `confidence` are `high`, `moderate`, `low`, or `unknown`.

## Chat API

### `POST /chat`

Request body (`application/json`):

```json
{
  "message": "Will it rain tomorrow in Pune?",
  "session_id": "guest-7f…",
  "selected_mode": "normal",
  "language": "en"
}
```

`message` is required. `session_id` defaults to `"default"`; `selected_mode` defaults to `"normal"` and is one of `normal`, `farmer`, `researcher`, `traveller`; `language` is nullable/optional. Invalid `selected_mode` is rejected with `422`.

Every observed chat branch returns `200` and includes `{session_id, selected_mode, active_mode, display_mode, message, understanding, tool, response}`. `response` is a string. `understanding` is a dynamic object normally containing `intent`, `location` (string|null), `time`, `activity` (string|null), `original_message`, and `language`; casual conversation omits `original_message`/`language`. `tool` normally contains `{tool, reason}` but tool/intent values are generated/routed dynamically. `session_id` always echoes the request; `language` remains branch-dependent.

Conditional top-level fields are below; consumers must feature-detect them.

| Routed branch | Additional fields when present |
|---|---|
| Casual conversation | `language` |
| Farmer context-only | `farmer_context: {crop: string|null, growth_stage: string|null}` |
| Current weather | `location: {name,country,state}`, `weather: CurrentWeather` |
| Daily forecast | `location`, `forecast: DailyForecast[]` |
| Hourly forecast | `location`, `hourly_forecast: HourlyForecast[]` |
| Historical | `location`, `historical_weather: HistoricalDaily[]` (same daily numeric shape as historical provider: `date`, `weather_code`, `temperature_max_c`, `temperature_min_c`, `precipitation_mm`, `wind_speed_max_kmh`) |
| Climate | `location`, `climate: {period: "last_7_days", average_temperature_c: number|null}` |
| General advisory | `location`, `advisories: Advisory[]` |
| Recommendation | `location`, `recommendations: string[]`, `weather_used: DailyForecast` |
| Derived disaster risk | `location`, `alerts: DerivedAlert[]`, `forecast_used: DailyForecast[]` |
| GFS | `location`, `nwp: {model,provider}`, `daily_forecast: GfsDaily[]`, `hourly_forecast: GfsHourly[]` (first 24 hours) |
| Model comparison | `location`, `model_comparison: {base_model, nwp_model, nwp_provider, comparison: ModelComparison[]}` |
| Official warning | `location`, `official_warnings: OfficialWarning[]` |
| Farmer mode | `location`, `weather_used: {current: CurrentWeather, forecast: DailyForecast[], hourly_forecast: HourlyForecast[]}`, `official_warnings`, `official_warning_status: "available"|"unavailable"`, `official_agromet` (optional object), `farmer_advisory` |
| Traveller mode | Same `weather_used` and official warning fields, plus `traveller_advisory` |

Unrelated, missing-location, unresolvable-location, unsupported historical-period, and unsupported-tool branches return only the common envelope; `location` and weather data are absent. These application outcomes are HTTP `200`, not errors. Database persistence and uncaught service failures can return `500`.

## Mode Behavior

`selected_mode` is the user’s explicit selection (or remembered session selection when omitted). `active_mode` is the server routing result. `display_mode` tells the UI what mode remains selected.

| Situation | selected_mode | active_mode | display_mode |
|---|---|---|---|
| Explicit `farmer`, `researcher`, or `traveller` | explicit value | same value | same value |
| Explicit/remembered `normal`, ordinary weather | `normal` | `normal` | `normal` |
| `normal` plus clear agricultural action/context | `normal` | `farmer` | `normal` |
| `normal` plus clear research/analysis wording | `normal` | `researcher` | `normal` |
| `normal` plus clear travel/outdoor-trip wording | `normal` | `traveller` | `normal` |

Automatic routing is intentionally conservative. The frontend should render `active_mode` response data while retaining the selector state from `display_mode`; do not overwrite a normal-mode selection merely because a single turn auto-routed.

## Farmer APIs/Behavior

There is no standalone farmer endpoint. Use `POST /chat` with `selected_mode: "farmer"`, or allow normal-mode automatic routing. `farmer_advisory` is:

```json
{
  "crop": "string or null",
  "growth_stage": "string or null",
  "weather_summary": {"current_time": "…", "forecast_day": {}},
  "irrigation": {"recommendation": "…", "reason": "…", "confidence": "medium|low"},
  "spraying": {"recommendation": "…", "reason": "…", "confidence": "medium|low"},
  "sowing": {"recommendation": "…", "reason": "…", "confidence": "medium|low"},
  "harvesting": {"recommendation": "…", "reason": "…", "confidence": "medium|low"},
  "today_advisory": ["…"],
  "imd_warning_status": "available|unavailable",
  "imd_actions": [{"official_imd_warning": {"event": "…", "severity": "…", "headline": "…"}, "weathergpt_farmer_advisory": "…"}],
  "agromet_advisory": {
    "available": true,
    "status": "available",
    "source": "IMD Agromet/GKMS",
    "location": {"state": "…", "district": "…", "latitude": 0, "longitude": 0},
    "advisories": [
      {
        "id": 101,
        "title": "…",
        "crop": "…",
        "variety": "…",
        "weather_condition": "…",
        "weather_condition_regional": "…",
        "recommendation": "…",
        "recommendation_regional": "…",
        "language": "…",
        "valid_from": "…",
        "valid_until": "…",
        "updated_at": "…"
      }
    ],
    "source_attribution": {
      "provider": "India Meteorological Department (IMD) - GKMS / Agromet Advisory",
      "url": "https://agromet.imd.gov.in",
      "retrieved_at": "…"
    }
  },
  "agromet_status": "available|unavailable",
  "limitations": ["…"]
}
```

`weather_summary` is data-dependent. It may contain `current_time`, `current_temperature_c`, `current_precipitation_mm`, `current_wind_speed_kmh`, `current_condition`, `forecast_day`, or only `availability`.

## Researcher APIs/Behavior

There is no standalone researcher endpoint. Use chat mode. Researcher routing retains the normal chat branch payload plus the underlying branch’s weather data. It does **not** add a `researcher_analysis` field to the public chat response: that object is passed internally to the LLM. The stable researcher-facing evidence remains the branch fields documented in Chat API (`weather`, `forecast`, `historical_weather`, GFS, comparison, warnings, etc.).

## Traveller APIs/Behavior

There is no standalone traveller endpoint. Use chat mode. `traveller_advisory` has:

```json
{
  "destination": "string or null",
  "travel_date_hint": "string or null",
  "suitability": {"status": "GOOD|CAUTION|UNFAVORABLE|UNAVAILABLE", "reasons": ["…"]},
  "weather_summary": {"forecast_day": {}, "current_weather": {}},
  "best_outdoor_window": {"period": "morning|afternoon|evening", "reason": "…"},
  "packing": ["…"],
  "official_warning_status": "available|unavailable",
  "official_warning_actions": [{"official_imd_warning": {"event": null, "severity": null, "headline": null}, "weathergpt_traveller_advice": "…"}],
  "limitations": ["…"]
}
```

`best_outdoor_window` is nullable, and summary keys are data-dependent.

## GFS APIs

Use `GET /weather/gfs` for direct model data, or chat for an intent-routed summary. GFS is labeled `model: "NCEP GFS"`, `provider: "NOAA"`. Direct GFS returns all fetched hourly/daily values; chat truncates GFS hourly data to 24 records.

## Model Comparison

Use `GET /weather/model-comparison` for deterministic daily comparisons, or the chat model-comparison branch for a generated text response plus the same comparison data under `model_comparison.comparison`.

## Official IMD Warnings

Use `GET /weather/official-warnings` for warnings filtered by coordinates. Its `warnings` remain dynamic CAP-derived objects. `official: true` and the IMD source identify official data; `alerts` returned by the chat disaster branch are separate, WeatherGPT-derived threshold risks.

## GIS APIs

| Method / path | Request | Actual success response | Errors / auth / priority |
|---|---|---|---|
| `GET /gis/location` | `query` required, min 2 | `GeographicPoint`: `{latitude, longitude, name|null, country|null, state|null}` | `404`, `422`, `502`; guest; P1. |
| `GET /gis/weather/current` | Either `name` (min 2) **or both** `latitude`,`longitude`; explicit coordinates take priority | `{location: GeographicPoint, weather: CurrentWeather, map: {latitude,longitude}, marker: {id,latitude,longitude,title,weather}, geojson: {type:"Feature",geometry:{type:"Point",coordinates:[longitude,latitude]},properties:{name,weather_code,temperature_c}}}` | `404`, `422`, `502`, upstream `500`; guest; P1. |
| `GET /gis/weather/forecast` | Same resolver inputs | `{location: GeographicPoint, forecast: DailyForecast[], map: {latitude,longitude}}` | Same; guest; P1. |
| `GET /gis/weather/hourly` | Same resolver inputs | `{location: GeographicPoint, hourly: HourlyForecast[], map: {latitude,longitude}}` | Same; guest; P1. |
| `GET /gis/warnings` | None | `{source:"India Meteorological Department", official:true, alerts: MapWarning[]}` | upstream `500`; guest; P1. |
| `GET /gis/viewport` | Required `north`,`south`,`east`,`west` | `{bounds:{north,south,east,west}}` | `422`; guest; P2. |

`MapWarning` is `{id|null,title|null,event|null,severity|null,sent_at|null,source:"IMD",official:boolean,coordinates_available:boolean,location: GeographicPoint|null}`. It reports a point only when CAP circle coordinates exist; it never geocodes alert text.

## Voice APIs

| Method / path | Request | Actual success response | Errors / auth / priority |
|---|---|---|---|
| `POST /voice/transcribe` | Multipart: required `audio`; optional `session_id` default `default`; optional `language` | `{success:true, transcript:string, language:string, session_id:string}` | `400`, `413` (> configured 10 MB default), `415` format/type/signature, `503` provider; guest; P1. |
| `POST /voice/chat` | Same multipart fields | `{success:true, transcript:string, language:string, session_id:string, response:string, chat: ChatResponse, tts:{provider:"browser_speech_synthesis",language,locale}}` | Same; guest; P1. |

Accepted audio extensions/types: WAV, MP3/MPEG, WebM, OGG, MP4, M4A; file signatures are validated. Browser TTS is a client-side contract only—no audio bytes or server-side synthesis endpoint exist.

## Realtime APIs

| Method / path | Request | Actual success response | Errors / auth / priority |
|---|---|---|---|
| `GET /realtime/status` | None | `{service:"WeatherGPT Real-Time Ingestion", status:"running", cached_sources:number, cache: CacheStatusByKey}` | `200`; guest; P2. |
| `POST /realtime/refresh/{location_name}` | Path location name | `RefreshLocationResult`: success object `{success:true,location:raw geocoder object,open_meteo:object|null,gfs:object|null,errors:SourceError[]}` or unresolved `{success:false,location:string,error:"Location not found."}` | HTTP `200` for both; guest; P2. |
| `GET /realtime/location/{location_name}` | Path location name | `{location:raw geocoder object,open_meteo: CacheEntry|null,gfs: CacheEntry|null}` | HTTP `200` unresolved `{error:"Location not found."}`; guest; P2. |
| `GET /realtime/imd` | None | Cache hit: `{cached:true,updated_at:string,alerts:OfficialWarning[]}`; missing: `{alerts:[],cached:false}` | upstream `500`; guest; P2. |
| `POST /realtime/refresh` | None | `{locations: RefreshLocationResult[], imd:boolean}` | `200`; guest; P2. |
| `DELETE /realtime/cache` | None | `{message:"Real-time cache cleared."}` | `200`; guest; P2. |

`CacheEntry` is `{data:any,source:string,updated_at:string,ttl_seconds:number,timestamp:number,age_seconds:number,expired:boolean}`. `CacheStatusByKey` has an arbitrary cache key mapped to `{source,updated_at,age_seconds,ttl_seconds,expired}`. `SourceError` is `{source:"Open-Meteo"|"GFS",error:string}`.

## Database/Performance APIs

| Method / path | Request | Actual success response | Errors / auth / priority |
|---|---|---|---|
| `GET /database/status` | None | Connected: `{database:"PostgreSQL",status:"connected"}`; failed probe: `{database:"PostgreSQL",status:"error",error:string}` | Both statuses are HTTP `200`; guest; P2. |
| `GET /database/summary` | None | `{users,conversations,chat_messages,weather_records,official_alerts,ingestion_logs}` (numbers) | DB `500`; guest; P2. |
| `GET /performance/cache` | None | `{entries,inflight_requests,hits,misses,expired,stale_hits,sets,upstream_requests,coalesced_requests,hit_rate_percent}` | `200`; guest; P2. |

## Authentication APIs

| Method / path | Request | Success response | Errors |
|---|---|---|---|
| `POST /auth/signup` | `{name?: string, email: string, password: string}`. Password is 12–256 characters and contains a letter and number. | `201`, `{user:{id,name,email,created_at}}`, plus auth cookie. | `409` duplicate email; `422` validation. |
| `POST /auth/login` | `{email:string,password:string}` | `200`, same user shape plus new auth cookie. | `401` generic invalid-credential error. |
| `POST /auth/logout` | None; uses auth cookie when present. | `200`, `{message:"Logged out."}` and expires cookie. | Safe for guest state. |
| `GET /auth/me` | Auth cookie | `200`, `{user:{id,name,email,created_at}}` | `401` guest/expired/invalid session. |

Authenticated `POST /chat` retains the guest request shape. It associates the conversation with the cookie user while preserving `session_id` as a separate conversation identifier. Guest conversations have `user_id:null`. On a subsequent authenticated chat with the same opaque guest session ID, an unowned guest conversation is safely claimed; a conversation owned by another account is never reused.

## Frontend Integration Notes

1. Treat `/chat` as a tagged-but-not-explicit union: inspect `tool.tool`, `active_mode`, and the presence of conditional data fields. Every response includes `session_id`, but do not assume every response contains weather, location, or `language`.
2. Persist a generated opaque guest `session_id`; include it on chat and voice calls. `/chat` echoes the same value. Login is optional; browser clients should send credentialed requests only for account features.
3. Render official IMD CAP content separately from derived alerts/advisories. Fields within `OfficialWarning` are dynamic and may be null.
4. Use `display_mode` for the mode selector and `active_mode` to select a specialized result renderer.
5. Handle FastAPI `422` and explicit GIS/voice errors, but also detect legacy HTTP-200 `{error}` payloads on location/realtime APIs.
6. Do not expose `/database/*`, `/performance/cache`, or `/realtime/*` as ordinary guest UI features; they are operational/admin-shaped endpoints and currently have no protection.

## Contract Issues

### P0

None found that prevents a frontend from integrating with the implemented endpoints. No code changes were made.

### P1

- `/chat` has no declared response model and varies by route; it consistently includes `session_id` but omits `language` on most branches.
- Name-based weather routes use HTTP `200` for unresolved-location `{error}` payloads, while GIS uses `404` and other failures use exceptions.
- `tool` / `understanding` values and key presence vary across chat branches; consumers must not model it as one fixed object.
- All mutable realtime/cache and database-summary/status endpoints are publicly callable; this conflicts with their likely operational role once the frontend/deployment starts.
- Provider failures mostly surface as unstructured `500` rather than a documented application error envelope.

### P2

- No `response_model`/OpenAPI error responses exist for public routes, so generated client types will be incomplete.
- Timestamp semantics mix provider-local weather strings, UTC cache timestamps, and naive database storage timestamps.
- `/gis/weather/hourly` uses `hourly` whereas `/weather/hourly-by-location` uses `hourly_forecast`; chat GFS uses `daily_forecast`/`hourly_forecast` whereas direct GFS uses `daily`/`hourly`.
- `/chat/session/{session_id}` says “Conversation cleared” but only clears in-memory context; database history remains.
