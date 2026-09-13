from fastapi import FastAPI, File, Form, HTTPException, Query, UploadFile
from pydantic import BaseModel
from datetime import date, timedelta
from app.services.recommendation_service import (
    generate_weather_recommendations,
)
from sqlalchemy import select, func
from app.models import (
    User,
    Conversation,
    ChatMessage,
    WeatherRecord,
    OfficialAlert,
    IngestionLog,
)
from app.database import (
    init_db,
    close_db,
)
from sqlalchemy import text

from app.database import AsyncSessionLocal
from app.services.disaster_service import (
    generate_disaster_alerts,
)
from app.services.cache_service import (
    get_all_cache_status,
    get_cache_metrics,
    clear_cache,
)
from app.services.database_service import (
    save_chat_message,
)
from app.services.realtime_ingestion_service import (
    refresh_location,
    get_cached_location_data,
    get_cached_imd_alerts,
    refresh_all_tracked_locations,
    start_realtime_ingestion,
    stop_realtime_ingestion,
)
from app.services.context_service import (
    get_context,
    update_context,
    clear_context,
)
from app.services.imd_cap_service import (
    get_imd_cap_notifications,
    normalize_imd_cap_notifications,
    filter_alerts_for_location,
)
from app.services.nwp_service import (
    get_gfs_forecast,
    format_gfs_forecast,
)
from app.services.model_comparison_service import (
    compare_daily_forecasts,
)
from app.services.time_service import (
    resolve_date,
    get_time_range,
    today_india,
    filter_hourly_forecast,
)
from app.services.llm_service import (
    understand_with_llm,
    choose_weather_tool,
    generate_weather_response,
)

from app.services.query_service import understand_query

from app.services.historical_service import (
    get_historical_weather,
    format_historical_weather,
    calculate_average_temperature,
)

from app.services.weather_service import (
    get_current_weather,
    format_current_weather,
    get_forecast,
    format_forecast,
    get_hourly_forecast,
    format_hourly_forecast,
)

from app.services.location_service import search_location, normalize_location_name
from app.services.language_service import (
    canonicalize_for_fallback,
    extract_location_hint,
    resolve_response_language,
)

from app.services.advisory_service import (
    generate_weather_advisories,
)
from app.services.conversation_service import (
    UNRELATED_RESPONSE,
    get_conversation_response,
)
from app.services.voice_service import (
    VoiceValidationError,
    browser_tts_contract,
    transcribe_audio,
)


app = FastAPI(
    title="DemoWeatherGPT",
    description="AI-powered conversational weather intelligence platform",
    version="0.1.0",
)

realtime_tasks = []
# ============================================================
# ROOT
# ============================================================

@app.get("/")
def root():
    return {
        "message": "Welcome to WeatherGPT",
        "status": "Backend is running"
    }

@app.on_event("startup")
async def start_realtime_services():

    await init_db()

    global realtime_tasks

    realtime_tasks = (
        start_realtime_ingestion()
    )

    print(
        "Real-time ingestion started."
    )


@app.on_event("shutdown")
async def stop_realtime_services():

    await close_db()

    await stop_realtime_ingestion(
        realtime_tasks
    )

    print(
        "Real-time ingestion stopped."
    )
# ============================================================
# CURRENT WEATHER
# ============================================================

@app.get("/weather/current")
async def current_weather(
    latitude: float = Query(..., description="Latitude of the location"),
    longitude: float = Query(..., description="Longitude of the location"),
):
    weather = await get_current_weather(latitude, longitude)
    formatted_weather = format_current_weather(weather)

    return {
        "latitude": latitude,
        "longitude": longitude,
        "weather": formatted_weather,
    }

@app.get("/realtime/status")
async def realtime_status():

    cache = (
        await get_all_cache_status()
    )

    return {
        "service":
            "WeatherGPT Real-Time Ingestion",

        "status": "running",

        "cached_sources":
            len(cache),

        "cache": cache,
    }


@app.get("/performance/cache")
async def cache_performance_status():
    return await get_cache_metrics()

@app.post(
    "/realtime/refresh/{location_name}"
)
async def realtime_refresh_location(
    location_name: str,
):

    result = await refresh_location(
        location_name
    )

    return result
@app.get("/database/status")
async def database_status():

    try:

        async with AsyncSessionLocal() as session:

            result = await session.execute(
                text("SELECT 1")
            )

            result.scalar_one()

        return {
            "database": "PostgreSQL",
            "status": "connected",
        }

    except Exception as exc:

        return {
            "database": "PostgreSQL",
            "status": "error",
            "error": str(exc),
        }

