import React, { useEffect, useRef, useState } from 'react';
import L from 'leaflet';
import { POI, TourRoute } from '../types';
import { getDistanceInMeters, LINH_UNG_CENTER } from '../utils/geo';
import { AudioPlayer } from '../components/AudioPlayer';
import { Navigation2, MapPin, Compass, PlayCircle, Eye, X } from 'lucide-react';

interface Props {
  pois: POI[];
  routes: TourRoute[];
  selectedLang: string;
}

export const MapView: React.FC<Props> = ({ pois, routes, selectedLang }) => {
  const mapContainerRef = useRef<HTMLDivElement>(null);
  const mapInstanceRef = useRef<L.Map | null>(null);
  const userMarkerRef = useRef<L.Marker | null>(null);
  const poiLayersRef = useRef<{ [key: string]: { marker: L.Marker; circle: L.Circle } }>({});
  const routeLineRef = useRef<L.Polyline | null>(null);

  // Vị trí người dùng (mặc định tại cổng Tam Quan)
  const [userPos, setUserPos] = useState<[number, number]>([16.09880, 108.27670]);
  
  // POI đang kích hoạt thuyết minh
  const [activePOI, setActivePOI] = useState<POI | null>(null);
  const [selectedRouteId, setSelectedRouteId] = useState<string>('route_1');

  // Lưu trữ các POI đã phát âm thanh để tránh lặp lại (mỗi lần vào vùng chỉ phát 1 lần)
  const triggeredPOIsRef = useRef<Set<string>>(new Set());

  // Chỉ số POI cho nút "Đi tới POI tiếp theo"
  const [nextPoiIndex, setNextPoiIndex] = useState(0);

  // 1. Khởi tạo bản đồ Leaflet
  useEffect(() => {
    if (!mapContainerRef.current || mapInstanceRef.current) return;

    const map = L.map(mapContainerRef.current, {
      center: [LINH_UNG_CENTER.lat, LINH_UNG_CENTER.lng],
      zoom: 17,
      maxZoom: 19,
      minZoom: 15,
    });

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '&copy; OpenStreetMap contributors'
    }).addTo(map);

    // Custom Icon vị trí người dùng
    const userIcon = L.divIcon({
      className: 'user-pos-icon',
      html: `
        <div class="relative flex items-center justify-center">
          <div class="w-5 h-5 bg-blue-600 rounded-full border-2 border-white shadow-lg animate-pulse"></div>
          <div class="absolute w-10 h-10 bg-blue-400 rounded-full opacity-30 animate-ping"></div>
        </div>
      `,
      iconSize: [24, 24],
      iconAnchor: [12, 12]
    });

    const marker = L.marker(userPos, { icon: userIcon, zIndexOffset: 1000 }).addTo(map);
    userMarkerRef.current = marker;

    // Click bản đồ để giả lập vị trí
    map.on('click', (e: L.LeafletMouseEvent) => {
      const newPos: [number, number] = [e.latlng.lat, e.latlng.lng];
      setUserPos(newPos);
    });

    mapInstanceRef.current = map;

    return () => {
      map.remove();
      mapInstanceRef.current = null;
    };
  }, []);

  // 2. Cập nhật vị trí Marker người dùng khi userPos thay đổi
  useEffect(() => {
    if (userMarkerRef.current) {
      userMarkerRef.current.setLatLng(userPos);
    }
    // Kiểm tra Geofence với các POIs
    checkGeofence(userPos[0], userPos[1]);
  }, [userPos, pois, selectedLang]);

  // 3. Render các POI và vòng tròn bán kính trigger
  useEffect(() => {
    const map = mapInstanceRef.current;
    if (!map) return;

    // Xóa layer cũ
    Object.values(poiLayersRef.current).forEach(({ marker, circle }) => {
      map.removeLayer(marker);
      map.removeLayer(circle);
    });
    poiLayersRef.current = {};

    pois.forEach((poi, idx) => {
      const loc = poi.localizations?.[selectedLang] || { title: poi.name, description: poi.original_description, audio_url: '' };

      // Icon POI
      const poiIcon = L.divIcon({
        className: 'poi-custom-marker',
        html: `
          <div class="w-8 h-8 bg-amber-600 text-white rounded-full border-2 border-white shadow-md flex items-center justify-center text-xs font-bold hover:scale-110 transition cursor-pointer">
            ${idx + 1}
          </div>
        `,
        iconSize: [32, 32],
        iconAnchor: [16, 16]
      });

      const marker = L.marker([poi.latitude, poi.longitude], { icon: poiIcon }).addTo(map);
      marker.on('click', () => {
        setActivePOI(poi);
      });

      // Vòng tròn Geofence (trigger_radius)
      const circle = L.circle([poi.latitude, poi.longitude], {
        radius: poi.trigger_radius,
        color: '#d97706',
        fillColor: '#f59e0b',
        fillOpacity: 0.15,
        weight: 1.5,
        dashArray: '4, 4'
      }).addTo(map);

      poiLayersRef.current[poi.poi_id] = { marker, circle };
    });
  }, [pois, selectedLang]);

  // 4. Vẽ lộ trình tham quan (Tour Route)
  useEffect(() => {
    const map = mapInstanceRef.current;
    if (!map) return;

    if (routeLineRef.current) {
      map.removeLayer(routeLineRef.current);
      routeLineRef.current = null;
    }

    const currentRoute = routes.find((r) => r.route_id === selectedRouteId);
    if (currentRoute && currentRoute.poi_ids.length > 0) {
      const latlngs: [number, number][] = [];
      currentRoute.poi_ids.forEach((pid) => {
        const p = pois.find((item) => item.poi_id === pid);
        if (p) latlngs.push([p.latitude, p.longitude]);
      });

      if (latlngs.length > 1) {
        const polyline = L.polyline(latlngs, {
          color: '#0f766e',
          weight: 4,
          opacity: 0.8,
          dashArray: '8, 6'
        }).addTo(map);
        routeLineRef.current = polyline;
      }
    }
  }, [routes, selectedRouteId, pois]);

  // 5. Logic Geofence
  const checkGeofence = (uLat: number, uLng: number) => {
    let enteredPoi: POI | null = null;

    pois.forEach((poi) => {
      const dist = getDistanceInMeters(uLat, uLng, poi.latitude, poi.longitude);

      if (dist <= poi.trigger_radius) {
        // Người dùng nằm trong bán kính POI
        if (!triggeredPOIsRef.current.has(poi.poi_id)) {
          // Lần đầu bước vào vùng này -> Kích hoạt thuyết minh
          triggeredPOIsRef.current.add(poi.poi_id);
          enteredPoi = poi;
        }
      } else {
        // Khi người dùng đi ra khỏi bán kính -> Reset để lần sau vào lại có thể phát lại
        if (triggeredPOIsRef.current.has(poi.poi_id)) {
          triggeredPOIsRef.current.delete(poi.poi_id);
        }
      }
    });

    if (enteredPoi) {
      setActivePOI(enteredPoi);
    }
  };

  // 6. Nút Giả lập vị trí: "Đi tới POI tiếp theo"
  const handleSimulateNextPOI = () => {
    if (!pois || pois.length === 0) return;
    const target = pois[nextPoiIndex % pois.length];
    // Đặt vị trí người dùng lệch một chút (trong bán kính trigger)
    const newLat = target.latitude + 0.00005;
    const newLng = target.longitude + 0.00005;
    setUserPos([newLat, newLng]);

    if (mapInstanceRef.current) {
      mapInstanceRef.current.panTo([newLat, newLng]);
    }
    setNextPoiIndex((prev) => prev + 1);
  };

  // Lấy dữ liệu bản dịch hiện tại của activePOI
  const currentLoc = activePOI
    ? activePOI.localizations?.[selectedLang] || {
        title: activePOI.name,
        description: activePOI.original_description,
        audio_url: ''
      }
    : null;

  return (
    <div className="relative w-full h-[calc(100vh-120px)] flex flex-col">
      {/* Thanh điều khiển trên bản đồ */}
      <div className="absolute top-3 left-3 right-3 z-[500] flex flex-wrap gap-2 items-center justify-between pointer-events-none">
        <div className="bg-white/95 backdrop-blur px-3 py-1.5 rounded-2xl shadow-md border border-slate-100 flex items-center space-x-2 pointer-events-auto">
          <Compass size={16} className="text-amber-600 animate-spin-slow" />
          <span className="text-xs font-semibold text-slate-800">
            {routes.find((r) => r.route_id === selectedRouteId)?.route_name || 'Lộ trình tham quan'}
          </span>
        </div>

        {/* Nút Giả Lập Vị Trí */}
        <div className="flex items-center space-x-2 pointer-events-auto">
          <button
            onClick={handleSimulateNextPOI}
            className="px-3 py-1.5 bg-blue-600 hover:bg-blue-700 active:scale-95 text-white rounded-2xl shadow-md text-xs font-semibold flex items-center space-x-1.5 transition"
            title="Mô phỏng bước chân người dùng tới POI kế tiếp"
          >
            <Navigation2 size={14} />
            <span>Đi tới POI tiếp theo ({((nextPoiIndex % pois.length) + 1)}/{pois.length})</span>
          </button>
        </div>
      </div>

      {/* Map Leaflet Container */}
      <div ref={mapContainerRef} className="w-full flex-1 z-0" />

      {/* Chú thích click bản đồ */}
      <div className="absolute bottom-4 left-3 z-[400] bg-white/90 backdrop-blur px-2.5 py-1 rounded-xl shadow text-[10px] text-slate-600 border border-slate-200">
        💡 <em>Mẹo: Click bất kỳ đâu trên bản đồ để di chuyển vị trí du khách</em>
      </div>

      {/* Modal / Card Thuyết minh POI khi Geofence kích hoạt */}
      {activePOI && currentLoc && (
        <div className="absolute bottom-3 left-3 right-3 z-[500] max-w-lg mx-auto bg-white rounded-3xl shadow-2xl border border-amber-200 p-4 transition-all transform animate-in fade-in slide-in-from-bottom duration-300">
          <div className="flex items-start justify-between pb-2 mb-2 border-b border-slate-100">
            <div className="flex items-center space-x-2">
              <span className="px-2 py-0.5 bg-amber-100 text-amber-800 font-bold rounded-lg text-xs">
                VÙNG THUYẾT MINH
              </span>
              <h3 className="text-sm font-bold text-slate-800 truncate max-w-[200px]">
                {currentLoc.title}
              </h3>
            </div>
            <button
              onClick={() => setActivePOI(null)}
              className="p-1 text-slate-400 hover:text-slate-600 rounded-full"
            >
              <X size={18} />
            </button>
          </div>

          <div className="flex gap-3 mb-3">
            {activePOI.thumbnail_url && (
              <img
                src={activePOI.thumbnail_url}
                alt={currentLoc.title}
                className="w-20 h-20 object-cover rounded-xl shadow-sm border border-slate-100 shrink-0"
              />
            )}
            <div className="overflow-y-auto max-h-24 pr-1 text-xs text-slate-600 leading-relaxed">
              {currentLoc.description}
            </div>
          </div>

          {/* Trình phát Audio Player tự động */}
          <AudioPlayer
            title={currentLoc.title}
            text={currentLoc.description}
            audioUrl={currentLoc.audio_url}
            langCode={selectedLang}
            autoPlay={true}
          />
        </div>
      )}
    </div>
  );
};
