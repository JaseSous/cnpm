import React, { useState, useEffect } from 'react';
import { poiClient } from '../api/client';
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
  X
} from 'lucide-react';

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

export const POIManager: React.FC = () => {
  const [pois, setPois] = useState<POIItem[]>([]);
  const [languages, setLanguages] = useState<Language[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState('');

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

  const handleOpenCreateModal = () => {
    setEditingPoi(null);
    setFormData({
      original_title: '',
      original_language_code: 'vi',
      original_description: '',
      latitude: 16.1001,
      longitude: 108.2775,
      trigger_radius: 30,
      thumbnail_url: '',
    });
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
    if (!window.confirm(`Bạn có chắc chắn muốn xóa điểm tham quan này (Mã: ${poiId}) không?`)) {
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
            CRUD điểm di tích, tọa độ GPS kích hoạt tự động và đồng bộ hóa qua Transactional Outbox.
          </p>
        </div>

        <button
          onClick={handleOpenCreateModal}
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

      {/* Search & Filter Bar */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-4 flex items-center space-x-4 shadow-xl">
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
        <div className="text-xs text-slate-400 font-medium whitespace-nowrap">
          Tổng số: <strong className="text-amber-400">{filteredPois.length}</strong> điểm
        </div>
      </div>

      {/* POI Table */}
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
                      <div className="font-semibold text-white">{poi.original_title}</div>
                      {poi.thumbnail_url && (
                        <span className="text-[11px] text-amber-400/80">Có ảnh thu nhỏ</span>
                      )}
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
                      {poi.trigger_radius != null ? `${poi.trigger_radius} m` : '30 m'}
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

      {/* Modal Tạo / Chỉnh sửa POI */}
      {isModalOpen && (
        <div className="fixed inset-0 bg-black/70 backdrop-blur-sm z-50 flex items-center justify-center p-4 overflow-y-auto">
          <div className="bg-slate-900 border border-slate-700 rounded-2xl max-w-2xl w-full p-6 shadow-2xl relative my-8">
            <button
              onClick={() => setIsModalOpen(false)}
              className="absolute top-5 right-5 text-slate-400 hover:text-white p-1 rounded-lg"
            >
              <X className="w-5 h-5" />
            </button>

            <h2 className="text-xl font-bold text-white mb-6">
              {editingPoi ? `Chỉnh sửa điểm POI #${editingPoi.poi_id}` : 'Thêm điểm tham quan mới'}
            </h2>

            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1.5">
                  Tên điểm tham quan
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
                  Ngôn ngữ gốc
                </label>
                <select
                  value={formData.original_language_code}
                  onChange={(e) => setFormData({ ...formData, original_language_code: e.target.value })}
                  className="w-full px-4 py-2.5 bg-slate-800 border border-slate-700 rounded-xl text-white text-sm focus:outline-none focus:ring-2 focus:ring-amber-500/50"
                >
                  {languages.map((l) => (
                    <option key={l.language_code} value={l.language_code}>
                      {l.language_code} - {l.native_name}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1.5">
                  Bài thuyết minh gốc
                </label>
                <textarea
                  required
                  rows={4}
                  value={formData.original_description}
                  onChange={(e) => setFormData({ ...formData, original_description: e.target.value })}
                  placeholder="Nhập nội dung bài thuyết minh lịch sử, văn hóa của điểm di tích..."
                  className="w-full px-4 py-2.5 bg-slate-800 border border-slate-700 rounded-xl text-white text-sm focus:outline-none focus:ring-2 focus:ring-amber-500/50"
                />
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div>
                  <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1.5">
                    Vĩ độ (Latitude)
                  </label>
                  <input
                    type="number"
                    step="0.0001"
                    required
                    value={formData.latitude}
                    onChange={(e) => setFormData({ ...formData, latitude: parseFloat(e.target.value) })}
                    className="w-full px-4 py-2.5 bg-slate-800 border border-slate-700 rounded-xl text-white text-sm font-mono"
                  />
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1.5">
                    Kinh độ (Longitude)
                  </label>
                  <input
                    type="number"
                    step="0.0001"
                    required
                    value={formData.longitude}
                    onChange={(e) => setFormData({ ...formData, longitude: parseFloat(e.target.value) })}
                    className="w-full px-4 py-2.5 bg-slate-800 border border-slate-700 rounded-xl text-white text-sm font-mono"
                  />
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1.5">
                    Bán kính GPS (m)
                  </label>
                  <input
                    type="number"
                    min="5"
                    max="200"
                    required
                    value={formData.trigger_radius}
                    onChange={(e) => setFormData({ ...formData, trigger_radius: parseFloat(e.target.value) })}
                    className="w-full px-4 py-2.5 bg-slate-800 border border-slate-700 rounded-xl text-white text-sm font-mono"
                  />
                </div>
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
                  <p className="text-xs text-emerald-400 mt-1 truncate">Ảnh: {formData.thumbnail_url}</p>
                )}
              </div>

              <div className="flex items-center justify-end space-x-3 pt-4 border-t border-slate-800">
                <button
                  type="button"
                  onClick={() => setIsModalOpen(false)}
                  className="px-5 py-2.5 rounded-xl text-sm font-semibold text-slate-400 hover:bg-slate-800 transition-colors"
                >
                  Hủy
                </button>
                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="px-6 py-2.5 bg-amber-500 hover:bg-amber-600 disabled:bg-amber-500/50 text-slate-950 font-bold rounded-xl shadow-lg shadow-amber-500/20 text-sm flex items-center space-x-2"
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