@app.get(
    "/realtime/location/{location_name}"
)
async def realtime_location(
    location_name: str,
):

    data = (
        await get_cached_location_data(
            location_name,
            refresh_if_missing=True,
        )
    )

    if not data:

        return {
            "error":
                "Location not found."
        }

    return data

@app.get("/database/summary")
async def database_summary():

    async with AsyncSessionLocal() as session:

        users = await session.scalar(
            select(func.count(User.id))
        )

        conversations = await session.scalar(
            select(
                func.count(
                    Conversation.id
                )
            )
        )

        messages = await session.scalar(
            select(
                func.count(
                    ChatMessage.id
                )
            )
        )

        weather = await session.scalar(
            select(
                func.count(
                    WeatherRecord.id
                )
            )
        )

        alerts = await session.scalar(
            select(
                func.count(
                    OfficialAlert.id
                )
            )
        )

        ingestion_logs = await session.scalar(
            select(
                func.count(
                    IngestionLog.id
                )
            )
        )

    return {
        "users": users or 0,
        "conversations":
            conversations or 0,
        "chat_messages":
            messages or 0,
        "weather_records":
            weather or 0,
        "official_alerts":
            alerts or 0,
        "ingestion_logs":
            ingestion_logs or 0,
    }
@app.get("/realtime/imd")
async def realtime_imd():

    cached = (
        await get_cached_imd_alerts(
            refresh_if_missing=True
        )
    )

    if not cached:

        return {
            "alerts": [],
            "cached": False,
        }

    return {
        "cached": True,
        "updated_at":
            cached.get(
                "updated_at"
            ),
        "alerts":
            cached["data"].get(
                "alerts",
                []
            ),
    }

@app.post("/realtime/refresh")
async def realtime_refresh_all():

    locations = (
        await refresh_all_tracked_locations()
    )

    imd = None

    try:

        imd = await (
            get_cached_imd_alerts(
                refresh_if_missing=True
            )
        )

    except Exception as exc:

        imd = {
            "error": str(exc)
        }

    return {
        "locations": locations,
        "imd": bool(imd),
    }

@app.delete("/realtime/cache")
async def realtime_clear_cache():

    await clear_cache()

    return {
        "message":
            "Real-time cache cleared."
    }

@app.get("/weather/official-warnings")
async def official_warnings(
    latitude: float = Query(
        ...,
        description="Latitude of the location",
    ),
    longitude: float = Query(
        ...,
        description="Longitude of the location",
    ),
):
    cached = await get_cached_imd_alerts(refresh_if_missing=True)
    alerts = cached["data"].get("alerts", []) if cached else []

    matching_alerts = filter_alerts_for_location(
        alerts,
        latitude,
        longitude,
    )

    return {
        "source": (
            "India Meteorological Department"
        ),
        "official": True,
        "latitude": latitude,
        "longitude": longitude,
        "total_alerts": len(alerts),
        "location_alerts": len(
            matching_alerts
        ),
        "warnings": matching_alerts,
    }
# ============================================================
# LOCATION SEARCH
# ============================================================

@app.get("/locations/search")
async def location_search(
    name: str = Query(..., min_length=2, description="City or place name"),
):
    results = await search_location(name)

    return {
        "query": name,
        "results": results,
    }


# ============================================================
# CURRENT WEATHER BY LOCATION
# ============================================================

@app.get("/weather/current-by-location")
async def current_weather_by_location(
    name: str = Query(..., min_length=2, description="City or place name"),
):
    locations = await search_location(name)

    if not locations:
        return {
            "error": f"Could not find a location for '{name}'"
        }

    location = locations[0]

    weather_data = await get_current_weather(
        location["latitude"],
        location["longitude"],
    )

    weather = format_current_weather(weather_data)

    return {
        "location": {
            "name": location["name"],
            "country": location.get("country"),
            "state": location.get("admin1"),
            "latitude": location["latitude"],
            "longitude": location["longitude"],
        },
        "weather": weather,
    }


# ============================================================
# FORECAST BY LOCATION
# ============================================================

@app.get("/weather/forecast-by-location")
async def weather_forecast_by_location(
    name: str = Query(..., min_length=2, description="City or place name"),
):
    locations = await search_location(name)

    if not locations:
        return {
            "error": f"Could not find a location for '{name}'"
        }

    location = locations[0]

    forecast_data = await get_forecast(
        location["latitude"],
        location["longitude"],
    )

    forecast = format_forecast(forecast_data)

    return {
        "location": {
            "name": location["name"],
            "country": location.get("country"),
            "state": location.get("admin1"),
            "latitude": location["latitude"],
            "longitude": location["longitude"],
        },
        "forecast": forecast,
    }


