import { ApiError, request } from './client';
import type {
  AuthUserResponse,
  ChatResponse,
  CurrentWeather,
  DailyForecast,
  GeographicPoint,
  GisWeather,
  HourlyForecast,
  Location,
  LocationResult,
  MapWarning,
  Mode,
  VoiceChatResponse,
  VoiceTranscription,
  Warning,
} from './types';

const isMode = (value: unknown): value is Mode =>
  value === 'normal' || value === 'farmer' || value === 'researcher' || value === 'traveller';

function normalizeChatResponse(payload: unknown): ChatResponse {
  if (!payload || typeof payload !== 'object') {
    throw new ApiError('WeatherGPT returned an unexpected response. Please try again.');
  }
  const response = payload as Record<string, unknown>;
  if (
    typeof response.session_id !== 'string' ||
    !isMode(response.selected_mode) ||
    !isMode(response.active_mode) ||
    !isMode(response.display_mode) ||
    typeof response.message !== 'string' ||
    typeof response.response !== 'string'
  ) {
    throw new ApiError('WeatherGPT returned an incomplete response. Please try again.');
  }
  return response as ChatResponse;
}

export const auth = {
  me: () => request<AuthUserResponse>('/auth/me'),
  login: (email: string, password: string) =>
    request<AuthUserResponse>('/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password }),
    }),
  signup: (name: string, email: string, password: string) =>
    request<AuthUserResponse>('/auth/signup', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name: name || undefined, email, password }),
    }),
  logout: () => request<{ message: string }>('/auth/logout', { method: 'POST' }),
};

export const chat = async (message: string, session_id: string, selected_mode: Mode, language?: string) =>
  normalizeChatResponse(
    await request<unknown>('/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        message,
        session_id,
        selected_mode,
        language: language || undefined,
      }),
    })
  );

export const locations = (name: string) =>
  request<{ query: string; results: LocationResult[] }>(`/locations/search?name=${encodeURIComponent(name)}`);

export const weather = {
  currentByLocation: (name: string) =>
    request<{ location: Location; weather: CurrentWeather }>(`/weather/current-by-location?name=${encodeURIComponent(name)}`),
  forecast: (name: string) =>
    request<{ location: Location; forecast: DailyForecast[] }>(`/weather/forecast-by-location?name=${encodeURIComponent(name)}`),
  hourly: (name: string) =>
    request<{ location: Location; hourly_forecast: HourlyForecast[] }>(`/weather/hourly-by-location?name=${encodeURIComponent(name)}`),
  warnings: (latitude: number, longitude: number) =>
    request<{ warnings: Warning[] }>(`/weather/official-warnings?latitude=${latitude}&longitude=${longitude}`),
  advisory: (name: string) =>
    request<{ location: Location; advisories: string[]; forecast_used: unknown[] }>(
      `/weather/advisory-by-location?name=${encodeURIComponent(name)}`
    ),
};

export const gis = {
  current: (name: string) => request<GisWeather>(`/gis/weather/current?name=${encodeURIComponent(name)}`),
  currentAt: (latitude: number, longitude: number) =>
    request<GisWeather>(`/gis/weather/current?latitude=${latitude}&longitude=${longitude}`),
  forecast: (name: string) =>
    request<{ location: GeographicPoint; forecast: DailyForecast[]; map: { latitude: number; longitude: number } }>(
      `/gis/weather/forecast?name=${encodeURIComponent(name)}`
    ),
  forecastAt: (latitude: number, longitude: number) =>
    request<{ location: GeographicPoint; forecast: DailyForecast[]; map: { latitude: number; longitude: number } }>(
      `/gis/weather/forecast?latitude=${latitude}&longitude=${longitude}`
    ),
  hourly: (name: string) =>
    request<{ location: GeographicPoint; hourly: HourlyForecast[]; map: { latitude: number; longitude: number } }>(
      `/gis/weather/hourly?name=${encodeURIComponent(name)}`
    ),
  hourlyAt: (latitude: number, longitude: number) =>
    request<{ location: GeographicPoint; hourly: HourlyForecast[]; map: { latitude: number; longitude: number } }>(
      `/gis/weather/hourly?latitude=${latitude}&longitude=${longitude}`
    ),
  location: (query: string) => request<GeographicPoint>(`/gis/location?query=${encodeURIComponent(query)}`),
  warnings: () => request<{ source: string; official: boolean; alerts: MapWarning[] }>('/gis/warnings'),
};

function voiceForm(audio: Blob, sessionId: string, language?: string, selected_mode?: Mode) {
  const data = new FormData();
  data.append('audio', audio, audio.type.includes('ogg') ? 'voice.ogg' : 'voice.webm');
  data.append('session_id', sessionId);
  if (language) {
    data.append('language', language);
  }
  if (selected_mode) {
    data.append('selected_mode', selected_mode);
  }
  return data;
}

export const voice = {
  transcribe: (audio: Blob, sessionId: string, language?: string) =>
    request<VoiceTranscription>('/voice/transcribe', {
      method: 'POST',
      body: voiceForm(audio, sessionId, language),
    }),
  chat: (audio: Blob, sessionId: string, language?: string, selected_mode?: Mode) =>
    request<VoiceChatResponse>('/voice/chat', {
      method: 'POST',
      body: voiceForm(audio, sessionId, language, selected_mode),
    }),
};

