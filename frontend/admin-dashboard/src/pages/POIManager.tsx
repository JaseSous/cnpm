import React, { useState, useEffect, useRef, useMemo } from 'react';
import { MapContainer, TileLayer, Marker, Popup, Circle, useMap, useMapEvents } from 'react-leaflet';
import L from 'leaflet';
import { poiClient, getMediaUrl, DEFAULT_POI_IMAGE } from '../api/client';
import { 
  MapPin, 
  Plus, 
  Edit2, 
  Trash2, 
  AlertCircle, 
  Loader2, 
  Search,
  CheckCircle,
  Clock,
  X,
  Map as MapIcon,
  List,
  Crosshair,
  Radio
} from 'lucide-react';

const TEMPLE_CENTER: [number, number] = [16.1001, 108.2775];

interface Language {
  language_code: string;
  native_name: string;
}

interface POIItem {
  poi_id: number;
  original_language_code: string;
  original_title: string;
  original_description: string;
  latitude: number;
  longitude: number;
  trigger_radius: number;
  thumbnail_url?: string;
  revision: number;
  vector_status: string;
  created_at: string;
}

// Icons for Leaflet Markers
const activePoiIcon = L.divIcon({
  className: 'active-poi-marker',
  html: `
    <div style="position: relative; width: 36px; height: 36px; display: flex; align-items: center; justify-content: center;">
      <div style="position: absolute; inset: -4px; border-radius: 50%; background: rgba(245, 158, 11, 0.4); animation: ping 1.8s cubic-bezier(0, 0, 0.2, 1) infinite;"></div>
      <div style="
        width: 32px;
        height: 32px;
        border-radius: 50%;
        background: #f59e0b;
        border: 2.5px solid #ffffff;
        box-shadow: 0 4px 10px rgba(0,0,0,0.5);
        display: flex;
        align-items: center;
        justify-content: center;
        color: #0f172a;
        font-weight: 900;
        font-size: 14px;
        cursor: grab;
      ">
        📍
      </div>
    </div>
  `,
  iconSize: [36, 36],
  iconAnchor: [18, 18],
  popupAnchor: [0, -20],
});

const createPoiBadgeIcon = (id: number, status: string, isCurrentEditing: boolean = false, isNearest: boolean = false) => {
  let bgColor = '#3b82f6';
  if (isNearest) {
    bgColor = '#eab308'; // Vàng nổi bật cho POI gần nhất
  } else if (isCurrentEditing) {
    bgColor = '#f59e0b';
  } else if (status === 'Synced') {
    bgColor = '#10b981';
  } else if (status === 'Failed') {
    bgColor = '#ef4444';
  }

  const borderStyle = isNearest ? '3px solid #fef08a' : '2px solid #ffffff';
  const shadowStyle = isNearest ? '0 0 12px rgba(234, 179, 8, 0.8)' : '0 3px 8px rgba(0,0,0,0.45)';

  return L.divIcon({
    className: 'badge-poi-marker',
    html: `
      <div style="
        width: 28px;
        height: 28px;
        border-radius: 50%;
        background: ${bgColor};
        border: ${borderStyle};
        box-shadow: ${shadowStyle};
        display: flex;
        align-items: center;
        justify-content: center;
        color: #ffffff;
        font-weight: 800;
        font-size: 11px;
      ">
        #${id}
      </div>
    `,
    iconSize: [28, 28],
    iconAnchor: [14, 14],
    popupAnchor: [0, -16],
  });
};

// Component xử lý click chọn tọa độ trên bản đồ
function MapLocationPicker({ onLocationSelect }: { onLocationSelect: (lat: number, lng: number) => void }) {
  useMapEvents({
    click(e) {
      onLocationSelect(Number(e.latlng.lat.toFixed(6)), Number(e.latlng.lng.toFixed(6)));
    },
  });
  return null;
}

// Component tự động sửa kích thước bản đồ khi modal mở
function MapAutoResize() {
  const map = useMap();
  useEffect(() => {
    map.invalidateSize();
    const t1 = setTimeout(() => map.invalidateSize(), 150);
    const t2 = setTimeout(() => map.invalidateSize(), 400);
    return () => {
      clearTimeout(t1);
      clearTimeout(t2);
    };
  }, [map]);
  return null;
}

// Component điều hướng tâm bản đồ
function MapRecenter({ center }: { center: [number, number] }) {
  const map = useMap();
  useEffect(() => {
    if (center && Number.isFinite(center[0]) && Number.isFinite(center[1])) {
      map.setView(center, map.getZoom());
    }
  }, [center, map]);
  return null;
}

// Component click trên Overview Map để tạo POI
function OverviewMapClickHandler({ onMapClick }: { onMapClick: (lat: number, lng: number) => void }) {
  useMapEvents({
    click(e) {
      onMapClick(Number(e.latlng.lat.toFixed(6)), Number(e.latlng.lng.toFixed(6)));
    },
  });
  return null;
}

