export interface SupportedLanguage {
  language_code: string;
  language_name: string;
  native_name: string;
  is_fallback: boolean;
  tts_supported: boolean;
  is_active: boolean;
}

export interface POI {
  poi_id: number;
  title: string;
  description: string;
  latitude: number;
  longitude: number;
  trigger_radius: number;
  thumbnail_url: string | null;
  audio_url: string | null;
  fallback: boolean;
  distance?: number;
  has_played?: boolean;
}

export interface ChatSource {
  poi_id: number;
  title: string;
  score: number;
}

export interface ChatMessage {
  id: string;
  sender: 'user' | 'bot';
  text: string;
  sources?: ChatSource[];
  timestamp: string;
}