# ============================================================
# HOURLY WEATHER BY LOCATION
# ============================================================

@app.get("/weather/hourly-by-location")
async def weather_hourly_by_location(
    name: str = Query(..., min_length=2, description="City or place name"),
):
    locations = await search_location(name)

    if not locations:
        return {
            "error": f"Could not find a location for '{name}'"
        }

    location = locations[0]

    hourly_data = await get_hourly_forecast(
        location["latitude"],
        location["longitude"],
    )

    hourly_forecast = format_hourly_forecast(hourly_data)

    return {
        "location": {
            "name": location["name"],
            "country": location.get("country"),
            "state": location.get("admin1"),
            "latitude": location["latitude"],
            "longitude": location["longitude"],
        },
        "hourly_forecast": hourly_forecast,
    }


# ============================================================
# WEATHER ADVISORY BY LOCATION
# ============================================================

@app.get("/weather/advisory-by-location")
async def weather_advisory_by_location(
    name: str = Query(..., min_length=2, description="City or place name"),
):
    locations = await search_location(name)

    if not locations:
        return {
            "error": f"Could not find a location for '{name}'"
        }

    location = locations[0]

    hourly_data = await get_hourly_forecast(
        location["latitude"],
        location["longitude"],
    )

    hourly_forecast = format_hourly_forecast(hourly_data)

    next_hours = hourly_forecast[:6]

    advisories = []

    for hour in next_hours:

        hour_advisories = generate_weather_advisories(
            temperature_c=hour["temperature_c"],
            rain_probability_percent=hour["rain_probability_percent"],
            wind_speed_kmh=hour["wind_speed_kmh"],
            precipitation_mm=hour["precipitation_mm"],
            weather_code=hour["weather_code"],
            humidity_percent=hour["humidity_percent"],
        )

        for advisory in hour_advisories:

            if advisory not in advisories:
                advisories.append(advisory)

    return {
        "location": {
            "name": location["name"],
            "country": location.get("country"),
            "state": location.get("admin1"),
        },
        "advisories": advisories,
        "forecast_used": next_hours,
    }
# whether gfs endpoint
@app.get("/weather/gfs")
async def gfs_weather(
    latitude: float = Query(
        ...,
        description="Latitude of the location",
    ),
    longitude: float = Query(
        ...,
        description="Longitude of the location",
    ),
):

    gfs_data = await get_gfs_forecast(
        latitude,
        longitude,
    )

    gfs_forecast = format_gfs_forecast(
        gfs_data
    )

    return {
        "latitude": latitude,
        "longitude": longitude,
        "model": gfs_forecast["model"],
        "provider": gfs_forecast["provider"],
        "hourly": gfs_forecast["hourly"],
        "daily": gfs_forecast["daily"],
    }
# ============================================================
# CHAT REQUEST
# ============================================================

class ChatRequest(BaseModel):
    message: str
    session_id: str = "default"
    language: str | None = None

@app.delete("/chat/session/{session_id}")
async def delete_chat_session(session_id: str):

    clear_context(session_id)

    return {
        "message": "Conversation cleared",
        "session_id": session_id,
    }

@app.get("/weather/model-comparison")
async def weather_model_comparison(
    latitude: float = Query(..., description="Latitude of the location"),
    longitude: float = Query(..., description="Longitude of the location"),
):
    # Existing weather forecast
    forecast_data = await get_forecast(
        latitude,
        longitude,
    )

    # Format using your existing forecast formatter
    forecast = format_forecast(forecast_data)

    # GFS forecast
    gfs_data = await get_gfs_forecast(
        latitude,
        longitude,
    )

    gfs_forecast = format_gfs_forecast(gfs_data)

    comparison = compare_daily_forecasts(
        forecast,
        gfs_forecast["daily"],
    )

    return {
        "latitude": latitude,
        "longitude": longitude,
        "base_forecast_model": "Open-Meteo",
        "nwp_model": gfs_forecast["model"],
        "nwp_provider": gfs_forecast["provider"],
        "comparison": comparison,
    }
# ============================================================
# CHAT
# ============================================================

