import os
import json
from dotenv import load_dotenv
from groq import AsyncGroq

from app.services.weather_tools import WEATHER_TOOLS

# Load environment variables
load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if not GROQ_API_KEY:
    raise ValueError("GROQ_API_KEY is not set in .env")

client = AsyncGroq(api_key=GROQ_API_KEY)

MODEL_NAME = "qwen/qwen3.8-27b"


async def ask_llm(message: str) -> str:
    """
    Send a request to Groq and return the response text.
    """

    response = await client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {
                "role": "user",
                "content": message
            }
        ],
        temperature=0
    )

    return response.choices[0].message.content


async def choose_weather_tool(
    message: str,
    context: dict | None = None,
) -> dict:

    context = context or {}

    previous_location = context.get("location")
    previous_intent = context.get("last_intent")

    prompt = f"""
You are the tool-selection system for WeatherGPT.

Choose exactly ONE tool that should handle the user's CURRENT question.

Previous conversation context:

Location:
{previous_location}

Previous intent:
{previous_intent}

Available tools:

- current_weather: Get current weather conditions.

- forecast: Get upcoming weather forecasts.

- historical_weather: Get weather from previous days.

- climate: Get climate information, climate averages, or long-term
  climate trends.

- advisory: Provide general weather-related safety advice, risks,
  or dangerous-condition guidance.

- recommendation: Provide practical weather-based recommendations
  for activities, clothing, travel, outdoor plans, farming,
  or daily decisions.

- disaster_alert: Detect extreme weather and disaster-related risks
  and provide preliminary risk alerts and early-warning information.

- nwp_gfs: Retrieve numerical weather prediction information
  specifically from the NCEP GFS model.

- model_comparison: Compare the normal weather forecast with
  the NCEP GFS model, compare weather models, explain differences
  between models, or determine whether models agree or disagree.

- official_warning: Retrieve official government weather warnings,
  IMD warnings, cyclone warnings, flood warnings, or other
  authoritative alerts.

Rules:

1. If the user explicitly asks for CURRENT weather:
   choose current_weather.

2. If the user asks about FUTURE weather or a forecast:
   choose forecast.

3. If the user asks about PAST weather:
   choose historical_weather.

4. If the user asks about climate averages, climate trends,
   or long-term climate information:
   choose climate.

5. If the user asks for practical advice such as:
   umbrella, clothing, running, travel, outdoor activities,
   farming decisions, or whether an activity is suitable:
   choose recommendation.

6. If the user asks about extreme weather risks or disaster risks,
   such as dangerous heat, heavy rain, severe storms, flooding risk,
   strong winds, or other potentially dangerous conditions:
   choose disaster_alert.

7. If the user specifically asks for GFS/NCEP GFS model data:
   choose nwp_gfs.

8. If the user asks to:
   - compare weather models
   - compare forecasts
   - compare GFS with the normal forecast
   - compare GFS with another model
   - explain differences between weather models
   - check whether weather models agree
   - check model agreement/disagreement
   - compare model predictions

   choose model_comparison.

9. If the user explicitly asks for:
   - IMD alerts
   - IMD warnings
   - official weather warnings
   - government weather alerts
   - cyclone warnings
   - flood warnings
   - authoritative weather warnings

   choose official_warning.

10. If the user asks a follow-up such as:
    "What about tomorrow?"
    "Will it rain?"
    "How about Sunday?"

    use the previous conversation context to determine the
    appropriate tool.

11. Use the user's CURRENT question as the primary signal.
    Use previous context only to resolve ambiguous follow-up questions.

12. If the question is unrelated to weather:
   choose none.

13. If the user is only greeting, making small talk, saying thanks,
    or saying goodbye, choose conversation. Do not select a weather tool.

Important:
- Do NOT choose none if the question is clearly about weather.
- Do NOT choose advisory merely because the question contains
  the word "warning" if the user is asking for an official IMD
  or government warning. Use official_warning in that case.
- Do NOT choose nwp_gfs when the user wants to COMPARE models.
  Use model_comparison instead.
- Do NOT choose forecast when the user explicitly asks to COMPARE
  weather models. Use model_comparison instead.

Return ONLY valid JSON with exactly these fields:

{{
    "tool": "current_weather | forecast | historical_weather | climate | advisory | recommendation | disaster_alert | nwp_gfs | model_comparison | official_warning | conversation | none",
    "reason": "short explanation"
}}

User question:

{message}
"""

    result = await ask_llm(prompt)

    return json.loads(result)

