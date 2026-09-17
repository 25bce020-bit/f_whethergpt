import { useCallback, useEffect, useRef, useState } from "react";
import type { FormEvent, ReactNode } from "react";
import {
  AlertTriangle,
  ArrowLeft,
  ArrowUp,
  CloudRain,
  CloudSun,
  Droplets,
  Lightbulb,
  MapPin,
  Mic,
  Send,
  ShieldAlert,
  Sparkles,
  Thermometer,
  Volume2,
  Wind,
} from "./components/icons";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import type { AuthState } from "./App";
import type {
  ChatResponse,
  CurrentWeather,
  DailyForecast,
  HourlyForecast,
  Location,
  LocationResult,
  MapWarning,
  Mode,
  Warning,
} from "./api/types";
import { auth, chat, gis, locations, voice, weather } from "./api/services";
import { getChatSession } from "./chatSession";
import { getSelectedLocation, selectLocation } from "./locationSelection";
import { WeatherMap } from "./components/WeatherMap";
import { WeatherVisual } from "./components/WeatherVisual";
import { StructuredResponse } from "./components/StructuredResponse";
import { SuggestedPrompts } from "./components/SuggestedPrompts";
import { saveVoiceConversation, takeVoiceConversation } from "./voiceConversation";
import type { Theme } from "./theme";

const modes: Mode[] = ["normal", "farmer", "researcher", "traveller"];
const modeLabel = (m: Mode) => m[0].toUpperCase() + m.slice(1);

function Back({ title }: { title: string }) {
  const navigate = useNavigate();
  const goBack = () => {
    if (window.history.length > 1) navigate(-1);
    else navigate("/", { replace: true });
  };
  return (
    <div className="page-title-row">
      <button
        className="icon-button page-back-btn"
        type="button"
        onClick={goBack}
        aria-label="Go back"
      >
        <ArrowLeft />
      </button>
      <h1 className="page-main-heading">{title}</h1>
    </div>
  );
}