async def process_chat_message(request: ChatRequest):

    # --------------------------------------------------------
    # STEP 0: Load conversation context
    # --------------------------------------------------------

    context = get_context(request.session_id)
    language = resolve_response_language(
        request.language,
        request.message,
        context.get("language"),
    )

    await save_chat_message(
        session_id=request.session_id,
        role="user",
        content=request.message,
    )

    async def save_assistant_response(
    response_text: str,
    tool_used: str | None = None,
    ):
        await save_chat_message(
            session_id=request.session_id,
            role="assistant",
            content=response_text,
            tool_used=tool_used,
        )

    conversation = get_conversation_response(request.message)

    if conversation:
        intent, response_text = conversation
        query = {
            "intent": "conversation",
            "location": None,
            "time": "unspecified",
            "activity": None,
        }
        tool_choice = {
            "tool": "conversation",
            "reason": "Recognized casual conversation.",
        }

        update_context(
            request.session_id,
            request.message,
            response_text,
            query,
            language=language,
        )
        await save_assistant_response(response_text, "conversation")

        return {
            "message": request.message,
            "understanding": query,
            "tool": tool_choice,
            "response": response_text,
            "language": language,
        }

    # --------------------------------------------------------
    # STEP 1: Understand query using Groq
    # --------------------------------------------------------

    try:
            query = await understand_with_llm(
        request.message,
        context,
        language,
    )

    except Exception:
        # Fallback to existing rule-based understanding
        query = understand_query(canonicalize_for_fallback(request.message, language))
        query["location"] = query.get("location") or extract_location_hint(
            request.message,
            language,
        )
    if query.get("intent") not in {"conversation", "unrelated", "unknown"} and not query.get("location"):
        previous_location = context.get("location")

        if previous_location:
            query["location"] = previous_location
    intent = query.get("intent")
    location_name = normalize_location_name(query.get("location"))
    query["location"] = location_name
    query["language"] = language

    # --------------------------------------------------------
    # STEP 2: Select weather tool using Groq
    # --------------------------------------------------------

    try:
        tool_choice = await choose_weather_tool(
    request.message,
    context,
    language,
)

    except Exception:
        tool_choice = {
            "tool": "none",
            "reason": "Tool selection was unavailable."
        }

    selected_tool = tool_choice.get("tool")

    # --------------------------------------------------------
    # STEP 3: Normalize tool name
    # --------------------------------------------------------

    # Our query understanding uses "historical",
    # while the weather tool is called "historical_weather".

    if selected_tool == "historical":
        selected_tool = "historical_weather"

    # --------------------------------------------------------
    # STEP 4: Fallback to intent if tool selection failed
    # --------------------------------------------------------

    if selected_tool in (None, "none"):

        intent_to_tool = {
            "current_weather": "current_weather",
            "forecast": "forecast",
            "historical": "historical_weather",
            "climate": "climate",
            "advisory": "advisory",
        }

        selected_tool = intent_to_tool.get(intent, "none")

    # Update returned tool information with the actual tool
    tool_choice["tool"] = selected_tool

    if query.get("intent") in {"unrelated", "unknown"} or selected_tool == "conversation":
        response_text = UNRELATED_RESPONSE

        if selected_tool == "conversation":
            response_text = (
                "I'm here to help with weather, forecasts, alerts, climate, "
                "and weather-related advice."
            )

        await save_assistant_response(response_text, selected_tool)

        return {
            "message": request.message,
            "understanding": query,
            "tool": tool_choice,
            "response": response_text,
        }

    # --------------------------------------------------------
    # STEP 5: Location required
    # --------------------------------------------------------

    if not location_name:

        response_text = (
            "Please provide a city or location. "
            "For example: What's the weather in Ahmedabad?"
        )

        await save_assistant_response(
            response_text,
            selected_tool,
        )

        return {
            "message": request.message,
            "understanding": query,
            "tool": tool_choice,
            "response": response_text,
        }

    # --------------------------------------------------------
    # STEP 6: Find location
    # --------------------------------------------------------

    locations = await search_location(location_name)

    if not locations:

        response_text = (
            f"I could not find a location named "
            f"'{location_name}'."
        )

        await save_assistant_response(
            response_text,
            selected_tool,
        )

        return {
            "message": request.message,
            "understanding": query,
            "tool": tool_choice,
            "response": response_text,
        }

    location = locations[0]

    latitude = location["latitude"]
    longitude = location["longitude"]

    location_info = {
        "name": location["name"],
        "country": location.get("country"),
        "state": location.get("admin1"),
    }

    # ========================================================
    # TOOL: CURRENT WEATHER
    # ========================================================

    if selected_tool == "current_weather":

        weather_data = await get_current_weather(
            latitude,
            longitude,
        )

        weather = format_current_weather(weather_data)

        data_for_llm = {
            "location": location_info,
            "weather": weather,
        }

        try:
            response_text = await generate_weather_response(
                request.message,
                data_for_llm,
                language,
            )
        except Exception:
            response_text = weather

        update_context(
            request.session_id,
            request.message,
            response_text,
            query,
            location_info,
        )
        await save_assistant_response(
            response_text,
            selected_tool,
        )
        return {
            "message": request.message,
            "understanding": query,
            "tool": tool_choice,
            "location": location_info,
            "weather": weather,
            "response": response_text,
        }

    # ========================================================
    # TOOL: FORECAST
    # ========================================================

    if selected_tool == "forecast":
        # ====================================================
        # HOURLY TIME REQUESTS
        # ====================================================

        hourly_time_values = {
            "tonight",
            "tomorrow_morning",
            "tomorrow_afternoon",
            "tomorrow_evening",
            "day_after_tomorrow_morning",
            "next_24_hours",
            "next_48_hours",
        }

        if query.get("time") in hourly_time_values:

            hourly_data = await get_hourly_forecast(
                latitude,
                longitude,
            )

            hourly_forecast = format_hourly_forecast(
                hourly_data
            )

            filtered_hourly = filter_hourly_forecast(
                hourly_forecast,
                query.get("time"),
            )

            data_for_llm = {
                "location": location_info,
                "hourly_forecast": filtered_hourly,
            }

            try:
                response_text = await generate_weather_response(
                    request.message,
                    data_for_llm,
                    language,
                )
            except Exception:
                response_text = (
                    "Here is the available hourly forecast."
                )

            update_context(
                request.session_id,
                request.message,
                response_text,
                query,
                location_info,
            )

            await save_assistant_response(
                response_text,
                selected_tool,
            )

            return {
                "message": request.message,
                "understanding": query,
                "tool": tool_choice,
                "location": location_info,
                "hourly_forecast": filtered_hourly,
                "response": response_text,
            }
        forecast_data = await get_forecast(
            latitude,
            longitude,
        )

        forecast = format_forecast(forecast_data)

        # Tomorrow
        if query.get("time") == "tomorrow":

            tomorrow = tomorrow = today_india() + timedelta(days=1)
            tomorrow_string = tomorrow.isoformat()

            forecast = [
                day
                for day in forecast
                if day["date"] == tomorrow_string
            ]

        # Day after tomorrow
        elif query.get("time") == "day_after_tomorrow":

            day_after_tomorrow = today_india() + timedelta(days=2)
            day_after_tomorrow_string = (
                day_after_tomorrow.isoformat()
            )

            forecast = [
                day
                for day in forecast
                if day["date"] == day_after_tomorrow_string
            ]

        # Today
        elif query.get("time") == "today":

            today_string = today_india().isoformat()

            forecast = [
                day
                for day in forecast
                if day["date"] == today_string
            ]

        # Next 3 days
        elif query.get("time") == "next_3_days":

            forecast = forecast[:3]

        # Next few days
        elif query.get("time") == "next_few_days":

            forecast = forecast[:5]

        # Next week
        elif query.get("time") == "next_week":

            forecast = forecast[:7]

        data_for_llm = {
            "location": location_info,
            "forecast": forecast,
        }

        try:
            response_text = await generate_weather_response(
                request.message,
                data_for_llm,
                language,
            )
        except Exception:
            response_text = "Here is the available forecast."

        update_context(
            request.session_id,
            request.message,
            response_text,
            query,
            location_info,
        )
        await save_assistant_response(
            response_text,
            selected_tool,
        )
        return {
            "message": request.message,
            "understanding": query,
            "tool": tool_choice,
            "location": location_info,
            "forecast": forecast,
            "response": response_text,
        }

    # ========================================================
    # TOOL: HISTORICAL WEATHER
    # ========================================================

    if selected_tool == "historical_weather":

        if query.get("time") == "yesterday":

            yesterday = today_india() - timedelta(days=1)
            date_string = yesterday.isoformat()

            historical_data = await get_historical_weather(
                latitude,
                longitude,
                date_string,
                date_string,
            )

        elif query.get("time") == "last_few_days":

            end_date = today_india() - timedelta(days=1)
            start_date = end_date - timedelta(days=2)

            historical_data = await get_historical_weather(
                latitude,
                longitude,
                start_date.isoformat(),
                end_date.isoformat(),
            )

        elif query.get("time") == "last_week":

            end_date = today_india() - timedelta(days=1)
            start_date = end_date - timedelta(days=6)

            historical_data = await get_historical_weather(
                latitude,
                longitude,
                start_date.isoformat(),
                end_date.isoformat(),
            )

        else:

            response_text = (
                "I can currently handle historical weather "
                "for yesterday, the last few days, or last week."
            )

            await save_assistant_response(
                response_text,
                selected_tool,
            )

            return {
                "message": request.message,
                "understanding": query,
                "tool": tool_choice,
                "response": response_text,
            }

        historical = format_historical_weather(
            historical_data
        )

        data_for_llm = {
            "location": location_info,
            "historical_weather": historical,
        }

        try:
            response_text = await generate_weather_response(
                request.message,
                data_for_llm,
                language,
            )
        except Exception:
            response_text = "Here is the available historical weather data."

        update_context(
            request.session_id,
            request.message,
            response_text,
            query,
            location_info,
        )

        await save_assistant_response(
            response_text,
            selected_tool,
        )
        return {
            "message": request.message,
            "understanding": query,
            "tool": tool_choice,
            "location": location_info,
            "historical_weather": historical,
            "response": response_text,
        }

    # ========================================================
    # TOOL: CLIMATE
    # ========================================================

    if selected_tool == "climate":

        end_date = today_india() - timedelta(days=1)
        start_date = end_date - timedelta(days=6)

        climate_data = await get_historical_weather(
            latitude,
            longitude,
            start_date.isoformat(),
            end_date.isoformat(),
        )

        climate = format_historical_weather(
            climate_data
        )

        average_temperature = calculate_average_temperature(
            climate
        )

        data_for_llm = {
            "location": location_info,
            "period": "last_7_days",
            "average_temperature_c": average_temperature,
            "climate_data": climate,
        }

        try:
            response_text = await generate_weather_response(
                request.message,
                data_for_llm,
                language,
            )
        except Exception:
            response_text = (
                f"The average temperature was "
                f"{average_temperature}°C."
            )


        update_context(
            request.session_id,
            request.message,
            response_text,
            query,
            location_info,
        )

        await save_assistant_response(
            response_text,
            selected_tool,
        )
        return {
            "message": request.message,
            "understanding": query,
            "tool": tool_choice,
            "location": location_info,
            "climate": {
                "period": "last_7_days",
                "average_temperature_c": average_temperature,
            },
            "response": response_text,
        }

    # ========================================================
    # TOOL: ADVISORY
    # ========================================================

    if selected_tool == "advisory":

        hourly_data = await get_hourly_forecast(
            latitude,
            longitude,
        )

        hourly_forecast = format_hourly_forecast(
            hourly_data
        )

        next_hours = hourly_forecast[:6]

        advisories = []

        for hour in next_hours:

            hour_advisories = generate_weather_advisories(
                temperature_c=hour["temperature_c"],
                rain_probability_percent=(
                    hour["rain_probability_percent"]
                ),
                wind_speed_kmh=hour["wind_speed_kmh"],
                precipitation_mm=hour["precipitation_mm"],
                weather_code=hour["weather_code"],
                humidity_percent=hour["humidity_percent"],
            )

            for advisory in hour_advisories:

                if advisory not in advisories:
                    advisories.append(advisory)

        data_for_llm = {
            "location": location_info,
            "advisories": advisories,
            "forecast_used": next_hours,
        }

        try:
            response_text = await generate_weather_response(
                request.message,
                data_for_llm,
                language,
            )
        except Exception:
            response_text = (
                "I checked the upcoming weather conditions "
                "for potential risks."
            )

        update_context(
            request.session_id,
            request.message,
            response_text,
            query,
            location_info,
        )
        await save_assistant_response(
            response_text,
            selected_tool,
        )
        return {
            "message": request.message,
            "understanding": query,
            "tool": tool_choice,
            "location": location_info,
            "advisories": advisories,
            "response": response_text,
        }
