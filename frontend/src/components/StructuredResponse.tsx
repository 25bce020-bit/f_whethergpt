import type { ReactNode } from "react";
import { useNavigate } from "react-router-dom";
import type { ChatResponse, Mode, AgrometItem } from "../api/types";
import {
  AlertTriangle,
  BarChart2,
  Calendar,
  CheckCircle2,
  CloudRain,
  Compass,
  Droplets,
  Info,
  Lightbulb,
  MapPin,
  ShieldAlert,
  Sparkles,
  Thermometer,
  Wind,
} from "./icons";
import { WeatherVisual } from "./WeatherVisual";
import { selectLocation } from "../locationSelection";

interface StructuredResponseProps {
  text: string;
  data?: ChatResponse;
  mode?: Mode;
}

export function StructuredResponse({ text, data: d, mode: currentMode = "normal" }: StructuredResponseProps) {
  const navigate = useNavigate();

  const location = d?.location;
  const locationName = location?.name || (typeof d?.understanding?.location === "string" ? d.understanding.location : null);
  const effectiveMode = (d?.active_mode || d?.selected_mode || currentMode) as Mode;
  const timeHint = d?.understanding?.time || "Current";

  // Check if we have weather, forecast, travel or farmer data to render structured widgets
  const hasWeather = Boolean(d?.weather);
  const hasForecast = Boolean(d?.forecast && d.forecast.length > 0);
  const hasHourly = Boolean(d?.hourly_forecast && d.hourly_forecast.length > 0);
  const hasTravel = Boolean(d?.traveller_advisory?.suitability);
  const hasFarmer = Boolean(d?.farmer_advisory?.today_advisory && d.farmer_advisory.today_advisory.length > 0);
  const agrometData = d?.official_agromet || d?.farmer_advisory?.agromet_advisory;
  const agrometAdvisories: AgrometItem[] = agrometData?.advisories || [];
  const hasAgromet = agrometAdvisories.length > 0;
  const hasWarnings = Boolean(d?.official_warnings && d.official_warnings.length > 0);

  const isStructuredEligible = hasWeather || hasForecast || hasHourly || hasTravel || hasFarmer || hasAgromet || hasWarnings;

  // Determine Primary Badge
  let badgeLabel = "Weather Outlook";
  let badgeIcon: ReactNode = <Sparkles />;

  if (effectiveMode === "traveller" || hasTravel) {
    badgeLabel = "Travel Outlook";
    badgeIcon = <Compass />;
  } else if (effectiveMode === "farmer" || hasFarmer) {
    badgeLabel = "Farmer Weather Outlook";
    badgeIcon = <Sparkles />;
  } else if (effectiveMode === "researcher") {
    badgeLabel = "Research Weather Summary";
    badgeIcon = <BarChart2 />;
  }

  // Travel Suitability Status
  const travelStatus = d?.traveller_advisory?.suitability?.status?.toUpperCase() || null;
  const travelReasons = d?.traveller_advisory?.suitability?.reasons || [];
  const packingItems = d?.traveller_advisory?.packing || [];

  // Farmer Decisions & Agromet
  const farmerItems = d?.farmer_advisory?.today_advisory || [];

  // Weather Metrics
  const currentWeather = d?.weather;
  const primaryDay = d?.forecast?.[0];
  const tempVal = currentWeather ? Math.round(currentWeather.temperature_c) : primaryDay ? Math.round(primaryDay.temperature_max_c) : null;
  const tempMin = primaryDay?.temperature_min_c !== undefined ? Math.round(primaryDay.temperature_min_c) : null;
  const feelsLike = currentWeather ? Math.round(currentWeather.feels_like_c) : null;
  const conditionText = currentWeather?.condition || primaryDay?.condition || null;
  const weatherCode = currentWeather?.weather_code ?? primaryDay?.weather_code ?? 0;
  const rainChance = d?.hourly_forecast?.[0]?.rain_probability_percent ?? (primaryDay?.precipitation_mm ? Math.min(Math.round(primaryDay.precipitation_mm * 20), 100) : null);
  const precMm = currentWeather?.precipitation_mm ?? primaryDay?.precipitation_mm ?? null;
  const windSpeed = currentWeather ? Math.round(currentWeather.wind_speed_kmh) : primaryDay ? Math.round(primaryDay.wind_speed_max_kmh) : null;
  const humidity = currentWeather?.humidity_percent ?? d?.hourly_forecast?.[0]?.humidity_percent ?? null;

  // Handle CTA navigation to Forecast Page
  const handleViewForecast = () => {
    if (location) {
      selectLocation(location);
      navigate(`/forecast?location=${encodeURIComponent(location.name)}`);
    } else if (locationName) {
      navigate(`/forecast?location=${encodeURIComponent(locationName)}`);
    } else {
      navigate("/forecast");
    }
  };

  // If no structured signals exist, render cleanly formatted text paragraphs
  if (!isStructuredEligible) {
    return (
      <div className="chat-bubble-text">
        <p className="chat-narrative-paragraph">{text}</p>
        {locationName && (
          <div className="chat-action-footer">
            <button
              type="button"
              className="forecast-cta-btn primary-action-pill"
              onClick={handleViewForecast}
              aria-label={`View full forecast for ${locationName}`}
            >
              <BarChart2 />
              <span>View Forecast</span>
            </button>
          </div>
        )}
      </div>
    );
  }

  return (
    <div className="structured-response-card glass">
      {/* 1. Header Banner & Location Meta */}
      <div className="structured-card-header">
        <div className="structured-badge">
          {badgeIcon}
          <span>{badgeLabel}</span>
        </div>
        {(locationName || timeHint) && (
          <div className="structured-location-meta">
            {locationName && (
              <span className="meta-item">
                <MapPin className="meta-icon" />
                <strong>{locationName}</strong>
              </span>
            )}
            {timeHint && timeHint !== "Current" && (
              <span className="meta-item">
                <Calendar className="meta-icon" />
                <span>{timeHint}</span>
              </span>
            )}
          </div>
        )}
      </div>

      {/* 2. Status Banner (for Travel or Severe Conditions) */}
      {travelStatus && (
        <div
          className={`response-status-banner ${
            travelStatus === "GOOD"
              ? "status-banner--good"
              : travelStatus === "CAUTION"
                ? "status-banner--caution"
                : "status-banner--warning"
          }`}
        >
          <div className="status-banner-badge">
            {travelStatus === "GOOD" ? (
              <CheckCircle2 className="status-icon" />
            ) : (
              <AlertTriangle className="status-icon" />
            )}
            <strong>TRAVEL STATUS: {travelStatus}</strong>
          </div>
        </div>
      )}

      {/* 3. Official IMD Weather Warnings */}
      {hasWarnings && d?.official_warnings && (
        <div className="response-alert-banner glass-danger">
          <div className="alert-banner-head">
            <ShieldAlert className="alert-banner-icon" />
            <strong>OFFICIAL IMD WARNING</strong>
          </div>
          <ul className="alert-bullet-list">
            {d.official_warnings.map((w, idx) => (
              <li key={idx}>
                <strong>{w.event || "Weather Alert"}</strong>
                {w.severity && <span className="warning-severity-tag"> ({w.severity})</span>}
                {w.headline && <p className="warning-headline-text">{w.headline}</p>}
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* 4. Compact Weather Metrics Strip */}
      {(tempVal !== null || conditionText) && (
        <div className="structured-metrics-strip glass-inset">
          <div className="metric-primary-cell">
            <WeatherVisual code={weatherCode} size="default" />
            <div className="metric-primary-text">
              <strong className="metric-temp-headline">
                {tempVal}°C
                {tempMin !== null && tempMin !== tempVal && (
                  <span className="metric-temp-range"> / {tempMin}°</span>
                )}
              </strong>
              {conditionText && <span className="metric-condition-sub">{conditionText}</span>}
            </div>
          </div>

          <div className="metric-secondary-grid">
            {feelsLike !== null && (
              <div className="metric-mini-chip" title="Feels like temperature">
                <Thermometer className="chip-icon" />
                <span>Feels {feelsLike}°C</span>
              </div>
            )}
            {rainChance !== null && rainChance > 0 && (
              <div className="metric-mini-chip" title="Rain probability">
                <CloudRain className="chip-icon" />
                <span>{rainChance}% rain</span>
              </div>
            )}
            {precMm !== null && precMm > 0 && (
              <div className="metric-mini-chip" title="Expected precipitation">
                <Droplets className="chip-icon" />
                <span>{precMm} mm</span>
              </div>
            )}
            {windSpeed !== null && (
              <div className="metric-mini-chip" title="Wind speed">
                <Wind className="chip-icon" />
                <span>{windSpeed} km/h</span>
              </div>
            )}
            {humidity !== null && (
              <div className="metric-mini-chip" title="Relative humidity">
                <Droplets className="chip-icon" />
                <span>{humidity}% hum</span>
              </div>
            )}
          </div>
        </div>
      )}

      {/* 5. Why? / Insights List (Travel Suitability Reasons) */}
      {travelReasons.length > 0 && (
        <div className="structured-section-block">
          <div className="section-block-heading">
            <Info className="section-icon" />
            <span>Key Travel Insights</span>
          </div>
          <ul className="structured-bullet-list">
            {travelReasons.map((reason, idx) => (
              <li key={idx}>{reason}</li>
            ))}
          </ul>
        </div>
      )}

      {/* 6. Agronomic / Farmer Insights */}
      {farmerItems.length > 0 && (
        <div className="structured-section-block">
          <div className="section-block-heading">
            <Lightbulb className="section-icon" />
            <span>Farming & Crop Guidance</span>
          </div>
          <ul className="structured-bullet-list">
            {farmerItems.map((item, idx) => (
              <li key={idx}>{item}</li>
            ))}
          </ul>
        </div>
      )}

      {/* 7. Official IMD Agromet / GKMS Bulletins */}
      {agrometAdvisories.length > 0 && (
        <div className="structured-section-block agromet-block glass-inset">
          <div className="section-block-heading text-primary">
            <Sparkles className="section-icon" />
            <span>Official IMD Agromet / GKMS Advisory</span>
          </div>
          <div className="agromet-advisories-container">
            {agrometAdvisories.map((adv: AgrometItem, idx: number) => (
              <div key={idx} className="agromet-advisory-item">
                <strong className="agromet-adv-title">
                  {adv.title || `Advisory for ${adv.crop || "District"}`}
                </strong>
                {adv.recommendation && (
                  <p className="agromet-adv-text">{adv.recommendation}</p>
                )}
                {adv.recommendation_regional && (
                  <p className="agromet-adv-regional">{adv.recommendation_regional}</p>
                )}
                {adv.valid_until && (
                  <span className="agromet-validity-tag">Valid until: {adv.valid_until}</span>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* 8. Packing & Practical Travel Advice */}
      {packingItems.length > 0 && (
        <div className="structured-section-block">
          <div className="section-block-heading">
            <Lightbulb className="section-icon" />
            <span>Recommended Packing</span>
          </div>
          <div className="packing-chips-wrap">
            {packingItems.map((item, idx) => (
              <span key={idx} className="packing-pill glass">
                {item}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* 9. AI Assistant Narrative Text Explanation */}
      {text && (
        <div className="structured-narrative-box">
          <p className="chat-narrative-paragraph">{text}</p>
        </div>
      )}

      {/* 10. Forecast CTA Button */}
      <div className="chat-action-footer">
        <button
          type="button"
          className="forecast-cta-btn primary-action-pill"
          onClick={handleViewForecast}
          aria-label={locationName ? `View full forecast for ${locationName}` : "View full forecast"}
        >
          <BarChart2 />
          <span>View Forecast</span>
        </button>
      </div>
    </div>
  );
}
