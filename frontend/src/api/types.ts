export type Mode = 'normal' | 'farmer' | 'researcher' | 'traveller';
export interface User { id: number; name: string | null; email: string; created_at: string }
export interface AuthUserResponse { user: User }
export interface Location { name: string; country: string | null; state: string | null; latitude?: number; longitude?: number }
export interface CurrentWeather { time: string; temperature_c: number; feels_like_c: number; humidity_percent: number; precipitation_mm: number; weather_code: number; condition: string; wind_speed_kmh: number; wind_direction_degrees: number; timezone: string }
export interface DailyForecast { date: string; condition: string; weather_code: number; temperature_max_c: number; temperature_min_c: number; precipitation_mm: number; wind_speed_max_kmh: number }
export interface HistoricalDaily { date: string; weather_code: number; temperature_max_c: number; temperature_min_c: number; precipitation_mm: number; wind_speed_max_kmh: number }
export interface HourlyForecast { time: string; temperature_c: number; humidity_percent: number; rain_probability_percent: number; precipitation_mm: number; condition: string; weather_code: number; wind_speed_kmh: number }
export interface Warning { identifier?: string; event?: string; severity?: string; headline?: string; description?: string; instruction?: string }
export interface GeographicPoint { latitude: number; longitude: number; name: string | null; country: string | null; state: string | null }
export interface MapWarning { id: string | null; title: string | null; event: string | null; severity: string | null; sent_at: string | null; source: 'IMD'; official: boolean; coordinates_available: boolean; location: GeographicPoint | null }
export interface ChatTool { tool?: string; reason?: string }
export interface AgrometItem { crop?: string; title?: string; recommendation?: string; recommendation_regional?: string; valid_until?: string }
export interface AgrometAdvisoryData { district?: string; state?: string; advisories?: AgrometItem[] }
export interface ChatUnderstanding { intent?: string; location?: string | null; time?: string | null; activity?: string | null; language?: string; topic?: string }
export interface Advisory { type: string; severity: string; message: string }
export interface FarmerAdvisory { today_advisory?: string[]; agromet_advisory?: AgrometAdvisoryData }
export interface TravellerAdvisory { suitability?: { status: string; reasons: string[] }; packing?: string[] }
export interface ChatResponse { session_id: string; selected_mode: Mode; active_mode: Mode; display_mode: Mode; message: string; response: string; language?: string; script?: string; mode_mismatch?: boolean; suggested_mode?: Mode; understanding?: ChatUnderstanding; tool?: ChatTool; location?: Location; weather?: CurrentWeather; forecast?: DailyForecast[]; hourly_forecast?: HourlyForecast[]; historical_weather?: HistoricalDaily[]; climate?: { period: 'last_7_days'; average_temperature_c: number | null }; official_warnings?: Warning[]; official_agromet?: AgrometAdvisoryData; advisories?: Advisory[]; recommendations?: string[]; farmer_advisory?: FarmerAdvisory; traveller_advisory?: TravellerAdvisory; [key: string]: unknown }
export interface LocationResult { name: string; latitude: number; longitude: number; country?: string | null; admin1?: string | null }
export interface GisWeather { location: GeographicPoint; weather: CurrentWeather; map: { latitude: number; longitude: number }; marker: { id: string; latitude: number; longitude: number; title: string; weather: CurrentWeather } }
export interface VoiceTranscription { success: true; transcript: string; language: string; session_id: string }
export interface VoiceChatResponse extends VoiceTranscription { response: string; chat: ChatResponse; tts: { provider: string; language: string; locale: string } }
