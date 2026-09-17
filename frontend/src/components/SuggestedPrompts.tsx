import { Sparkles } from "./icons";
import { generateSuggestedPrompts, type SuggestedPrompt } from "../languageDetection";

interface SuggestedPromptsProps {
  query?: string;
  mode?: string;
  locationName?: string;
  language?: string;
  script?: string;
  hasRain?: boolean;
  isTravel?: boolean;
  isFarmer?: boolean;
  onPromptSelect: (prompt: string) => void;
  disabled?: boolean;
}

export function SuggestedPrompts({
  query = "",
  mode = "normal",
  locationName = "",
  language = "en",
  script = "latin",
  hasRain = false,
  isTravel = false,
  isFarmer = false,
  onPromptSelect,
  disabled = false,
}: SuggestedPromptsProps) {
  const prompts: SuggestedPrompt[] = generateSuggestedPrompts({
    query,
    mode,
    locationName,
    language,
    script,
    hasRain,
    isTravel,
    isFarmer,
  });

  if (!prompts || prompts.length === 0) return null;

  const headerLabel =
    language === "gu" && script === "native"
      ? "તમે આ પણ પૂછી શકો છો"
      : language === "gu" && script === "latin"
        ? "You might also ask"
        : language === "hi" && script === "native"
          ? "आप यह भी पूछ सकते हैं"
          : "You might also ask";

  return (
    <div className="suggested-prompts-container" role="region" aria-label="Suggested prompts">
      <div className="suggested-prompts-title">
        <Sparkles className="suggested-prompts-icon" />
        <span>{headerLabel}</span>
      </div>
      <div className="suggested-prompts-list">
        {prompts.map((p, idx) => (
          <button
            key={idx}
            type="button"
            className="suggested-prompt-chip glass"
            disabled={disabled}
            onClick={() => onPromptSelect(p.prompt)}
            aria-label={`Ask suggested prompt: ${p.prompt}`}
          >
            <span>{p.label}</span>
          </button>
        ))}
      </div>
    </div>
  );
}