# ========================================================
# TOOL: RECOMMENDATION
# ========================================================

    if selected_tool == "recommendation":

        forecast_data = await get_forecast(
            latitude,
            longitude,
        )

        forecast = format_forecast(forecast_data)

        # Use tomorrow when the user asks about future weather.
        # Otherwise use today's forecast when available.
        target_weather = forecast[0] if forecast else {}

        if query.get("time") == "tomorrow" and len(forecast) > 1:
            target_weather = forecast[1]

        recommendations = generate_weather_recommendations(
            temperature_c=target_weather.get("temperature_max_c"),
            temperature_max_c=target_weather.get("temperature_max_c"),
            temperature_min_c=target_weather.get("temperature_min_c"),
            precipitation_mm=target_weather.get("precipitation_mm"),
            wind_speed_max_kmh=target_weather.get("wind_speed_max_kmh"),
            condition=target_weather.get("condition"),
            activity=query.get("activity"),
    )

        data_for_llm = {
            "location": location_info,
            "weather": target_weather,
            "recommendations": recommendations,
        }

        try:
            response_text = await generate_weather_response(
                request.message,
                data_for_llm,
                language,
            )
        except Exception:
            response_text = "Here are my weather-based recommendations."

        update_context(
            request.session_id,
            request.message,
            response_text,
            query,
            location_info,
        )

        await save_assistant_response(
            response_text,
            selected_tool,
        )

        return {
            "message": request.message,
            "understanding": query,
            "tool": tool_choice,
            "location": location_info,
            "recommendations": recommendations,
            "weather_used": target_weather,
            "response": response_text,
        }
