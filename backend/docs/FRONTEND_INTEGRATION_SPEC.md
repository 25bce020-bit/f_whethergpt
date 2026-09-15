# WeatherGPT Frontend Integration Specification

This is the post-Sprint-22 frontend contract. The backend implementation is the source of truth; use [API_CONTRACT.md](API_CONTRACT.md) for the complete endpoint inventory and exact polymorphic shapes.

## 1. Architecture and base URL

The backend has no configured public base URL or path prefix. Configure an environment-specific origin in the frontend and append the absolute paths in this document. Do not hardcode a production URL. The app is guest-first: authentication sits above conversation/context, mode resolution, weather intelligence, and Groq response generation.

## 2. Guest session

On first launch, generate and persist a cryptographically opaque browser-local value such as `guest-<random-id>`. Send it as `session_id` on `POST /chat` and voice calls. Do not use the shared default `"default"` value in a real client. Login is not required for any ordinary weather, GIS, voice, or chat request.

`session_id` is a client conversation/context identifier. It is **not** a `user_id`, email, password, or authentication credential. It is echoed by every `/chat` response and is kept in memory server-side only for the running process; its database conversation history persists separately.

## 3. Authentication and authenticated session

`POST /auth/signup` accepts JSON `{name?: string, email: string, password: string}`. Name is optional and at most 100 characters. Email is normalized to lowercase and must match the implemented basic email validation. Password is 12–256 characters and contains at least one letter and number. Success is `201` with `{user:{id,name,email,created_at}}`; duplicate email is `409`; validation is FastAPI `422`.

`POST /auth/login` accepts `{email:string,password:string}` and returns the same user shape. Bad credentials return `401` with a generic error. `GET /auth/me` returns that user shape when authenticated and `401` otherwise. `POST /auth/logout` is safe for guest state, returns `{message:"Logged out."}`, invalidates the current session when present, and expires the cookie.

The browser receives the `weathergpt_auth` HttpOnly cookie. It contains an opaque random token; the server stores only a digest and checks expiry. Lifetime defaults to 14 days and is configurable with `AUTH_SESSION_LIFETIME_DAYS`. The cookie is `SameSite=Lax`, path `/`, and uses `Secure` only when `AUTH_COOKIE_SECURE=true`; production TLS deployment must set that variable. JavaScript must not read, persist, or manually construct this cookie. Use browser credentialed requests where required.

## 4. Login transition and conversation ownership

For guest chat, a `Conversation` has `user_id:null` and the supplied `session_id`. For authenticated chat, `user_id` is the authenticated account and `session_id` remains the conversation/context identifier. Therefore `session_id != user_id`.

After login or signup, the next authenticated `/chat` call using the same guest session ID claims that unowned guest conversation. A conversation already owned by a different account is not reused. Signup/login themselves do not claim conversations. `UserPreference` and `SavedLocation` relationships already exist but have no frontend settings or saved-location API in this contract.

## 5. Chat

Send JSON to `POST /chat`:

```json
{"message":"Will it rain tomorrow in Pune?","session_id":"guest-...","selected_mode":"normal","language":"en"}
```

`message` is required. `session_id` defaults to `"default"`; `selected_mode` defaults to `normal` and must be `normal`, `farmer`, `researcher`, or `traveller`; `language` is optional. Invalid request values return `422`.

Every successful chat branch returns HTTP `200` with these fields: `session_id`, `selected_mode`, `active_mode`, `display_mode`, `message`, `understanding`, `tool`, and text `response`. `session_id` exactly echoes the request. `understanding` and `tool` have dynamic values. Treat the payload as a discriminated-by-presence union, not one fixed weather object.

Conditional fields include `location`, `weather`, `forecast`, `hourly_forecast`, `historical_weather`, `climate`, `advisories`, `recommendations`, `weather_used`, `forecast_used`, `alerts`, `nwp`, `daily_forecast`, `model_comparison`, `official_warnings`, `farmer_context`, `farmer_advisory`, and `traveller_advisory`. Missing-location, casual, unsupported, and unrelated branches may have only the common envelope. See the Chat API table in [API_CONTRACT.md](API_CONTRACT.md).

`DELETE /chat/session/{session_id}` clears only in-memory context. It does not delete persisted conversation rows or messages.

## 6. Modes

Use `display_mode` to control the selected UI mode and `active_mode` to select specialized result rendering. In Normal mode, conservative automatic routing may set `active_mode` to Farmer, Researcher, or Traveller while both `selected_mode` and `display_mode` remain `normal`. Do not overwrite the Normal selector because of that single response.

