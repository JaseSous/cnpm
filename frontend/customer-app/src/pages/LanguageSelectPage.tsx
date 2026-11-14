import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { poiClient } from '../api/client';
import { SupportedLanguage } from '../types';
import { Globe2, ArrowRight, Compass } from 'lucide-react';

const FALLBACK_LANGUAGES: SupportedLanguage[] = [
  { language_code: 'vi', language_name: 'Vietnamese', native_name: 'Tiếng Việt', is_fallback: true, tts_supported: true, is_active: true },
  { language_code: 'en', language_name: 'English', native_name: 'English', is_fallback: false, tts_supported: true, is_active: true },
  { language_code: 'zh', language_name: 'Chinese', native_name: '中文 (简体)', is_fallback: false, tts_supported: true, is_active: true },
  { language_code: 'ja', language_name: 'Japanese', native_name: '日本語', is_fallback: false, tts_supported: true, is_active: true },
  { language_code: 'ko', language_name: 'Korean', native_name: '한국어', is_fallback: false, tts_supported: true, is_active: true },
  { language_code: 'fr', language_name: 'French', native_name: 'Français', is_fallback: false, tts_supported: true, is_active: true },
  { language_code: 'de', language_name: 'German', native_name: 'Deutsch', is_fallback: false, tts_supported: true, is_active: true },
  { language_code: 'es', language_name: 'Spanish', native_name: 'Español', is_fallback: false, tts_supported: true, is_active: true },
  { language_code: 'th', language_name: 'Thai', native_name: 'ไทย', is_fallback: false, tts_supported: true, is_active: true },
  { language_code: 'ru', language_name: 'Russian', native_name: 'Русский', is_fallback: false, tts_supported: true, is_active: true },
  { language_code: 'pt', language_name: 'Portuguese', native_name: 'Português', is_fallback: false, tts_supported: true, is_active: true },
  { language_code: 'it', language_name: 'Italian', native_name: 'Italiano', is_fallback: false, tts_supported: true, is_active: true },
  { language_code: 'id', language_name: 'Indonesian', native_name: 'Bahasa Indonesia', is_fallback: false, tts_supported: true, is_active: true },
  { language_code: 'ar', language_name: 'Arabic', native_name: 'العربية', is_fallback: false, tts_supported: true, is_active: true },
  { language_code: 'hi', language_name: 'Hindi', native_name: 'हिन्दी', is_fallback: false, tts_supported: true, is_active: true },
];

export default function LanguageSelectPage() {
  const navigate = useNavigate();
  const [languages, setLanguages] = useState<SupportedLanguage[]>(FALLBACK_LANGUAGES);
  const [selectedLang, setSelectedLang] = useState<string>('vi');
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    // Nếu đã chọn ngôn ngữ trước đó, tự động chuyển tiếp
    const savedLang = localStorage.getItem('customer_lang');
    if (savedLang) {
      setSelectedLang(savedLang);
    }

    const fetchLanguages = async () => {
      try {
        const res = await poiClient.get('/api/languages');
        if (res.data && Array.isArray(res.data.languages) && res.data.languages.length > 0) {
          setLanguages(res.data.languages);
        }
      } catch {
        // Dùng fallback danh sách 15 ngôn ngữ
      } finally {
        setLoading(false);
      }
    };

    fetchLanguages();
  }, []);

  const handleConfirmLanguage = () => {
    localStorage.setItem('customer_lang', selectedLang);
    // Kiểm tra nếu đã có token vé hợp lệ thì vào thẳng bản đồ, ngược lại quét mã vé
    const token = localStorage.getItem('customer_token');
    if (token) {
      navigate('/map');
    } else {
      navigate('/auth');
    }
  };

  return (
    <div className="flex-1 flex flex-col justify-between p-6 bg-gradient-to-b from-amber-50 via-white to-amber-50">
      <div>
        {/* Header Logo */}
        <div className="text-center mt-6 mb-8">
          <div className="inline-flex p-3 rounded-full bg-amber-100 text-amber-700 mb-3 shadow-inner">
            <Compass className="w-10 h-10 animate-pulse" />
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-amber-900">CHÙA LINH ỨNG</h1>
          <p className="text-xs uppercase tracking-widest text-amber-700/80 mt-1 font-semibold">
            BÃI BỤT - BÁN ĐẢO SƠN TRÀ - ĐÀ NẴNG
          </p>
          <div className="mt-4 flex items-center justify-center gap-2 text-sm text-stone-600">
            <Globe2 className="w-4 h-4 text-amber-600" />
            <span>Vui lòng chọn ngôn ngữ / Choose your language</span>
          </div>
        </div>

        {/* Danh sách ngôn ngữ */}
        {loading ? (
          <div className="flex justify-center py-12">
            <div className="w-8 h-8 border-4 border-amber-600 border-t-transparent rounded-full animate-spin"></div>
          </div>
        ) : (
          <div className="grid grid-cols-1 gap-2.5 max-h-[50vh] overflow-y-auto pr-1">
            {languages.map((lang) => {
              const isSelected = selectedLang === lang.language_code;
              return (
                <button
                  key={lang.language_code}
                  onClick={() => setSelectedLang(lang.language_code)}
                  className={`flex items-center justify-between p-3.5 rounded-xl border transition-all text-left ${
                    isSelected
                      ? 'border-amber-600 bg-amber-50 text-amber-900 shadow-sm ring-1 ring-amber-500'
                      : 'border-stone-200 bg-white hover:bg-stone-50 text-stone-700'
                  }`}
                >
                  <div>
                    <div className="font-semibold text-base">{lang.native_name}</div>
                    <div className="text-xs text-stone-500">{lang.language_name}</div>
                  </div>
                  {isSelected && (
                    <div className="w-6 h-6 rounded-full bg-amber-600 text-white flex items-center justify-center text-xs font-bold">
                      ✓
                    </div>
                  )}
                </button>
              );
            })}
          </div>
        )}
      </div>

      {/* Nút xác nhận */}
      <div className="mt-6 pt-4 border-t border-amber-100">
        <button
          onClick={handleConfirmLanguage}
          className="w-full py-3.5 px-6 rounded-xl bg-amber-600 hover:bg-amber-700 active:scale-[0.99] text-white font-medium flex items-center justify-center gap-2 shadow-lg shadow-amber-600/30 transition-all text-base"
        >
          <span>Tiếp tục / Continue</span>
          <ArrowRight className="w-5 h-5" />
        </button>
      </div>
    </div>
  );
}