# ========================================================
# DISASTER ALERT
# ========================================================

    if selected_tool == "disaster_alert":

        forecast_data = await get_forecast(
            latitude,
            longitude,
        )

        forecast = format_forecast(
            forecast_data
        )

        alerts = generate_disaster_alerts(
            forecast
        )

        data_for_llm = {
            "location": location_info,
            "alerts": alerts,
            "forecast": forecast,
        }

        try:

            response_text = await generate_weather_response(
                request.message,
                data_for_llm,
                language,
            )

        except Exception:

            if alerts:

                response_text = (
                    f"I found {len(alerts)} potential "
                    "weather risk alert(s). Please review "
                    "the alerts and follow official warnings."
                )

            else:

                response_text = (
                    "No significant extreme-weather risk "
                    "was detected in the available forecast."
                )

        update_context(
            request.session_id,
            request.message,
            response_text,
            query,
            location_info,
        )

        await save_assistant_response(
            response_text,
            selected_tool,
        )

        return {
            "message": request.message,
            "understanding": query,
            "tool": tool_choice,
            "location": location_info,
            "alerts": alerts,
            "forecast_used": forecast,
            "response": response_text,
        }
# ========================================================
# NWP / GFS
# ========================================================

    if selected_tool == "nwp_gfs":

        realtime_data = (
            await get_cached_location_data(
                location_info.get("name"),
                refresh_if_missing=True,
            )
    )

        cached_gfs = (
            realtime_data.get("gfs")
            if realtime_data
            else None
    )

        if cached_gfs:

            gfs_forecast = (
                cached_gfs[
                    "data"
                ].get(
                    "formatted"
                )
            )

        else:

            gfs_data = (
                await get_gfs_forecast(
                    latitude,
                    longitude,
                )
            )

            gfs_forecast = (
                format_gfs_forecast(
                    gfs_data
                )
            )

        data_for_llm = {
            "location": location_info,
            "model": gfs_forecast["model"],
            "provider": gfs_forecast["provider"],
            "daily": gfs_forecast["daily"],
            "hourly": gfs_forecast["hourly"][:24],
        }

        try:

            response_text = await generate_weather_response(
                request.message,
                data_for_llm,
                language,
            )

        except Exception:

            response_text = (
                "Here is the available NCEP GFS "
                "numerical weather prediction data."
            )

        update_context(
            request.session_id,
            request.message,
            response_text,
            query,
            location_info,
        )
        await save_assistant_response(
            response_text,
            selected_tool,
        )
        return {
            "message": request.message,
            "understanding": query,
            "tool": tool_choice,
            "location": location_info,
            "nwp": {
                "model": gfs_forecast["model"],
                "provider": gfs_forecast["provider"],
            },
            "daily_forecast": gfs_forecast["daily"],
            "hourly_forecast": gfs_forecast["hourly"][:24],
            "response": response_text,
        }