async def understand_with_llm(
    message: str,
    context: dict | None = None,
) -> dict:

    context = context or {}

    previous_location = context.get("location")
    previous_intent = context.get("last_intent")
    previous_time = context.get("last_time")

    history = context.get("history", [])

    history_text = "\n".join(
        f"User: {item['user']}\nAssistant: {item['assistant']}"
        for item in history
    )

    prompt = f"""
You are the query understanding system for WeatherGPT.

Analyze the user's current weather question using both
the current message and the previous conversation context.

Previous context:

Location:
{previous_location}

Previous intent:
{previous_intent}

Previous time:
{previous_time}

Recent conversation:
{history_text}

Return ONLY valid JSON.

The JSON must contain exactly these fields:

{{
    "intent": "current_weather | forecast | advisory | historical | climate | recommendation | disaster_alert | nwp_gfs | model_comparison | official_warning | conversation | unrelated",
    "location": "city name or null",
    "time": "now | today | tonight | tomorrow | tomorrow_morning | tomorrow_afternoon | tomorrow_evening | day_after_tomorrow | day_after_tomorrow_morning | next_3_days | next_few_days | next_week | this_weekend | this_saturday | this_sunday | next_monday | next_tuesday | next_wednesday | next_thursday | next_friday | next_saturday | next_sunday | next_24_hours | next_48_hours | yesterday | last_few_days | last_week | unspecified"
    "activity": "activity or decision being asked about, or null"
}}

Rules:

1. Understand the CURRENT user message first.

- disaster_alert = questions about extreme weather,
  severe weather, disaster risk, early warnings, flooding,
  extreme heat, dangerous winds, thunderstorms, or emergency weather alerts.
2. If the current message does not contain a location,
   use the previous conversation location when appropriate.
Time interpretation:

- "tonight" = tonight
- "tomorrow morning" = tomorrow_morning
- "tomorrow afternoon" = tomorrow_afternoon
- "tomorrow evening" = tomorrow_evening
- "day after tomorrow morning" = day_after_tomorrow_morning
- "this weekend" = this_weekend
- "this Saturday" = this_saturday
- "this Sunday" = this_sunday
- "next Monday" = next_monday
- "next Tuesday" = next_tuesday
- "next Wednesday" = next_wednesday
- "next Thursday" = next_thursday
- "next Friday" = next_friday
- "next Saturday" = next_saturday
- "next Sunday" = next_sunday
- "next 24 hours" = next_24_hours
- "next 48 hours" = next_48_hours

If the user asks about a specific weekday, determine the appropriate
upcoming occurrence relative to today's date.

Do not guess a date if the wording is genuinely ambiguous.
3. Example:

Previous location: Delhi
User: What about tomorrow?

Return:
{{
    "intent": "forecast",
    "location": "Delhi",
    "time": "tomorrow"
}}

4. Example:

Previous location: Mumbai
User: Will it rain?

Return a forecast-related intent and use Mumbai as the location.

5. Do not put time expressions inside location.

6. Extract only the actual city/location name.

7. If no location exists in the current message or context,
   return null.
"Is there an official warning for Delhi?"
"Any IMD alert in Mumbai?"
"Is there a government weather warning?"
"Are there any official alerts near me?"
8. If no time is specified, return "unspecified".

9. current_weather = current conditions.

10. forecast = future weather.

11. advisory = warnings, risks, dangerous or severe weather.

12. historical = weather from the past.
- model_comparison = questions asking to compare weather models,
  compare GFS with the normal forecast, check model agreement,
  forecast confidence, or differences between models.
  example:"Compare GFS with the weather forecast"
"Do the models agree for Delhi?"
"How confident is tomorrow's forecast?"
"Compare the NCEP GFS prediction"
"Are the weather models showing the same rain forecast?"
13. climate = climate averages, trends or climate analysis.

- nwp_gfs = questions specifically asking about numerical weather
  prediction, GFS model data, model forecasts, or NWP information.
  Example:"Show me the GFS forecast for Delhi."

"What does the GFS model predict for Mumbai?"

"Give me the numerical weather prediction for Pune."

"Compare the GFS forecast for Ahmedabad."

14. conversation = greetings, small talk, thanks, or goodbyes.

15. unrelated = a non-weather question that is not casual conversation.
- recommendation = questions asking what the user should do based on weather,
  including umbrella, clothing, outdoor activities, running, travel,
  farming, events, or safety decisions.
  
Current user message:

{message}
"""

    result = await ask_llm(prompt)

    return json.loads(result)

async def generate_weather_response(
    user_message: str,
    weather_data: dict,
) -> str:
    """
    Generate a natural-language response using the weather data.
    """

    prompt = f"""
You are WeatherGPT, an intelligent weather assistant.

Answer the user's question using ONLY the weather data provided below.

User question:
{user_message}

Weather data:
{json.dumps(weather_data, ensure_ascii=False, default=str)}

Instructions:

- Give a clear, natural and useful answer.
- Do not invent weather information.
- Do not mention internal tools, APIs, Python, JSON, or implementation details.
- If the data contains temperatures, mention them with °C.
- If rain probability or precipitation is available, mention it when relevant.
- If wind information is available, mention it when relevant.
- For forecasts, summarize the relevant days rather than dumping raw data.
- For historical questions, summarize the historical information clearly.
- For advisories, clearly mention any risks or warnings.
- Keep the answer concise unless the user asks for detail.
When responding to disaster or extreme-weather alerts:

- Clearly state the risk.
- State the affected date/time when available.
- Explain the practical precaution.
- Do not exaggerate the risk.
- Do not claim an official warning unless the data explicitly
  comes from an official warning source.
- Distinguish between forecast-based risk and official alerts.
Return ONLY the final answer text.
"""

    return await ask_llm(prompt)
