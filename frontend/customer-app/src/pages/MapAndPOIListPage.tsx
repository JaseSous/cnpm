import { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { MapContainer, TileLayer, Marker, Popup, useMap } from 'react-leaflet';
import L from 'leaflet';
import { POI } from '../types';
import { syncPOIs } from '../services/poiSync';
import { calculateHaversineDistance, useGPSTracker } from '../services/gpsEngine';
import { 
  Map as MapIcon, 
  List, 
  Headphones, 
  Navigation2, 
  MessageSquare, 
  Globe2, 
  ChevronRight, 
  AlertTriangle,
  Radio,
  Play,
  Pause,
  X
} from 'lucide-react';

const TEMPLE_CENTER: [number, number] = [16.1005, 108.2772];

const createPoiIcon = (title: string, index: number) => {
  return L.divIcon({
    className: 'poi-custom-marker',
    html: `
      <div style="
        background: #d97706;
        color: white;
        border: 2px solid white;
        border-radius: 50%;
        width: 32px;
        height: 32px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: bold;
        font-size: 13px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.3);
      " title="${title}">
        ${index + 1}
      </div>
    `,
    iconSize: [32, 32],
    iconAnchor: [16, 16],
    popupAnchor: [0, -18],
  });
};

const userLocationIcon = L.divIcon({
  className: 'user-location-marker',
  html: `
    <div style="position: relative; width: 22px; height: 22px;">
      <div style="
        position: absolute; width: 100%; height: 100%; border-radius: 50%;
        background: rgba(59, 130, 246, 0.4); animation: ping 1.5s cubic-bezier(0, 0, 0.2, 1) infinite;
      "></div>
      <div style="
        position: absolute; top: 3px; left: 3px; width: 16px; height: 16px;
        border-radius: 50%; background: #2563eb; border: 2.5px solid white;
        box-shadow: 0 2px 4px rgba(0,0,0,0.3);
      "></div>
    </div>
  `,
  iconSize: [22, 22],
  iconAnchor: [11, 11],
});

function MapController({ center }: { center: [number, number] }) {
  const map = useMap();
  useEffect(() => {
    map.setView(center, map.getZoom());
  }, [center, map]);
  return null;
}

export default function MapAndPOIListPage() {
  const navigate = useNavigate();
  const [pois, setPois] = useState<POI[]>([]);
  const [activeTab, setActiveTab] = useState<'map' | 'list'>('map');
  const [currentLang, setCurrentLang] = useState<string>('vi');
  const [loading, setLoading] = useState<boolean>(true);
  const [mapCenter, setMapCenter] = useState<[number, number]>(TEMPLE_CENTER);
  
  // Trạng thái GPS và Auto-Audio Trigger
  const [autoAudioEnabled, setAutoAudioEnabled] = useState<boolean>(true);
  const [miniPlayerPlaying, setMiniPlayerPlaying] = useState<boolean>(false);
  const miniAudioRef = useRef<HTMLAudioElement | null>(null);

  const {
    currentCoords,
    activeTriggeredPoi,
    setActiveTriggeredPoi,
  } = useGPSTracker(pois, {
    autoAudioEnabled,
    onTriggerPOI: (poi) => {
      // Khi bước vào vùng POI, tự động phát audio
      if (miniAudioRef.current && poi.audio_url) {
        miniAudioRef.current.src = poi.audio_url;
        miniAudioRef.current.play().catch((e) => console.warn('Autoplay blocked:', e));
        setMiniPlayerPlaying(true);
      }
    },
  });

  useEffect(() => {
    const lang = localStorage.getItem('customer_lang') || 'vi';
    setCurrentLang(lang);
    loadPOIs(lang);
  }, []);

  const loadPOIs = async (lang: string) => {
    setLoading(true);
    try {
      const result = await syncPOIs(lang);
      setPois(result.pois);
    } catch (e) {
      console.warn('Lỗi load POIs:', e);
    } finally {
      setLoading(false);
    }
  };

  const handleLocateMe = () => {
    if (currentCoords) {
      setMapCenter(currentCoords);
    } else {
      alert('Đang tìm vị trí GPS của bạn. Vui lòng cấp quyền truy cập vị trí trên trình duyệt.');
    }
  };

  // Tính khoảng cách cho từng POI nếu đã có tọa độ GPS
  const processedPOIs = pois.map((p) => {
    if (currentCoords) {
      const dist = calculateHaversineDistance(currentCoords[0], currentCoords[1], p.latitude, p.longitude);
      return { ...p, distance: dist };
    }
    return p;
  });

  if (currentCoords) {
    processedPOIs.sort((a, b) => (a.distance || 0) - (b.distance || 0));
  }

  const toggleMiniPlay = () => {
    if (!miniAudioRef.current) return;
    if (miniPlayerPlaying) {
      miniAudioRef.current.pause();
      setMiniPlayerPlaying(false);
    } else {
      miniAudioRef.current.play().then(() => setMiniPlayerPlaying(true)).catch(() => {});
    }
  };

  return (
    <div className="flex-1 flex flex-col h-screen overflow-hidden bg-stone-50">
      {/* Hidden Auto Audio Element */}
      <audio
        ref={miniAudioRef}
        onEnded={() => setMiniPlayerPlaying(false)}
        onPause={() => setMiniPlayerPlaying(false)}
        onPlay={() => setMiniPlayerPlaying(true)}
      />

      {/* Top Header */}
      <header className="px-4 py-3 bg-amber-600 text-white flex items-center justify-between shadow-md z-10 shrink-0">
        <div>
          <h1 className="text-base font-bold tracking-tight">CHÙA LINH ỨNG</h1>
          <p className="text-[11px] text-amber-100 flex items-center gap-1">
            <span>Bãi Bụt - Sơn Trà</span>
            <span>•</span>
            <span className="uppercase font-semibold">{currentLang}</span>
          </p>
        </div>

        <div className="flex items-center gap-2">
          {/* Toggle Auto Audio GPS */}
          <button
            onClick={() => setAutoAudioEnabled(!autoAudioEnabled)}
            className={`flex items-center gap-1 px-2.5 py-1.5 rounded-full text-xs font-semibold transition-all ${
              autoAudioEnabled
                ? 'bg-amber-100 text-amber-900 shadow-sm'
                : 'bg-amber-800/60 text-amber-200'
            }`}
            title="Thuyết minh GPS tự động"
          >
            <Radio className={`w-3.5 h-3.5 ${autoAudioEnabled ? 'text-amber-700 animate-pulse' : ''}`} />
            <span>GPS {autoAudioEnabled ? 'BẬT' : 'TẮT'}</span>
          </button>

          {/* Nút đổi ngôn ngữ */}
          <button
            onClick={() => navigate('/')}
            className="p-2 rounded-full bg-amber-700/60 hover:bg-amber-700 text-white transition-colors"
            title="Đổi ngôn ngữ"
          >
            <Globe2 className="w-4 h-4" />
          </button>

          {/* Nút Chatbot AI */}
          <button
            onClick={() => navigate('/chat')}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-white text-amber-800 text-xs font-semibold shadow hover:bg-amber-50 active:scale-95 transition-all"
          >
            <MessageSquare className="w-3.5 h-3.5 text-amber-600" />
            <span>Hỏi AI</span>
          </button>
        </div>
      </header>

      {/* Segment Tab Control (Bản đồ / Danh sách) */}
      <div className="px-4 py-2 bg-white border-b border-stone-200 flex items-center justify-between shrink-0 shadow-sm">
        <div className="flex bg-stone-100 p-1 rounded-xl text-xs font-medium w-full max-w-[260px] mx-auto">
          <button
            onClick={() => setActiveTab('map')}
            className={`flex-1 py-1.5 rounded-lg flex items-center justify-center gap-1.5 transition-all ${
              activeTab === 'map' ? 'bg-white text-amber-800 shadow-sm font-semibold' : 'text-stone-500'
            }`}
          >
            <MapIcon className="w-3.5 h-3.5" />
            <span>Bản đồ</span>
          </button>
          <button
            onClick={() => setActiveTab('list')}
            className={`flex-1 py-1.5 rounded-lg flex items-center justify-center gap-1.5 transition-all ${
              activeTab === 'list' ? 'bg-white text-amber-800 shadow-sm font-semibold' : 'text-stone-500'
            }`}
          >
            <List className="w-3.5 h-3.5" />
            <span>Danh sách ({pois.length})</span>
          </button>
        </div>
      </div>

      {/* Main Content Area */}
      <div className="flex-1 relative overflow-hidden flex flex-col">
        {loading ? (
          <div className="flex-1 flex flex-col items-center justify-center gap-3">
            <div className="w-8 h-8 border-3 border-amber-600 border-t-transparent rounded-full animate-spin" />
            <span className="text-xs text-stone-500">Đang tải bản đồ & điểm tham quan...</span>
          </div>
        ) : (
          <>
            {/* View Bản đồ */}
            <div className={`flex-1 relative ${activeTab === 'map' ? 'block' : 'hidden'}`}>
              <MapContainer
                center={mapCenter}
                zoom={17}
                style={{ width: '100%', height: '100%' }}
                zoomControl={false}
              >
                <TileLayer
                  attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
                  url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                />
                <MapController center={mapCenter} />

                {/* Vị trí của du khách */}
                {currentCoords && (
                  <Marker position={currentCoords} icon={userLocationIcon}>
                    <Popup>
                      <div className="text-xs font-semibold text-stone-800">
                        📍 Vị trí hiện tại của bạn
                      </div>
                    </Popup>
                  </Marker>
                )}

                {/* Markers các điểm POI */}
                {pois.map((poi, idx) => (
                  <Marker
                    key={poi.poi_id}
                    position={[poi.latitude, poi.longitude]}
                    icon={createPoiIcon(poi.title, idx)}
                  >
                    <Popup>
                      <div className="p-1 max-w-[200px]">
                        <h4 className="font-bold text-sm text-stone-900 leading-snug">{poi.title}</h4>
                        <p className="text-xs text-stone-500 line-clamp-2 mt-1">
                          {poi.description}
                        </p>
                        <button
                          onClick={() => navigate(`/poi/${poi.poi_id}`)}
                          className="mt-2 w-full py-1.5 px-3 rounded-lg bg-amber-600 text-white text-xs font-semibold hover:bg-amber-700 flex items-center justify-center gap-1"
                        >
                          <Headphones className="w-3.5 h-3.5" />
                          <span>Nghe thuyết minh</span>
                        </button>
                      </div>
                    </Popup>
                  </Marker>
                ))}
              </MapContainer>

              {/* Nút định vị vị trí người dùng */}
              <button
                onClick={handleLocateMe}
                className="absolute right-4 bottom-6 z-[400] p-3 rounded-full bg-white text-stone-800 shadow-xl border border-stone-200 active:scale-95 transition-transform"
                title="Định vị vị trí của tôi"
              >
                <Navigation2 className="w-5 h-5 text-blue-600" />
              </button>
            </div>

            {/* View Danh sách POI */}
            <div className={`flex-1 overflow-y-auto p-4 space-y-3 ${activeTab === 'list' ? 'block' : 'hidden'}`}>
              {processedPOIs.length === 0 ? (
                <div className="text-center py-16 text-stone-400 text-sm">
                  Chưa có điểm tham quan nào được cập nhật.
                </div>
              ) : (
                processedPOIs.map((poi, idx) => (
                  <div
                    key={poi.poi_id}
                    onClick={() => navigate(`/poi/${poi.poi_id}`)}
                    className="p-3.5 bg-white rounded-2xl border border-stone-200/80 shadow-sm hover:shadow-md transition-all active:scale-[0.99] flex items-center gap-3.5 cursor-pointer"
                  >
                    <div className="relative w-16 h-16 rounded-xl bg-amber-50 border border-amber-200 overflow-hidden shrink-0 flex items-center justify-center">
                      {poi.thumbnail_url ? (
                        <img
                          src={poi.thumbnail_url}
                          alt={poi.title}
                          className="w-full h-full object-cover"
                        />
                      ) : (
                        <span className="text-amber-800 font-bold text-lg">{idx + 1}</span>
                      )}
                      {poi.audio_url && (
                        <div className="absolute bottom-1 right-1 p-1 rounded-full bg-amber-600 text-white shadow">
                          <Headphones className="w-2.5 h-2.5" />
                        </div>
                      )}
                    </div>

                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2">
                        <span className="text-[11px] font-bold text-amber-700 bg-amber-50 px-1.5 py-0.5 rounded">
                          #{idx + 1}
                        </span>
                        {poi.distance !== undefined && (
                          <span className="text-[11px] font-medium text-stone-600 bg-stone-100 px-1.5 py-0.5 rounded">
                            Cách {poi.distance}m
                          </span>
                        )}
                        {poi.fallback && (
                          <span className="text-[10px] text-amber-700 bg-amber-100/70 px-1.5 py-0.5 rounded flex items-center gap-0.5">
                            <AlertTriangle className="w-2.5 h-2.5" />
                            Dự phòng
                          </span>
                        )}
                      </div>
                      <h3 className="font-bold text-sm text-stone-900 truncate mt-0.5">
                        {poi.title}
                      </h3>
                      <p className="text-xs text-stone-500 line-clamp-1 mt-0.5">
                        {poi.description}
                      </p>
                    </div>

                    <ChevronRight className="w-5 h-5 text-stone-300 shrink-0" />
                  </div>
                ))
              )}
            </div>
          </>
        )}

        {/* Floating Mini Player khi GPS tự động kích hoạt POI */}
        {activeTriggeredPoi && (
          <div className="absolute bottom-4 left-4 right-4 z-[500] p-3.5 rounded-2xl bg-stone-900/95 text-white shadow-2xl backdrop-blur border border-amber-500/30 flex items-center justify-between gap-3 animate-slide-up">
            <div
              className="flex items-center gap-3 min-w-0 flex-1 cursor-pointer"
              onClick={() => navigate(`/poi/${activeTriggeredPoi.poi_id}`)}
            >
              <div className="w-10 h-10 rounded-xl bg-amber-600 text-white flex items-center justify-center shrink-0">
                <Headphones className="w-5 h-5 animate-bounce" />
              </div>
              <div className="min-w-0 flex-1">
                <div className="text-[10px] font-bold uppercase tracking-wider text-amber-400">
                  TỰ ĐỘNG THUYẾT MINH
                </div>
                <div className="text-xs font-semibold truncate text-white">
                  {activeTriggeredPoi.title}
                </div>
              </div>
            </div>

            <div className="flex items-center gap-1.5 shrink-0">
              <button
                onClick={toggleMiniPlay}
                className="p-2 rounded-full bg-amber-600 text-white hover:bg-amber-500 transition-colors"
                title={miniPlayerPlaying ? 'Tạm dừng' : 'Phát tiếp'}
              >
                {miniPlayerPlaying ? <Pause className="w-4 h-4" /> : <Play className="w-4 h-4 ml-0.5" />}
              </button>
              <button
                onClick={() => setActiveTriggeredPoi(null)}
                className="p-2 rounded-full hover:bg-stone-800 text-stone-400 hover:text-white transition-colors"
                title="Đóng thông báo"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