#model comparison endpoint chat connection
    if selected_tool == "model_comparison":
        # Get the normal forecast
        forecast_data = await get_forecast(
            latitude,
            longitude,
        )

        forecast = format_forecast(forecast_data)

        # Get GFS
        gfs_data = await get_gfs_forecast(
            latitude,
            longitude,
        )

        gfs_forecast = format_gfs_forecast(gfs_data)

        # Compare both models
        comparison = compare_daily_forecasts(
            forecast,
            gfs_forecast["daily"],
        )

        data_for_llm = {
            "location": location_info,
            "base_forecast_model": "Open-Meteo",
            "nwp_model": gfs_forecast["model"],
            "nwp_provider": gfs_forecast["provider"],
            "comparison": comparison,
        }

        try:
            response_text = await generate_weather_response(
                request.message,
                data_for_llm,
                language,
            )
        except Exception:
            if comparison:
                first = comparison[0]

                response_text = (
                    f"Model comparison for {first['date']}: "
                    f"confidence is {first['confidence']}. "
                    f"{first['explanation']}"
                )
            else:
                response_text = (
                    "There is not enough overlapping forecast "
                    "data to compare the models."
                )

        update_context(
            request.session_id,
            request.message,
            response_text,
            query,
            location_info,
        )
        await save_assistant_response(
            response_text,
            selected_tool,
        )
        return {
            "message": request.message,
            "understanding": query,
            "tool": tool_choice,
            "location": location_info,
            "model_comparison": {
                "base_model": "Open-Meteo",
                "nwp_model": gfs_forecast["model"],
                "nwp_provider": gfs_forecast["provider"],
                "comparison": comparison,
            },
            "response": response_text,
        }   
    
    if selected_tool == "official_warning":
        cached_imd = (
        await get_cached_imd_alerts(
            refresh_if_missing=True
        )
    )

        if cached_imd:

            all_alerts = (
                cached_imd[
                    "data"
                ].get(
                    "alerts",
                    []
                )
            )

        else:

            all_alerts = []

        matching_alerts = filter_alerts_for_location(
            all_alerts,
            latitude,
            longitude,
            location_info.get("name"),
            location_info.get("state"),
        )

        data_for_llm = {
            "location": location_info,
            "source": (
                "India Meteorological Department"
            ),
            "official": True,
            "warnings": matching_alerts,
        }

        try:
            response_text = await generate_weather_response(
                request.message,
                data_for_llm,
                language,
            )
        except Exception:
            if matching_alerts:
                response_text = (
                    "There is an official IMD warning "
                    "affecting this location. "
                    f"Event: "
                    f"{matching_alerts[0].get('event')}. "
                    f"Severity: "
                    f"{matching_alerts[0].get('severity')}."
                )
            else:
                response_text = (
                    "No matching official IMD warning "
                    "was found for this location in "
                    "the latest available alerts."
                )

        update_context(
            request.session_id,
            request.message,
            response_text,
            query,
            location_info,
        )
        await save_assistant_response(
            response_text,
            selected_tool,
        )
        return {
            "message": request.message,
            "understanding": query,
            "tool": tool_choice,
            "location": location_info,
            "official_warnings": matching_alerts,
            "response": response_text,
        }   
    # ========================================================
    # UNKNOWN / UNSUPPORTED
    # ========================================================

    response_text = (
    "I'm not sure how to handle that weather question yet."
    )

    await save_assistant_response(
            response_text,
            selected_tool,
        )

    return {
            "message": request.message,
            "understanding": query,
            "tool": tool_choice,
            "response": response_text,
        }


