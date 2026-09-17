/**
 * Client-side language, script, and contextual prompt generator for WeatherGPT.
 * Supports English, Gujarati Unicode, Gujlish (Roman Gujarati), Hindi Unicode, Hinglish (Roman Hindi), etc.
 */

export interface DetectedLanguage {
  language: string;
  script: "native" | "latin";
}

const SCRIPT_RANGES: Record<string, [string, string]> = {
  gu: ["\u0a80", "\u0aff"],
  bn: ["\u0980", "\u09ff"],
  ta: ["\u0b80", "\u0bff"],
  te: ["\u0c00", "\u0c7f"],
  kn: ["\u0c80", "\u0cff"],
  ml: ["\u0d00", "\u0d7f"],
  pa: ["\u0a00", "\u0a7f"],
  or: ["\u0b00", "\u0b7f"],
  hi: ["\u0900", "\u097f"],
};

const GUJLISH_WORDS = new Set([
  "kale", "kaale", "aaje", "aje", "bapore", "bapor", "savare", "sanje",
  "raate", "ratre", "paramdivse", "varsad", "varshadh", "tapman", "taapman",
  "havaman", "havaaman", "thandi", "garmi", "dhukhas", "vavazodu", "pavan",
  "maru", "mari", "maro", "tamaru", "tamari", "tamaro", "aapnu", "aapna",
  "kem", "cho", "su", "shu", "che", "chhe", "nathi", "ane", "mate",
  "ma", "maa", "nu", "ni", "no", "na", "mathi", "sathe", "pasi", "pachi",
  "padse", "padshe", "rehse", "rehshe", "thase", "thashe", "aavse", "aavshe",
  "chale", "chalse", "batavo", "janavo", "aapo", "lagse", "jovu", "karo",
  "karjo", "kevu", "kevi", "kevo", "keva", "ketlu", "ketla", "ketli",
  "kyare", "kya", "kona", "kheti", "khedut", "atyare", "atyar", "hava",
  "khatar", "vapru", "vapravu", "asar", "ghau", "pak", "nuksan", "faydo",
]);

const HINGLISH_WORDS = new Set([
  "aaj", "kal", "parso", "subah", "dopahar", "shaam", "sham", "raat",
  "hona", "hogi", "hoga", "honge", "mausam", "mosam", "baarish", "barish",
  "barsat", "sardi", "thand", "hawa", "toofan", "tufan", "mera", "meri",
  "mere", "aapka", "aapki", "aapke", "kya", "kyu", "kyon", "kaise",
  "kaisa", "kaisi", "kitna", "kitni", "kitne", "kab", "kaha", "kahan",
  "hai", "hain", "tha", "thi", "nahi", "nahin", "aur", "ya", "lekin",
  "mein", "liye", "keliye", "batao", "bataye", "bataiye", "padega",
  "padegi", "karega", "karegi", "rahega", "rahegi", "khet", "kisan", "fasal",
]);

export function detectLanguageAndScript(text: string): DetectedLanguage {
  if (!text) return { language: "en", script: "latin" };

  // 1. Check Unicode script ranges
  for (const char of text) {
    for (const [lang, [start, end]] of Object.entries(SCRIPT_RANGES)) {
      if (char >= start && char <= end) {
        return { language: lang, script: "native" };
      }
    }
  }

  // 2. Check Latin Indic lexical tokens
  const words = text
    .toLowerCase()
    .replace(/[^\w\s]/g, " ")
    .split(/\s+/)
    .filter(Boolean);

  let gujScore = 0;
  let hinScore = 0;

  for (const w of words) {
    if (GUJLISH_WORDS.has(w)) gujScore++;
    if (HINGLISH_WORDS.has(w)) hinScore++;
  }

  if (gujScore > 0 && gujScore >= hinScore) {
    return { language: "gu", script: "latin" };
  }
  if (hinScore > 0) {
    return { language: "hi", script: "latin" };
  }

  return { language: "en", script: "latin" };
}

export interface SuggestedPrompt {
  label: string;
  prompt: string;
}

