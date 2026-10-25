import React, { useState, useEffect, useRef } from 'react';
import L from 'leaflet';
import {
  adminLogin,
  adminCreateCashCode,
  adminCreatePOI,
  adminUpdatePOI,
  adminDeletePOI,
  adminGetMonitoring,
  adminGetPOIs,
  fetchAllPOIs,
  getAdminToken,
  setAdminToken,
  clearAdminToken,
  parseJwt,
  getActiveVisitorsCount
} from '../services/api';
import { POI } from '../types';
import { LINH_UNG_CENTER } from '../utils/geo';
import {
  ShieldCheck,
  PlusCircle,
  Banknote,
  Activity,
  Layers,
  LogOut,
  RefreshCw,
  Edit2,
  Trash2,
  CheckCircle,
  AlertTriangle,
  Clock,
  MapPin,
  X,
  Users,
  ArrowLeft
} from 'lucide-react';

interface AdminDashboardProps {
  onBack?: () => void;
}

export const AdminDashboard: React.FC<AdminDashboardProps> = ({ onBack }) => {
  const [isLoggedIn, setIsLoggedIn] = useState<boolean>(false);
  const [username, setUsername] = useState('admin');
  const [password, setPassword] = useState('admin123');
  const [loginError, setLoginError] = useState<string | null>(null);

  // Số lượng khách tham quan trực tuyến thời gian thực
  const [activeVisitors, setActiveVisitors] = useState<number>(0);

  // Dữ liệu quản trị
  const [pois, setPois] = useState<POI[]>([]);
  const [activeTab, setActiveTab] = useState<'pois' | 'monitoring'>('pois');
  const [loading, setLoading] = useState(false);
  const [msg, setMsg] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  // Modal tạo mã tiền mặt
  const [cashCodeModal, setCashCodeModal] = useState<string | null>(null);

  // Form Thêm / Sửa POI
  const [isFormOpen, setIsFormOpen] = useState<boolean>(false);
  const [editingPoi, setEditingPoi] = useState<POI | null>(null);
  const [formData, setFormData] = useState({
    name: '',
    latitude: 16.0998,
    longitude: 108.2773,
    trigger_radius: 30,
    thumbnail_url: '',
    original_description: ''
  });

  // Monitoring data
  const [monitoringData, setMonitoringData] = useState<{
    dlq_count: number;
    dlq_messages: any[];
    recent_errors: any[];
  } | null>(null);

  // Mini map cho việc click chọn tọa độ
  const miniMapRef = useRef<HTMLDivElement>(null);
  const miniMapInstance = useRef<L.Map | null>(null);
  const pickMarkerRef = useRef<L.Marker | null>(null);

  // Kiểm tra token admin khi load
  useEffect(() => {
    const token = getAdminToken();
    if (token) {
      const payload = parseJwt(token);
      if (payload && payload.role === 'admin') {
        setIsLoggedIn(true);
        loadPois();
        loadMonitoring();
        return;
      }
    }
    setIsLoggedIn(false);
  }, []);

  // Polling tiến độ pipeline và Lượng khách tham quan mỗi 2 giây theo thời gian thực
  useEffect(() => {
    if (!isLoggedIn) return;

    const poll = () => {
      adminGetPOIs()
        .then((data) => {
          if (Array.isArray(data)) {
            setPois(data);
          }
        })
        .catch(() => {});

      getActiveVisitorsCount()
        .then((data) => {
          if (typeof data.active_visitors === 'number') {
            setActiveVisitors(data.active_visitors);
          }
        })
        .catch(() => {});
    };

    poll();
    const interval = setInterval(poll, 2000);

    return () => clearInterval(interval);
  }, [isLoggedIn]);

  const loadPois = async () => {
    setLoading(true);
    try {
      const data = await adminGetPOIs();
      setPois(Array.isArray(data) ? data : []);
    } catch (err: any) {
      setMsg({ type: 'error', text: err.message });
    } finally {
      setLoading(false);
    }
  };

  const loadMonitoring = async () => {
    try {
      const data = await adminGetMonitoring();
      setMonitoringData(data);
    } catch (err) {}
  };

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoginError(null);
    try {
      const res = await adminLogin(username, password);
      if (res.role !== 'admin') {
        throw new Error('Tài khoản không có quyền Admin');
      }
      setAdminToken(res.access_token);
      setIsLoggedIn(true);
      loadPois();
      loadMonitoring();
    } catch (err: any) {
      setLoginError(err.message || 'Đăng nhập thất bại');
    }
  };

  const handleLogout = () => {
    clearAdminToken();
    setIsLoggedIn(false);
  };

  // Tạo mã tiền mặt (shorted_code)
  const handleGenerateCashCode = async () => {
    try {
      const res = await adminCreateCashCode();
      setCashCodeModal(res.shorted_code);
      setMsg({ type: 'success', text: `Đã sinh mã tiền mặt 10 ký tự: ${res.shorted_code}` });
    } catch (err: any) {
      setMsg({ type: 'error', text: err.message });
    }
  };

  // Khởi tạo mini-map chọn tọa độ
  const openPoiForm = (poi?: POI) => {
    setIsFormOpen(true);
    if (poi) {
      setEditingPoi(poi);
      setFormData({
        name: poi.name,
        latitude: poi.latitude,
        longitude: poi.longitude,
        trigger_radius: poi.trigger_radius,
        thumbnail_url: poi.thumbnail_url || '',
        original_description: poi.original_description
      });
    } else {
      setEditingPoi(null);
      setFormData({
        name: '',
        latitude: 16.0998,
        longitude: 108.2773,
        trigger_radius: 30,
        thumbnail_url: '',
        original_description: ''
      });
    }

    setTimeout(() => {
      initMiniMap(poi ? [poi.latitude, poi.longitude] : [16.0998, 108.2773]);
    }, 150);
  };

  const closePoiForm = () => {
    setIsFormOpen(false);
    setEditingPoi(null);
    setFormData({
      name: '',
      latitude: 16.0998,
      longitude: 108.2773,
      trigger_radius: 30,
      thumbnail_url: '',
      original_description: ''
    });
    if (miniMapInstance.current) {
      miniMapInstance.current.remove();
      miniMapInstance.current = null;
    }
  };

  const initMiniMap = (center: [number, number]) => {
    if (!miniMapRef.current) return;
    if (miniMapInstance.current) {
      miniMapInstance.current.remove();
      miniMapInstance.current = null;
    }

    const map = L.map(miniMapRef.current).setView(center, 17);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png').addTo(map);

    const marker = L.marker(center, { draggable: true }).addTo(map);
    pickMarkerRef.current = marker;

    marker.on('dragend', () => {
      const pos = marker.getLatLng();
      setFormData((prev) => ({ ...prev, latitude: Number(pos.lat.toFixed(5)), longitude: Number(pos.lng.toFixed(5)) }));
    });

    map.on('click', (e) => {
      marker.setLatLng(e.latlng);
      setFormData((prev) => ({ ...prev, latitude: Number(e.latlng.lat.toFixed(5)), longitude: Number(e.latlng.lng.toFixed(5)) }));
    });

    miniMapInstance.current = map;
  };

  const handleSavePOI = async (e: React.FormEvent) => {
    e.preventDefault();
    setMsg(null);
    try {
      if (editingPoi) {
        // Cập nhật POI
        const res = await adminUpdatePOI(editingPoi.poi_id, formData);
        setMsg({
          type: 'success',
          text: res.message || 'Cập nhật POI thành công'
        });
      } else {
        // Thêm mới POI
        const res = await adminCreatePOI(formData);
        setMsg({
          type: 'success',
          text: `Đã thêm ${res.name}. Pipeline dịch 15 ngôn ngữ đang chạy ngầm!`
        });
      }
      closePoiForm();
      loadPois();
    } catch (err: any) {
      setMsg({ type: 'error', text: err.message });
    }
  };

  const handleDeletePOI = async (poiId: string) => {
    if (!confirm('Bạn có chắc chắn muốn xóa điểm tham quan này?')) return;
    try {
      await adminDeletePOI(poiId);
      setMsg({ type: 'success', text: 'Đã xóa POI thành công' });
      loadPois();
    } catch (err: any) {
      setMsg({ type: 'error', text: err.message });
    }
  };

  // Màn hình đăng nhập nếu chưa login
  if (!isLoggedIn) {
    return (
      <div className="min-h-screen bg-slate-100 flex items-center justify-center p-4">
        <div className="bg-white rounded-3xl shadow-2xl p-8 max-w-sm w-full border border-slate-200">
          <div className="w-16 h-16 bg-amber-100 text-amber-700 rounded-2xl flex items-center justify-center mx-auto mb-4">
            <ShieldCheck size={36} />
          </div>
          <h2 className="text-xl font-bold text-center text-slate-800">Quản Trị Viên</h2>
          <p className="text-xs text-center text-slate-500 mb-6">Hệ thống Thuyết minh Chùa Linh Ứng</p>

          <form onSubmit={handleLogin} className="space-y-4">
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">Tài khoản</label>
              <input
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                className="w-full px-4 py-2.5 bg-slate-50 border rounded-xl text-sm"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">Mật khẩu</label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full px-4 py-2.5 bg-slate-50 border rounded-xl text-sm"
              />
            </div>

            {loginError && (
              <p className="text-xs text-red-600 bg-red-50 p-2.5 rounded-xl">{loginError}</p>
            )}

            <button
              type="submit"
              className="w-full py-3 bg-amber-600 hover:bg-amber-700 text-white font-semibold rounded-xl text-sm transition"
            >
              Đăng Nhập Quản Trị
            </button>
          </form>

          {onBack && (
            <button
              type="button"
              onClick={onBack}
              className="w-full mt-3 py-2 text-xs text-slate-500 hover:text-slate-800 transition flex items-center justify-center space-x-1.5 border border-slate-200 rounded-xl hover:bg-slate-50"
            >
              <ArrowLeft size={14} />
              <span>Quay lại Bản đồ Du khách</span>
            </button>
          )}

          <div className="text-[11px] text-slate-400 text-center mt-4">
            Seed mặc định: <code>admin</code> / <code>admin123</code>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-50">
      {/* Navbar Admin */}
      <nav className="bg-slate-900 text-white px-6 py-3.5 flex items-center justify-between shadow-md">
        <div className="flex items-center space-x-3">
          {onBack && (
            <button
              onClick={onBack}
              className="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded-xl text-xs flex items-center space-x-1.5 transition border border-slate-700 active:scale-95 mr-1"
              title="Quay lại Bản đồ Du khách"
            >
              <ArrowLeft size={14} />
              <span className="hidden sm:inline">Về Bản Đồ</span>
            </button>
          )}
          <span className="text-xl">⛩️</span>
          <div>
            <h1 className="text-sm font-bold tracking-wide">ADMIN DASHBOARD</h1>
            <p className="text-[10px] text-amber-400">ỨNG DỤNG THUYẾT MINH CHÙA LINH ỨNG</p>
          </div>
        </div>

        <div className="flex items-center space-x-3">
          <button
            onClick={handleGenerateCashCode}
            className="px-3.5 py-1.5 bg-emerald-600 hover:bg-emerald-700 active:scale-95 text-white rounded-xl text-xs font-semibold flex items-center space-x-1.5 transition shadow"
          >
            <Banknote size={15} />
            <span>Tạo Mã Tiền Mặt</span>
          </button>

          <button
            onClick={() => openPoiForm()}
            className="px-3.5 py-1.5 bg-amber-600 hover:bg-amber-700 active:scale-95 text-white rounded-xl text-xs font-semibold flex items-center space-x-1.5 transition shadow"
          >
            <PlusCircle size={15} />
            <span>Thêm POI Mới</span>
          </button>

          <button
            onClick={handleLogout}
            className="p-2 text-slate-400 hover:text-white rounded-xl hover:bg-slate-800 transition"
            title="Đăng xuất"
          >
            <LogOut size={16} />
          </button>
        </div>
      </nav>

      {/* Thông báo Alert */}
      {msg && (
        <div className={`p-3 text-xs flex items-center justify-between ${msg.type === 'success' ? 'bg-emerald-100 text-emerald-800' : 'bg-red-100 text-red-800'}`}>
          <span>{msg.text}</span>
          <button onClick={() => setMsg(null)} className="font-bold">✕</button>
        </div>
      )}

      {/* Main Content */}
      <div className="max-w-7xl mx-auto p-4 sm:p-6 space-y-6">
        {/* Thẻ Thống Kê Lượng Khách Tham Quan (User) Đang Dùng Theo Thời Gian Thực */}
        <div className="bg-gradient-to-r from-emerald-50 via-teal-50 to-emerald-50 border border-emerald-200 rounded-2xl p-4 flex items-center justify-between shadow-sm">
          <div className="flex items-center space-x-3.5">
            <div className="relative flex items-center justify-center w-12 h-12 bg-emerald-100 text-emerald-700 rounded-2xl shadow-inner">
              <Users size={24} />
              <span className="absolute -top-1 -right-1 flex h-3.5 w-3.5">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                <span className="relative inline-flex rounded-full h-3.5 w-3.5 bg-emerald-500"></span>
              </span>
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <span className="text-xs font-bold text-slate-700 uppercase tracking-wider">
                  Lượng khách tham quan (User) đang dùng
                </span>
                <span className="inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-bold bg-emerald-100 text-emerald-800 border border-emerald-300">
                  Thời gian thực (Live)
                </span>
              </div>
              <p className="text-[11px] text-slate-500 mt-0.5">
                Tự động cập nhật mỗi 2 giây dựa trên thiết bị du khách đang trực tuyến
              </p>
            </div>
          </div>

          <div className="text-right">
            <div className="flex items-baseline space-x-1.5 justify-end">
              <span className="text-3xl font-black text-emerald-600 font-mono tracking-tight">
                {activeVisitors}
              </span>
              <span className="text-xs font-bold text-slate-500">người</span>
            </div>
            <p className="text-[10px] text-emerald-600 font-medium flex items-center justify-end space-x-1">
              <span className="w-1.5 h-1.5 bg-emerald-500 rounded-full animate-ping"></span>
              <span>Đang kết nối</span>
            </p>
          </div>
        </div>

        {/* Main Tabs */}
        <div className="flex space-x-2 border-b border-slate-200 pb-2">
          <button
            onClick={() => setActiveTab('pois')}
            className={`px-4 py-2 rounded-xl text-xs font-bold transition flex items-center space-x-2 ${
              activeTab === 'pois' ? 'bg-amber-600 text-white' : 'bg-white text-slate-600 hover:bg-slate-100'
            }`}
          >
            <Layers size={16} />
            <span>Danh Sách Điểm Tham Quan (POIs)</span>
          </button>
          <button
            onClick={() => {
              setActiveTab('monitoring');
              loadMonitoring();
            }}
            className={`px-4 py-2 rounded-xl text-xs font-bold transition flex items-center space-x-2 ${
              activeTab === 'monitoring' ? 'bg-amber-600 text-white' : 'bg-white text-slate-600 hover:bg-slate-100'
            }`}
          >
            <Activity size={16} />
            <span>Giám Sát Pipeline & Dead-Letter Queue (DLQ)</span>
          </button>
        </div>

        {activeTab === 'pois' && (
          <div className="bg-white rounded-2xl shadow-sm border border-slate-200 overflow-hidden">
            <div className="p-4 border-b border-slate-100 flex items-center justify-between">
              <div>
                <h3 className="text-sm font-bold text-slate-800">Các điểm tham quan hiện có ({pois.length})</h3>
                <p className="text-[11px] text-slate-500">Cột tiến độ cập nhật bất đồng bộ tự động mỗi 2 giây</p>
              </div>
              <button
                onClick={loadPois}
                className="p-2 hover:bg-slate-100 rounded-xl text-slate-600 transition"
                title="Làm mới"
              >
                <RefreshCw size={16} className={loading ? 'animate-spin' : ''} />
              </button>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead className="bg-slate-50 text-slate-600 uppercase font-semibold text-[10px] tracking-wider border-b">
                  <tr>
                    <th className="p-3">POI</th>
                    <th className="p-3">Tọa độ GPS</th>
                    <th className="p-3">Bán kính</th>
                    <th className="p-3">Tiến độ Pipeline (Dịch 15 Ngôn Ngữ)</th>
                    <th className="p-3 text-right">Thao tác</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {pois.length === 0 ? (
                    <tr>
                      <td colSpan={5} className="p-8 text-center text-slate-400">
                        {loading ? 'Đang tải danh sách điểm tham quan...' : 'Chưa có điểm tham quan nào trong hệ thống.'}
                      </td>
                    </tr>
                  ) : (
                    pois.map((poi) => {
                      const isDone = poi.pipeline_status?.includes('done') || poi.pipeline_status?.includes('Hoàn tất');
                      const isProcessing = poi.pipeline_status?.includes('Đang xử lý');
                      const isError = poi.pipeline_status?.includes('Lỗi');

                      return (
                        <tr key={poi.poi_id} className="hover:bg-slate-50 transition">
                          <td className="p-3 flex items-center space-x-3">
                            {poi.thumbnail_url ? (
                              <img src={poi.thumbnail_url} className="w-10 h-10 rounded-lg object-cover" />
                            ) : (
                              <div className="w-10 h-10 bg-amber-100 rounded-lg flex items-center justify-center text-amber-700 font-bold">
                                ⛩️
                              </div>
                            )}
                            <div>
                              <p className="font-semibold text-slate-800 text-xs">{poi.name}</p>
                              <p className="text-[10px] text-slate-400 font-mono">{poi.poi_id}</p>
                            </div>
                          </td>
                          <td className="p-3 font-mono text-slate-600">
                            {Number(poi.latitude).toFixed(5)}, {Number(poi.longitude).toFixed(5)}
                          </td>
                          <td className="p-3 font-semibold text-slate-700">
                            {poi.trigger_radius}m
                          </td>
                          <td className="p-3">
                            <div className="flex items-center space-x-2">
                              {isDone ? (
                                <span className="inline-flex items-center space-x-1 px-2.5 py-1 bg-emerald-100 text-emerald-800 rounded-full font-bold text-[10px]">
                                  <CheckCircle size={12} />
                                  <span>{poi.pipeline_status === 'done' ? 'Hoàn tất (15/15)' : poi.pipeline_status}</span>
                                </span>
                              ) : isProcessing ? (
                                <span className="inline-flex items-center space-x-1 px-2.5 py-1 bg-amber-100 text-amber-800 rounded-full font-bold text-[10px] animate-pulse">
                                  <Clock size={12} />
                                  <span>{poi.pipeline_status}</span>
                                </span>
                              ) : (
                                <span className="inline-flex items-center space-x-1 px-2.5 py-1 bg-red-100 text-red-800 rounded-full font-bold text-[10px]">
                                  <AlertTriangle size={12} />
                                  <span>{poi.pipeline_status}</span>
                                </span>
                              )}
                            </div>
                          </td>
                          <td className="p-3 text-right space-x-2">
                            <button
                              onClick={() => openPoiForm(poi)}
                              className="p-1.5 text-blue-600 hover:bg-blue-50 rounded-lg transition"
                              title="Sửa POI"
                            >
                              <Edit2 size={15} />
                            </button>
                            <button
                              onClick={() => handleDeletePOI(poi.poi_id)}
                              className="p-1.5 text-red-600 hover:bg-red-50 rounded-lg transition"
                              title="Xóa POI"
                            >
                              <Trash2 size={15} />
                            </button>
                          </td>
                        </tr>
                      );
                    })
                  )}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* Tab Giám sát (Monitoring Dashboard) */}
        {activeTab === 'monitoring' && (
          <div className="space-y-4">
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm">
                <span className="text-[11px] font-bold text-slate-400 uppercase">Dead-Letter Queue (DLQ)</span>
                <p className="text-3xl font-extrabold text-red-600 mt-1">
                  {monitoringData?.dlq_count || 0}
                </p>
                <p className="text-[11px] text-slate-500 mt-1">Số tin nhắn lỗi sau 3 lần retry</p>
              </div>

              <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm">
                <span className="text-[11px] font-bold text-slate-400 uppercase">Trạng Thái Message Queue</span>
                <p className="text-xl font-bold text-emerald-600 mt-1 flex items-center space-x-1.5">
                  <span className="w-3 h-3 bg-emerald-500 rounded-full animate-ping"></span>
                  <span>Hoạt động bình thường</span>
                </p>
                <p className="text-[11px] text-slate-500 mt-1">Exchange: poi.exchange</p>
              </div>

              <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm">
                <span className="text-[11px] font-bold text-slate-400 uppercase">Ngôn ngữ hỗ trợ</span>
                <p className="text-3xl font-extrabold text-amber-600 mt-1">15</p>
                <p className="text-[11px] text-slate-500 mt-1">Dịch tự động ngầm không chặn Client</p>
              </div>
            </div>

            <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-4">
              <h4 className="text-xs font-bold text-slate-800 mb-2 uppercase">Lịch sử cảnh báo / Ghi log lỗi</h4>
              {(!monitoringData?.recent_errors || monitoringData.recent_errors.length === 0) ? (
                <p className="text-xs text-slate-400 italic">Không có lỗi nào được ghi nhận. Hệ thống đang vận hành hoàn hảo.</p>
              ) : (
                <div className="space-y-2 max-h-60 overflow-y-auto font-mono text-[11px]">
                  {monitoringData.recent_errors.map((err, i) => (
                    <div key={i} className="p-2.5 bg-red-50 text-red-700 rounded-xl border border-red-200">
                      <span className="text-slate-400">[{err.time}]</span> {err.error}
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        )}
      </div>

      {/* Modal Form Thêm/Sửa POI */}
      {isFormOpen && (
        <div className="fixed inset-0 z-[1000] bg-slate-900/50 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white rounded-3xl shadow-2xl max-w-xl w-full max-h-[90vh] overflow-y-auto p-6 border border-slate-100">
            <div className="flex items-center justify-between pb-3 mb-4 border-b">
              <h3 className="text-base font-bold text-slate-800">
                {editingPoi ? `Sửa Điểm Tham Quan: ${editingPoi.name}` : 'Thêm Điểm Tham Quan Mới'}
              </h3>
              <button
                onClick={closePoiForm}
                className="p-1 text-slate-400 hover:text-slate-600"
              >
                <X size={20} />
              </button>
            </div>

            <form onSubmit={handleSavePOI} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Tên Điểm Tham Quan</label>
                <input
                  type="text"
                  required
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  className="w-full px-3.5 py-2 bg-slate-50 border rounded-xl text-xs sm:text-sm"
                  placeholder="VD: Tháp Chuông Đại Hồng Chung"
                />
              </div>

              <div className="grid grid-cols-3 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">Vĩ độ (Lat)</label>
                  <input
                    type="number"
                    step="any"
                    required
                    value={formData.latitude}
                    onChange={(e) => setFormData({ ...formData, latitude: parseFloat(e.target.value) })}
                    className="w-full px-3 py-2 bg-slate-50 border rounded-xl text-xs font-mono"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">Kinh độ (Lng)</label>
                  <input
                    type="number"
                    step="any"
                    required
                    value={formData.longitude}
                    onChange={(e) => setFormData({ ...formData, longitude: parseFloat(e.target.value) })}
                    className="w-full px-3 py-2 bg-slate-50 border rounded-xl text-xs font-mono"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">Bán kính (mét)</label>
                  <input
                    type="number"
                    required
                    value={formData.trigger_radius}
                    onChange={(e) => setFormData({ ...formData, trigger_radius: parseInt(e.target.value) })}
                    className="w-full px-3 py-2 bg-slate-50 border rounded-xl text-xs font-mono"
                  />
                </div>
              </div>

              {/* Bản đồ chọn tọa độ trực quan */}
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1 flex items-center justify-between">
                  <span>📍 Chọn vị trí trên bản đồ (Click hoặc Kéo marker)</span>
                  <span className="text-[10px] text-amber-600 font-mono">
                    {formData.latitude.toFixed(5)}, {formData.longitude.toFixed(5)}
                  </span>
                </label>
                <div ref={miniMapRef} className="w-full h-44 rounded-xl border border-slate-200 z-0" />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">URL Hình Ảnh Thumbnail</label>
                <input
                  type="url"
                  value={formData.thumbnail_url}
                  onChange={(e) => setFormData({ ...formData, thumbnail_url: e.target.value })}
                  className="w-full px-3.5 py-2 bg-slate-50 border rounded-xl text-xs"
                  placeholder="https://..."
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Mô tả gốc tiếng Việt (Hệ thống sẽ tự động dịch sang 15 ngôn ngữ)
                </label>
                <textarea
                  required
                  rows={4}
                  value={formData.original_description}
                  onChange={(e) => setFormData({ ...formData, original_description: e.target.value })}
                  className="w-full px-3.5 py-2 bg-slate-50 border rounded-xl text-xs leading-relaxed"
                  placeholder="Nhập nội dung thuyết minh chi tiết..."
                />
              </div>

              <div className="flex justify-end space-x-2 pt-3 border-t">
                <button
                  type="button"
                  onClick={closePoiForm}
                  className="px-4 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-xl text-xs font-medium"
                >
                  Hủy
                </button>
                <button
                  type="submit"
                  className="px-5 py-2 bg-amber-600 hover:bg-amber-700 text-white rounded-xl text-xs font-semibold shadow-sm"
                >
                  Lưu & Kích Hoạt Pipeline
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Modal Hiển thị Mã Tiền Mặt vừa tạo */}
      {cashCodeModal && (
        <div className="fixed inset-0 z-[1100] bg-slate-900/50 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white rounded-3xl shadow-2xl max-w-sm w-full p-6 text-center border border-slate-100 animate-in zoom-in-95">
            <div className="w-16 h-16 bg-emerald-100 text-emerald-600 rounded-full flex items-center justify-center mx-auto mb-3">
              <Banknote size={36} />
            </div>
            <h3 className="text-base font-bold text-slate-800">Mã Xác Thực Tiền Mặt</h3>
            <p className="text-xs text-slate-500 mt-1 mb-4">
              Cung cấp mã này cho du khách đã thanh toán tiền mặt tại cổng
            </p>

            <div className="p-3 bg-emerald-50 border border-emerald-200 rounded-2xl font-mono text-xl font-bold tracking-widest text-emerald-800 select-all mb-4">
              {cashCodeModal}
            </div>

            <p className="text-[11px] text-slate-400 mb-6">
              * Mã có thời hạn 1 giờ (TTL) và chỉ đổi lấy access_token được 1 lần duy nhất.
            </p>

            <button
              onClick={() => {
                navigator.clipboard.writeText(cashCodeModal);
                setCashCodeModal(null);
              }}
              className="w-full py-2.5 bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-bold rounded-xl transition"
            >
              Sao Chép & Đóng
            </button>
          </div>
        </div>
      )}
    </div>
  );
};
