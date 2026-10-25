import React, { useState, useEffect } from 'react';
import { Volume2, VolumeX, Play, Pause, RotateCcw } from 'lucide-react';

interface Props {
  text: string;
  audioUrl?: string;
  langCode: string;
  title: string;
  autoPlay?: boolean;
}

const LANG_MAP: Record<string, string> = {
  vi: 'vi-VN',
  en: 'en-US',
  zh: 'zh-CN',
  ja: 'ja-JP',
  ko: 'ko-KR',
  fr: 'fr-FR',
  de: 'de-DE',
  es: 'es-ES',
  ru: 'ru-RU',
  th: 'th-TH',
  id: 'id-ID',
  ms: 'ms-MY',
  it: 'it-IT',
  pt: 'pt-PT',
  ar: 'ar-SA',
};

export const AudioPlayer: React.FC<Props> = ({
  text,
  audioUrl,
  langCode,
  title,
  autoPlay = false,
}) => {
  const [isPlaying, setIsPlaying] = useState(false);
  const [audioElement, setAudioElement] = useState<HTMLAudioElement | null>(null);
  const [voices, setVoices] = useState<SpeechSynthesisVoice[]>([]);
  const [activeVoiceName, setActiveVoiceName] = useState<string>('');

  // Nạp danh sách giọng đọc từ trình duyệt (Web Speech API)
  useEffect(() => {
    const loadVoices = () => {
      if ('speechSynthesis' in window) {
        const availableVoices = window.speechSynthesis.getVoices();
        setVoices(availableVoices);
      }
    };

    loadVoices();
    if ('speechSynthesis' in window) {
      window.speechSynthesis.onvoiceschanged = loadVoices;
    }
  }, []);

  // Tìm giọng đọc phù hợp nhất với mã ngôn ngữ
  const findBestVoice = (targetLangCode: string, availableVoices: SpeechSynthesisVoice[]): SpeechSynthesisVoice | null => {
    if (!availableVoices || availableVoices.length === 0) return null;

    const bcp47 = LANG_MAP[targetLangCode] || 'vi-VN';
    const primary = targetLangCode.toLowerCase();

    // 1. Khớp chính xác BCP-47 tag (vd: vi-VN, en-US)
    let match = availableVoices.find(
      v => v.lang.replace('_', '-').toLowerCase() === bcp47.toLowerCase()
    );
    if (match) return match;

    // 2. Khớp tiền tố ngôn ngữ (vd: vi-*, en-*, fr-*)
    match = availableVoices.find(
      v => v.lang.toLowerCase().startsWith(primary + '-') || v.lang.toLowerCase() === primary
    );
    if (match) return match;

    // 3. Khớp tên voice theo từ khóa định danh ngôn ngữ
    const langKeywords: Record<string, string[]> = {
      vi: ['vietnamese', 'tiếng việt', 'việt nam', 'hoaimy', 'namminh', 'an'],
      en: ['english', 'david', 'zira', 'mark', 'george', 'susan', 'hazel', 'natural'],
      zh: ['chinese', 'mandarin', 'huihui', 'yaoyao', 'kangkang', 'taiwan'],
      ja: ['japanese', 'haruka', 'ayumi', 'ichiro', 'sayaka'],
      ko: ['korean', 'heami', 'sunhi', 'insoo'],
      fr: ['french', 'hortense', 'julie', 'paul', 'denise', 'henri'],
      de: ['german', 'hedda', 'stefan', 'katja', 'conrad'],
      es: ['spanish', 'helena', 'laura', 'pablo', 'elena'],
      ru: ['russian', 'irina', 'pavel', 'dmitry'],
      th: ['thai', 'niwat', 'prew', 'achara'],
      id: ['indonesian', 'gadis', 'andika'],
      ms: ['malay', 'osman', 'yasmin'],
      it: ['italian', 'elsa', 'cosimo', 'isabella'],
      pt: ['portuguese', 'maria', 'helio', 'raquel'],
      ar: ['arabic', 'hoda', 'naayf', 'zeina'],
    };

    const keywords = langKeywords[primary] || [];
    for (const kw of keywords) {
      match = availableVoices.find(v => v.name.toLowerCase().includes(kw));
      if (match) return match;
    }

    return null;
  };

  // Cập nhật tên giọng đọc hiển thị khi đổi ngôn ngữ hoặc danh sách giọng
  useEffect(() => {
    const currentVoices = voices.length > 0 ? voices : ('speechSynthesis' in window ? window.speechSynthesis.getVoices() : []);
    const matched = findBestVoice(langCode, currentVoices);
    if (matched) {
      setActiveVoiceName(matched.name);
    } else {
      setActiveVoiceName(`Giọng đọc mặc định (${LANG_MAP[langCode] || langCode})`);
    }
  }, [langCode, voices]);

  useEffect(() => {
    // Dừng âm thanh cũ khi đổi POI hoặc đổi ngôn ngữ
    stopPlayback();

    if (autoPlay) {
      handlePlay();
    }

    return () => {
      stopPlayback();
    };
  }, [text, audioUrl, langCode]);

  const stopPlayback = () => {
    if (audioElement) {
      audioElement.pause();
      audioElement.currentTime = 0;
    }
    if ('speechSynthesis' in window) {
      window.speechSynthesis.cancel();
    }
    setIsPlaying(false);
  };

  const handlePlay = () => {
    if (isPlaying) {
      stopPlayback();
      return;
    }

    // 1. Nếu có file audio thật
    if (audioUrl && audioUrl.trim().length > 0) {
      const audio = new Audio(audioUrl);
      audio.onended = () => setIsPlaying(false);
      audio.onerror = () => {
        // Fallback sang Web Speech API
        speakText();
      };
      audio.play();
      setAudioElement(audio);
      setIsPlaying(true);
      return;
    }

    // 2. Dự phòng Web Speech API (SpeechSynthesis) theo đúng PRD
    speakText();
  };

  const speakText = () => {
    if (!('speechSynthesis' in window)) {
      alert('Trình duyệt của bạn không hỗ trợ phát âm thanh tổng hợp');
      return;
    }

    window.speechSynthesis.cancel();

    // Làm sạch tiền tố mã ngôn ngữ trong ngoặc vuông (vd: [en], [vi], [fr]) nếu có
    const cleanText = (text || '').replace(/^\[[a-zA-Z\-]{2,5}\]\s*/, '').trim();
    if (!cleanText) return;

    const utterance = new SpeechSynthesisUtterance(cleanText);
    const targetBcp47 = LANG_MAP[langCode] || 'vi-VN';
    utterance.lang = targetBcp47;
    utterance.rate = 0.95; // Tốc độ vừa phải cho bài thuyết minh

    // Tìm và áp dụng chính xác Voice cho ngôn ngữ đã chọn
    const currentVoices = voices.length > 0 ? voices : window.speechSynthesis.getVoices();
    const matchedVoice = findBestVoice(langCode, currentVoices);

    if (matchedVoice) {
      utterance.voice = matchedVoice;
      utterance.lang = matchedVoice.lang;
    }

    utterance.onend = () => setIsPlaying(false);
    utterance.onerror = (e) => {
      console.warn('SpeechSynthesis error:', e);
      setIsPlaying(false);
    };

    window.speechSynthesis.speak(utterance);
    setIsPlaying(true);
  };

  return (
    <div className="bg-amber-50 border border-amber-200 rounded-xl p-3 flex items-center justify-between shadow-sm">
      <div className="flex items-center space-x-3 overflow-hidden">
        <div className={`w-10 h-10 rounded-full flex items-center justify-center shrink-0 ${isPlaying ? 'bg-amber-600 text-white animate-pulse' : 'bg-amber-100 text-amber-700'}`}>
          {isPlaying ? <Volume2 size={20} /> : <VolumeX size={20} />}
        </div>
        <div className="truncate">
          <p className="text-xs font-semibold text-slate-800 truncate">{title}</p>
          <p className="text-[10px] text-amber-700 font-medium truncate" title={activeVoiceName}>
            {audioUrl ? '🎵 Audio MP3' : `🗣️ Web Speech: ${activeVoiceName || 'Tự động'}`}
          </p>
        </div>
      </div>

      <div className="flex items-center space-x-2 shrink-0">
        <button
          onClick={handlePlay}
          className="p-2 bg-amber-600 hover:bg-amber-700 text-white rounded-full transition shadow-sm active:scale-95"
          title={isPlaying ? 'Tạm dừng' : 'Phát thuyết minh'}
        >
          {isPlaying ? <Pause size={16} /> : <Play size={16} />}
        </button>
        <button
          onClick={() => {
            stopPlayback();
            handlePlay();
          }}
          className="p-2 bg-slate-100 hover:bg-slate-200 text-slate-600 rounded-full transition active:scale-95"
          title="Phát lại từ đầu"
        >
          <RotateCcw size={16} />
        </button>
      </div>
    </div>
  );
};
