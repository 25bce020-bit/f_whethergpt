# Sprint 14 GIS API

The GIS layer is a thin formatter over the existing location, Open-Meteo weather, and IMD CAP services. It does not call map providers, use an LLM, or persist map state.

- `GET /gis/location?query=Ahmedabad` resolves a location to `{name, latitude, longitude, country, state}`.
- `GET /gis/weather/current`, `/gis/weather/forecast`, and `/gis/weather/hourly` accept either `name` or an explicit `latitude` and `longitude`. They return the location plus the existing WeatherGPT weather records. Current weather also includes a simple `marker` and GeoJSON Point.
- `GET /gis/warnings` returns authoritative IMD CAP alerts. Only an explicit CAP circle centre is exposed as a point; alerts without reliable point coordinates return `location: null`.
- `GET /gis/viewport?north=...&south=...&east=...&west=...` validates and echoes simple map bounds.

Coordinates are decimal degrees: latitude is `[-90, 90]`, longitude is `[-180, 180]`; non-finite or invalid values return HTTP 422. GeoJSON coordinates are always `[longitude, latitude]`.

For weather endpoints, coordinates take priority when supplied. A location name is resolved once through the existing geocoder; no location is inferred when neither form is supplied.