export const POIManager: React.FC = () => {
  const [pois, setPois] = useState<POIItem[]>([]);
  const [languages, setLanguages] = useState<Language[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [viewMode, setViewMode] = useState<'table' | 'map'>('table');

  // Overview map click popup
  const [overviewClickPos, setOverviewClickPos] = useState<[number, number] | null>(null);

  // Modal State
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingPoi, setEditingPoi] = useState<POIItem | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isUploadingThumb, setIsUploadingThumb] = useState(false);

  // Form Fields
  const [formData, setFormData] = useState({
    original_title: '',
    original_language_code: 'vi',
    original_description: '',
    latitude: 16.1001,
    longitude: 108.2775,
    trigger_radius: 30,
    thumbnail_url: '',
  });

  const markerRef = useRef<L.Marker | null>(null);

  const markerDragHandlers = useMemo(
    () => ({
      dragend() {
        const marker = markerRef.current;
        if (marker != null) {
          const latLng = marker.getLatLng();
          setFormData((prev) => ({
            ...prev,
            latitude: Number(latLng.lat.toFixed(6)),
            longitude: Number(latLng.lng.toFixed(6)),
          }));
        }
      },
    }),
    []
  );

  const fetchData = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const [poisRes, langsRes] = await Promise.all([
        poiClient.get('/api/pois/pipeline-status'),
        poiClient.get('/api/languages')
      ]);
      setPois(poisRes.data);
      setLanguages(langsRes.data);
    } catch (err: any) {
      setError(err.response?.data?.detail?.message || 'Không thể tải dữ liệu điểm tham quan.');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleOpenCreateModal = (initLat?: number, initLng?: number) => {
    setEditingPoi(null);
    setFormData({
      original_title: '',
      original_language_code: 'vi',
      original_description: '',
      latitude: initLat ?? 16.1001,
      longitude: initLng ?? 108.2775,
      trigger_radius: 30,
      thumbnail_url: '',
    });
    setOverviewClickPos(null);
    setIsModalOpen(true);
  };

  const handleOpenEditModal = (poi: POIItem) => {
    setEditingPoi(poi);
    setFormData({
      original_title: poi.original_title || '',
      original_language_code: poi.original_language_code || 'vi',
      original_description: poi.original_description || '',
      latitude: poi.latitude ?? 16.1001,
      longitude: poi.longitude ?? 108.2775,
      trigger_radius: poi.trigger_radius ?? 30,
      thumbnail_url: poi.thumbnail_url || '',
    });
    setOverviewClickPos(null);
    setIsModalOpen(true);
  };

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (!e.target.files || e.target.files.length === 0) return;
    const file = e.target.files[0];
    const data = new FormData();
    data.append('file', file);

    setIsUploadingThumb(true);
    try {
      const res = await poiClient.post('/api/pois/upload-thumbnail', data, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      setFormData((prev) => ({ ...prev, thumbnail_url: res.data.thumbnail_url }));
    } catch (err: any) {
      alert('Không thể upload ảnh: ' + (err.response?.data?.detail || err.message));
    } finally {
      setIsUploadingThumb(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    setError(null);

    try {
      if (editingPoi) {
        // Cập nhật POI
        await poiClient.put(`/api/pois/${editingPoi.poi_id}`, formData);
      } else {
        // Tạo mới POI
        await poiClient.post('/api/pois', formData);
      }
      setIsModalOpen(false);
      await fetchData();
    } catch (err: any) {
      setError(err.response?.data?.detail?.message || 'Có lỗi khi lưu điểm tham quan.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleDelete = async (poiId: number) => {
    if (!window.confirm(`Bạn có chắc chắn muốn xóa điểm tham quan này (Mã: #${poiId}) không?`)) {
      return;
    }
    try {
      await poiClient.delete(`/api/pois/${poiId}`);
      await fetchData();
    } catch (err: any) {
      alert('Không thể xóa điểm tham quan: ' + (err.response?.data?.detail?.message || err.message));
    }
  };

  const filteredPois = pois.filter((p) =>
    (p.original_title || '').toLowerCase().includes(searchTerm.toLowerCase())
  );

  // Validated coordinates for map picker
  const validLat = Number.isFinite(formData.latitude) ? formData.latitude : 16.1001;
  const validLng = Number.isFinite(formData.longitude) ? formData.longitude : 108.2775;
  const validRadius = Number.isFinite(formData.trigger_radius) && formData.trigger_radius > 0 ? formData.trigger_radius : 30;

  // Tính toán khoảng cách (Haversine) và tìm POI gần nhất so với vị trí đang chọn
  const nearestPoi = useMemo<{ poi: POIItem; distance: number } | null>(() => {
    const candidates = pois.filter((p) => p.poi_id !== editingPoi?.poi_id && Number.isFinite(p.latitude) && Number.isFinite(p.longitude));
    if (candidates.length === 0) return null;

    const toRad = (val: number) => (val * Math.PI) / 180;
    const R = 6371e3; // mét
    const phi1 = toRad(validLat);
    const lambda1 = toRad(validLng);

    let minDistance = Infinity;
    let closestPoi: POIItem | null = null;

    candidates.forEach((p) => {
      const phi2 = toRad(p.latitude);
      const lambda2 = toRad(p.longitude);
      const deltaPhi = phi2 - phi1;
      const deltaLambda = lambda2 - lambda1;

      const a =
        Math.sin(deltaPhi / 2) * Math.sin(deltaPhi / 2) +
        Math.cos(phi1) * Math.cos(phi2) * Math.sin(deltaLambda / 2) * Math.sin(deltaLambda / 2);
      const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
      const d = R * c; // mét

      if (d < minDistance) {
        minDistance = d;
        closestPoi = p;
      }
    });

    if (!closestPoi) return null;
    return { poi: closestPoi, distance: Math.round(minDistance) };
  }, [pois, editingPoi, validLat, validLng]);

  return (
    <div className="p-6 md:p-10 max-w-7xl mx-auto space-y-8">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <h1 className="text-2xl md:text-3xl font-bold text-white tracking-tight flex items-center space-x-3">
            <MapPin className="w-8 h-8 text-amber-500" />
            <span>Quản lý điểm tham quan Chùa Linh Ứng (UC10)</span>
          </h1>
          <p className="text-slate-400 mt-1 text-sm md:text-base">
            CRUD điểm di tích, chọn vị trí GPS trực quan trên bản đồ kèm bán kính kích hoạt tự động.
          </p>
        </div>

        <button
          onClick={() => handleOpenCreateModal()}
          className="inline-flex items-center space-x-2 px-5 py-3 bg-amber-500 hover:bg-amber-600 text-slate-950 font-bold rounded-xl shadow-lg shadow-amber-500/20 transition-all cursor-pointer text-sm"
        >
          <Plus className="w-5 h-5" />
          <span>Thêm điểm POI mới</span>
        </button>
      </div>

      {error && (
        <div className="p-4 rounded-xl bg-red-500/10 border border-red-500/30 flex items-start space-x-3 text-red-400 text-sm">
          <AlertCircle className="w-5 h-5 flex-shrink-0 mt-0.5" />
          <span>{error}</span>
        </div>
      )}

      {/* Search & View Mode Switcher */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-4 flex flex-col md:flex-row items-stretch md:items-center justify-between gap-4 shadow-xl">
        <div className="relative flex-1">
          <Search className="w-5 h-5 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            placeholder="Tìm kiếm điểm tham quan theo tên..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-11 pr-4 py-2.5 bg-slate-800 border border-slate-700 rounded-xl text-white placeholder-slate-500 text-sm focus:outline-none focus:ring-2 focus:ring-amber-500/50"
          />
        </div>

        <div className="flex items-center space-x-3 justify-end">
          <div className="bg-slate-800 p-1 rounded-xl flex items-center border border-slate-700">
            <button
              onClick={() => setViewMode('table')}
              className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all cursor-pointer ${
                viewMode === 'table' 
                  ? 'bg-amber-500 text-slate-950 shadow-md font-bold' 
                  : 'text-slate-400 hover:text-white'
              }`}
            >
              <List className="w-4 h-4" />
              <span>Dạng bảng</span>
            </button>
            <button
              onClick={() => setViewMode('map')}
              className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all cursor-pointer ${
                viewMode === 'map' 
                  ? 'bg-amber-500 text-slate-950 shadow-md font-bold' 
                  : 'text-slate-400 hover:text-white'
              }`}
            >
              <MapIcon className="w-4 h-4" />
              <span>Bản đồ tổng quan</span>
            </button>
          </div>

          <div className="text-xs text-slate-400 font-medium whitespace-nowrap pl-2 border-l border-slate-800">
            Tổng số: <strong className="text-amber-400">{filteredPois.length}</strong> điểm
          </div>
        </div>
      </div>

      {/* MAIN VIEW: TABLE OR OVERVIEW MAP */}
      {viewMode === 'map' ? (
        /* MAP OVERVIEW VIEW */
        <div className="bg-slate-900 border border-slate-800 rounded-2xl shadow-xl overflow-hidden p-4 space-y-3">
          <div className="flex flex-wrap items-center justify-between text-xs text-slate-400 px-2 gap-2">
            <div className="flex items-center space-x-4">
              <span className="flex items-center space-x-1.5">
                <span className="w-3 h-3 rounded-full bg-emerald-500 inline-block border border-white/40"></span>
                <span>Đã đồng bộ Vector</span>
              </span>
              <span className="flex items-center space-x-1.5">
                <span className="w-3 h-3 rounded-full bg-amber-500 inline-block border border-white/40"></span>
                <span>Đang xử lý / Pending</span>
              </span>
              <span className="flex items-center space-x-1.5">
                <span className="w-3 h-3 rounded-full bg-red-500 inline-block border border-white/40"></span>
                <span>Lỗi đồng bộ</span>
              </span>
            </div>
            <div className="text-slate-400 italic">
              💡 Mẹo: Nhấp vào bất kỳ đâu trên bản đồ để tạo nhanh POI mới tại vị trí đó.
            </div>
          </div>

          <div className="h-[600px] w-full rounded-xl overflow-hidden border border-slate-800 relative">
            <MapContainer
              center={TEMPLE_CENTER}
              zoom={17}
              scrollWheelZoom={true}
              className="w-full h-full"
            >
              <TileLayer
                attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
                url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
              />
              <MapAutoResize />
              <OverviewMapClickHandler
                onMapClick={(lat, lng) => setOverviewClickPos([lat, lng])}
              />

              {/* Popup khi click vào vị trí trống trên Overview Map */}
              {overviewClickPos && (
                <Popup position={overviewClickPos} eventHandlers={{ remove: () => setOverviewClickPos(null) }}>
                  <div className="p-2 space-y-2 min-w-[180px]">
                    <div className="text-xs font-bold text-white flex items-center space-x-1">
                      <Crosshair className="w-3.5 h-3.5 text-amber-400" />
                      <span>Vị trí đã chọn</span>
                    </div>
                    <div className="text-[11px] font-mono text-slate-300">
                      Lat: {overviewClickPos[0].toFixed(6)}<br />
                      Lng: {overviewClickPos[1].toFixed(6)}
                    </div>
                    <button
                      onClick={() => handleOpenCreateModal(overviewClickPos[0], overviewClickPos[1])}
                      className="w-full py-1.5 px-2 bg-amber-500 hover:bg-amber-600 text-slate-950 font-bold rounded-lg text-xs flex items-center justify-center space-x-1 shadow transition-colors cursor-pointer"
                    >
                      <Plus className="w-3.5 h-3.5" />
                      <span>Tạo POI tại đây</span>
                    </button>
                  </div>
                </Popup>
              )}

              {/* Hiển thị tất cả POIs kèm Marker và Vòng tròn Bán kính */}
              {filteredPois.map((poi) => {
                const lat = poi.latitude ?? 16.1001;
                const lng = poi.longitude ?? 108.2775;
                const radius = poi.trigger_radius ?? 30;
                const circleColor = 
                  poi.vector_status === 'Synced' ? '#10b981' :
                  poi.vector_status === 'Failed' ? '#ef4444' : '#f59e0b';

                return (
                  <React.Fragment key={poi.poi_id}>
                    {/* Vòng tròn bán kính */}
                    <Circle
                      center={[lat, lng]}
                      radius={radius}
                      pathOptions={{
                        color: circleColor,
                        fillColor: circleColor,
                        fillOpacity: 0.18,
                        weight: 2,
                        dashArray: '4, 4',
                      }}
                    />
                    {/* Marker POI */}
                    <Marker
                      position={[lat, lng]}
                      icon={createPoiBadgeIcon(poi.poi_id, poi.vector_status)}
                    >
                      <Popup>
                        <div className="p-2 min-w-[220px] max-w-[260px] space-y-2">
                          <div className="flex items-start space-x-2.5">
                            <img
                              src={getMediaUrl(poi.thumbnail_url)}
                              alt={poi.original_title}
                              onError={(e) => { (e.currentTarget as HTMLImageElement).src = DEFAULT_POI_IMAGE; }}
                              className="w-12 h-12 rounded-lg object-cover bg-slate-800 border border-slate-700 shrink-0"
                            />
                            <div className="min-w-0 flex-1">
                              <div className="font-bold text-white text-xs leading-snug line-clamp-2">
                                #{poi.poi_id} - {poi.original_title}
                              </div>
                              <span className="text-[10px] text-amber-400 font-mono">
                                Rev v{poi.revision ?? 1} • {poi.original_language_code.toUpperCase()}
                              </span>
                            </div>
                          </div>

                          <div className="text-[11px] text-slate-300 font-mono space-y-0.5 border-t border-slate-800 pt-1.5">
                            <div>📍 Tọa độ: {lat.toFixed(5)}, {lng.toFixed(5)}</div>
                            <div className="text-amber-400 font-sans font-medium">🎯 Bán kính: {radius} mét</div>
                          </div>

                          <div className="flex items-center space-x-2 pt-1">
                            <button
                              onClick={() => handleOpenEditModal(poi)}
                              className="flex-1 py-1.5 px-2 bg-slate-800 hover:bg-slate-700 text-white rounded-lg text-xs font-semibold flex items-center justify-center space-x-1 transition-colors cursor-pointer"
                            >
                              <Edit2 className="w-3 h-3 text-amber-400" />
                              <span>Chỉnh sửa</span>
                            </button>
                            <button
                              onClick={() => handleDelete(poi.poi_id)}
                              className="py-1.5 px-2 bg-red-950/40 hover:bg-red-900/60 text-red-400 rounded-lg text-xs font-semibold transition-colors cursor-pointer"
                              title="Xóa POI"
                            >
                              <Trash2 className="w-3 h-3" />
                            </button>
                          </div>
                        </div>
                      </Popup>
                    </Marker>
                  </React.Fragment>
                );
              })}
            </MapContainer>
          </div>
        </div>
      ) : (
        /* TABLE VIEW */
        <div className="bg-slate-900 border border-slate-800 rounded-2xl shadow-xl overflow-hidden">
          {isLoading ? (
            <div className="p-12 text-center text-slate-400 flex flex-col items-center space-y-3">
              <Loader2 className="w-8 h-8 animate-spin text-amber-500" />
              <span>Đang tải danh sách điểm tham quan...</span>
            </div>
          ) : filteredPois.length === 0 ? (
            <div className="p-12 text-center text-slate-500">
              Không tìm thấy điểm tham quan nào phù hợp.
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm">
                <thead className="text-xs uppercase bg-slate-800/60 text-slate-400 border-b border-slate-800">
                  <tr>
                    <th className="px-6 py-4">Mã</th>
                    <th className="px-6 py-4">Tên điểm di tích</th>
                    <th className="px-6 py-4">Ngôn ngữ gốc</th>
                    <th className="px-6 py-4">Tọa độ GPS (Lat / Lng)</th>
                    <th className="px-6 py-4">Bán kính</th>
                    <th className="px-6 py-4">Revision</th>
                    <th className="px-6 py-4">Vector Status</th>
                    <th className="px-6 py-4 text-right">Thao tác</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800 text-slate-300">
                  {filteredPois.map((poi) => (
                    <tr key={poi.poi_id} className="hover:bg-slate-800/30 transition-colors">
                      <td className="px-6 py-4 font-mono font-bold text-slate-400">#{poi.poi_id}</td>
                      <td className="px-6 py-4">
                        <div className="flex items-center space-x-3">
                          <img 
                            src={getMediaUrl(poi.thumbnail_url)} 
                            alt={poi.original_title}
                            onError={(e) => { (e.currentTarget as HTMLImageElement).src = DEFAULT_POI_IMAGE; }}
                            className="w-10 h-10 rounded-lg object-cover bg-slate-800 shrink-0 border border-slate-700" 
                          />
                          <div>
                            <div className="font-semibold text-white">{poi.original_title}</div>
                            {poi.thumbnail_url && (
                              <span className="text-[11px] text-amber-400/80">Có ảnh thu nhỏ</span>
                            )}
                          </div>
                        </div>
                      </td>
                      <td className="px-6 py-4">
                        <span className="px-2 py-0.5 rounded bg-slate-800 text-xs font-mono uppercase text-slate-300">
                          {poi.original_language_code}
                        </span>
                      </td>
                      <td className="px-6 py-4 font-mono text-xs text-slate-400">
                        {poi.latitude != null && poi.longitude != null
                          ? `${Number(poi.latitude).toFixed(4)}, ${Number(poi.longitude).toFixed(4)}`
                          : 'Chưa có tọa độ'}
                      </td>
                      <td className="px-6 py-4 text-slate-300 font-medium">
                        <span className="inline-flex items-center space-x-1 px-2.5 py-0.5 rounded-md bg-amber-500/10 text-amber-400 border border-amber-500/20 text-xs font-semibold">
                          <Radio className="w-3 h-3" />
                          <span>{poi.trigger_radius != null ? `${poi.trigger_radius} m` : '30 m'}</span>
                        </span>
                      </td>
                      <td className="px-6 py-4 font-mono font-bold text-amber-400">
                        v{poi.revision ?? 1}
                      </td>
                      <td className="px-6 py-4">
                        <span className={`inline-flex items-center space-x-1 px-2.5 py-1 rounded-full text-xs font-semibold ${
                          poi.vector_status === 'Synced' 
                            ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                            : poi.vector_status === 'Failed'
                            ? 'bg-red-500/10 text-red-400 border border-red-500/20'
                            : 'bg-amber-500/10 text-amber-400 border border-amber-500/20'
                        }`}>
                          {poi.vector_status === 'Synced' && <CheckCircle className="w-3.5 h-3.5" />}
                          {poi.vector_status === 'Pending' && <Clock className="w-3.5 h-3.5" />}
                          {poi.vector_status === 'Failed' && <AlertCircle className="w-3.5 h-3.5" />}
                          <span>{poi.vector_status || 'Pending'}</span>
                        </span>
                      </td>
                      <td className="px-6 py-4 text-right space-x-2">
                        <button
                          onClick={() => handleOpenEditModal(poi)}
                          className="p-2 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded-lg transition-colors cursor-pointer"
                          title="Chỉnh sửa POI"
                        >
                          <Edit2 className="w-4 h-4" />
                        </button>
                        <button
                          onClick={() => handleDelete(poi.poi_id)}
                          className="p-2 bg-slate-800 hover:bg-red-900/40 text-red-400 rounded-lg transition-colors cursor-pointer"
                          title="Xóa POI"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {/* MODAL TẠO / CHỈNH SỬA POI KÈM KHUNG BẢN ĐỒ CHỌN VỊ TRÍ & BÁN KÍNH */}
      {isModalOpen && (
        <div className="fixed inset-0 bg-black/75 backdrop-blur-sm z-50 flex items-center justify-center p-4 overflow-y-auto">
          <div className="bg-slate-900 border border-slate-700 rounded-2xl max-w-5xl w-full p-6 md:p-8 shadow-2xl relative my-8">
            <button
              onClick={() => setIsModalOpen(false)}
              className="absolute top-5 right-5 text-slate-400 hover:text-white p-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 transition-colors cursor-pointer"
            >
              <X className="w-5 h-5" />
            </button>

            <div className="flex items-center space-x-3 mb-6">
              <div className="p-2.5 rounded-xl bg-amber-500/10 border border-amber-500/20 text-amber-500">
                <MapPin className="w-6 h-6" />
              </div>
              <div>
                <h2 className="text-xl md:text-2xl font-bold text-white">
                  {editingPoi ? `Chỉnh sửa điểm POI #${editingPoi.poi_id}` : 'Thêm điểm tham quan mới'}
                </h2>
                <p className="text-xs text-slate-400">
                  Điền thông tin và nhấp chuột trên bản đồ để chọn tọa độ chính xác kèm bán kính phát âm thanh.
                </p>
              </div>
            </div>

            <form onSubmit={handleSubmit} className="space-y-6">
              <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
                {/* CỘT TRÁI: THÔNG TIN CƠ BẢN VÀ THUYẾT MINH (5 COLS) */}
                <div className="lg:col-span-5 space-y-4">
                  <div>
                    <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1.5">
                      Tên điểm tham quan *
                    </label>
                    <input
                      type="text"
                      required
                      value={formData.original_title}
                      onChange={(e) => setFormData({ ...formData, original_title: e.target.value })}
                      placeholder="Ví dụ: Tượng Phật Bà Quan Âm"
                      className="w-full px-4 py-2.5 bg-slate-800 border border-slate-700 rounded-xl text-white text-sm focus:outline-none focus:ring-2 focus:ring-amber-500/50"
                    />
                  </div>

                  <div>
                    <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1.5">
                      Ngôn ngữ gốc *
                    </label>
                    <select
                      value={formData.original_language_code}
                      onChange={(e) => setFormData({ ...formData, original_language_code: e.target.value })}
                      className="w-full px-4 py-2.5 bg-slate-800 border border-slate-700 rounded-xl text-white text-sm focus:outline-none focus:ring-2 focus:ring-amber-500/50"
                    >
                      {languages.map((l) => (
                        <option key={l.language_code} value={l.language_code}>
                          {l.language_code.toUpperCase()} - {l.native_name}
                        </option>
                      ))}
                    </select>
                  </div>

                  <div>
                    <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1.5">
                      Bài thuyết minh gốc *
                    </label>
                    <textarea
                      required
                      rows={5}
                      value={formData.original_description}
                      onChange={(e) => setFormData({ ...formData, original_description: e.target.value })}
                      placeholder="Nhập nội dung bài thuyết minh lịch sử, văn hóa của điểm di tích..."
                      className="w-full px-4 py-2.5 bg-slate-800 border border-slate-700 rounded-xl text-white text-sm focus:outline-none focus:ring-2 focus:ring-amber-500/50 leading-relaxed"
                    />
                  </div>

                  <div>
                    <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1.5">
                      Ảnh Thumbnail
                    </label>
                    <div className="flex items-center space-x-3">
                      <input
                        type="file"
                        accept="image/*"
                        onChange={handleFileUpload}
                        className="block w-full text-xs text-slate-400 file:mr-4 file:py-2 file:px-4 file:rounded-xl file:border-0 file:text-xs file:font-semibold file:bg-slate-800 file:text-amber-400 hover:file:bg-slate-700 cursor-pointer"
                      />
                      {isUploadingThumb && <Loader2 className="w-5 h-5 animate-spin text-amber-500" />}
                    </div>
                    {formData.thumbnail_url && (
                      <div className="mt-2.5 flex items-center space-x-3 bg-slate-800/60 p-2 rounded-xl border border-slate-700/60">
                        <img 
                          src={getMediaUrl(formData.thumbnail_url)} 
                          alt="Thumbnail Preview"
                          onError={(e) => { (e.currentTarget as HTMLImageElement).src = DEFAULT_POI_IMAGE; }}
                          className="w-14 h-14 rounded-lg object-cover bg-slate-800 border border-slate-700 shrink-0"
                        />
                        <div className="min-w-0 flex-1">
                          <p className="text-xs text-emerald-400 truncate">Ảnh đã tải lên</p>
                          <button
                            type="button"
                            onClick={() => setFormData((prev) => ({ ...prev, thumbnail_url: '' }))}
                            className="text-[11px] text-red-400 hover:text-red-300 mt-0.5 underline cursor-pointer"
                          >
                            Xóa ảnh này
                          </button>
                        </div>
                      </div>
                    )}
                  </div>
                </div>

                {/* CỘT PHẢI: KHUNG BẢN ĐỒ CHỌN TỌA ĐỘ VÀ BÁN KÍNH GPS (7 COLS) */}
                <div className="lg:col-span-7 space-y-4 flex flex-col">
                  <div className="flex items-center justify-between">
                    <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider">
                      Khung bản đồ chọn vị trí & Bán kính (GPS)
                    </label>
                    <button
                      type="button"
                      onClick={() => setFormData((prev) => ({ ...prev, latitude: 16.1001, longitude: 108.2775 }))}
                      className="text-xs text-amber-400 hover:text-amber-300 flex items-center space-x-1 cursor-pointer"
                    >
                      <Crosshair className="w-3.5 h-3.5" />
                      <span>Về Chùa Linh Ứng</span>
                    </button>
                  </div>

                  {/* Bản đồ Leaflet tương tác */}
                  <div className="h-[280px] md:h-[320px] w-full rounded-xl overflow-hidden border border-slate-700 relative shadow-inner">
                    <MapContainer
                      center={[validLat, validLng]}
                      zoom={17}
                      scrollWheelZoom={true}
                      className="w-full h-full"
                    >
                      <TileLayer
                        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
                        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                      />
                      <MapAutoResize />
                      <MapRecenter center={[validLat, validLng]} />
                      <MapLocationPicker
                        onLocationSelect={(lat, lng) => {
                          setFormData((prev) => ({ ...prev, latitude: lat, longitude: lng }));
                        }}
                      />

                      {/* Các POI khác để đối chiếu vị trí (màu xanh/mờ, POI gần nhất màu vàng) */}
                      {pois
                        .filter((p) => p.poi_id !== editingPoi?.poi_id)
                        .map((otherPoi) => {
                          const isNearest = nearestPoi?.poi?.poi_id === otherPoi.poi_id;
                          return (
                            <React.Fragment key={otherPoi.poi_id}>
                              <Circle
                                center={[otherPoi.latitude ?? 16.1001, otherPoi.longitude ?? 108.2775]}
                                radius={otherPoi.trigger_radius ?? 30}
                                pathOptions={{
                                  color: isNearest ? '#eab308' : '#64748b',
                                  fillColor: isNearest ? '#eab308' : '#64748b',
                                  fillOpacity: isNearest ? 0.28 : 0.1,
                                  weight: isNearest ? 2.5 : 1,
                                  dashArray: isNearest ? undefined : '3, 4',
                                }}
                              />
                              <Marker
                                position={[otherPoi.latitude ?? 16.1001, otherPoi.longitude ?? 108.2775]}
                                icon={createPoiBadgeIcon(otherPoi.poi_id, 'other', false, isNearest)}
                              >
                                <Popup>
                                  <div className="text-xs p-1">
                                    <div className="font-bold text-white flex items-center gap-1.5">
                                      {isNearest && <span className="text-amber-400">★ POI gần nhất:</span>}
                                      <span>#{otherPoi.poi_id} - {otherPoi.original_title}</span>
                                    </div>
                                    <div className="text-slate-400 text-[10px]">
                                      Bán kính: {otherPoi.trigger_radius ?? 30}m
                                      {isNearest && nearestPoi && (
                                        <span className="text-amber-300 font-semibold block mt-0.5">
                                          Khoảng cách: ~{nearestPoi.distance}m
                                        </span>
                                      )}
                                    </div>
                                  </div>
                                </Popup>
                              </Marker>
                            </React.Fragment>
                          );
                        })}

                      {/* Vòng tròn bán kính của POI đang chỉnh sửa */}
                      <Circle
                        center={[validLat, validLng]}
                        radius={validRadius}
                        pathOptions={{
                          color: '#f59e0b',
                          fillColor: '#f59e0b',
                          fillOpacity: 0.28,
                          weight: 2.5,
                          dashArray: '5, 5',
                        }}
                      />

                      {/* Marker của POI đang chỉnh sửa (Có thể kéo thả drag & drop) */}
                      <Marker
                        position={[validLat, validLng]}
                        draggable={true}
                        eventHandlers={markerDragHandlers}
                        ref={markerRef}
                        icon={activePoiIcon}
                      >
                        <Popup>
                          <div className="p-1 text-xs space-y-1">
                            <div className="font-bold text-amber-400">Điểm đang chọn</div>
                            <div className="text-slate-300 font-mono text-[11px]">
                              Lat: {validLat.toFixed(6)}<br />
                              Lng: {validLng.toFixed(6)}
                            </div>
                            <div className="text-amber-300 font-semibold text-[11px]">
                              Bán kính: {validRadius}m
                            </div>
                          </div>
                        </Popup>
                      </Marker>
                    </MapContainer>

                    {/* Hint overlay trên bản đồ */}
                    <div className="absolute bottom-2 left-2 right-2 pointer-events-none z-[1000] flex flex-wrap justify-between items-center gap-1.5">
                      <div className="bg-slate-900/90 backdrop-blur-md px-2.5 py-1 rounded-lg border border-slate-700/80 text-[11px] text-amber-300 shadow flex items-center gap-1.5">
                        <span>💡 Click bản đồ hoặc kéo marker 📍</span>
                        {nearestPoi && (
                          <span className="text-yellow-400 font-semibold border-l border-slate-700 pl-1.5">
                            🟡 Gần nhất: #{nearestPoi.poi.poi_id} (~{nearestPoi.distance}m)
                          </span>
                        )}
                      </div>
                      <div className="bg-slate-900/90 backdrop-blur-md px-2.5 py-1 rounded-lg border border-slate-700/80 text-[11px] font-mono text-slate-300 shadow">
                        R = {validRadius}m
                      </div>
                    </div>
                  </div>

                  {/* Ô nhập số tọa độ và bán kính */}
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                    <div>
                      <label className="block text-[11px] font-semibold text-slate-400 uppercase tracking-wider mb-1">
                        Vĩ độ (Latitude)
                      </label>
                      <input
                        type="number"
                        step="0.000001"
                        required
                        value={formData.latitude}
                        onChange={(e) => setFormData({ ...formData, latitude: parseFloat(e.target.value) || 0 })}
                        className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-xl text-white text-xs font-mono focus:outline-none focus:ring-2 focus:ring-amber-500/50"
                      />
                    </div>

                    <div>
                      <label className="block text-[11px] font-semibold text-slate-400 uppercase tracking-wider mb-1">
                        Kinh độ (Longitude)
                      </label>
                      <input
                        type="number"
                        step="0.000001"
                        required
                        value={formData.longitude}
                        onChange={(e) => setFormData({ ...formData, longitude: parseFloat(e.target.value) || 0 })}
                        className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-xl text-white text-xs font-mono focus:outline-none focus:ring-2 focus:ring-amber-500/50"
                      />
                    </div>

                    <div>
                      <label className="block text-[11px] font-semibold text-slate-400 uppercase tracking-wider mb-1">
                        Bán kính GPS (m)
                      </label>
                      <input
                        type="number"
                        min="5"
                        max="200"
                        required
                        value={formData.trigger_radius}
                        onChange={(e) => setFormData({ ...formData, trigger_radius: parseFloat(e.target.value) || 30 })}
                        className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-xl text-white text-xs font-mono focus:outline-none focus:ring-2 focus:ring-amber-500/50"
                      />
                    </div>
                  </div>

                  {/* Nút chọn nhanh bán kính thường dùng */}
                  <div className="flex items-center space-x-2 text-xs">
                    <span className="text-slate-400 text-[11px]">Bán kính mẫu:</span>
                    {[15, 25, 30, 45, 60].map((r) => (
                      <button
                        key={r}
                        type="button"
                        onClick={() => setFormData((prev) => ({ ...prev, trigger_radius: r }))}
                        className={`px-2.5 py-1 rounded-lg text-xs font-semibold border transition-colors cursor-pointer ${
                          formData.trigger_radius === r
                            ? 'bg-amber-500 text-slate-950 border-amber-500'
                            : 'bg-slate-800 text-slate-300 border-slate-700 hover:border-slate-600'
                        }`}
                      >
                        {r}m
                      </button>
                    ))}
                  </div>
                </div>
              </div>

              {/* Nút Hủy và Lưu */}
              <div className="flex items-center justify-end space-x-3 pt-4 border-t border-slate-800">
                <button
                  type="button"
                  onClick={() => setIsModalOpen(false)}
                  className="px-5 py-2.5 rounded-xl text-sm font-semibold text-slate-400 hover:bg-slate-800 transition-colors cursor-pointer"
                >
                  Hủy
                </button>
                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="px-6 py-2.5 bg-amber-500 hover:bg-amber-600 disabled:bg-amber-500/50 text-slate-950 font-bold rounded-xl shadow-lg shadow-amber-500/20 text-sm flex items-center space-x-2 cursor-pointer transition-all"
                >
                  {isSubmitting && <Loader2 className="w-4 h-4 animate-spin" />}
                  <span>{editingPoi ? 'Cập nhật POI' : 'Tạo mới POI'}</span>
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
