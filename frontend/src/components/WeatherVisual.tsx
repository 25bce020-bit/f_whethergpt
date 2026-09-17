import type { ReactNode } from "react";
import {
  Cloud,
  CloudDrizzle,
  CloudFog,
  CloudLightning,
  CloudRain,
  CloudSnow,
  CloudSun,
  Sun,
} from "./icons";

export type WeatherVisualSize =
  | "compact"
  | "small"
  | "default"
  | "medium"
  | "large"
  | "hero";

export interface WeatherVisualProps {
  code?: number;
  condition?: string;
  size?: WeatherVisualSize;
  className?: string;
  "aria-label"?: string;
  "aria-hidden"?: boolean | "true" | "false";
}

function renderWeatherIcon(code?: number, condition?: string): ReactNode {
  const cond = (condition || "").toLowerCase().trim();

  // 1. Explicit condition text mapping
  if (
    cond.includes("thunder") ||
    cond.includes("lightning") ||
    cond.includes("storm")
  ) {
    return <CloudLightning />;
  }
  if (
    cond.includes("snow") ||
    cond.includes("blizzard") ||
    cond.includes("flurr") ||
    cond.includes("sleet") ||
    cond.includes("hail") ||
    cond.includes("ice")
  ) {
    return <CloudSnow />;
  }
  if (
    cond.includes("heavy rain") ||
    cond.includes("torrential") ||
    cond.includes("violent") ||
    cond.includes("rain shower") ||
    cond.includes("moderate rain")
  ) {
    return <CloudRain />;
  }
  if (
    cond.includes("drizzle") ||
    cond.includes("light rain") ||
    cond.includes("sprinkle")
  ) {
    return <CloudDrizzle />;
  }
  if (cond.includes("rain")) {
    return <CloudRain />;
  }
  if (
    cond.includes("fog") ||
    cond.includes("mist") ||
    cond.includes("haze") ||
    cond.includes("smoke") ||
    cond.includes("dust") ||
    cond.includes("sand")
  ) {
    return <CloudFog />;
  }
  if (
    cond.includes("partly") ||
    cond.includes("mainly clear") ||
    cond.includes("few clouds")
  ) {
    return <CloudSun />;
  }
  if (cond.includes("overcast") || cond.includes("cloud")) {
    return <Cloud />;
  }
  if (
    cond.includes("clear") ||
    cond.includes("sunny") ||
    cond.includes("sun")
  ) {
    return <Sun />;
  }

  // 2. Standard WMO Weather Code mapping (0–99)
  if (code !== undefined) {
    // Thunderstorm (95: Thunderstorm, 96: with slight hail, 99: with heavy hail)
    if (code === 95 || code === 96 || code === 99) {
      return <CloudLightning />;
    }
    // Snow & snow showers (71, 73, 75: snow fall; 77: snow grains; 85, 86: snow showers)
    if ((code >= 71 && code <= 77) || code === 85 || code === 86) {
      return <CloudSnow />;
    }
    // Rain & heavy showers (61, 63, 65: rain; 66, 67: freezing rain; 80, 81, 82: rain showers)
    if ((code >= 61 && code <= 67) || (code >= 80 && code <= 82)) {
      return <CloudRain />;
    }
    // Drizzle (51, 53, 55: drizzle; 56, 57: freezing drizzle)
    if (code >= 51 && code <= 57) {
      return <CloudDrizzle />;
    }
    // Fog & depositing rime fog (45, 48)
    if (code === 45 || code === 48) {
      return <CloudFog />;
    }
    // Overcast (3)
    if (code === 3) {
      return <Cloud />;
    }
    // Mainly clear / Partly cloudy (2)
    if (code === 2) {
      return <CloudSun />;
    }
    // Clear sky (0, 1)
    if (code === 0 || code === 1) {
      return <Sun />;
    }
  }

  return <Sun />;
}

/**
 * Universal bounded weather-condition visual.
 *
 * Guaranteed bounding box:
 * - small / compact: 20px - 24px
 * - medium / default: 44px - 52px
 * - large / hero: 64px - 72px
 */
export function WeatherVisual({
  code = 0,
  condition,
  size = "default",
  className = "",
  "aria-label": ariaLabel,
  "aria-hidden": ariaHidden,
}: WeatherVisualProps) {
  const sizeClass =
    size === "compact" || size === "small"
      ? "weather-visual--small"
      : size === "large" || size === "hero"
        ? "weather-visual--large"
        : "weather-visual--medium";

  const isDecorative = ariaHidden !== undefined ? ariaHidden : !ariaLabel;

  return (
    <span
      className={`weather-visual ${sizeClass} ${className}`.trim()}
      role={ariaLabel ? "img" : undefined}
      aria-label={ariaLabel}
      aria-hidden={isDecorative ? "true" : undefined}
    >
      {renderWeatherIcon(code, condition)}
    </span>
  );
}

/** Alias export for future-proof feature development */
export const WeatherIcon = WeatherVisual;

