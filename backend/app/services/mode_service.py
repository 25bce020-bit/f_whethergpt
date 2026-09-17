"""Mode selection and persona configuration for WeatherGPT chat requests."""

from dataclasses import dataclass
from enum import Enum
import re


class WeatherMode(str, Enum):
    NORMAL = "normal"
    FARMER = "farmer"
    RESEARCHER = "researcher"
    TRAVELLER = "traveller"


@dataclass(frozen=True)
class ModeConfiguration:
    name: str
    description: str
    persona_prompt: str


MODE_CONFIGURATIONS: dict[WeatherMode, ModeConfiguration] = {
    WeatherMode.NORMAL: ModeConfiguration(
        name="Normal Mode",
        description="Universal weather intelligence for everyday questions.",
        persona_prompt="Provide clear, practical general weather guidance.",
    ),
    WeatherMode.FARMER: ModeConfiguration(
        name="Farmer Mode",
        description="Weather framing for agricultural decisions.",
        persona_prompt=(
            "Frame supplied farmer_advisory data for an agricultural user. Use only "
            "the supplied weather facts and deterministic recommendations. Clearly "
            "separate official IMD warnings from WeatherGPT farmer advice. Never claim "
            "soil-moisture readings, crop maturity, chemical-specific instructions, or "
            "crop facts not present in the data."
        ),
    ),
    WeatherMode.RESEARCHER: ModeConfiguration(
        name="Researcher Mode",
        description="Structured analysis of retrieved weather observations, forecasts, and model output.",
        persona_prompt=(
            "Provide a concise research-style summary using only the supplied "
            "researcher_analysis and weather data. Clearly separate retrieved "
            "observations, forecast/model output, WeatherGPT-derived interpretation, "
            "and official IMD warnings. Do not invent measurements, confidence, "
            "long-term climate trends, causal conclusions, or scientific claims. "
            "State limitations when the supplied data is insufficient."
        ),
    ),
    WeatherMode.TRAVELLER: ModeConfiguration(
        name="Traveller Mode",
        description="Weather framing for trip and outdoor planning.",
        persona_prompt=(
            "Provide practical, concise, destination-aware travel and outdoor guidance using only "
            "the supplied traveller_advisory and weather data. Preserve the deterministic travel "
            "suitability status; do not invent temperature, rainfall, rain probability, warnings, "
            "road conditions, restrictions, attractions, itineraries, or booking details. Clearly "
            "separate official IMD warnings from WeatherGPT traveller advice and state limitations "
            "when weather or hourly data is unavailable."
        ),
    ),
}


@dataclass(frozen=True)
class ModeResolution:
    selected_mode: WeatherMode
    active_mode: WeatherMode
    display_mode: WeatherMode
    routing: str
    is_mismatch: bool = False
    suggested_mode: WeatherMode | None = None


def get_mode_configuration(mode: WeatherMode | str) -> ModeConfiguration:
    return MODE_CONFIGURATIONS[WeatherMode(mode)]


def resolve_selected_mode(
    requested_mode: WeatherMode | str | None,
    remembered_mode: WeatherMode | str | None = None,
    *,
    was_explicitly_supplied: bool = True,
) -> WeatherMode:
    """Respect an explicit request; otherwise retain a valid session selection."""
    if was_explicitly_supplied and requested_mode is not None:
        return WeatherMode(requested_mode)
    if remembered_mode is not None:
        return WeatherMode(remembered_mode)
    return WeatherMode.NORMAL


