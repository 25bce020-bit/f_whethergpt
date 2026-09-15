import { useCallback, useEffect, useRef, useState } from "react";
import type { FormEvent, ReactNode } from "react";
import {
  ArrowLeft,
  ArrowUp,
  Cloud,
  CloudRain,
  CloudSun,
  Droplets,
  MapPin,
  Mic,
  Send,
  Sun,
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
  GisWeather,
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
import { saveVoiceConversation, takeVoiceConversation } from "./voiceConversation";
const modes: Mode[] = ["normal", "farmer", "researcher", "traveller"];
const modeLabel = (m: Mode) => m[0].toUpperCase() + m.slice(1);
function WeatherIcon({ code = 0 }: { code?: number }) {
  return code >= 51 ? <CloudRain /> : code >= 3 ? <Cloud /> : <Sun />;
}
function Back({ title }: { title: string }) {
  const navigate = useNavigate();
  const goBack = () => {
    if (window.history.length > 1) navigate(-1);
    else navigate("/", { replace: true });
  };
  return (
    <div className="page-title">
      <button
        className="icon-button page-back"
        type="button"
        onClick={goBack}
        aria-label="Go back"
      >
        <ArrowLeft />
      </button>
      <h1>{title}</h1>
    </div>
  );
}
function LocationSearch({
  onSelect,
}: {
  onSelect: (location: LocationResult) => void;
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
      if (data.results.length === 0) setError("No matching locations found.");
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
    <form className="location-search" onSubmit={find}>
      <MapPin />
      <input
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        placeholder="Search a location"
        aria-label="Search a location"
      />
      <button aria-label="Search" disabled={busy}>
        {busy ? "…" : <ArrowUp />}
      </button>
      {items.length > 0 && (
        <div
          className="search-results glass-raised"
          role="listbox"
          aria-label="Location results"
        >
          {items.map((item, i) => (
            <button
              key={`${item.name}-${i}`}
              type="button"
              role="option"
              onClick={() => {
                setQuery(item.name);
                setItems([]);
                onSelect(item);
              }}
            >
              <strong>{item.name}</strong>
              <small>
                {[item.admin1, item.country].filter(Boolean).join(", ")}
              </small>
            </button>
          ))}
        </div>
      )}
      {error && <small className="search-error">{error}</small>}
    </form>
  );
}
function Message({
  message,
}: {
  message: { role: "user" | "ai"; text: string; data?: ChatResponse };
}) {
  const d = message.data;
  return (
    <article className={`message ${message.role}`}>
      {message.role === "ai" && (
        <span className="assistant-dot">
          <CloudSun />
        </span>
      )}
      <div className="message-copy">
        <p>{message.text}</p>
        {d?.weather && (
          <WeatherMini weather={d.weather} location={d.location} />
        )}{" "}
        {d?.forecast && (
          <>
            <ForecastStrip items={d.forecast} />
            {d.location?.name && (
              <Link
                className="primary-link"
                to={`/forecast?location=${encodeURIComponent(d.location.name)}`}
              >
                View Forecast
              </Link>
            )}
          </>
        )}{" "}
        {d?.traveller_advisory?.suitability && (
          <div className="advisory">
            <strong>
              Travel suitability: {d.traveller_advisory.suitability.status}
            </strong>
            {d.traveller_advisory.suitability.reasons.map((x) => (
              <span key={x}>{x}</span>
            ))}
          </div>
        )}{" "}
        {d?.farmer_advisory?.today_advisory && (
          <div className="advisory">
            {d.farmer_advisory.today_advisory.map((x) => (
              <span key={x}>{x}</span>
            ))}
          </div>
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
  const scroll = useRef<HTMLDivElement>(null);
  const last = useRef(0);
  useEffect(() => {
    const el = scroll.current;
    if (!el) return;
    const onScroll = () => {
      const up = el.scrollTop < last.current;
      setShowModes(!(up && el.scrollTop > 40));
      last.current = el.scrollTop;
    };
    el.addEventListener("scroll", onScroll);
    return () => el.removeEventListener("scroll", onScroll);
  }, []);
  const sendMessage = async (
    value: string,
    selectedMode: Mode,
    showUserMessage: boolean,
  ) => {
    if (busy) return;
    setError("");
    setLastFailed(null);
    if (showUserMessage)
      setMessages((m) => [...m, { role: "user", text: value }]);
    setBusy(true);
    try {
      const response = await chat(value, getChatSession(), selectedMode);
      setMessages((m) => [
        ...m,
        { role: "ai", text: response.response, data: response },
      ]);
    } catch (e) {
      setLastFailed({ message: value, mode: selectedMode });
      setError(e instanceof Error ? e.message : "Unable to send message.");
    } finally {
      setBusy(false);
      setTimeout(
        () =>
          scroll.current?.scrollTo({
            top: scroll.current.scrollHeight,
            behavior: "smooth",
          }),
        0,
      );
    }
  };
  async function send(e: FormEvent) {
    e.preventDefault();
    const value = text.trim();
    if (!value || busy) return;
    setText("");
    await sendMessage(value, mode, true);
  }
  return (
    <div className="chat-page">
      <div className="chat-scroll" ref={scroll}>
        <section className="chat-intro">
          <div className="orb">
            <CloudSun />
          </div>
          <p className="eyebrow">ATMOSPHERIC INTELLIGENCE</p>
          <h1>Weather, with a clearer point of view.</h1>
          <p>
            Ask about conditions, forecasts, farming, research, and travel—no
            account needed.
          </p>
        </section>
        <div className="message-list">
          {messages.length === 0 ? (
            <div className="empty-chat">Ask WeatherGPT about the weather.</div>
          ) : (
            messages.map((m, i) => <Message key={i} message={m} />)
          )}
          {busy && (
            <article className="message ai loading">
              <span className="assistant-dot">
                <CloudSun />
              </span>
              <div className="message-copy">WeatherGPT is thinking…</div>
            </article>
          )}
          {error && (
            <div className="error-inline">
              {error}
              {lastFailed && (
                <button
                  onClick={() =>
                    void sendMessage(lastFailed.message, lastFailed.mode, false)
                  }
                  disabled={busy}
                >
                  Retry
                </button>
              )}
              <button
                onClick={() => {
                  setError("");
                  setLastFailed(null);
                }}
              >
                Dismiss
              </button>
            </div>
          )}
        </div>
      </div>
      <div className="composer-zone">
        <form className="composer glass-raised" onSubmit={send}>
          <Mic aria-hidden="true" />
          <input
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
          />
          <button
            className="send"
            type="submit"
            disabled={!text.trim() || busy}
            aria-label="Send message"
          >
            <Send />
          </button>
        </form>
        <div className={`mode-selector ${showModes ? "visible" : "hidden"}`}>
          {modes.map((m) => (
            <button
              key={m}
              className={mode === m ? "selected" : ""}
              onClick={() => setMode(m)}
            >
              {modeLabel(m)}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}
function WeatherMini({
  weather: w,
  location,
}: {
  weather: CurrentWeather;
  location?: Location;
}) {
  return (
    <div className="weather-mini">
      <WeatherIcon code={w.weather_code} />
      <div>
        <small>
          {location?.name ?? "Current weather"} · {w.condition}
        </small>
        <strong>{Math.round(w.temperature_c)}°C</strong>
      </div>
      <span>Feels {Math.round(w.feels_like_c)}°</span>
    </div>
  );
}
function ForecastStrip({ items }: { items: DailyForecast[] }) {
  return (
    <div className="forecast-strip">
      {items.slice(0, 5).map((day) => (
        <div key={day.date}>
          <small>
            {new Date(day.date).toLocaleDateString(undefined, {
              weekday: "short",
            })}
          </small>
          <WeatherIcon code={day.weather_code} />
          <strong>{Math.round(day.temperature_max_c)}°</strong>
          <small>{Math.round(day.temperature_min_c)}°</small>
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
        warnings = (
          await weather.warnings(
            daily.location.latitude,
            daily.location.longitude,
          )
        ).warnings;
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
    <Empty text="Search for a location to view its forecast." />
  );
  if (loading) content = <Skeleton />;
  else if (error) content = <ErrorState text={error} />;
  else if (state)
    content = (
      <>
        <section className="weather-hero glass">
          <div>
            <p className="eyebrow">
              <MapPin /> {state.location.name}
            </p>
            <h2>{Math.round(state.current.temperature_c)}°</h2>
            <p>
              {state.current.condition} · Feels like{" "}
              {Math.round(state.current.feels_like_c)}°C
            </p>
          </div>
          <WeatherIcon code={state.current.weather_code} />
        </section>
        <section>
          <h2>Next hours</h2>
          <HourlyStrip items={state.hourly} />
        </section>
        <section>
          <h2>Daily outlook</h2>
          <ForecastStrip items={state.daily} />
        </section>
        <section className="metric-grid">
          <Metric
            icon={<Droplets />}
            label="Humidity"
            value={`${state.current.humidity_percent}%`}
          />
          <Metric
            icon={<Wind />}
            label="Wind"
            value={`${state.current.wind_speed_kmh} km/h`}
          />
          <Metric
            icon={<CloudRain />}
            label="Precipitation"
            value={`${state.current.precipitation_mm} mm`}
          />
        </section>
        {state.warnings.length > 0 && (
          <section className="warning">
            <strong>Official IMD warning</strong>
            {state.warnings.map((warning, index) => (
              <p key={warning.identifier ?? index}>
                {warning.headline ??
                  warning.event ??
                  "Official weather warning"}
              </p>
            ))}
          </section>
        )}
      </>
    );
  return (
    <Page>
      <Back title="Forecast" />
      <LocationSearch onSelect={selectForecastLocation} />
      {content}
    </Page>
  );
}
function HourlyStrip({ items }: { items: HourlyForecast[] }) {
  return (
    <div className="hourly-strip glass">
      {items.slice(0, 10).map((x) => (
        <div key={x.time}>
          <small>
            {new Date(x.time).toLocaleTimeString([], { hour: "numeric" })}
          </small>
          <WeatherIcon code={x.weather_code} />
          <strong>{Math.round(x.temperature_c)}°</strong>
          <small>{x.rain_probability_percent}% rain</small>
        </div>
      ))}
    </div>
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
    <div className="metric glass">
      {icon}
      <small>{label}</small>
      <strong>{value}</strong>
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
        setError("Climate data is not currently available for this location.");
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
      <LocationSearch onSelect={(selected) => void loadClimate(selected)} />
      <section className="glass info-panel">
        <Thermometer />
        <div>
          <h2>{location ? `Recent climate for ${location.name}` : "Climate history"}</h2>
          <p>
            WeatherGPT provides a real recent seven-day climate summary through
            Chat. There is no standalone climate-history or custom-range API.
          </p>
          {loading && <p>Loading the available climate summary…</p>}
          {result?.climate && (
            <div className="advisory">
              <strong>Last 7 days</strong>
              <span>
                Average temperature: {result.climate.average_temperature_c === null ? "Unavailable" : `${Math.round(result.climate.average_temperature_c)}°C`}
              </span>
              <span>{result.response}</span>
            </div>
          )}
          {error && <div className="error-inline" role="alert">{error}</div>}
          <Link className="primary-link" to="/">Open WeatherGPT chat</Link>
        </div>
      </section>
    </Page>
  );
}
export function Maps() {
  const [data, setData] = useState<GisWeather | null>(null);
  const [warnings, setWarnings] = useState<MapWarning[]>([]);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const requestId = useRef(0);
  useEffect(() => {
    void gis
      .warnings()
      .then((result) => setWarnings(result.alerts))
      .catch(() => setWarnings([]));
  }, []);
  const applyData = (result: GisWeather, id: number) => {
    if (id !== requestId.current) return;
    setData(result);
    setLoading(false);
    if (result.location.name)
      selectLocation({
        name: result.location.name,
        latitude: result.location.latitude,
        longitude: result.location.longitude,
        country: result.location.country,
        admin1: result.location.state,
      });
  };
  useEffect(() => {
    const selected = getSelectedLocation();
    if (!selected) return;
    const id = ++requestId.current;
    void Promise.resolve().then(async () => {
      setLoading(true);
      try {
        applyData(await gis.current(selected.name), id);
      } catch {
        if (id === requestId.current) {
          setLoading(false);
          setError("Could not restore the selected location.");
        }
      }
    });
  }, []);
  const loadLocation = async (location: LocationResult) => {
    const id = ++requestId.current;
    selectLocation(location);
    setLoading(true);
    setError("");
    try {
      applyData(await gis.current(location.name), id);
    } catch (e) {
      if (id === requestId.current) {
        setLoading(false);
        setError(
          e instanceof Error
            ? e.message
            : "Could not load weather for this location.",
        );
      }
    }
  };
  const loadPoint = async (latitude: number, longitude: number) => {
    const id = ++requestId.current;
    setLoading(true);
    setError("");
    try {
      applyData(await gis.currentAt(latitude, longitude), id);
    } catch (e) {
      if (id === requestId.current) {
        setLoading(false);
        setError(
          e instanceof Error
            ? e.message
            : "Could not load weather for this point.",
        );
      }
    }
  };
  const selectedWarning =
    data &&
    warnings.some(
      (warning) =>
        warning.location?.latitude === data.location.latitude &&
        warning.location.longitude === data.location.longitude,
    );
  return (
    <Page>
      <Back title="Maps" />
      <LocationSearch onSelect={loadLocation} />
      <section className="map-area glass">
        <WeatherMap
          latitude={data?.map.latitude}
          longitude={data?.map.longitude}
          warnings={warnings}
          onSelect={loadPoint}
        />
      </section>
      {loading && (
        <section className="map-location-card glass-raised">
          <div>
            <p className="eyebrow">Selected location</p>
            <h2>Loading weather…</h2>
          </div>
        </section>
      )}
      {error && (
        <section className="map-location-card glass-raised">
          <div>
            <p className="eyebrow">Map selection</p>
            <p>{error}</p>
          </div>
          <button
            className="primary-button"
            onClick={() =>
              data && void loadPoint(data.map.latitude, data.map.longitude)
            }
          >
            Retry
          </button>
        </section>
      )}
      {data && (
        <section className="map-location-card glass-raised">
          <div>
            <p className="eyebrow">
              <MapPin /> {data.location.name ?? "Selected point"}
            </p>
            <h2>{data.weather.condition}</h2>
            <p>
              {Math.round(data.weather.temperature_c)}°C · Wind{" "}
              {Math.round(data.weather.wind_speed_kmh)} km/h
            </p>
            {selectedWarning && (
              <small className="map-warning">
                Official IMD warning at this mapped point
              </small>
            )}
          </div>
          {data.location.name && (
            <Link
              className="primary-link"
              to={`/forecast?location=${encodeURIComponent(data.location.name)}`}
            >
              View Forecast
            </Link>
          )}
        </section>
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
      const result = await voice.chat(audio, getChatSession());
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
          setError("Recording failed. Please try again.");
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
      ? "Listening…"
      : status === "requesting"
        ? "Requesting microphone access…"
        : status === "transcribing"
          ? "Transcribing…"
          : status === "thinking"
            ? "WeatherGPT is thinking…"
            : status === "complete"
              ? "Your voice conversation is ready."
              : "Speak to WeatherGPT";
  return (
    <Page>
      <Back title="Voice" />
      <section className="voice-stage" aria-live="polite">
        <div
          className={`voice-orb ${status === "listening" ? "recording" : status}`}
        >
          <Volume2 />
          <span className="ring" />
        </div>
        <h2>{heading}</h2>
        <p>
          {status === "listening"
            ? "When you are finished, tap Done."
            : "Record a weather question and WeatherGPT will return it to chat."}
        </p>
        <button
          className="primary-button"
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
            "Done"
          ) : (
            <>
              <Mic /> Start listening
            </>
          )}
        </button>
        {(status === "error" || status === "complete") && (
          <button className="text-button" onClick={reset}>
            Record again
          </button>
        )}
        {transcript && (
          <div className="voice-result glass">
            <small className="eyebrow">Your transcription</small>
            <p>{transcript}</p>
          </div>
        )}
        {response && (
          <div className="voice-result glass">
            <small className="eyebrow">WeatherGPT response</small>
            <p>{response}</p>
            <Link to="/">Continue in Chat</Link>
          </div>
        )}
        {error && (
          <div className="error-inline" role="alert">
            {error}
          </div>
        )}
      </section>
    </Page>
  );
}
export function Settings() {
  const [units, setUnits] = useState(localStorage.getItem("units") ?? "C");
  return (
    <Page>
      <Back title="Settings" />
      <section className="settings-card glass">
        <p className="eyebrow">LOCAL PREFERENCE</p>
        <h2>Temperature unit</h2>
        <p>
          This display preference is stored only in this browser. Weather data
          is currently presented in Celsius, and the backend does not provide a
          preferences API or account-synced unit conversion.
        </p>
        <div className="toggle-row">
          <button
            className={units === "C" ? "selected" : ""}
            onClick={() => {
              setUnits("C");
              localStorage.setItem("units", "C");
            }}
          >
            °C
          </button>
          <button
            className={units === "F" ? "selected" : ""}
            onClick={() => {
              setUnits("F");
              localStorage.setItem("units", "F");
            }}
          >
            °F
          </button>
        </div>
      </section>
      <section className="settings-card glass">
        <p className="eyebrow">ABOUT</p>
        <Link to="/about">About WeatherGPT</Link>
      </section>
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
        <section className="profile-page glass">
          <span className="large-avatar">
            {state.user.name?.[0]?.toUpperCase() ?? "W"}
          </span>
          <h2>{state.user.name || "WeatherGPT member"}</h2>
          <p>{state.user.email}</p>
          <Link className="primary-link" to="/settings">
            Account settings
          </Link>
          <button className="text-button" onClick={onLogout}>
            Logout
          </button>
        </section>
      ) : (
        <section className="profile-page glass">
          <span className="large-avatar">G</span>
          <h2>Guest</h2>
          <p>
            You’re using guest mode. Sign in to associate future chats with your
            account.
          </p>
          <Link className="primary-link" to="/login">
            Login
          </Link>
          <Link className="text-button" to="/signup">
            Sign Up
          </Link>
        </section>
      )}
    </Page>
  );
}
export function About() {
  return (
    <Page>
      <Back title="About WeatherGPT" />
      <section className="glass info-panel">
        <CloudSun />
        <div>
          <h2>A calmer way to understand weather.</h2>
          <p>
            WeatherGPT combines conversational weather intelligence with
            practical forecasts, official warning context, and location-aware
            tools.
          </p>
          <small>
            Version 1.0 · Weather data is provided by connected backend
            services.
          </small>
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
      setError(e instanceof Error ? e.message : "Unable to continue.");
    } finally {
      setBusy(false);
    }
  };
  return (
    <Page>
      <section className="auth-card glass-raised">
        <CloudSun />
        <h1>{kind === "login" ? "Welcome back" : "Create your account"}</h1>
        <p>WeatherGPT is always available as a guest.</p>
        <form onSubmit={submit}>
          {kind === "signup" && (
            <label>
              Name
              <input
                value={name}
                onChange={(e) => setName(e.target.value)}
                maxLength={100}
              />
            </label>
          )}
          <label>
            Email
            <input
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
            />
          </label>
          <label>
            Password
            <input
              type="password"
              required
              minLength={12}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
            />
          </label>
          {kind === "signup" && (
            <small>
              Use 12+ characters with at least one letter and number.
            </small>
          )}
          {error && <div className="error-inline">{error}</div>}
          <button className="primary-button" disabled={busy}>
            {busy ? "Please wait…" : kind === "login" ? "Login" : "Sign Up"}
          </button>
        </form>
        <Link to={kind === "login" ? "/signup" : "/login"}>
          {kind === "login"
            ? "Need an account? Sign up"
            : "Already have an account? Login"}
        </Link>
      </section>
    </Page>
  );
}
function Page({ children }: { children: ReactNode }) {
  return <div className="page">{children}</div>;
}
function Empty({ text }: { text: string }) {
  return <div className="empty-state glass">{text}</div>;
}
function ErrorState({ text }: { text: string }) {
  return (
    <div className="error-state glass">
      <strong>We couldn’t complete that request.</strong>
      <p>{text}</p>
    </div>
  );
}
function Skeleton() {
  return <div className="skeleton glass" />;
}