Explicit Farmer, Researcher, and Traveller selections set all three values to that mode. Farmer returns `farmer_advisory` when weather data is available; Researcher uses ordinary branch evidence rather than a public `researcher_analysis` field; Traveller returns `traveller_advisory` when available.

## 7. Weather and warnings

Use direct weather endpoints for deterministic data: `/weather/current`, `/weather/current-by-location`, `/weather/forecast-by-location`, `/weather/hourly-by-location`, `/weather/advisory-by-location`, `/weather/gfs`, `/weather/model-comparison`, and `/weather/official-warnings`. Their exact request and response fields are frozen in [API_CONTRACT.md](API_CONTRACT.md).

Official IMD CAP warnings use `official:true` and the `warnings` field. Chat `alerts` are WeatherGPT-derived risks, not official IMD warnings. Render and label them separately. Name-based current/forecast/hourly/advisory endpoints retain legacy HTTP-200 `{error:"Could not find a location for '…'"}` behavior.

## 8. GIS

Use `/gis/location?query=` for lookup. Use `/gis/weather/current` for a current-weather map, `/gis/weather/forecast` for a forecast map, `/gis/weather/hourly` for hourly data, `/gis/warnings` for map-safe warning points, and `/gis/viewport` to validate bounds. Weather GIS routes accept a location name or both coordinates; explicit coordinates take priority. GIS uses `404` for an unresolved name, `422` for invalid inputs, and can return `502` for invalid geocoder coordinates.

Current-map GeoJSON is a Feature with Point coordinates in `[longitude, latitude]` order. Map warning `location` is nullable because alert text is not geocoded.

## 9. Voice

`POST /voice/transcribe` and `/voice/chat` use `multipart/form-data`: required `audio`, optional `session_id` (default `default`), optional `language`. They are guest-accessible and do not consume the auth cookie for conversation ownership. Supported types are WAV, MP3/MPEG, WebM, OGG, MP4, and M4A, with signature validation and a default 10 MB configured maximum.

Transcribe returns `{success,transcript,language,session_id}`. Voice chat additionally returns `{response,chat,tts}`; `chat` is the standard polymorphic chat envelope and `tts` describes browser SpeechSynthesis only—no server audio is returned. Errors are `400`, `413`, `415`, or `503` with `{detail:string}`.

## 10. CORS and API client behavior

Development origins are `http://localhost:3000` and `http://localhost:5173`. The backend enables credentials and accepts only `GET`, `POST`, `DELETE`, and `OPTIONS`, with `Content-Type` and `X-Requested-With` headers. Configure the comma-separated `CORS_ALLOWED_ORIGINS` backend variable with the actual frontend deployment origin before production; do not use a wildcard with credentials.

Use a single client wrapper: JSON GET/POST requests use `Content-Type: application/json`; voice requests use `FormData` and must not manually set its content-type boundary. For browser requests that need the HttpOnly auth cookie, use the browser's credentialed-request option. On `401`, transition to guest and optionally offer login; do not block chat. Surface `422` field validation, legacy HTTP-200 `error` objects, network failure, and unstructured server `500` responses separately.

## 11. Frontend state expectations

- Auth state: `loading`, `guest`, or `authenticated`; user is the `/auth/me` user shape or null.
- Session state: opaque guest `session_id`, chosen `selected_mode`, and optional language.
- Chat state: messages, loading, error, last `active_mode`, last `display_mode`, and feature-detected response data.
- Preferences: user preferences are persistence-ready server models only; no preference endpoint exists yet.

At app bootstrap, resolve `/auth/me` without treating `401` as an application failure, then permit full guest use immediately.

## 12. Errors and known limitations

FastAPI validation uses `422` and `{"detail":[...]}`. Auth uses `401` for guest/current-user and invalid credentials, and `409` only for duplicate signup. GIS uses `404`, `422`, and `502` as described above. Voice uses `400`, `413`, `415`, and `503`. Provider/database failures elsewhere can be unstructured `500`.

`/realtime/*`, `/database/*`, and `/performance/cache` are currently public operational endpoints. They are **not for normal frontend UI** and require protection in the later security sprint.

## 13. Do not do

Do not require login on launch; use `user_id` as `session_id`; store or manually manage the AuthSession cookie; assume every chat response has weather data; overwrite Normal mode because `active_mode` changed; expose operational endpoints; expose `password_hash`; hardcode backend URLs or API keys; invent weather values or IMD warnings; or present derived alerts as official IMD alerts.