FARMER_ACTION_SIGNALS = re.compile(
    r"\b(irrigat(?:e|ion)|sow(?:ing)?|fertili[sz](?:e|er|ing)|pesticide|"
    r"spray(?:ing)?|harvest(?:ing)?|growth stage|field|farm(?:er|ing)?|"
    r"agricultur(?:e|al)|kheti|khedut|kisan|fasal|khet|krishi|sinchai|"
    r"vavetar|fashal|sheti|shet|chash|khatar|vapru|ખાતર|વાવેતર|"
    r"खेती|किसान|फसल|कृषि|सिंचाई|खाद|"
    r"ખેતી|ખેડૂત|પાક|સિંચાઈ|ચાસ|চাষ|কৃষি|পসল)\b",
    re.IGNORECASE,
)
FARMER_CROP_SIGNALS = re.compile(
    r"\b(crop(?:s)?|wheat|rice|paddy|cotton|tomato|maize|soybean|sugarcane|"
    r"gehu|chawal|dhan|kapas|tamatar|makka|sarson|gahu|dhaan|bajra|juvar|"
    r"ઘઉં|ચોખા|કપાસ|ટામેટા|ગેહું|गेहूं|धान|चावल|कपास|टमाटर|ধান|গম)\b",
    re.IGNORECASE,
)
RESEARCHER_SIGNALS = re.compile(
    r"\b(gfs|open-meteo|wrf|nwp|numerical weather prediction|historical weather|"
    r"weather history|model comparison|compare (?:weather )?models?|forecast model|"
    r"model agreement|model disagreement|analy[sz]e|analysis|rainfall trend|"
    r"temperature trend|weather trend|research|study|observations)\b",
    re.IGNORECASE,
)
TRAVELLER_SIGNALS = re.compile(
    r"\b(travel(?:ling)?|traveller|traveler|trip|vacation|holiday|journey|"
    r"destination|sightseeing|tourism|tourist|outdoor activit(?:y|ies)|packing|"
    r"pack|raincoat|ghumna|yatra|pravas|safar|tour|hotel|stay|flight|booking|umbrella|"
    r"resort|chhatri|chata|छाता|छतरी|होटल|"
    r"પ્રવાસ|યાત્રા|હોટેલ|છત્રી|ভ্রমણ|যাত্রা)\b",
    re.IGNORECASE,
)
FARMER_FOLLOW_UP_SIGNALS = re.compile(
    r"\b(irrigat(?:e|ion)|sow(?:ing)?|fertili[sz](?:e|er|ing)|pesticide|"
    r"spray(?:ing)?|harvest(?:ing)?|field|kheti|fasal|sinchai|sheti|"
    r"खेती|फसल|सिंचाई|ખેતી|પાક)\b",
    re.IGNORECASE,
)
TRAVELLER_FOLLOW_UP_SIGNALS = re.compile(
    r"\b(pack(?:ing)?|raincoat|umbrella|outdoor activit(?:y|ies)|"
    r"carry|departure|chhatri|chata|छाता|छतरी|છત્રી)\b",
    re.IGNORECASE,
)
RESEARCHER_FOLLOW_UP_SIGNALS = re.compile(
    r"\b(model|agree(?:s|ment)?|disagree(?:ment)?|comparison|forecast confidence)\b"
)


def _recent_user_messages(context: dict | None) -> str:
    """Return only the small, existing session window used for routing context."""
    if not context:
        return ""
    return " ".join(
        str(item.get("user", "")) for item in context.get("history", [])[-6:]
        if isinstance(item, dict)
    ).lower()


