import type { Location, LocationResult } from './api/types';

const STORAGE_KEY = 'weathergpt_selected_location';

export interface SelectedLocation {
  name: string;
  latitude: number;
  longitude: number;
  country: string | null;
  state: string | null;
}

export function selectLocation(location: LocationResult | Location): SelectedLocation | null {
  if (location.latitude === undefined || location.longitude === undefined) return null;
  const selected: SelectedLocation = {
    name: location.name,
    latitude: location.latitude,
    longitude: location.longitude,
    country: location.country ?? null,
    state: 'state' in location ? location.state ?? null : location.admin1 ?? null,
  };
  sessionStorage.setItem(STORAGE_KEY, JSON.stringify(selected));
  return selected;
}

export function getSelectedLocation(): SelectedLocation | null {
  try {
    const value: unknown = JSON.parse(sessionStorage.getItem(STORAGE_KEY) ?? 'null');
    if (!value || typeof value !== 'object') return null;
    const location = value as Record<string, unknown>;
    return typeof location.name === 'string' && typeof location.latitude === 'number' && typeof location.longitude === 'number'
      ? { name: location.name, latitude: location.latitude, longitude: location.longitude, country: typeof location.country === 'string' ? location.country : null, state: typeof location.state === 'string' ? location.state : null }
      : null;
  } catch { return null; }
}