function LocationSearch({
  onSelect,
  placeholder = "Search a location (e.g. Ahmedabad, Mumbai, Tokyo)",
}: {
  onSelect: (location: LocationResult) => void;
  placeholder?: string;
}) {
  const [query, setQuery] = useState("");
  const [items, setItems] = useState<LocationResult[]>([]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  async function find(e: FormEvent) {
    e.preventDefault();
    if (query.trim().length < 2) return;
    setBusy(true);
    setError("");
    try {
      const data = await locations(query.trim());
      setItems(data.results.slice(0, 5));
      if (data.results.length === 0) {
        setError("No matching locations found.");
      }
      if (data.results.length === 1) {
        setQuery(data.results[0].name);
        setItems([]);
        onSelect(data.results[0]);
      }
    } catch (e) {
      setItems([]);
      setError(e instanceof Error ? e.message : "Unable to search locations.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <form className="location-search-form" onSubmit={find}>
      <div className="location-search-input-wrap glass">
        <span className="search-pin-icon">
          <MapPin />
        </span>
        <input
          className="search-text-input"
          value={query}
          onChange={(e) => {
            setQuery(e.target.value);
            if (error) setError("");
          }}
          placeholder={placeholder}
          aria-label="Search location"
        />
        <button
          className="search-submit-btn"
          type="submit"
          aria-label="Search"
          disabled={busy || !query.trim()}
        >
          {busy ? "…" : <ArrowUp />}
        </button>
      </div>

      {items.length > 0 && (
        <div
          className="search-dropdown-menu glass-raised"
          role="listbox"
          aria-label="Location suggestions"
        >
          {items.map((item, i) => (
            <button
              key={`${item.name}-${item.latitude}-${item.longitude}-${i}`}
              type="button"
              className="search-dropdown-item"
              role="option"
              onClick={() => {
                setQuery(item.name);
                setItems([]);
                onSelect(item);
              }}
            >
              <span className="search-item-primary">{item.name}</span>
              <span className="search-item-secondary">
                {[item.admin1, item.country].filter(Boolean).join(", ")}
              </span>
            </button>
          ))}
        </div>
      )}
      {error && <div className="search-error-message">{error}</div>}
    </form>
  );
}

function Message({
  message,
  userQuery,
  onSwitchMode,
  onPromptSelect,
}: {
  message: { role: "user" | "ai"; text: string; data?: ChatResponse };
  userQuery?: string;
  onSwitchMode?: (mode: Mode) => void;
  onPromptSelect?: (prompt: string) => void;
}) {
  const d = message.data;
  const isUser = message.role === "user";

  return (
    <article className={`chat-message-row ${isUser ? "chat-message-row--user" : "chat-message-row--ai"}`}>
      {!isUser && (
        <div className="chat-avatar-badge" aria-hidden="true">
          <CloudSun />
        </div>
      )}
      <div className="chat-bubble-container">
        {isUser ? (
          <div className="chat-bubble-text">
            <p>{message.text}</p>
          </div>
        ) : (
          <>
            {d?.mode_mismatch && d.suggested_mode && (
              <div className="mode-mismatch-action-box glass">
                <span className="mode-mismatch-note">
                  Suggested mode: <strong>{modeLabel(d.suggested_mode)}</strong>
                </span>
                {onSwitchMode && (
                  <button
                    type="button"
                    className="mode-mismatch-switch-btn primary-action-pill"
                    onClick={() => onSwitchMode(d.suggested_mode!)}
                  >
                    Switch to {modeLabel(d.suggested_mode)}
                  </button>
                )}
              </div>
            )}

            <StructuredResponse
              text={message.text}
              data={d}
              mode={d?.active_mode ?? d?.selected_mode}
            />

            {d?.hourly_forecast && d.hourly_forecast.length > 0 && (
              <div className="chat-structured-card glass">
                <div className="chat-card-title">
                  <Sparkles />
                  <span>Hourly Forecast</span>
                </div>
                <HourlyStrip items={d.hourly_forecast} />
                {d.location?.name && (
                  <div className="chat-card-action">
                    <Link
                      className="primary-action-pill"
                      to={`/forecast?location=${encodeURIComponent(d.location.name)}`}
                    >
                      View Full Forecast
                    </Link>
                  </div>
                )}
              </div>
            )}

            {d?.forecast && d.forecast.length > 0 && (
              <div className="chat-structured-card glass">
                <div className="chat-card-title">
                  <CloudSun />
                  <span>Daily Outlook</span>
                </div>
                <ForecastStrip
                  items={d.forecast}
                  locationName={d.location?.name}
                  mode={d.active_mode ?? "normal"}
                  language={d.language as string | undefined}
                  script={d.script as string | undefined}
                  warnings={d.official_warnings}
                />
              </div>
            )}

            {onPromptSelect && (
              <SuggestedPrompts
                query={userQuery || message.text}
                mode={d?.active_mode || d?.selected_mode}
                locationName={d?.location?.name || (typeof d?.understanding?.location === "string" ? d.understanding.location : "")}
                language={d?.language}
                script={d?.script}
                hasRain={Boolean(d?.understanding?.topic === "rain" || (d?.weather?.precipitation_mm && d.weather.precipitation_mm > 0))}
                isTravel={Boolean(d?.active_mode === "traveller" || d?.understanding?.topic === "travel" || d?.traveller_advisory)}
                isFarmer={Boolean(d?.active_mode === "farmer" || d?.understanding?.topic === "farming" || d?.farmer_advisory)}
                onPromptSelect={onPromptSelect}
              />
            )}
          </>
        )}
      </div>
    </article>
  );
}

export function ChatPage() {
  const [mode, setMode] = useState<Mode>("normal");
  const [text, setText] = useState("");
  const [messages, setMessages] = useState<
    { role: "user" | "ai"; text: string; data?: ChatResponse }[]
  >(() => {
    const conversation = takeVoiceConversation();
    return conversation
      ? [
          { role: "user", text: conversation.transcript },
          { role: "ai", text: conversation.response.response, data: conversation.response },
        ]
      : [];
  });
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [lastFailed, setLastFailed] = useState<{
    message: string;
    mode: Mode;
  } | null>(null);
  const [showModes, setShowModes] = useState(true);
  const scrollRef = useRef<HTMLDivElement>(null);
  const lastScrollTop = useRef(0);

  useEffect(() => {
    const el = scrollRef.current;
    if (!el) return;
    const onScroll = () => {
      const up = el.scrollTop < lastScrollTop.current;
      setShowModes(!(up && el.scrollTop > 50));
      lastScrollTop.current = el.scrollTop;
    };
    el.addEventListener("scroll", onScroll, { passive: true });
    return () => el.removeEventListener("scroll", onScroll);
  }, []);

  const scrollToBottom = useCallback((smooth = true) => {
    if (scrollRef.current) {
      scrollRef.current.scrollTo({
        top: scrollRef.current.scrollHeight,
        behavior: smooth ? "smooth" : "auto",
      });
    }
  }, []);

  const sendMessage = async (
    value: string,
    selectedMode: Mode,
    showUserMessage: boolean,
  ) => {
    if (busy) return;
    setError("");
    setLastFailed(null);
    if (showUserMessage) {
      setMessages((m) => [...m, { role: "user", text: value }]);
    }
    setBusy(true);
    setTimeout(() => scrollToBottom(), 50);

    try {
      const response = await chat(value, getChatSession(), selectedMode);
      if (response.location) {
        selectLocation(response.location);
      }
      setMessages((m) => [
        ...m,
        { role: "ai", text: response.response, data: response },
      ]);
    } catch (e) {
      setLastFailed({ message: value, mode: selectedMode });
      setError(e instanceof Error ? e.message : "Unable to complete request.");
    } finally {
      setBusy(false);
      setTimeout(() => scrollToBottom(), 100);
    }
  };

  async function handleSend(e: FormEvent) {
    e.preventDefault();
    const value = text.trim();
    if (!value || busy) return;
    setText("");
    await sendMessage(value, mode, true);
  }

  const promptSuggestions = [
    { label: "Current weather in Ahmedabad", prompt: "What is the current weather in Ahmedabad?" },
    { label: "3-day forecast for Mumbai", prompt: "What is the 3-day forecast for Mumbai?" },
    { label: "Travel suitability for Delhi", prompt: "Is it a good time to travel to Delhi right now?" },
  ];

  return (
    <div className="chat-page-layout">
      <div className="chat-scroll-area" ref={scrollRef}>
        {messages.length === 0 && (
          <section className="chat-welcome-hero">
            <div className="hero-orb-visual">
              <CloudSun />
            </div>
            <p className="hero-eyebrow">ATMOSPHERIC INTELLIGENCE</p>
            <h1 className="hero-heading">Weather, with a clearer point of view.</h1>
            <p className="hero-subtext">
              Real-time atmospheric conditions, tailored agricultural insights, research datasets, and travel recommendations.
            </p>

            <div className="suggestion-chips-grid">
              {promptSuggestions.map((suggestion) => (
                <button
                  key={suggestion.label}
                  type="button"
                  className="suggestion-chip glass"
                  onClick={() => {
                    setText(suggestion.prompt);
                    void sendMessage(suggestion.prompt, mode, true);
                  }}
                >
                  <Sparkles />
                  <span>{suggestion.label}</span>
                </button>
              ))}
            </div>
          </section>
        )}

        <div className="chat-feed-container">
          {messages.map((m, i) => {
            const prevUserQuery =
              i > 0 && messages[i - 1]?.role === "user"
                ? messages[i - 1].text
                : undefined;
            return (
              <Message
                key={i}
                message={m}
                userQuery={prevUserQuery}
                onSwitchMode={(targetMode) => setMode(targetMode)}
                onPromptSelect={(prompt) => {
                  void sendMessage(prompt, mode, true);
                }}
              />
            );
          })}

          {busy && (
            <article className="chat-message-row chat-message-row--ai">
              <div className="chat-avatar-badge" aria-hidden="true">
                <CloudSun />
              </div>
              <div className="chat-bubble-container">
                <div className="chat-bubble-text loading-shimmer">
                  <p>WeatherGPT is thinking…</p>
                </div>
              </div>
            </article>
          )}

          {error && (
            <div className="chat-error-banner" role="alert">
              <div className="error-copy">
                <ShieldAlert />
                <span>{error}</span>
              </div>
              <div className="error-actions">
                {lastFailed && (
                  <button
                    type="button"
                    className="error-retry-btn"
                    onClick={() =>
                      void sendMessage(lastFailed.message, lastFailed.mode, false)
                    }
                    disabled={busy}
                  >
                    Retry
                  </button>
                )}
                <button
                  type="button"
                  className="error-dismiss-btn"
                  onClick={() => {
                    setError("");
                    setLastFailed(null);
                  }}
                >
                  Dismiss
                </button>
              </div>
            </div>
          )}
        </div>
      </div>

      <div className="composer-floating-zone">
        <div className="composer-box-container">
          <form className="composer-form glass-raised" onSubmit={handleSend}>
            <Link to="/voice" className="composer-mic-action" aria-label="Use voice input">
              <Mic />
            </Link>
            <input
              className="composer-input"
              value={text}
              onChange={(e) => setText(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter" && !e.shiftKey) {
                  e.preventDefault();
                  e.currentTarget.form?.requestSubmit();
                }
              }}
              placeholder="Ask WeatherGPT anything about the weather…"
              disabled={busy}
              aria-label="Chat input message"
            />
            <button
              className="composer-submit-btn"
              type="submit"
              disabled={!text.trim() || busy}
              aria-label="Send message"
            >
              <Send />
            </button>
          </form>

          <div className={`mode-selector-strip ${showModes ? "mode-selector--visible" : "mode-selector--hidden"}`}>
            {modes.map((m) => (
              <button
                key={m}
                type="button"
                className={`mode-segmented-btn ${mode === m ? "selected" : ""}`}
                onClick={() => setMode(m)}
                aria-pressed={mode === m}
              >
                {modeLabel(m)}
              </button>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

export function WeatherMini({
  weather: w,
  location,
}: {
  weather: CurrentWeather;
  location?: Location;
}) {
  return (
    <div className="weather-mini-card glass">
      <div className="weather-mini-glyph">
        <WeatherVisual code={w.weather_code} size="compact" />
      </div>
      <div className="weather-mini-meta">
        <span className="weather-mini-location">
          {location?.name ?? "Current weather"} · {w.condition}
        </span>
        <strong className="weather-mini-temp">
          {Math.round(w.temperature_c)}°C
        </strong>
      </div>
      <div className="weather-mini-feels">
        <span>Feels {Math.round(w.feels_like_c)}°</span>
      </div>
    </div>
  );
}

function generateDailyAdvice(
  day: DailyForecast,
  mode: Mode = "normal",
  language: string = "en",
  script: string = "latin"
): string {
  const code = day.weather_code;
  const prec = day.precipitation_mm ?? 0;
  const tMax = day.temperature_max_c ?? 25;
  const wind = day.wind_speed_max_kmh ?? 10;
  const condLower = (day.condition || "").toLowerCase();

  const isThunderstorm = code === 95 || code === 96 || code === 99 || condLower.includes("thunderstorm");
  const isHeavyRain = prec >= 5.0 || condLower.includes("heavy") || condLower.includes("violent");
  const isLightRain = prec > 0.0 || condLower.includes("rain") || condLower.includes("shower") || condLower.includes("drizzle");
  const isHeat = tMax >= 38.0;
  const isWindy = wind >= 25.0;

  let langKey = "en";
  if (language === "gu" && script === "latin") langKey = "gu-latin";
  else if (language === "gu") langKey = "gu";
  else if (language === "hi" && script === "latin") langKey = "hi-latin";
  else if (language === "hi") langKey = "hi";
  else if (language === "mr" && script === "latin") langKey = "mr-latin";
  else if (["bn", "ta", "te", "kn", "ml", "pa", "or", "mr"].includes(language)) langKey = language;

  if (isThunderstorm) {
    if (langKey === "gu-latin") {
      if (mode === "farmer") return "Toofan ane varsad ni sambhavna che; kheti na kam ma savcheti rakhvo ane pashuo ane pak ne surakshit rakhvo.";
      if (mode === "researcher") return "Thunderstorm conditions expected; atmospheric variance ane electrical activity monitor karvo.";
      if (mode === "traveller") return "Toofan na lidhe transit delay thai shake che; exposed open routes avoid karva.";
      return "Toofan ane varsad ni sambhavna che; bahar jata savcheti rakhvo ane umbrella sathe rakhvo.";
    }
    if (langKey === "gu") {
      if (mode === "farmer") return "તોફાનની શક્યતા છે; ખેતીના કામમાં સાવધાની રાખવી અને પશુઓ તેમજ પાકનું રક્ષણ કરવું.";
      if (mode === "researcher") return "ગાજવીજ સાથે વાતાવરણમાં વિદ્યુત ગતિવિધિ નોંધાઈ શકે છે; સાધનો સુરક્ષિત રાખવા.";
      if (mode === "traveller") return "ગાજવીજને કારણે મુસાફરીમાં વિલંબ થઈ શકે છે; ખુલ્લા માર્ગો ટાળવા.";
      return "ગાજવીજ સાથે વરસાદની શક્યતા છે; બહાર જતી વખતે સાવચેતી રાખવી અને છત્રી સાથે રાખવી.";
    }
    if (langKey === "hi-latin") {
      if (mode === "farmer") return "Toofan aur baarish ki aashanka hai; kheton me savdhani bartein aur fasal ka dhyan rakhein.";
      if (mode === "researcher") return "Thunderstorm activity expected; atmospheric fluctuations monitor karein.";
      if (mode === "traveller") return "Toofan ke chalte transit me delay ho sakta hai; savdhani se yatra karein.";
      return "Toofan aur baarish ki sambhavna hai; bahar nikalte samay umbrella saath rakhein aur savdhaan rahein.";
    }
    if (langKey === "hi") {
      if (mode === "farmer") return "तूफान और बारिश की संभावना है; खेतों में काम टालें और फसलों को सुरक्षित करें।";
      if (mode === "researcher") return "तूफानी गतिविधि के संकेत हैं; वायुमंडलीय उपकरणों की सुरक्षा सुनिश्चित करें।";
      if (mode === "traveller") return "तूफान से यात्रा में देरी हो सकती है; खुले रास्तों से बचें और सतर्क रहें।";
      return "गरज के साथ बारिश की संभावना है; खुले स्थानों से बचें और सावधानी बरतें।";
    }
    if (langKey === "bn") return "বজ্রবিদ্যুৎসহ বৃষ্টির সম্ভাবনা রয়েছে; বাইরে যাওয়ার সময় সতর্কতা অবলম্বন করুন।";
    if (langKey === "ta") return "இடிமின்னலுடன் கூடிய மழைக்கு வாய்ப்புள்ளது; வெளியில் செல்லும்போது குடை எடுத்துச் செல்லவும்.";
    if (langKey === "mr") return "विजांच्या कडकडाटासह वादळाची शक्यता; बाहेर पडताना छत्री सोबत ठेवा आणि काळजी घ्या.";
    if (mode === "farmer") return "Delay field operations and safeguard exposed crops and equipment during thunderstorms.";
    if (mode === "researcher") return "Thunderstorm conditions expected; monitor electrical and atmospheric fluctuations.";
    if (mode === "traveller") return "Thunderstorms likely; avoid exposed transit routes and expect travel delays.";
    return "Use caution outdoors and avoid exposed areas during possible thunderstorms.";
  }

  if (isHeavyRain) {
    if (langKey === "gu-latin") {
      if (mode === "farmer") return "Bhari varsad expected che; drainage check karvo ane pesticide spray delay karvo.";
      if (mode === "researcher") return "Significant precipitation window; field sensors ne rain protection aapo.";
      if (mode === "traveller") return "Varsad na lidhe traffic ane travel delay thai shake che; extra travel buffer rakhvo.";
      return "Bhari varsad ni sambhavna che; bahar jata umbrella sathe rakhvo ane wet conditions mate plan karvo.";
    }
    if (langKey === "gu") {
      if (mode === "farmer") return "ભારે વરસાદની શક્યતા છે; ખેતરમાં નિકાસ વ્યવસ્થા તપાસવી અને દવાનો છંટકાવ મોકૂફ રાખવો.";
      if (mode === "researcher") return "નોંધપાત્ર વરસાદની શક્યતા; ફિલ્ડ સાધનોને વરસાદથી રક્ષણ આપવું.";
      if (mode === "traveller") return "વરસાદને કારણે પ્રવાસમાં વધુ સમય લાગી શકે છે; રેઈન ગિયર સાથે રાખવું.";
      return "ભારે વરસાદની શક્યતા છે; છત્રી સાથે રાખવી અને ભીના વાતાવરણ માટે તૈયાર રહેવું.";
    }
    if (langKey === "hi-latin") {
      if (mode === "farmer") return "Bhari baarish ho sakti hai; drainage check karein aur spray delay karein.";
      if (mode === "researcher") return "High rainfall anticipated; sensor equipment ko wet exposure se bachayein.";
      if (mode === "traveller") return "Baarish se travel time badh sakta hai; rain gear saath rakhein.";
      return "Bhari baarish ho sakti hai; bahar jaate samay umbrella saath rakhein.";
    }
    if (langKey === "hi") {
      if (mode === "farmer") return "भारी बारिश की संभावना है; जल निकासी की व्यवस्था करें और छिड़काव रोकें।";
      if (mode === "researcher") return "भारी वर्षा का अनुमान है; फील्ड उपकरणों को वर्षा से सुरक्षित रखें।";
      if (mode === "traveller") return "बारिश से यात्रा में अतिरिक्त समय लग सकता है; रेन गियर साथ रखें।";
      return "भारी बारिश की संभावना है; बाहर जाते समय छाता साथ रखें और सुरक्षित रहें।";
    }
    if (langKey === "bn") return "ভারী বৃষ্টির সম্ভাবনা; ছাতা সঙ্গে রাখুন এবং সতর্ক থাকুন।";
    if (langKey === "ta") return "கனமழை பெய்ய வாய்ப்புள்ளது; வெளியில் செல்லும்போது குடை எடுத்துச் செல்லவும்.";
    if (langKey === "mr") return "मुसळधार पावसाची शक्यता; बाहेर पडताना रेनकोट किंवा छत्री सोबत ठेवा.";
    if (mode === "farmer") return "Moderate-to-heavy rain expected; monitor field drainage and delay spraying.";
    if (mode === "researcher") return "Significant precipitation window; plan equipment protection for field sensors.";
    if (mode === "traveller") return "Carry rain gear and allow extra travel buffer for wet road conditions.";
    return "Rain is expected; carry an umbrella and plan for wet outdoor conditions.";
  }

  if (isLightRain) {
    if (langKey === "gu-latin") {
      if (mode === "farmer") return "Halka chanta aavi shake che; sinchai karta pehla matini bhej jarur check karvi.";
      if (mode === "researcher") return "Intermittent light precipitation expected during the forecast period.";
      if (mode === "traveller") return "Halka varsad na chanta thai shake che; light rain protection sathe rakhvo.";
      return "Halko varsad aavi shake che; umbrella sathe rakhvu faydamand rehse.";
    }
    if (langKey === "gu") {
      if (mode === "farmer") return "હળવા ઝાપટાં પડી શકે છે; પિયત આપતા પહેલા જમીનમાં ભેજનું પ્રમાણ તપાસવું.";
      if (mode === "researcher") return "હળવા ઝાપટાંની શક્યતા; વાતાવરણીય ભેજ અને વરસાદના આંકડા મોનિટર કરવા.";
      if (mode === "traveller") return "હળવો વરસાદ થઈ શકે છે; હળવું રેઈન ગિયર સાથે રાખવું.";
      return "હળવા વરસાદની શક્યતા છે; બહાર નીકળતી વખતે છત્રી સાથે રાખવી યોગ્ય રહેશે.";
    }
    if (langKey === "hi-latin") {
      if (mode === "farmer") return "Halki boondabandi ho sakti hai; sinchai se pehle soil moisture check karein.";
      if (mode === "researcher") return "Light intermittent showers expected across the observation period.";
      if (mode === "traveller") return "Halki baarish ho sakti hai; light rain gear saath rakhein.";
      return "Halki baarish ki sambhavna hai; umbrella saath rakhna theek rahega.";
    }
    if (langKey === "hi") {
      if (mode === "farmer") return "हल्की बारिश के आसार हैं; सिंचाई से पहले मिट्टी की नमी की जांच करें।";
      if (mode === "researcher") return "हल्की बौछारों का अनुमान है; नमी में उतार-चढ़ाव दर्ज करें।";
      if (mode === "traveller") return "हल्की बारिश हो सकती है; हल्का रेन गियर साथ रखें।";
      return "हल्की बारिश के आसार हैं; छाता साथ रखना मददगार रहेगा।";
    }
    if (langKey === "bn") return "হালকা বৃষ্টির সম্ভাবনা রয়েছে; ছাতা সঙ্গে রাখা ভালো।";
    if (langKey === "ta") return "லேசான மழைக்கு வாய்ப்புள்ளது; குடை எடுத்துச் செல்வது நல்லது.";
    if (langKey === "mr") return "हलक्या पावसाची शक्यता; सोबत छत्री ठेवणे सोयीचे ठरेल.";
    if (mode === "farmer") return "Light showers possible; verify soil moisture before scheduled irrigation.";
    if (mode === "researcher") return "Intermittent light precipitation expected during the forecast period.";
    if (mode === "traveller") return "Light showers possible; keep light rain protection available.";
    return "Light rain is possible; carrying an umbrella is recommended.";
  }

  if (isHeat) {
    if (langKey === "gu-latin") {
      if (mode === "farmer") return "Gharmi vadhu rehse; kheti na kam saware ke sanje karva hithavah che.";
      if (mode === "researcher") return "High daytime temperature; sensor thermal limits dhyan ma rakhva.";
      if (mode === "traveller") return "Bapore garmi vadhu rehse; hydration dhyan ma rakhvo ane early sightseeing plan karvo.";
      return "Bapore tapman vadhu rehse; purti matra ma pani pivu ane dhup thi bachvu.";
    }
    if (langKey === "gu") {
      if (mode === "farmer") return "ગરમી વધુ રહેશે; ખેતીના કાર્યો વહેલી સવારે અથવા સાંજે કરવા હિતાવહ છે.";
      if (mode === "researcher") return "ઉચ્ચ તાપમાનની શક્યતા; થર્મલ ડેટા કલેક્શન માટે યોગ્ય આયોજન કરવું.";
      if (mode === "traveller") return "બપોરે તડકો વધુ રહેશે; હાઇડ્રેશન જાળવવું અને સવારે ફરવાનું આયોજન કરવું.";
      return "તાપમાન વધુ રહેવાની શક્યતા છે; પૂરતું પાણી પીવું અને બપોરના તડકાથી બચવું.";
    }
    if (langKey === "hi-latin") {
      if (mode === "farmer") return "Garmi zyada rahegi; kheti ke kaam subah ya shaam ko karein.";
      if (mode === "researcher") return "High ambient temperature; monitor thermal drift in sensors.";
      if (mode === "traveller") return "Dopehar me dhoop tez rahegi; hydration banaye rakhein.";
      return "Tapman zyada rahega; paani peete rahein aur dhoop se bachein.";
    }
    if (langKey === "hi") {
      if (mode === "farmer") return "अधिक तापमान रहेगा; खेतों में काम सुबह या शाम को करना बेहतर होगा।";
      if (mode === "researcher") return "उच्च तापमान की स्थिति; उपकरणों के थर्मल ड्रिफ्ट पर नजर रखें।";
      if (mode === "traveller") return "दोपहर में तेज धूप रहेगी; पर्याप्त पानी पिएं और सावधानी बरतें।";
      return "अधिक तापमान रहने की संभावना है; पर्याप्त पानी पिएं और धूप से बचें।";
    }
    if (langKey === "bn") return "উচ্চ তাপমাত্রার সম্ভাবনা; প্রচুর জল পান করুন এবং রোদ এড়িয়ে চলুন।";
    if (langKey === "ta") return "வெப்பநிலை அதிகமாக இருக்கும்; போதுமான தண்ணீர் குடித்து நீரேற்றத்துடன் இருங்கள்.";
    if (langKey === "mr") return "तापमान अधिक राहण्याचा अंदाज; भरपूर पाणी प्या आणि उन्हापासून बचाव करा.";
    if (mode === "farmer") return "Peak daytime heat; schedule field tasks during cooler morning hours.";
    if (mode === "researcher") return "Elevated thermal conditions; account for temperature impact on field measurements.";
    if (mode === "traveller") return "High daytime heat; stay well hydrated and plan outdoor sightseeing early.";
    return "High temperatures expected; stay hydrated and limit prolonged outdoor heat exposure.";
  }

  if (isWindy) {
    if (langKey === "gu-latin") {
      if (mode === "farmer") return "Tez pavan fookashe; spraying avoid karvo ane uncha pak ne support aapo.";
      if (mode === "researcher") return "Elevated wind velocity; sampling devices ma turbulence dhyan ma rakhvu.";
      if (mode === "traveller") return "Pavan vadhu rehse; open highway transit ma drive savcheti thi karvu.";
      return "Pavan ni gati vadhu rehse; bahar na kam ma savcheti rakhvi.";
    }
    if (langKey === "gu") {
      if (mode === "farmer") return "તેજ પવનને કારણે દવાનો છંટકાવ ટાળવો અને ઊંચા પાકને ટેકો આપવો.";
      if (mode === "researcher") return "પવનની ગતિ વધુ રહેશે; સેમ્પલિંગ અને માપનમાં પવનની અસર ધ્યાને લેવી.";
      if (mode === "traveller") return "પવન વધુ રહેશે; ખુલ્લા માર્ગો પર વાહન ચલાવતી વખતે સાવચેતી રાખવી.";
      return "તેજ પવન ફૂંકાવાની શક્યતા છે; બહારની પ્રવૃત્તિઓમાં સાવચેતી રાખવી.";
    }
    if (langKey === "hi-latin") {
      if (mode === "farmer") return "Tez hawayein chalengi; spraying se bachein aur unchi fasal ko sahara dein.";
      if (mode === "researcher") return "High wind speed expected; secure external measurement rigs.";
      if (mode === "traveller") return "Hawayein tez rahengi; highway driving me savdhani bartein.";
      return "Tez hawayein chalengi; outdoor activities me savdhani rakhein.";
    }
    if (langKey === "hi") {
      if (mode === "farmer") return "तेज हवाएं चलेंगी; छिड़काव से बचें और फसलों को सहारा दें।";
      if (mode === "researcher") return "हवा की गति अधिक रहेगी; बाहरी मापक उपकरणों को सुरक्षित करें।";
      if (mode === "traveller") return "हवाएं तेज रहेंगी; राजमार्गों पर सावधानी से वाहन चलाएं।";
      return "तेज हवाएं चलने की संभावना है; बाहरी गतिविधियों में सावधानी बरतें।";
    }
    if (langKey === "bn") return "ঝড়ো বাতাস বইতে পারে; বাইরের কাজকর্মে সতর্ক থাকুন।";
    if (langKey === "ta") return "பலத்த காற்று வீசக்கூடும்; வெளியில் செல்லும்போது கவனமாக இருக்கவும்.";
    if (langKey === "mr") return "वेगाने वारे वाहण्याची शक्यता; बाहेरील कामांमध्ये काळजी घ्या.";
    if (mode === "farmer") return "Strong winds expected; avoid spraying and inspect structural crop supports.";
    if (mode === "researcher") return "Elevated wind velocity; account for gust interference in sampling.";
    if (mode === "traveller") return "Windy conditions; secure loose belongings and exercise caution on exposed roads.";
    return "Gusty winds expected; exercise caution with outdoor activities.";
  }

  if (langKey === "gu-latin") {
    if (mode === "farmer") return "Kheti na niyamit kam ane fasal ni dekhbhal mate havaman anukul che.";
    if (mode === "researcher") return "Stable atmospheric baseline conditions; outdoor data collection mate ideal che.";
    if (mode === "traveller") return "Havaman khullu ane anukul che; travel ane sightseeing mate uttam divas.";
    return "Havaman saru ane anukul rehse; bahar na activities mate uttam divas che.";
  }
  if (langKey === "gu") {
    if (mode === "farmer") return "ખેતીના સામાન્ય કામકાજ અને પાકની માવજત માટે હવામાન અનુકૂળ છે.";
    if (mode === "researcher") return "વાતાવરણ સ્થિર રહેશે; ડેટા કલેક્શન અને અવલોકન માટે આદર્શ સ્થિતિ છે.";
    if (mode === "traveller") return "હવામાન સ્વચ્છ અને આહલાદક રહેશે; પ્રવાસ માટે ઉત્તમ સમય છે.";
    return "હવામાન સાનુકૂળ અને સ્વચ્છ રહેશે; બહારના કામકાજ માટે સારો દિવસ છે.";
  }
  if (langKey === "hi-latin") {
    if (mode === "farmer") return "Kheti ke niyamit kamo aur fasal ki dekhbhal ke liye mausam anukool hai.";
    if (mode === "researcher") return "Stable weather conditions; outdoor data collection ke liye upyogi.";
    if (mode === "traveller") return "Mausam saaf aur suhavna rahega; ghoomne aur travel ke liye behtar din.";
    return "Mausam accha aur saaf rahega; bahar ke kaamo ke liye badhiya din hai.";
  }
  if (langKey === "hi") {
    if (mode === "farmer") return "खेती के नियमित कार्यों और फसल की देखभाल के लिए मौसम अनुकूल है।";
    if (mode === "researcher") return "स्थिर वायुमंडलीय स्थितियां; डेटा संग्रह के लिए उपयुक्त समय।";
    if (mode === "traveller") return "मौसम साफ़ और सुहावना रहेगा; यात्रा और पर्यटन के लिए उत्तम दिन।";
    return "मौसम अनुकूल और साफ़ रहेगा; बाहरी गतिविधियों के लिए अच्छा दिन है।";
  }
  if (langKey === "bn") return "অনুকূল এবং পরিষ্কার আবহাওয়া; বাইরের কাজকর্মের জন্য ভালো দিন।";
  if (langKey === "ta") return "வானிலை சாதகமாகவும் தெளிவாகவும் இருக்கும்; வெளிப்புற செயல்பாடுகளுக்கு ஏற்ற நாள்.";
  if (langKey === "mr") return "हवामान अनुकूल आणि निरभ्र राहील; बाहेरील कामांसाठी उत्तम दिवस.";
  if (mode === "farmer") return "Favorable weather for routine field work and crop maintenance.";
  if (mode === "researcher") return "Stable atmospheric baseline conditions for field observations.";
  if (mode === "traveller") return "Pleasant travel conditions with clear and stable weather.";
  return "Favorable and clear weather; good conditions for outdoor activities.";
}

function ForecastStrip({
  items,
  locationName,
  mode = "normal",
  language = "en",
  script = "latin",
  warnings,
}: {
  items: DailyForecast[];
  locationName?: string;
  mode?: Mode;
  language?: string;
  script?: string;
  warnings?: Warning[] | null;
}) {
  const [selectedIndex, setSelectedIndex] = useState(0);

  if (!items || items.length === 0) return null;

  const validIndex = selectedIndex < items.length ? selectedIndex : 0;
  const selectedDay = items[validIndex];
  const advice = generateDailyAdvice(selectedDay, mode, language, script);

  const selectedDate = new Date(selectedDay.date);
  const isSelectedToday = validIndex === 0;
  const fullDayTitle = isSelectedToday
    ? `TODAY · ${selectedDate.toLocaleDateString(undefined, { weekday: "short", month: "short", day: "numeric" })}`
    : selectedDate.toLocaleDateString(undefined, { weekday: "long", month: "short", day: "numeric" });

  const hasWarning = warnings && warnings.length > 0;

  return (
    <div className="daily-outlook-card">
      {/* Horizontal Day Selector */}
      <div className="daily-selector-strip" role="tablist" aria-label="Forecast days">
        {items.slice(0, 7).map((day, idx) => {
          const isDayToday = idx === 0;
          const d = new Date(day.date);
          const dayLabel = isDayToday ? "Today" : d.toLocaleDateString(undefined, { weekday: "short" });
          const dateLabel = d.toLocaleDateString(undefined, { month: "short", day: "numeric" });
          const active = idx === validIndex;

          return (
            <button
              key={day.date}
              type="button"
              role="tab"
              aria-selected={active}
              className={`daily-tab-btn ${active ? "active" : ""}`}
              onClick={() => setSelectedIndex(idx)}
            >
              <span className={`daily-tab-day ${isDayToday ? "today-badge" : ""}`}>{dayLabel}</span>
              <span className="daily-tab-date">{dateLabel}</span>
              <div className="daily-tab-visual">
                <WeatherVisual code={day.weather_code} size="compact" />
              </div>
              <div className="daily-tab-temp">
                <strong className="temp-hi">{Math.round(day.temperature_max_c)}°</strong>
                <span className="temp-lo">{Math.round(day.temperature_min_c)}°</span>
              </div>
            </button>
          );
        })}
      </div>

      {/* Selected Day Rich Details */}
      <div className="daily-selected-body">
        <div className="daily-header-row">
          <div className="daily-title-meta">
            <span className="daily-day-badge">{fullDayTitle}</span>
            <span className="daily-condition-label">{selectedDay.condition}</span>
          </div>
          <div className="daily-visual-hero">
            <WeatherVisual code={selectedDay.weather_code} size="default" />
          </div>
        </div>

        <div className="daily-temp-row">
          <div className="daily-temp-group">
            <strong className="daily-temp-hi-val">{Math.round(selectedDay.temperature_max_c)}°C</strong>
            <span className="daily-temp-sub">High</span>
          </div>
          <span className="daily-temp-separator">/</span>
          <div className="daily-temp-group">
            <span className="daily-temp-lo-val">{Math.round(selectedDay.temperature_min_c)}°C</span>
            <span className="daily-temp-sub">Low</span>
          </div>
        </div>

        <div className="daily-metrics-compact">
          <div className="daily-metric-chip">
            <CloudRain className="metric-chip-icon" />
            <div className="metric-chip-data">
              <span className="metric-chip-label">Precipitation</span>
              <strong className="metric-chip-val">{selectedDay.precipitation_mm ?? 0} mm</strong>
            </div>
          </div>

          <div className="daily-metric-chip">
            <Wind className="metric-chip-icon" />
            <div className="metric-chip-data">
              <span className="metric-chip-label">Max Wind</span>
              <strong className="metric-chip-val">{Math.round(selectedDay.wind_speed_max_kmh)} km/h</strong>
            </div>
          </div>

          {typeof (selectedDay as unknown as { humidity_percent?: number }).humidity_percent === "number" && (
            <div className="daily-metric-chip">
              <Droplets className="metric-chip-icon" />
              <div className="metric-chip-data">
                <span className="metric-chip-label">Humidity</span>
                <strong className="metric-chip-val">
                  {(selectedDay as unknown as { humidity_percent: number }).humidity_percent}%
                </strong>
              </div>
            </div>
          )}
        </div>

        {/* Day-specific Advice Callout */}
        <div className="daily-advice-box">
          <Lightbulb className="daily-advice-icon" />
          <div className="daily-advice-content">
            <strong className="daily-advice-heading">Advice</strong>
            <p className="daily-advice-text">{advice}</p>
          </div>
        </div>

        {/* Official Warning Indicator */}
        {hasWarning && (
          <div className="daily-warning-tag">
            <AlertTriangle className="warning-tag-icon" />
            <span>Official weather warning issued for this location</span>
          </div>
        )}

        {/* Optional Full Forecast Link */}
        {locationName && (
          <div className="daily-footer-action">
            <Link
              className="primary-action-pill"
              to={`/forecast?location=${encodeURIComponent(locationName)}`}
            >
              View Full Forecast
            </Link>
          </div>
        )}
      </div>
    </div>
  );
}

function HourlyStrip({ items }: { items: HourlyForecast[] }) {
  return (
    <div className="hourly-horizontal-strip">
      {items.slice(0, 10).map((x) => (
        <div key={x.time} className="hourly-hour-cell">
          <span className="cell-time-label">
            {new Date(x.time).toLocaleTimeString([], { hour: "numeric" })}
          </span>
          <div className="cell-visual-wrap">
            <WeatherVisual code={x.weather_code} size="compact" />
          </div>
          <strong className="cell-temp-val">{Math.round(x.temperature_c)}°</strong>
          <span className="cell-rain-prob">{x.rain_probability_percent}% rain</span>
        </div>
      ))}
    </div>
  );
}

export function Forecast() {
  const [state, setState] = useState<{
    location: Location;
    current: CurrentWeather;
    daily: DailyForecast[];
    hourly: HourlyForecast[];
    warnings: Warning[];
  } | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [searchParams] = useSearchParams();

  const load = useCallback(async (location: string) => {
    setLoading(true);
    setError("");
    try {
      const [current, daily, hourly] = await Promise.all([
        weather.currentByLocation(location),
        weather.forecast(location),
        weather.hourly(location),
      ]);
      let warnings: Warning[] = [];
      if (
        daily.location.latitude !== undefined &&
        daily.location.longitude !== undefined
      ) {
        selectLocation(daily.location);
        try {
          const warnResp = await weather.warnings(
            daily.location.latitude,
            daily.location.longitude,
          );
          warnings = warnResp.warnings;
        } catch {
          warnings = [];
        }
      }
      setState({
        location: daily.location,
        current: current.weather,
        daily: daily.forecast,
        hourly: hourly.hourly_forecast,
        warnings,
      });
    } catch (e) {
      setError(e instanceof Error ? e.message : "No forecast available.");
    } finally {
      setLoading(false);
    }
  }, []);

  const selectForecastLocation = useCallback(
    (location: LocationResult) => {
      selectLocation(location);
      void load(location.name);
    },
    [load],
  );

  useEffect(() => {
    const requested = searchParams.get("location");
    const selected = requested ?? getSelectedLocation()?.name;
    const timer = selected
      ? window.setTimeout(() => {
          void load(selected);
        }, 0)
      : undefined;
    return () => {
      if (timer !== undefined) window.clearTimeout(timer);
    };
  }, [load, searchParams]);

  let content: ReactNode = (
    <Empty text="Search for a location above to view atmospheric forecasts and outlooks." />
  );

  if (loading) {
    content = <Skeleton />;
  } else if (error) {
    content = <ErrorState text={error} />;
  } else if (state) {
    content = (
      <div className="forecast-content-stack">
        <section className="forecast-hero-card glass">
          <div className="hero-weather-details">
            <p className="hero-location-tag">
              <MapPin />
              <span>{state.location.name}</span>
            </p>
            <div className="hero-temperature-display">
              <span className="hero-temp-number">{Math.round(state.current.temperature_c)}°</span>
            </div>
            <p className="hero-condition-sub">
              {state.current.condition} · Feels like {Math.round(state.current.feels_like_c)}°C
            </p>
          </div>
          <div className="hero-visual-container">
            <WeatherVisual code={state.current.weather_code} size="default" />
          </div>
        </section>

        <section className="forecast-section-block glass">
          <h2 className="section-block-title">Next hours</h2>
          <HourlyStrip items={state.hourly} />
        </section>

        <section className="forecast-section-block glass">
          <h2 className="section-block-title">Daily outlook</h2>
          <ForecastStrip
            items={state.daily}
            locationName={state.location.name}
            warnings={state.warnings}
          />
        </section>

        <section className="forecast-metrics-grid">
          <Metric
            icon={<Droplets />}
            label="Humidity"
            value={`${state.current.humidity_percent}%`}
          />
          <Metric
            icon={<Wind />}
            label="Wind Speed"
            value={`${state.current.wind_speed_kmh} km/h`}
          />
          <Metric
            icon={<CloudRain />}
            label="Precipitation"
            value={`${state.current.precipitation_mm} mm`}
          />
        </section>

        {state.warnings.length > 0 && (
          <section className="official-warning-card">
            <div className="warning-card-header">
              <ShieldAlert />
              <strong>Official IMD Weather Warning</strong>
            </div>
            {state.warnings.map((warning, index) => (
              <p key={warning.identifier ?? index} className="warning-item-text">
                {warning.headline ?? warning.event ?? "Official atmospheric warning issued for this sector."}
              </p>
            ))}
          </section>
        )}
      </div>
    );
  }

  return (
    <Page>
      <Back title="Forecast" />
      <LocationSearch onSelect={selectForecastLocation} />
      {content}
    </Page>
  );
}

function Metric({
  icon,
  label,
  value,
}: {
  icon: ReactNode;
  label: string;
  value: string;
}) {
  return (
    <div className="metric-tile glass">
      <div className="metric-icon-disc">{icon}</div>
      <div className="metric-data-wrap">
        <span className="metric-label">{label}</span>
        <strong className="metric-value">{value}</strong>
      </div>
    </div>
  );
}

export function Climate() {
  const [location, setLocation] = useState<LocationResult | null>(
    () => getSelectedLocation(),
  );
  const [result, setResult] = useState<ChatResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const loadClimate = async (selected: LocationResult) => {
    selectLocation(selected);
    setLocation(selected);
    setLoading(true);
    setError("");
    setResult(null);
    try {
      const response = await chat(
        `What was the climate summary for ${selected.name} over the last 7 days?`,
        getChatSession(),
        "researcher",
      );
      if (!response.climate) {
        setError("Climate historical data is not currently available for this location.");
      } else {
        setResult(response);
      }
    } catch (requestError) {
      setError(
        requestError instanceof Error
          ? requestError.message
          : "Climate data could not be loaded.",
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <Page>
      <Back title="Climate History" />
      <LocationSearch
        onSelect={(selected) => void loadClimate(selected)}
        placeholder="Search location for 7-day climate history…"
      />

      <section className="info-showcase-panel glass">
        <div className="showcase-icon-disc">
          <Thermometer />
        </div>
        <div className="showcase-body">
          <h2 className="showcase-heading">
            {location ? `Recent climate for ${location.name}` : "Climate History Insights"}
          </h2>
          <p className="showcase-description">
            WeatherGPT synthesizes 7-day retrospective climate data through the researcher AI model. WeatherGPT adheres strictly to live provider APIs and does not fabricate historical charts.
          </p>

          {loading && (
            <div className="climate-loading-banner">
              <Sparkles />
              <span>Fetching and synthesizing 7-day climate record…</span>
            </div>
          )}

          {result?.climate && (
            <div className="climate-advisory-box glass">
              <div className="climate-advisory-headline">
                <strong>7-Day Climate Summary</strong>
                <span className="avg-temp-pill">
                  Avg: {result.climate.average_temperature_c === null ? "N/A" : `${Math.round(result.climate.average_temperature_c)}°C`}
                </span>
              </div>
              <p className="climate-narrative">{result.response}</p>
            </div>
          )}

          {error && (
            <div className="chat-error-banner" role="alert">
              <ShieldAlert />
              <span>{error}</span>
            </div>
          )}

          <div className="showcase-cta">
            <Link className="primary-action-pill" to="/">
              Open WeatherGPT Chat
            </Link>
          </div>
        </div>
      </section>
    </Page>
  );
}

interface MapSelectedState {
  location: {
    name: string | null;
    country: string | null;
    state: string | null;
    latitude: number;
    longitude: number;
  };
  current: CurrentWeather | null;
  currentError?: string;
  hourly: HourlyForecast[] | null;
  hourlyError?: string;
  daily: DailyForecast[] | null;
  dailyError?: string;
  warnings: Warning[] | null;
  warningsStatus: "available" | "unavailable";
  advisories: string[] | null;
}

export function Maps() {
  const [mapPoint, setMapPoint] = useState<{ latitude: number; longitude: number } | null>(null);
  const [selected, setSelected] = useState<MapSelectedState | null>(null);
  const [mapWarnings, setMapWarnings] = useState<MapWarning[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const requestId = useRef(0);

  useEffect(() => {
    void gis
      .warnings()
      .then((result) => setMapWarnings(result.alerts))
      .catch(() => setMapWarnings([]));
  }, []);

  const loadNamedLocation = useCallback(async (loc: LocationResult, id: number) => {
    setLoading(true);
    setError("");
    setMapPoint({ latitude: loc.latitude, longitude: loc.longitude });

    const [currentRes, forecastRes, hourlyRes, warningsRes, advisoryRes] = await Promise.allSettled([
      gis.current(loc.name),
      gis.forecast(loc.name),
      gis.hourly(loc.name),
      weather.warnings(loc.latitude, loc.longitude),
      weather.advisory(loc.name),
    ]);

    if (id !== requestId.current) return;

    const current = currentRes.status === "fulfilled" ? currentRes.value.weather : null;
    const daily = forecastRes.status === "fulfilled" ? forecastRes.value.forecast : null;
    const hourly = hourlyRes.status === "fulfilled" ? hourlyRes.value.hourly : null;
    const warnings = warningsRes.status === "fulfilled" ? warningsRes.value.warnings : null;
    const warningsStatus = warningsRes.status === "fulfilled" ? "available" : "unavailable";
    const advisories =
      advisoryRes.status === "fulfilled" && advisoryRes.value.advisories && advisoryRes.value.advisories.length > 0
        ? advisoryRes.value.advisories
        : null;

    if (!current && !daily && !hourly) {
      setLoading(false);
      setError("Weather data is currently unavailable for this location.");
      return;
    }

    setSelected({
      location: {
        name: loc.name,
        country: loc.country ?? null,
        state: loc.admin1 ?? null,
        latitude: loc.latitude,
        longitude: loc.longitude,
      },
      current,
      currentError: currentRes.status === "rejected" ? "Current weather unavailable" : undefined,
      hourly,
      hourlyError: hourlyRes.status === "rejected" ? "Hourly forecast unavailable" : undefined,
      daily,
      dailyError: forecastRes.status === "rejected" ? "Daily outlook unavailable" : undefined,
      warnings,
      warningsStatus,
      advisories,
    });
    setLoading(false);

    selectLocation({
      name: loc.name,
      latitude: loc.latitude,
      longitude: loc.longitude,
      country: loc.country,
      admin1: loc.admin1,
    });
  }, []);

  const loadCoordinatePoint = useCallback(async (latitude: number, longitude: number, id: number) => {
    setLoading(true);
    setError("");
    setMapPoint({ latitude, longitude });

    const [currentRes, forecastRes, hourlyRes, warningsRes] = await Promise.allSettled([
      gis.currentAt(latitude, longitude),
      gis.forecastAt(latitude, longitude),
      gis.hourlyAt(latitude, longitude),
      weather.warnings(latitude, longitude),
    ]);

    if (id !== requestId.current) return;

    const current = currentRes.status === "fulfilled" ? currentRes.value.weather : null;
    const daily = forecastRes.status === "fulfilled" ? forecastRes.value.forecast : null;
    const hourly = hourlyRes.status === "fulfilled" ? hourlyRes.value.hourly : null;
    const warnings = warningsRes.status === "fulfilled" ? warningsRes.value.warnings : null;
    const warningsStatus = warningsRes.status === "fulfilled" ? "available" : "unavailable";

    const resolvedPoint = currentRes.status === "fulfilled" ? currentRes.value.location : null;

    if (!current && !daily && !hourly) {
      setLoading(false);
      setError("Weather data is currently unavailable for these coordinates.");
      return;
    }

    setSelected({
      location: {
        name: resolvedPoint?.name ?? null,
        country: resolvedPoint?.country ?? null,
        state: resolvedPoint?.state ?? null,
        latitude,
        longitude,
      },
      current,
      currentError: currentRes.status === "rejected" ? "Current weather unavailable" : undefined,
      hourly,
      hourlyError: hourlyRes.status === "rejected" ? "Hourly forecast unavailable" : undefined,
      daily,
      dailyError: forecastRes.status === "rejected" ? "Daily outlook unavailable" : undefined,
      warnings,
      warningsStatus,
      advisories: null,
    });
    setLoading(false);

    if (resolvedPoint?.name) {
      selectLocation({
        name: resolvedPoint.name,
        latitude,
        longitude,
        country: resolvedPoint.country,
        admin1: resolvedPoint.state,
      });
    }
  }, []);

  useEffect(() => {
    const selectedLoc = getSelectedLocation();
    if (!selectedLoc) return;
    const id = ++requestId.current;
    void loadNamedLocation(
      {
        name: selectedLoc.name,
        latitude: selectedLoc.latitude ?? 23.0225,
        longitude: selectedLoc.longitude ?? 72.5714,
        country: selectedLoc.country,
        admin1: selectedLoc.state,
      },
      id,
    );
  }, [loadNamedLocation]);

  const selectLocationHandler = (loc: LocationResult) => {
    const id = ++requestId.current;
    void loadNamedLocation(loc, id);
  };

  const selectPointHandler = (lat: number, lon: number) => {
    const id = ++requestId.current;
    void loadCoordinatePoint(lat, lon, id);
  };

  return (
    <Page>
      <Back title="Maps" />
      <LocationSearch
        onSelect={selectLocationHandler}
        placeholder="Search location or click anywhere on the map…"
      />

      <section className="map-view-container glass">
        <WeatherMap
          latitude={mapPoint?.latitude}
          longitude={mapPoint?.longitude}
          warnings={mapWarnings}
          onSelect={selectPointHandler}
        />
      </section>

      {loading && (
        <section className="map-selected-card glass-raised">
          <div className="map-selected-copy">
            <span className="card-eyebrow">
              <MapPin /> SELECTED LOCATION
            </span>
            <h2 className="map-condition-text">Loading weather for selected location…</h2>
          </div>
        </section>
      )}

      {error && !loading && (
        <section className="map-selected-card glass-raised">
          <div className="map-selected-copy">
            <span className="card-eyebrow">
              <ShieldAlert /> MAP LOCATION ERROR
            </span>
            <p className="map-meta-sub">{error}</p>
          </div>
          {mapPoint && (
            <button
              type="button"
              className="primary-action-pill"
              onClick={() => selectPointHandler(mapPoint.latitude, mapPoint.longitude)}
            >
              Retry
            </button>
          )}
        </section>
      )}

      {selected && !loading && (
        <div className="map-details-stack">
          <section className="map-selected-card glass-raised">
            <div className="map-selected-header">
              <div className="map-selected-copy">
                <span className="card-eyebrow">
                  <MapPin />
                  {selected.location.name ? selected.location.name : "Selected Location"}
                </span>
                <p className="map-meta-sub">
                  {selected.location.name
                    ? [selected.location.state, selected.location.country].filter(Boolean).join(", ")
                    : `${selected.location.latitude.toFixed(4)}°, ${selected.location.longitude.toFixed(4)}`}
                </p>
                {selected.current && (
                  <>
                    <h2 className="map-condition-text">{selected.current.condition}</h2>
                    <p className="map-meta-sub">
                      {Math.round(selected.current.temperature_c)}°C · Feels like {Math.round(selected.current.feels_like_c)}°C
                    </p>
                  </>
                )}
                {selected.currentError && (
                  <div className="map-partial-note">{selected.currentError}</div>
                )}
              </div>

              {selected.location.name && (
                <Link
                  className="primary-action-pill"
                  to={`/forecast?location=${encodeURIComponent(selected.location.name)}`}
                >
                  View Forecast
                </Link>
              )}
            </div>

            {selected.current && (
              <div className="forecast-metrics-grid">
                <Metric
                  icon={<Droplets />}
                  label="Humidity"
                  value={`${selected.current.humidity_percent}%`}
                />
                <Metric
                  icon={<Wind />}
                  label="Wind Speed"
                  value={`${selected.current.wind_speed_kmh} km/h`}
                />
                <Metric
                  icon={<CloudRain />}
                  label="Precipitation"
                  value={`${selected.current.precipitation_mm} mm`}
                />
              </div>
            )}
          </section>

          {selected.hourly && selected.hourly.length > 0 && (
            <section className="forecast-section-block glass">
              <h3 className="section-block-title">Hourly Forecast</h3>
              <HourlyStrip items={selected.hourly} />
            </section>
          )}

          {selected.hourlyError && (
            <div className="map-partial-note">{selected.hourlyError}</div>
          )}

          {selected.daily && selected.daily.length > 0 && (
            <section className="forecast-section-block glass">
              <h3 className="section-block-title">Daily Outlook</h3>
              <ForecastStrip
                items={selected.daily}
                locationName={selected.location.name ?? undefined}
                warnings={selected.warnings}
              />
            </section>
          )}

          {selected.dailyError && (
            <div className="map-partial-note">{selected.dailyError}</div>
          )}

          {selected.warningsStatus === "unavailable" && (
            <div className="map-partial-note">Warning data unavailable</div>
          )}

          {selected.warningsStatus === "available" && selected.warnings && selected.warnings.length > 0 && (
            <section className="official-warning-card">
              <div className="warning-card-header">
                <ShieldAlert />
                <strong>Official IMD Weather Warning</strong>
              </div>
              {selected.warnings.map((warning, index) => (
                <p key={warning.identifier ?? index} className="warning-item-text">
                  {warning.headline ?? warning.event ?? "Official weather warning issued for this location."}
                </p>
              ))}
            </section>
          )}

          {selected.advisories && selected.advisories.length > 0 && (
            <section className="advisory-card advisory-card--farmer glass">
              <div className="advisory-header">
                <span className="advisory-badge">Weather Advisory</span>
              </div>
              <ul className="advisory-reasons-list">
                {selected.advisories.map((advisory, idx) => (
                  <li key={idx}>{advisory}</li>
                ))}
              </ul>
            </section>
          )}
        </div>
      )}
    </Page>
  );
}

export function Voice() {
  type VoiceStatus =
    | "idle"
    | "requesting"
    | "listening"
    | "transcribing"
    | "thinking"
    | "complete"
    | "error";

  const [status, setStatus] = useState<VoiceStatus>("idle");
  const [voiceMode, setVoiceMode] = useState<Mode>("normal");
  const [transcript, setTranscript] = useState("");
  const [response, setResponse] = useState("");
  const [error, setError] = useState("");
  const recorder = useRef<MediaRecorder | null>(null);
  const stream = useRef<MediaStream | null>(null);
  const chunks = useRef<Blob[]>([]);
  const alive = useRef(true);

  const release = () => {
    stream.current?.getTracks().forEach((track) => track.stop());
    stream.current = null;
    recorder.current = null;
  };

  useEffect(
    () => () => {
      alive.current = false;
      if (recorder.current?.state === "recording") recorder.current.stop();
      release();
    },
    [],
  );

  const reset = () => {
    if (status === "listening") recorder.current?.stop();
    setTranscript("");
    setResponse("");
    setError("");
    setStatus("idle");
  };

  const processAudio = async (audio: Blob) => {
    if (audio.size === 0) {
      setError("I couldn't hear anything clearly. Please try again.");
      setStatus("error");
      return;
    }
    try {
      setStatus("transcribing");
      const transcription = await voice.transcribe(audio, getChatSession());
      if (!alive.current) return;
      const text = transcription.transcript.trim();
      if (!text) {
        setError("I couldn't hear anything clearly. Please try again.");
        setStatus("error");
        return;
      }
      setTranscript(text);
      setStatus("thinking");
      const result = await voice.chat(audio, getChatSession(), undefined, voiceMode);
      if (!alive.current) return;
      setResponse(result.response);
      saveVoiceConversation({
        transcript: result.transcript,
        response: result.chat,
      });
      setStatus("complete");
    } catch (e) {
      if (!alive.current) return;
      setError(
        e instanceof Error
          ? e.message
          : "Voice could not be processed. Please try again.",
      );
      setStatus("error");
    }
  };

  const start = async () => {
    if (status !== "idle" && status !== "error" && status !== "complete")
      return;
    if (
      !navigator.mediaDevices?.getUserMedia ||
      typeof MediaRecorder === "undefined"
    ) {
      setError("Voice recording is not supported by this browser.");
      setStatus("error");
      return;
    }
    setError("");
    setTranscript("");
    setResponse("");
    setStatus("requesting");
    try {
      const activeStream = await navigator.mediaDevices.getUserMedia({
        audio: true,
      });
      if (!alive.current) {
        activeStream.getTracks().forEach((track) => track.stop());
        return;
      }
      stream.current = activeStream;
      const activeRecorder = new MediaRecorder(activeStream);
      chunks.current = [];
      activeRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) chunks.current.push(event.data);
      };
      activeRecorder.onerror = () => {
        release();
        if (alive.current) {
          setError("Recording encountered an issue. Please try again.");
          setStatus("error");
        }
      };
      activeRecorder.onstop = () => {
        const audio = new Blob(chunks.current, {
          type: activeRecorder.mimeType || "audio/webm",
        });
        release();
        if (alive.current) void processAudio(audio);
      };
      recorder.current = activeRecorder;
      activeRecorder.start();
      setStatus("listening");
    } catch {
      if (alive.current) {
        setError("Microphone access is required to use Voice.");
        setStatus("error");
      }
    }
  };

  const stop = () => {
    if (recorder.current?.state === "recording") recorder.current.stop();
  };

  const heading =
    status === "listening"
      ? "Listening to your question…"
      : status === "requesting"
        ? "Accessing microphone…"
        : status === "transcribing"
          ? "Transcribing voice…"
          : status === "thinking"
            ? "Synthesizing answer…"
            : status === "complete"
              ? "Voice conversation processed."
              : "Speak to WeatherGPT";

  return (
    <Page>
      <Back title="Voice" />
      <section className="voice-stage-card glass" aria-live="polite">
        <div
          className={`voice-interactive-orb ${status === "listening" ? "recording" : status}`}
        >
          <Volume2 />
          <span className="pulse-ring pulse-ring--1" />
          <span className="pulse-ring pulse-ring--2" />
        </div>

        <h2 className="voice-state-heading">{heading}</h2>
        <p className="voice-state-desc">
          {status === "listening"
            ? "Speak your weather question clearly, then tap Done."
            : "Ask about current forecasts, rainfall, or advisories and continue directly in chat."}
        </p>

        <div className="mode-selector-strip" style={{ marginBottom: "1rem" }}>
          {modes.map((m) => (
            <button
              key={m}
              type="button"
              className={`mode-segmented-btn ${voiceMode === m ? "selected" : ""}`}
              onClick={() => setVoiceMode(m)}
              aria-pressed={voiceMode === m}
            >
              {modeLabel(m)}
            </button>
          ))}
        </div>

        <div className="voice-action-row">
          <button
            className="primary-action-pill voice-primary-btn"
            type="button"
            onClick={status === "listening" ? stop : () => void start()}
            disabled={
              status === "requesting" ||
              status === "transcribing" ||
              status === "thinking"
            }
            aria-label={
              status === "listening"
                ? "Stop voice recording"
                : "Start voice recording"
            }
          >
            {status === "listening" ? (
              "Done Recording"
            ) : (
              <>
                <Mic />
                <span>Start Listening</span>
              </>
            )}
          </button>

          {(status === "error" || status === "complete") && (
            <button className="secondary-text-btn" type="button" onClick={reset}>
              Record Again
            </button>
          )}
        </div>

        {transcript && (
          <div className="voice-transcript-bubble glass">
            <span className="bubble-label">You said:</span>
            <p>{transcript}</p>
          </div>
        )}

        {response && (
          <div className="voice-response-bubble glass-raised">
            <span className="bubble-label">WeatherGPT:</span>
            <p>{response}</p>
            <Link to="/" className="primary-action-pill voice-continue-link">
              Continue in Chat
            </Link>
          </div>
        )}

        {error && (
          <div className="chat-error-banner" role="alert">
            <ShieldAlert />
            <span>{error}</span>
          </div>
        )}
      </section>
    </Page>
  );
}

export function Settings({
  theme,
  onThemeChange,
}: {
  theme?: Theme;
  onThemeChange?: (theme: Theme) => void;
}) {
  const [units, setUnits] = useState(localStorage.getItem("units") ?? "C");

  return (
    <Page>
      <Back title="Settings" />
      <div className="settings-stack">
        {onThemeChange && theme && (
          <section className="settings-group-card glass">
            <span className="group-eyebrow">APPEARANCE</span>
            <h2 className="settings-title">Theme</h2>
            <p className="settings-explanation">
              Switch between the warm cream light palette and deep charcoal dark palette.
            </p>
            <div className="segmented-toggle-group" role="group" aria-label="Theme selection">
              <button
                type="button"
                className={`toggle-option-btn ${theme === "light" ? "selected" : ""}`}
                onClick={() => onThemeChange("light")}
                aria-pressed={theme === "light"}
              >
                Light
              </button>
              <button
                type="button"
                className={`toggle-option-btn ${theme === "dark" ? "selected" : ""}`}
                onClick={() => onThemeChange("dark")}
                aria-pressed={theme === "dark"}
              >
                Dark
              </button>
            </div>
          </section>
        )}

        <section className="settings-group-card glass">
          <span className="group-eyebrow">WEATHER PREFERENCES</span>
          <h2 className="settings-title">Temperature Unit</h2>
          <p className="settings-explanation">
            Local browser display preference. Weather data is currently presented in Celsius, and the backend does not provide a preferences sync API.
          </p>
          <div className="segmented-toggle-group">
            <button
              type="button"
              className={`toggle-option-btn ${units === "C" ? "selected" : ""}`}
              onClick={() => {
                setUnits("C");
                localStorage.setItem("units", "C");
              }}
              aria-pressed={units === "C"}
            >
              °C (Celsius)
            </button>
            <button
              type="button"
              className={`toggle-option-btn ${units === "F" ? "selected" : ""}`}
              onClick={() => {
                setUnits("F");
                localStorage.setItem("units", "F");
              }}
              aria-pressed={units === "F"}
            >
              °F (Fahrenheit)
            </button>
          </div>
        </section>

        <section className="settings-group-card glass">
          <span className="group-eyebrow">ABOUT & APP</span>
          <h2 className="settings-title">Application Info</h2>
          <p className="settings-explanation">
            Discover how WeatherGPT combines conversational intelligence with live meteorological feeds.
          </p>
          <div>
            <Link to="/about" className="primary-action-pill">
              About WeatherGPT
            </Link>
          </div>
        </section>
      </div>
    </Page>
  );
}

export function Profile({
  auth: state,
  onLogout,
}: {
  auth: AuthState;
  onLogout: () => void;
}) {
  return (
    <Page>
      <Back title="Profile" />
      {state.status === "loading" ? (
        <Skeleton />
      ) : state.user ? (
        <section className="profile-identity-card glass-raised">
          <div className="profile-large-avatar">
            {state.user.name?.[0]?.toUpperCase() ?? "W"}
          </div>
          <h2 className="profile-name-text">
            {state.user.name || "WeatherGPT Member"}
          </h2>
          <p className="profile-email-text">{state.user.email}</p>

          <div className="profile-actions-stack">
            <Link className="primary-action-pill" to="/settings">
              Account Settings
            </Link>
            <button className="secondary-text-btn" type="button" onClick={onLogout}>
              Logout
            </button>
          </div>
        </section>
      ) : (
        <section className="profile-identity-card glass-raised">
          <div className="profile-large-avatar guest-avatar-disc">G</div>
          <h2 className="profile-name-text">Guest Mode</h2>
          <p className="profile-email-text">
            You’re using WeatherGPT in guest mode. Sign in to save chats across sessions.
          </p>

          <div className="profile-actions-stack">
            <Link className="primary-action-pill" to="/login">
              Login to Account
            </Link>
            <Link className="secondary-text-btn" to="/signup">
              Create an Account
            </Link>
          </div>
        </section>
      )}
    </Page>
  );
}

export function About() {
  return (
    <Page>
      <Back title="About WeatherGPT" />
      <section className="info-showcase-panel glass">
        <div className="showcase-icon-disc">
          <CloudSun />
        </div>
        <div className="showcase-body">
          <h2 className="showcase-heading">A calmer way to understand weather.</h2>
          <p className="showcase-description">
            WeatherGPT combines atmospheric conversational intelligence with real-time Open-Meteo forecasts, GIS geospatial mapping, and official IMD warnings.
          </p>
          <div className="about-meta-tag">
            <span>Version 1.0 · Atmospheric Intelligence</span>
          </div>
        </div>
      </section>
    </Page>
  );
}

export function AuthPage({
  kind,
  refresh,
}: {
  kind: "login" | "signup";
  refresh: () => Promise<void>;
}) {
  const nav = useNavigate();
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  const submit = async (e: FormEvent) => {
    e.preventDefault();
    setBusy(true);
    setError("");
    try {
      if (kind === "login") await auth.login(email, password);
      else await auth.signup(name, email, password);
      await refresh();
      nav("/");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Unable to authenticate.");
    } finally {
      setBusy(false);
    }
  };

  return (
    <Page>
      <section className="auth-container-card glass-raised">
        <div className="auth-brand-badge">
          <CloudSun />
        </div>
        <h1 className="auth-heading">
          {kind === "login" ? "Welcome back" : "Create your account"}
        </h1>
        <p className="auth-subtitle">
          {kind === "login"
            ? "Sign in to access your WeatherGPT space."
            : "Sign up to associate your conversation history."}
        </p>

        <form onSubmit={submit} className="auth-form-layout">
          {kind === "signup" && (
            <label className="auth-field-label">
              <span>Full Name</span>
              <input
                className="auth-text-input"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="e.g. Alex Mercer"
                maxLength={100}
                required
              />
            </label>
          )}

          <label className="auth-field-label">
            <span>Email Address</span>
            <input
              className="auth-text-input"
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="alex@example.com"
            />
          </label>

          <label className="auth-field-label">
            <span>Password</span>
            <input
              className="auth-text-input"
              type="password"
              required
              minLength={kind === "signup" ? 12 : 1}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••••••"
            />
          </label>

          {kind === "signup" && (
            <small className="auth-helper-note">
              Use 12+ characters with at least one letter and number.
            </small>
          )}

          {error && (
            <div className="chat-error-banner" role="alert">
              <ShieldAlert />
              <span>{error}</span>
            </div>
          )}

          <button
            className="primary-action-pill auth-submit-btn"
            type="submit"
            disabled={busy}
          >
            {busy ? "Authenticating…" : kind === "login" ? "Log In" : "Create Account"}
          </button>
        </form>

        <div className="auth-footer-toggle">
          <Link to={kind === "login" ? "/signup" : "/login"}>
            {kind === "login"
              ? "Need an account? Sign up here"
              : "Already have an account? Sign in here"}
          </Link>
        </div>
      </section>
    </Page>
  );
}

function Page({ children }: { children: ReactNode }) {
  return <div className="page-shell-container">{children}</div>;
}

function Empty({ text }: { text: string }) {
  return <div className="empty-message-plate glass">{text}</div>;
}

function ErrorState({ text }: { text: string }) {
  return (
    <div className="error-message-plate glass" role="alert">
      <ShieldAlert />
      <div>
        <strong>We couldn’t complete that request.</strong>
        <p>{text}</p>
      </div>
    </div>
  );
}

function Skeleton() {
  return <div className="skeleton-placeholder-box glass" />;
}