def detect_automatic_mode(message: str, context: dict | None = None) -> WeatherMode:
    """Conservatively identify a specialized request without changing selection.

    A named destination and generic weather wording remain Normal.  Session context
    is used only for narrow follow-ups (for example, raincoat after a stated trip),
    never as a permanent preference or cross-session profile.
    """
    text = message.lower()
    if FARMER_ACTION_SIGNALS.search(text):
        return WeatherMode.FARMER
    # An explicit crop statement establishes the existing short-lived farmer context.
    if FARMER_CROP_SIGNALS.search(text) and (
        re.search(
            r"\b(grow(?:ing)?|plant(?:ing)?|crop(?:s)?|asar|effect|affect|impact|damage|saro|kharaab|"
            r"nuksan|faydo|khatar|vapru|sinchai|soil|yield|pak|fasal|farming|farmer)\b",
            text,
        )
        or re.search(r"\b(for|mate|keliye|ke liye|sathi)\b", text)
    ):
        return WeatherMode.FARMER
    if RESEARCHER_SIGNALS.search(text):
        return WeatherMode.RESEARCHER
    if TRAVELLER_SIGNALS.search(text):
        return WeatherMode.TRAVELLER

    history = _recent_user_messages(context)
    if context and context.get("crop") and FARMER_FOLLOW_UP_SIGNALS.search(text):
        return WeatherMode.FARMER
    if FARMER_CROP_SIGNALS.search(history) and FARMER_FOLLOW_UP_SIGNALS.search(text):
        return WeatherMode.FARMER
    if TRAVELLER_SIGNALS.search(history) and TRAVELLER_FOLLOW_UP_SIGNALS.search(text):
        return WeatherMode.TRAVELLER
    if context and context.get("research_tool") and RESEARCHER_FOLLOW_UP_SIGNALS.search(text):
        return WeatherMode.RESEARCHER
    return WeatherMode.NORMAL


def resolve_mode(
    message: str,
    selected_mode: WeatherMode | str,
    context: dict | None = None,
) -> ModeResolution:
    """Resolve active mode without mutating the selected/display mode, enforcing manual boundaries."""
    selected = WeatherMode(selected_mode)
    if selected is WeatherMode.NORMAL:
        active = detect_automatic_mode(message, context)
        return ModeResolution(
            selected_mode=selected,
            active_mode=active,
            display_mode=selected,
            routing="automatic",
            is_mismatch=False,
            suggested_mode=None,
        )

    # Manual specialized mode is selected.
    # Check if the query is specialized for another mode (mode mismatch).
    detected = detect_automatic_mode(message, context)
    if detected is not WeatherMode.NORMAL and detected != selected:
        return ModeResolution(
            selected_mode=selected,
            active_mode=selected,
            display_mode=selected,
            routing="manual",
            is_mismatch=True,
            suggested_mode=detected,
        )

    return ModeResolution(
        selected_mode=selected,
        active_mode=selected,
        display_mode=selected,
        routing="manual",
        is_mismatch=False,
        suggested_mode=None,
    )