export function generateSuggestedPrompts({
  query = "",
  mode = "normal",
  locationName = "",
  language = "en",
  script = "latin",
  hasRain = false,
  isTravel = false,
  isFarmer = false,
}: {
  query?: string;
  mode?: string;
  locationName?: string;
  language?: string;
  script?: string;
  hasRain?: boolean;
  isTravel?: boolean;
  isFarmer?: boolean;
}): SuggestedPrompt[] {
  const loc = locationName || (language === "gu" ? "અહીં" : language === "hi" ? "यहाँ" : "here");
  const locPhrase = locationName ? ` in ${locationName}` : "";
  const locPhraseGu = locationName ? ` ${locationName}માં` : "";
  const locPhraseHi = locationName ? ` ${locationName} में` : "";

  const qLower = query.toLowerCase();
  const effectiveMode = mode || "normal";
  const isRainRelevant = hasRain || qLower.includes("rain") || qLower.includes("varsad") || qLower.includes("barish") || qLower.includes("વરસાદ") || qLower.includes("बारिश");

  // 1. GUJARATI UNICODE
  if (language === "gu" && script === "native") {
    if (effectiveMode === "farmer" || isFarmer || qLower.includes("પાક") || qLower.includes("ખેતી")) {
      return [
        { label: "પાક પર વરસાદની અસર?", prompt: `${locPhraseGu} પાક પર વરસાદની શું અસર થશે?` },
        { label: "પિયત આપવું યોગ્ય છે?", prompt: `${locPhraseGu} શું કાલે પાકને પિયત આપવું જોઈએ?` },
        { label: "આગામી ૩ દિવસનું હવામાન", prompt: `${locPhraseGu} આગામી ૩ દિવસનું હવામાન કેવું રહેશે?` },
        { label: "સરકારી કૃષિ સલાહ", prompt: `${locPhraseGu} સત્તાવાર IMD કૃષિ સલાહ બતાવો.` },
      ];
    }
    if (effectiveMode === "traveller" || isTravel || qLower.includes("પ્રવાસ") || qLower.includes("મુસાફરી")) {
      return [
        { label: "મુસાફરીનો શ્રેષ્ઠ સમય?", prompt: `${locPhraseGu} મુસાફરી માટે શ્રેષ્ઠ સમય કયો છે?` },
        { label: "કાલે વરસાદ પડશે?", prompt: `${locPhraseGu} શું કાલે વરસાદ પડશે?` },
        { label: "પેકિંગ માટે શું રાખવું?", prompt: `${locPhraseGu} પ્રવાસ માટે પેકિંગમાં શું સાથે રાખવું?` },
        { label: "૭ દિવસની આગાહી", prompt: `${locPhraseGu} આગામી ૭ દિવસની આગાહી બતાવો.` },
      ];
    }
    if (effectiveMode === "researcher") {
      return [
        { label: "કલાકવાર ટ્રેન્ડ બતાવો", prompt: `${locPhraseGu} કલાકવાર તાપમાન અને વરસાદનો ટ્રેન્ડ બતાવો.` },
        { label: "હવામાન મોડલ સરખામણી", prompt: `${locPhraseGu} GFS અને Open-Meteo મોડલની સરખામણી કરો.` },
        { label: "વરસાદની ચોક્કસ સંભાવના", prompt: `${locPhraseGu} વરસાદની ચોક્કસ ટકાવારી કેટલી છે?` },
      ];
    }
    // Rain specific prompt
    if (isRainRelevant) {
      return [
        { label: "વરસાદ કયા સમયે પડશે?", prompt: `${locPhraseGu} કયા સમયે સૌથી વધુ વરસાદ પડશે?` },
        { label: "કાલનું તાપમાન કેટલું?", prompt: `${locPhraseGu} કાલે તાપમાન કેટલું રહેશે?` },
        { label: "કલાકવાર આગાહી બતાવો", prompt: `${locPhraseGu} કલાકવાર વરસાદની આગાહી બતાવો.` },
        { label: "૭ દિવસની આગાહી", prompt: `${locPhraseGu} ૭ દિવસની સંપૂર્ણ આગાહી બતાવો.` },
      ];
    }
    // General / Normal
    return [
      { label: "કાલે વરસાદ પડશે?", prompt: `${locPhraseGu} કાલે વરસાદ પડશે?` },
      { label: "કાલનું તાપમાન કેટલું?", prompt: `${locPhraseGu} કાલે મહત્તમ તાપમાન કેટલું રહેશે?` },
      { label: "કલાકવાર હવામાન બતાવો", prompt: `${locPhraseGu} કલાકવાર આગાહી બતાવો.` },
      { label: "૭ દિવસની આગાહી", prompt: `${locPhraseGu} ૭ દિવસની સંપૂર્ણ આગાહી બતાવો.` },
    ];
  }

  // 2. GUJLISH (ROMAN GUJARATI)
  if (language === "gu" && script === "latin") {
    if (effectiveMode === "farmer" || isFarmer) {
      return [
        { label: "Pak par varsad ni asar?", prompt: `${loc} ma pak par varsad ni su asar thase?` },
        { label: "Kale piyas aapi shakay?", prompt: `${loc} ma kale khetar ma piyas apay ke nahi?` },
        { label: "Aagami 3 divas nu havaman", prompt: `${loc} ma aavta 3 divas nu havaman batavo.` },
        { label: "IMD Kheti Advisory", prompt: `${loc} mate official IMD kheti advisory su che?` },
      ];
    }
    if (effectiveMode === "traveller" || isTravel) {
      return [
        { label: "Travel mate best time?", prompt: `${loc} travel karva mate best time kayo che?` },
        { label: "Kale varsad padse?", prompt: `Kale ${loc} ma varsad padse?` },
        { label: "Packing ma su rakhvu?", prompt: `${loc} javanu hoy to sathe su rakhvu?` },
        { label: "Full forecast batavo", prompt: `${loc} nu aavta divaso nu forecast batavo.` },
      ];
    }
    if (effectiveMode === "researcher") {
      return [
        { label: "Hourly trend batavo", prompt: `${loc} nu hourly weather trend batavo.` },
        { label: "Compare models", prompt: `${loc} mate GFS ane standard model compare karo.` },
        { label: "Rain probability", prompt: `${loc} ma varsad ni probability ketli che?` },
      ];
    }
    // Normal Gujlish
    return [
      { label: "Kale varsad padse?", prompt: `Kale ${loc} ma varsad padse?` },
      { label: "Kal nu tapman ketlu?", prompt: `Kale ${loc} ma tapman ketlu rehse?` },
      { label: "Hourly forecast batavo", prompt: `${loc} nu hourly forecast batavo.` },
      { label: "7 days forecast", prompt: `${loc} nu 7 days forecast batavo.` },
    ];
  }

  // 3. HINDI UNICODE
  if (language === "hi" && script === "native") {
    if (effectiveMode === "farmer" || isFarmer) {
      return [
        { label: "फसल पर बारिश का असर?", prompt: `${locPhraseHi} फसल पर बारिश का क्या असर होगा?` },
        { label: "क्या कल सिंचाई करें?", prompt: `${locPhraseHi} क्या कल सिंचाई करना सही रहेगा?` },
        { label: "अगले ३ दिनों का मौसम", prompt: `${locPhraseHi} अगले ३ दिनों का मौसम कैसा रहेगा?` },
        { label: "कृषि मौसम सलाह", prompt: `${locPhraseHi} आधिकारिक मौसम कृषि सलाह दिखाएं।` },
      ];
    }
    if (effectiveMode === "traveller" || isTravel) {
      return [
        { label: "यात्रा का सबसे अच्छा समय?", prompt: `${locPhraseHi} यात्रा के लिए सबसे अच्छा समय क्या है?` },
        { label: "क्या कल बारिश होगी?", prompt: `${locPhraseHi} क्या कल बारिश होगी?` },
        { label: "पैकिंग में क्या रखें?", prompt: `${locPhraseHi} यात्रा के लिए साथ में क्या सामान रखें?` },
        { label: "पूरा मौसम पूर्वानुमान", prompt: `${locPhraseHi} अगले ७ दिनों का पूर्वानुमान दिखाएं।` },
      ];
    }
    if (effectiveMode === "researcher") {
      return [
        { label: "घंटेवार रुझान दिखाएं", prompt: `${locPhraseHi} घंटेवार तापमान और बारिश का रुझान दिखाएं।` },
        { label: "मौसम मॉडल तुलना", prompt: `${locPhraseHi} GFS और मुख्य मॉडल की तुलना करें।` },
        { label: "वर्षा की सटीक संभावना", prompt: `${locPhraseHi} बारिश की संभावना कितने प्रतिशत है?` },
      ];
    }
    // Normal Hindi
    return [
      { label: "क्या कल बारिश होगी?", prompt: `क्या कल ${locPhraseHi} बारिश होगी?` },
      { label: "कल का तापमान कितना रहेगा?", prompt: `कल ${locPhraseHi} तापमान कितना रहेगा?` },
      { label: "घंटेवार पूर्वानुमान", prompt: `${locPhraseHi} घंटेवार मौसम दिखाएं।` },
      { label: "७ दिनों का पूर्वानुमान", prompt: `${locPhraseHi} ७ दिनों का मौसम पूर्वानुमान दिखाएं।` },
    ];
  }

  // 4. ROMAN HINDI (HINGLISH)
  if (language === "hi" && script === "latin") {
    if (effectiveMode === "farmer" || isFarmer) {
      return [
        { label: "Fasal par barish ka asar?", prompt: `${loc} me fasal par barish ka kya asar hoga?` },
        { label: "Kya kal sinchai karein?", prompt: `${loc} me kal sinchai karni chahiye ya nahi?` },
        { label: "Next 3 days mausam", prompt: `${loc} me agle 3 dino ka mausam kaisa rahega?` },
      ];
    }
    if (effectiveMode === "traveller" || isTravel) {
      return [
        { label: "Best time to travel?", prompt: `${loc} travel karne ke liye best time kya hai?` },
        { label: "Kya kal barish hogi?", prompt: `Kya kal ${loc} me barish hogi?` },
        { label: "Packing me kya rakhein?", prompt: `${loc} trip ke liye kya pack karein?` },
      ];
    }
    return [
      { label: "Kya kal barish hogi?", prompt: `Kya kal ${loc} me barish hogi?` },
      { label: "Kal ka temperature kitna?", prompt: `Kal ${loc} me temperature kitna rahega?` },
      { label: "Hourly forecast dikhao", prompt: `${loc} ka hourly forecast dikhao.` },
    ];
  }

  // 5. ENGLISH (DEFAULT)
  if (effectiveMode === "farmer" || isFarmer) {
    return [
      { label: "Will rain affect my crop?", prompt: `Will the forecast rain affect crops${locPhrase}?` },
      { label: "Should I irrigate tomorrow?", prompt: `Is it advisable to irrigate tomorrow${locPhrase}?` },
      { label: "3-day farming outlook", prompt: `Show 3-day agricultural forecast${locPhrase}.` },
      { label: "Official Agromet Advisory", prompt: `Show official IMD Agromet advisory${locPhrase}.` },
    ];
  }

  if (effectiveMode === "traveller" || isTravel) {
    return [
      { label: "Best time to travel?", prompt: `What is the best time to travel${locPhrase}?` },
      { label: "Will it rain during trip?", prompt: `Will it rain during my visit${locPhrase}?` },
      { label: "Packing recommendations", prompt: `What should I pack for travel${locPhrase}?` },
      { label: "View full forecast", prompt: `Show the upcoming forecast${locPhrase}.` },
    ];
  }

  if (effectiveMode === "researcher") {
    return [
      { label: "Show hourly trend", prompt: `Show hourly meteorological trend${locPhrase}.` },
      { label: "Compare forecast models", prompt: `Compare GFS and standard forecast models${locPhrase}.` },
      { label: "Precipitation probability", prompt: `What is the exact precipitation probability${locPhrase}?` },
    ];
  }

  // Normal English
  return [
    { label: "Will it rain tomorrow?", prompt: `Will it rain tomorrow${locPhrase}?` },
    { label: "What will the temperature be?", prompt: `What will the temperature be tomorrow${locPhrase}?` },
    { label: "Show hourly forecast", prompt: `Show the hourly forecast${locPhrase}.` },
    { label: "Show 7-day outlook", prompt: `Show the 7-day weather outlook${locPhrase}.` },
  ];
}
