import { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { getPOIsFromDB } from '../services/db';
import { syncPOIs } from '../services/poiSync';
import { POI } from '../types';
import { 
  ArrowLeft, 
  Play, 
  Pause, 
  RotateCcw, 
  RotateCw, 
  Headphones, 
  AlertTriangle, 
  MessageSquare, 
  MapPin, 
  Volume2
} from 'lucide-react';

export default function POIDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const poiId = Number(id);

  const [poi, setPoi] = useState<POI | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [isPlaying, setIsPlaying] = useState<boolean>(false);
  const [currentTime, setCurrentTime] = useState<number>(0);
  const [duration, setDuration] = useState<number>(0);

  const audioRef = useRef<HTMLAudioElement | null>(null);

  useEffect(() => {
    const loadPoiDetail = async () => {
      const lang = localStorage.getItem('customer_lang') || 'vi';
      try {
        // Đọc từ IndexedDB trước
        let list = await getPOIsFromDB(lang);
        let found = list.find((p) => p.poi_id === poiId);

        if (!found) {
          // Thử sync nếu chưa có trong DB
          const result = await syncPOIs(lang);
          found = result.pois.find((p) => p.poi_id === poiId);
        }

        if (found) {
          setPoi(found);
        }
      } catch (err) {
        console.warn('Lỗi đọc POI chi tiết:', err);
      } finally {
        setLoading(false);
      }
    };

    loadPoiDetail();
  }, [poiId]);

  // Điều khiển Audio
  const togglePlay = () => {
    if (!audioRef.current) return;
    if (isPlaying) {
      audioRef.current.pause();
    } else {
      audioRef.current.play().catch((err) => console.warn('Lỗi phát audio:', err));
    }
  };

  const handleTimeUpdate = () => {
    if (audioRef.current) {
      setCurrentTime(audioRef.current.currentTime);
      setDuration(audioRef.current.duration || 0);
    }
  };

  const handleSeek = (e: React.ChangeEvent<HTMLInputElement>) => {
    const time = Number(e.target.value);
    if (audioRef.current) {
      audioRef.current.currentTime = time;
      setCurrentTime(time);
    }
  };

  const skipSeconds = (seconds: number) => {
    if (audioRef.current) {
      audioRef.current.currentTime = Math.max(0, Math.min(audioRef.current.currentTime + seconds, duration));
    }
  };

  const formatTime = (secs: number) => {
    if (isNaN(secs) || secs < 0) return '00:00';
    const m = Math.floor(secs / 60);
    const s = Math.floor(secs % 60);
    return `${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`;
  };

  const handleAskAIAboutThis = () => {
    if (poi) {
      navigate('/chat', { state: { prefilledQuestion: `Hãy kể cho tôi nghe lịch sử và ý nghĩa của ${poi.title}` } });
    } else {
      navigate('/chat');
    }
  };

  if (loading) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center p-6 bg-amber-50/50">
        <div className="w-8 h-8 border-3 border-amber-600 border-t-transparent rounded-full animate-spin mb-2" />
        <span className="text-xs text-stone-500">Đang tải thông tin điểm tham quan...</span>
      </div>
    );
  }

  if (!poi) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center p-6 text-center">
        <p className="text-stone-500 mb-4">Không tìm thấy thông tin điểm tham quan này.</p>
        <button
          onClick={() => navigate('/map')}
          className="px-4 py-2 rounded-xl bg-amber-600 text-white text-xs font-semibold"
        >
          Quay lại bản đồ
        </button>
      </div>
    );
  }

  const hasAudio = Boolean(poi.audio_url && !poi.fallback);

  return (
    <div className="flex-1 flex flex-col min-h-screen bg-stone-50 pb-8">
      {/* Hidden Audio Element */}
      {hasAudio && (
        <audio
          ref={audioRef}
          src={poi.audio_url!}
          onPlay={() => setIsPlaying(true)}
          onPause={() => setIsPlaying(false)}
          onEnded={() => setIsPlaying(false)}
          onTimeUpdate={handleTimeUpdate}
          onLoadedMetadata={handleTimeUpdate}
          preload="metadata"
        />
      )}

      {/* Top Bar Floating Back */}
      <div className="relative">
        {/* Ảnh Thumbnail */}
        <div className="w-full h-64 bg-stone-900 relative overflow-hidden">
          {poi.thumbnail_url ? (
            <img
              src={poi.thumbnail_url}
              alt={poi.title}
              className="w-full h-full object-cover"
            />
          ) : (
            <div className="w-full h-full flex flex-col items-center justify-center bg-gradient-to-br from-amber-700 to-amber-900 text-white p-6 text-center">
              <MapPin className="w-12 h-12 mb-2 text-amber-300 opacity-80" />
              <h2 className="text-xl font-bold">{poi.title}</h2>
            </div>
          )}

          {/* Gradient Overlay */}
          <div className="absolute inset-0 bg-gradient-to-t from-stone-900/80 via-transparent to-stone-900/40" />

          {/* Nút Quay lại */}
          <button
            onClick={() => navigate('/map')}
            className="absolute top-4 left-4 p-2.5 rounded-full bg-white/80 hover:bg-white text-stone-800 backdrop-blur shadow-md transition-all active:scale-95"
            title="Quay lại"
          >
            <ArrowLeft className="w-5 h-5" />
          </button>

          {/* Badges trên ảnh */}
          <div className="absolute bottom-4 left-4 right-4 flex items-center justify-between">
            <span className="text-xs font-semibold px-2.5 py-1 rounded-full bg-amber-600 text-white shadow">
              Điểm #{poi.poi_id}
            </span>
            {poi.fallback && (
              <span className="text-xs font-medium px-2.5 py-1 rounded-full bg-amber-100 text-amber-800 flex items-center gap-1 shadow">
                <AlertTriangle className="w-3.5 h-3.5" />
                Bản dịch dự phòng
              </span>
            )}
          </div>
        </div>
      </div>

      {/* Nội dung chi tiết */}
      <div className="flex-1 px-5 pt-4 space-y-5">
        <div>
          <h1 className="text-xl font-bold text-stone-900 leading-snug">{poi.title}</h1>
          <p className="text-xs text-stone-500 mt-1 flex items-center gap-1">
            <MapPin className="w-3.5 h-3.5 text-amber-600" />
            <span>Tọa độ: {poi.latitude.toFixed(4)}, {poi.longitude.toFixed(4)}</span>
            <span>•</span>
            <span>Bán kính tự phát: {poi.trigger_radius}m</span>
          </p>
        </div>

        {/* Trình phát Audio Player Thuyết minh */}
        {hasAudio ? (
          <div className="p-4 rounded-2xl bg-amber-500/10 border border-amber-200/80 shadow-sm space-y-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2 text-amber-900 font-semibold text-xs">
                <Headphones className="w-4 h-4 text-amber-600" />
                <span>Thuyết minh tự động bằng âm thanh</span>
              </div>
              <span className="text-[11px] text-amber-700 font-mono">
                {formatTime(currentTime)} / {formatTime(duration)}
              </span>
            </div>

            {/* Slider tua âm thanh */}
            <input
              type="range"
              min={0}
              max={duration || 100}
              value={currentTime}
              onChange={handleSeek}
              className="w-full h-1.5 bg-amber-200 rounded-lg appearance-none cursor-pointer accent-amber-600"
            />

            {/* Điều khiển Play / Rewind / Fast-forward */}
            <div className="flex items-center justify-center gap-6 pt-1">
              <button
                onClick={() => skipSeconds(-10)}
                className="p-2 rounded-full hover:bg-amber-100 text-amber-900 transition-colors"
                title="Lùi 10 giây"
              >
                <RotateCcw className="w-5 h-5" />
              </button>

              <button
                onClick={togglePlay}
                className="p-4 rounded-full bg-amber-600 hover:bg-amber-700 text-white shadow-md active:scale-95 transition-all"
                title={isPlaying ? 'Tạm dừng' : 'Phát thuyết minh'}
              >
                {isPlaying ? <Pause className="w-6 h-6" /> : <Play className="w-6 h-6 ml-0.5" />}
              </button>

              <button
                onClick={() => skipSeconds(10)}
                className="p-2 rounded-full hover:bg-amber-100 text-amber-900 transition-colors"
                title="Tua 10 giây"
              >
                <RotateCw className="w-5 h-5" />
              </button>
            </div>
          </div>
        ) : (
          <div className="p-3.5 rounded-xl bg-stone-100 border border-stone-200 text-stone-500 text-xs flex items-center gap-2">
            <Volume2 className="w-4 h-4 shrink-0 text-stone-400" />
            <span>Chưa có bản ghi âm thuyết minh cho ngôn ngữ này.</span>
          </div>
        )}

        {/* Nội dung bài viết thuyết minh */}
        <div className="bg-white p-4 rounded-2xl border border-stone-200/80 shadow-sm">
          <h3 className="text-xs font-bold text-stone-400 uppercase tracking-wider mb-2">
            THUYẾT MINH CHI TIẾT
          </h3>
          <div className="text-stone-700 text-sm leading-relaxed whitespace-pre-line">
            {poi.description}
          </div>
        </div>

        {/* Nút Gọi Hỏi AI */}
        <button
          onClick={handleAskAIAboutThis}
          className="w-full py-3.5 px-4 rounded-xl border border-amber-300 bg-gradient-to-r from-amber-50 to-amber-100/70 hover:from-amber-100 hover:to-amber-200/80 text-amber-900 font-semibold text-xs flex items-center justify-center gap-2 shadow-sm transition-all"
        >
          <MessageSquare className="w-4 h-4 text-amber-700" />
          <span>Hỏi trợ lý AI về điểm tham quan này</span>
        </button>
      </div>
    </div>
  );
}