def build_mode_mismatch_response(
    selected_mode: WeatherMode | str,
    suggested_mode: WeatherMode | str,
    language: str = "en",
    script: str = "latin",
) -> str:
    """Generate concise, localized mode-boundary guidance matching user language and script."""
    suggested = WeatherMode(suggested_mode)
    mode_title = suggested.value.capitalize()

    # 1. Gujlish / Roman Gujarati
    if language == "gu" and script == "latin":
        if suggested is WeatherMode.FARMER:
            return "Aa prashna Farmer mode mate vadhu yogya che. Kheti ane pak sambandhit havaman margdarshan mate krupya Farmer mode ma switch karo."
        if suggested is WeatherMode.TRAVELLER:
            return "Aa prashna Traveller mode mate vadhu yogya che. Pravas ane travel sambandhit havaman margdarshan mate krupya Traveller mode ma switch karo."
        if suggested is WeatherMode.RESEARCHER:
            return "Aa prashna Researcher mode mate vadhu yogya che. Scientific ane research data analysis mate krupya Researcher mode ma switch karo."
        return f"Aa prashna {mode_title} mode mate vadhu yogya che. Krupya {mode_title} mode ma switch karo."

    # 2. Gujarati Unicode Script
    if language == "gu":
        if suggested is WeatherMode.FARMER:
            return "આ પ્રશ્ન Farmer મોડ માટે વધુ યોગ્ય છે. કૃષિ અને પાક સંબંધિત હવામાન માર્ગદર્શન માટે કૃપા કરીને Farmer મોડ પસંદ કરો."
        if suggested is WeatherMode.TRAVELLER:
            return "આ પ્રશ્ન Traveller મોડ માટે વધુ યોગ્ય છે. પ્રવાસ અને યાત્રા સંબંધિત હવામાન માર્ગદર્શન માટે કૃપા કરીને Traveller મોડ પસંદ કરો."
        if suggested is WeatherMode.RESEARCHER:
            return "આ પ્રશ્ન Researcher મોડ માટે વધુ યોગ્ય છે. વૈજ્ઞાનિક અને સંશોધન વિશ્લેષણ માટે કૃપા કરીને Researcher મોડ પસંદ કરો."
        return f"આ પ્રશ્ન {mode_title} મોડ માટે વધુ યોગ્ય છે. કૃપા કરીને {mode_title} મોડ પસંદ કરો."

    # 3. Hinglish / Roman Hindi
    if language == "hi" and script == "latin":
        if suggested is WeatherMode.FARMER:
            return "Yeh sawal Farmer mode ke liye zyada upyukt hai. Kheti aur fasal sambandhit mausam jankari ke liye kripya Farmer mode me switch karein."
        if suggested is WeatherMode.TRAVELLER:
            return "Yeh sawal Traveller mode ke liye zyada upyukt hai. Yatra aur travel sambandhit mausam jankari ke liye kripya Traveller mode me switch karein."
        if suggested is WeatherMode.RESEARCHER:
            return "Yeh sawal Researcher mode ke liye zyada upyukt hai. Scientific aur research data analysis ke liye kripya Researcher mode me switch karein."
        return f"Yeh sawal {mode_title} mode ke liye zyada upyukt hai. Kripya {mode_title} mode me switch karein."

    # 4. Hindi Unicode Script
    if language == "hi":
        if suggested is WeatherMode.FARMER:
            return "यह प्रश्न Farmer मोड के लिए अधिक उपयुक्त है। कृषि और फसल संबंधित मौसम मार्गदर्शन के लिए कृपया Farmer मोड चुनें।"
        if suggested is WeatherMode.TRAVELLER:
            return "यह प्रश्न Traveller मोड के लिए अधिक उपयुक्त है। यात्रा संबंधित मौसम मार्गदर्शन के लिए कृपया Traveller मोड चुनें।"
        if suggested is WeatherMode.RESEARCHER:
            return "यह प्रश्न Researcher मोड के लिए अधिक उपयुक्त है। वैज्ञानिक और अनुसंधान विश्लेषण के लिए कृपया Researcher मोड चुनें।"
        return f"यह प्रश्न {mode_title} मोड के लिए अधिक उपयुक्त है। कृपया {mode_title} मोड चुनें।"

    # 5. Marathi
    if language == "mr":
        if script == "latin":
            if suggested is WeatherMode.FARMER:
                return "Ha prashna Farmer mode sathi jasta yogya aahe. Sheti ani pik sambandhit havaman margdarshanasathi krupaya Farmer mode nivda."
            if suggested is WeatherMode.TRAVELLER:
                return "Ha prashna Traveller mode sathi jasta yogya aahe. Pravas sambandhit havaman margdarshanasathi krupaya Traveller mode nivda."
            if suggested is WeatherMode.RESEARCHER:
                return "Ha prashna Researcher mode sathi jasta yogya aahe. Sanshodhan ani scientific analysis sathi krupaya Researcher mode nivda."
            return f"Ha prashna {mode_title} mode sathi jasta yogya aahe. Krupaya {mode_title} mode nivda."
        if suggested is WeatherMode.FARMER:
            return "हा प्रश्न Farmer मोडसाठी अधिक योग्य आहे. शेती आणि पीक संबंधित हवामान मार्गदर्शनासाठी कृपया Farmer मोड निवडा."
        if suggested is WeatherMode.TRAVELLER:
            return "हा प्रश्न Traveller मोडसाठी अधिक योग्य आहे. प्रवास संबंधित हवामान मार्गदर्शनासाठी कृपया Traveller मोड निवडा."
        if suggested is WeatherMode.RESEARCHER:
            return "हा प्रश्न Researcher मोडसाठी अधिक योग्य आहे. वैज्ञानिक आणि संशोधन विश्लेषणासाठी कृपया Researcher मोड निवडा."
        return f"हा प्रश्न {mode_title} मोडसाठी अधिक योग्य आहे. कृपया {mode_title} मोड निवडा."

    # 6. Bengali
    if language == "bn":
        if suggested is WeatherMode.FARMER:
            return "এই প্রশ্নটি Farmer মোডের জন্য আরও উপযুক্ত। কৃষি এবং ফসল সম্পর্কিত আবহাওয়ার নির্দেশনার জন্য অনুগ্রহ করে Farmer মোড নির্বাচন করুন।"
        if suggested is WeatherMode.TRAVELLER:
            return "এই প্রশ্নটি Traveller মোডের জন্য আরও উপযুক্ত। ভ্রমণ সম্পর্কিত আবহাওয়ার নির্দেশনার জন্য অনুগ্রহ করে Traveller মোড নির্বাচন করুন।"
        if suggested is WeatherMode.RESEARCHER:
            return "এই প্রশ্নটি Researcher মোডের জন্য আরও উপযুক্ত। বৈজ্ঞানিক এবং গবেষণামূলক বিশ্লেষণের জন্য অনুগ্রহ করে Researcher মোড নির্বাচন করুন।"
        return f"এই প্রশ্নটি {mode_title} মোডের জন্য আরও উপযুক্ত। অনুগ্রহ করে {mode_title} মোডে পরিবর্তন করুন।"

    # 7. Tamil
    if language == "ta":
        if suggested is WeatherMode.FARMER:
            return "இந்த கேள்வி Farmer பயன்முறைக்கு மிகவும் பொருத்தமானது. விவசாய வானிலை வழிகாட்டுதலுக்கு தயவுசெய்து Farmer பயன்முறைக்கு மாறவும்."
        if suggested is WeatherMode.TRAVELLER:
            return "இந்த கேள்வி Traveller பயன்முறைக்கு மிகவும் பொருத்தமானது. பயண வானிலை வழிகாட்டுதலுக்கு தயவுசெய்து Traveller பயன்முறைக்கு மாறவும்."
        if suggested is WeatherMode.RESEARCHER:
            return "இந்த கேள்வி Researcher பயன்முறைக்கு மிகவும் பொருத்தமானது. அறிவியல் வானிலை பகுப்பாய்வுக்கு தயவுசெய்து Researcher பயன்முறைக்கு மாறவும்."
        return f"இந்த கேள்வி {mode_title} பயன்முறைக்கு மிகவும் பொருத்தமானது. தயவுசெய்து {mode_title} பயன்முறைக்கு மாறவும்."

    # 8. Telugu
    if language == "te":
        if suggested is WeatherMode.FARMER:
            return "ఈ ప్రశ్న Farmer మోడ్‌కు మరింత అనుకూలంగా ఉంటుంది. వ్యవసాయ వాతావరణ మార్గదర్శకత్వం కోసం దయచేసి Farmer మోడ్‌కి మారండి."
        if suggested is WeatherMode.TRAVELLER:
            return "ఈ ప్రశ్న Traveller మోడ్‌కు మరింత అనుకూలంగా ఉంటుంది. ప్రయాణ వాతావరణ మార్గదర్శకత్వం కోసం దయచేసి Traveller మోడ్‌కి మారండి."
        if suggested is WeatherMode.RESEARCHER:
            return "ఈ ప్రశ్న Researcher మోడ్‌కు మరింత అనుకూలంగా ఉంటుంది. శాస్త్రీయ విశ్లేషణ కోసం దయచేసి Researcher మోడ్‌కి మారండి."
        return f"ఈ ప్రశ్న {mode_title} మోడ్‌కు మరింత అనుకూలంగా ఉంటుంది. దయచేసి {mode_title} మోడ్‌కి మారండి."

    # 9. Kannada
    if language == "kn":
        if suggested is WeatherMode.FARMER:
            return "ಈ ಪ್ರಶ್ನೆಯು Farmer ಮೋಡ್‌ಗೆ ಹೆಚ್ಚು ಸೂಕ್ತವಾಗಿದೆ. ಕೃಷಿ ಹವಾಮಾನ ಮಾರ್ಗದರ್ಶನಕ್ಕಾಗಿ ದಯವಿಟ್ಟು Farmer ಮೋಡ್‌ಗೆ ಬದಲಾಯಿಸಿ."
        if suggested is WeatherMode.TRAVELLER:
            return "ಈ ಪ್ರಶ್ನೆಯು Traveller ಮೋಡ್‌ಗೆ ಹೆಚ್ಚು ಸೂಕ್ತವಾಗಿದೆ. ಪ್ರಯಾಣ ಹವಾಮಾನ ಮಾರ್ಗದರ್ಶನಕ್ಕಾಗಿ ದಯವಿಟ್ಟು Traveller ಮೋಡ್‌ಗೆ ಬದಲಾಯಿಸಿ."
        if suggested is WeatherMode.RESEARCHER:
            return "ಈ ಪ್ರಶ್ನೆಯು Researcher ಮೋಡ್‌ಗೆ ಹೆಚ್ಚು ಸೂಕ್ತವಾಗಿದೆ. ಸಂಶೋಧನಾ ವಿಶ್ಲೇಷಣೆಗಾಗಿ ದಯವಿಟ್ಟು Researcher ಮೋಡ್‌ಗೆ ಬದಲಾಯಿಸಿ."
        return f"ಈ ಪ್ರಶ್ನೆಯು {mode_title} ಮೋಡ್‌ಗೆ ಹೆಚ್ಚು ಸೂಕ್ತವಾಗಿದೆ. ದಯವಿಟ್ಟು {mode_title} ಮೋಡ್‌ಗೆ ಬದಲಾಯಿಸಿ."

    # 10. Malayalam
    if language == "ml":
        if suggested is WeatherMode.FARMER:
            return "ഈ ചോദ്യം Farmer മോഡിന് കൂടുതൽ അനുയോജ്യമാണ്. കാർഷിക കാലാവസ്ഥാ മാർഗ്ഗനിർദ്ദേശത്തിനായി ദയവായി Farmer മോഡിലേക്ക് മാറുക."
        if suggested is WeatherMode.TRAVELLER:
            return "ഈ ചോദ്യം Traveller മോഡിന് കൂടുതൽ അനുയോജ്യമാണ്. യാത്രാ കാലാവസ്ഥാ മാർഗ്ഗനിർദ്ദേശത്തിനായി ദയവായി Traveller മോഡിലേക്ക് മാറുക."
        if suggested is WeatherMode.RESEARCHER:
            return "ഈ ചോദ്യം Researcher മോഡിന് കൂടുതൽ അനുയോജ്യമാണ്. ശാസ്ത്രീയ കാലാവസ്ഥാ വിശകലനത്തിനായി ദയവായി Researcher മോഡിലേക്ക് മാറുക."
        return f"ഈ ചോദ്യം {mode_title} മോഡിന് കൂടുതൽ അനുയോജ്യമാണ്. ദയവായി {mode_title} മോഡിലേക്ക് മാറുക."

    # 11. Punjabi
    if language == "pa":
        if suggested is WeatherMode.FARMER:
            return "ਇਹ ਸਵਾਲ Farmer ਮੋਡ ਲਈ ਵਧੇਰੇ ਢੁਕਵਾਂ ਹੈ। ਖੇਤੀਬਾੜੀ ਮੌਸਮ ਸੰਬੰਧੀ ਮਾਰਗਦਰਸ਼ਨ ਲਈ ਕਿਰਪਾ ਕਰਕੇ Farmer ਮੋਡ ਚੁਣੋ।"
        if suggested is WeatherMode.TRAVELLER:
            return "ਇਹ ਸਵਾਲ Traveller ਮੋਡ ਲਈ ਵਧੇਰੇ ਢੁਕਵਾਂ ਹੈ। ਯਾਤਰਾ ਮੌਸਮ ਸੰਬੰਧੀ ਮਾਰਗਦਰਸ਼ਨ ਲਈ ਕਿਰਪਾ ਕਰਕੇ Traveller ਮੋਡ ਚੁਣੋ।"
        if suggested is WeatherMode.RESEARCHER:
            return "ਇਹ ਸਵਾਲ Researcher ਮੋਡ ਲਈ ਵਧੇਰੇ ਢੁਕਵਾਂ ਹੈ। ਵਿਗਿਆਨਕ ਮੌਸਮ ਵਿਸ਼ਲੇਸ਼ਣ ਲਈ ਕਿਰਪਾ ਕਰਕੇ Researcher ਮੋਡ ਚੁਣੋ।"
        return f"ਇਹ ਸਵਾਲ {mode_title} ਮੋਡ ਲਈ ਵਧੇਰੇ ਢੁਕਵਾਂ ਹੈ। ਕਿਰਪਾ ਕਰਕੇ {mode_title} ਮੋਡ ਚੁਣੋ।"

    # 12. Odia
    if language == "or":
        if suggested is WeatherMode.FARMER:
            return "ଏହି ପ୍ରଶ୍ନଟି Farmer ମୋଡ୍ ପାଇଁ ଅଧିକ ଉପଯୁକ୍ତ। କୃଷି ପାଣିପାଗ ମାର୍ଗଦର୍ଶନ ପାଇଁ ଦୟାକରି Farmer ମୋଡ୍ ବାଛନ୍ତୁ।"
        if suggested is WeatherMode.TRAVELLER:
            return "ଏହି ପ୍ରଶ୍ନଟି Traveller ମୋଡ୍ ପାଇଁ ଅଧିକ ଉପଯୁକ୍ତ। ଯାତ୍ରା ପାଣିପାଗ ମାର୍ଗଦର୍ଶନ ପାଇଁ ଦୟାକରି Traveller ମୋଡ୍ ବାଛନ୍ତୁ।"
        if suggested is WeatherMode.RESEARCHER:
            return "ଏହି ପ୍ରଶ୍ନଟି Researcher ମୋଡ୍ ପାଇଁ ଅଧିକ ଉପଯୁକ୍ତ। ବୈଜ୍ଞାନିକ ବିଶ୍ଳେଷଣ ପାଇଁ ଦୟାକରି Researcher ମୋଡ୍ ବାଛନ୍ତୁ।"
        return f"ଏହି ପ୍ରଶ୍ନଟି {mode_title} ମୋଡ୍ ପାଇଁ ଅଧିକ ଉପଯୁକ୍ତ। ଦୟାକରି {mode_title} ମୋଡ୍ ବାଛନ୍ତୁ।"

    # Default: English
    if suggested is WeatherMode.FARMER:
        return "This question is better suited for Farmer mode. Please switch to Farmer mode for agricultural weather guidance."
    if suggested is WeatherMode.TRAVELLER:
        return "This question is better suited for Traveller mode. Please switch to Traveller mode for travel-focused weather guidance."
    if suggested is WeatherMode.RESEARCHER:
        return "This question is better suited for Researcher mode. Please switch to Researcher mode for scientific and model analysis."
    return f"This question is better suited for {mode_title} mode. Please switch to {mode_title} mode."

