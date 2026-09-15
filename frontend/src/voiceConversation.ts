import type { ChatResponse } from './api/types';

const STORAGE_KEY = 'weathergpt_voice_conversation';
export type VoiceConversation = { transcript: string; response: ChatResponse };
export function saveVoiceConversation(conversation: VoiceConversation): void { sessionStorage.setItem(STORAGE_KEY, JSON.stringify(conversation)); }
export function takeVoiceConversation(): VoiceConversation | null { const saved = sessionStorage.getItem(STORAGE_KEY); sessionStorage.removeItem(STORAGE_KEY); if (!saved) return null; try { return JSON.parse(saved) as VoiceConversation; } catch { return null; } }
