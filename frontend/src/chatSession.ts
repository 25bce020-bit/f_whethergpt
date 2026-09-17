import { clearSelectedLocation } from './locationSelection';

const STORAGE_KEY = 'weathergpt_session';

export function getChatSession(): string {
  let sessionId = sessionStorage.getItem(STORAGE_KEY);
  if (!sessionId) {
    sessionId = `guest-${crypto.randomUUID()}`;
    sessionStorage.setItem(STORAGE_KEY, sessionId);
  }
  return sessionId;
}

export function startNewChat(): void {
  sessionStorage.setItem(STORAGE_KEY, `guest-${crypto.randomUUID()}`);
  clearSelectedLocation();
}