@app.post("/chat", summary="Send a text query to WeatherGPT")
async def chat(request: ChatRequest):
    """Public text-chat endpoint retained for backward compatibility."""
    return await process_chat_message(request)


async def _voice_transcription(audio: UploadFile, language: str | None) -> dict:
    try:
        return await transcribe_audio(
            audio.filename,
            audio.content_type,
            await audio.read(),
            language,
        )
    except VoiceValidationError as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail="Speech transcription is unavailable. Please try again.") from exc
    finally:
        await audio.close()


@app.post(
    "/voice/transcribe",
    summary="Transcribe an uploaded audio recording",
    description="Accepts WAV, MP3, WebM, OGG, MP4, or M4A up to VOICE_MAX_AUDIO_SIZE_MB (10 MB by default).",
)
async def voice_transcribe(
    audio: UploadFile = File(..., description="Audio recording to transcribe"),
    session_id: str = Form("default", description="Conversation session identifier"),
    language: str | None = Form(None, description="Optional supported language code"),
):
    transcription = await _voice_transcription(audio, language)
    return {"success": True, **transcription, "session_id": session_id}


@app.post(
    "/voice/chat",
    summary="Transcribe audio and send it through the WeatherGPT chat pipeline",
    description="Uses the same session context, database persistence, language layer, and weather tools as POST /chat.",
)
async def voice_chat(
    audio: UploadFile = File(..., description="Audio recording to transcribe and process"),
    session_id: str = Form("default", description="Conversation session identifier"),
    language: str | None = Form(None, description="Optional supported language code"),
):
    transcription = await _voice_transcription(audio, language)
    response = await process_chat_message(ChatRequest(
        message=transcription["transcript"],
        session_id=session_id,
        language=transcription["language"],
    ))
    return {
        "success": True,
        "transcript": transcription["transcript"],
        "language": transcription["language"],
        "session_id": session_id,
        "response": response.get("response"),
        "chat": response,
        "tts": browser_tts_contract(transcription["language"]),
    }
