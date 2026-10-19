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
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = LANG_MAP[langCode] || 'vi-VN';
    utterance.rate = 0.95; // Tốc độ vừa phải cho bài thuyết minh

    utterance.onend = () => setIsPlaying(false);
    utterance.onerror = () => setIsPlaying(false);

    window.speechSynthesis.speak(utterance);
    setIsPlaying(true);
  };

  return (
    <div className="bg-amber-50 border border-amber-200 rounded-xl p-3 flex items-center justify-between shadow-sm">
      <div className="flex items-center space-x-3 overflow-hidden">
        <div className={`w-10 h-10 rounded-full flex items-center justify-center ${isPlaying ? 'bg-amber-600 text-white animate-pulse' : 'bg-amber-100 text-amber-700'}`}>
          {isPlaying ? <Volume2 size={20} /> : <VolumeX size={20} />}
        </div>
        <div className="truncate">
          <p className="text-xs font-semibold text-slate-800 truncate">{title}</p>
          <p className="text-[10px] text-amber-700 font-medium">
            {audioUrl ? '🎵 Audio MP3' : '🗣️ Web Speech Thuyết Minh AI'}
          </p>
        </div>
      </div>

      <div className="flex items-center space-x-2">
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
