export interface Localization {
  title: string;
  description: string;
  audio_url: string;
}

export interface POI {
  poi_id: string;
  name: string;
  latitude: number;
  longitude: number;
  trigger_radius: number;
  thumbnail_url?: string;
  original_description: string;
  pipeline_status: string;
  localizations?: Record<string, Localization>;
}

export interface TourRoute {
  route_id: string;
  route_name: string;
  description: string;
  estimated_duration: number;
  poi_ids: string[];
}

export interface ChatMessage {
  id: string;
  sender: 'user' | 'bot';
  text: string;
  from_cache?: boolean;
  in_scope?: boolean;
  sources?: Array<{ poi_id: string; similarity: number }>;
  timestamp: string;
}

export interface LanguageOption {
  code: string;
  name: string;
  flag: string;
}

export const LANGUAGES: LanguageOption[] = [
  { code: 'vi', name: 'Tiếng Việt', flag: '🇻🇳' },
  { code: 'en', name: 'English', flag: '🇬🇧' },
  { code: 'zh', name: '中文 (Chinese)', flag: '🇨🇳' },
  { code: 'ja', name: '日本語 (Japanese)', flag: '🇯🇵' },
  { code: 'ko', name: '한국어 (Korean)', flag: '🇰🇷' },
  { code: 'fr', name: 'Français', flag: '🇫🇷' },
  { code: 'de', name: 'Deutsch', flag: '🇩🇪' },
  { code: 'es', name: 'Español', flag: '🇪🇸' },
  { code: 'ru', name: 'Русский', flag: '🇷🇺' },
  { code: 'th', name: 'ไทย (Thai)', flag: '🇹🇭' },
  { code: 'id', name: 'Bahasa Indonesia', flag: '🇮🇩' },
  { code: 'ms', name: 'Bahasa Melayu', flag: '🇲🇾' },
  { code: 'it', name: 'Italiano', flag: '🇮🇹' },
  { code: 'pt', name: 'Português', flag: '🇵🇹' },
  { code: 'ar', name: 'العربية (Arabic)', flag: '🇸🇦' }
];
