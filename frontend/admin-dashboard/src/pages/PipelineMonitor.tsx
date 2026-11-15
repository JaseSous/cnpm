import React, { useState, useEffect } from 'react';
import { poiClient } from '../api/client';
import { 
  Activity, 
  RotateCw, 
  CheckCircle2, 
  Clock, 
  AlertTriangle, 
  Volume2, 
  Database,
  Loader2,
  AlertCircle
} from 'lucide-react';

interface LocalizationStatus {
  language_code: string;
  status: 'Pending' | 'Done' | 'Failed';
  applied_revision: number;
  audio_url?: string;
  last_error?: string;
  attempt_count: number;
}

interface AlertItem {
  alert_id: number;
  language_code?: string;
  alert_type: string;
  error_message: string;
  created_at: string;
}

interface POIPipelineItem {
  poi_id: number;
  original_title: string;
  original_language_code: string;
  revision: number;
  vector_status: 'Pending' | 'Synced' | 'Failed';
  vector_last_error?: string;
  vector_attempt_count: number;
  localizations: LocalizationStatus[];
  unresolved_alerts: AlertItem[];
}

export const PipelineMonitor: React.FC = () => {
  const [pipelineData, setPipelineData] = useState<POIPipelineItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isRetrying, setIsRetrying] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [selectedLanguages, setSelectedLanguages] = useState<{ [poiId: number]: string[] }>({});
  const [retryVector, setRetryVector] = useState<{ [poiId: number]: boolean }>({});

  const fetchStatus = async () => {
    try {
      const res = await poiClient.get('/api/pois/pipeline-status');
      setPipelineData(res.data);
    } catch (err: any) {
      setError(err.response?.data?.detail?.message || 'Không thể tải trạng thái Pipeline.');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchStatus();
    // Tự động làm mới mỗi 15 giây khi người dùng đang mở tab
    const interval = setInterval(() => {
      if (document.visibilityState === 'visible') {
        fetchStatus();
      }
    }, 15000);
    return () => clearInterval(interval);
  }, []);

  const toggleLanguage = (poiId: number, langCode: string) => {
    setSelectedLanguages((prev) => {
      const current = prev[poiId] || [];
      const updated = current.includes(langCode)
        ? current.filter((l) => l !== langCode)
        : [...current, langCode];
      return { ...prev, [poiId]: updated };
    });
  };

  const handleSelectAllFailed = (poi: POIPipelineItem) => {
    const failedLangs = poi.localizations
      .filter((l) => l.status === 'Failed')
      .map((l) => l.language_code);
    setSelectedLanguages((prev) => ({ ...prev, [poi.poi_id]: failedLangs }));
    if (poi.vector_status === 'Failed') {
      setRetryVector((prev) => ({ ...prev, [poi.poi_id]: true }));
    }
  };

  const handleTriggerRetry = async (poiId: number) => {
    const langs = selectedLanguages[poiId] || [];
    const vector = !!retryVector[poiId];

    if (langs.length === 0 && !vector) {
      alert('Vui lòng chọn ít nhất 1 ngôn ngữ hoặc chọn đồng bộ Vector DB để xử lý lại.');
      return;
    }

    setIsRetrying(poiId);
    try {
      await poiClient.post(`/api/pois/${poiId}/retry`, {
        language_codes: langs,
        retry_vector: vector,
      });
      // Xóa selection và làm mới
      setSelectedLanguages((prev) => ({ ...prev, [poiId]: [] }));
      await fetchStatus();
    } catch (err: any) {
      alert('Không thể kích hoạt retry: ' + (err.response?.data?.detail?.message || err.message));
    } finally {
      setIsRetrying(null);
    }
  };

  return (
    <div className="p-6 md:p-10 max-w-7xl mx-auto space-y-8">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <h1 className="text-2xl md:text-3xl font-bold text-white tracking-tight flex items-center space-x-3">
            <Activity className="w-8 h-8 text-amber-500" />
            <span>Giám sát tiến độ Pipeline & Xử lý lỗi (UC11)</span>
          </h1>
          <p className="text-slate-400 mt-1 text-sm md:text-base">
            Theo dõi thời gian thực quá trình dịch 15+ ngôn ngữ, tạo Edge-TTS và đồng bộ Qdrant Vector DB.
          </p>
        </div>

        <button
          onClick={fetchStatus}
          className="inline-flex items-center space-x-2 px-4 py-2.5 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded-xl border border-slate-700 transition-colors text-sm cursor-pointer"
        >
          <RotateCw className="w-4 h-4" />
          <span>Làm mới</span>
        </button>
      </div>

      {error && (
        <div className="p-4 rounded-xl bg-red-500/10 border border-red-500/30 flex items-start space-x-3 text-red-400 text-sm">
          <AlertCircle className="w-5 h-5 flex-shrink-0 mt-0.5" />
          <span>{error}</span>
        </div>
      )}

      {/* POI Pipeline Cards */}
      {isLoading ? (
        <div className="p-12 text-center text-slate-400 flex flex-col items-center space-y-3">
          <Loader2 className="w-8 h-8 animate-spin text-amber-500" />
          <span>Đang tải thông tin tiến trình xử lý...</span>
        </div>
      ) : pipelineData.length === 0 ? (
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-12 text-center text-slate-500">
          Chưa có điểm tham quan nào trong hệ thống.
        </div>
      ) : (
        <div className="space-y-6">
          {pipelineData.map((poi) => {
            const langsSelected = selectedLanguages[poi.poi_id] || [];
            const isVecSelected = !!retryVector[poi.poi_id];
            const hasFailed = poi.localizations.some((l) => l.status === 'Failed') || poi.vector_status === 'Failed';

            return (
              <div 
                key={poi.poi_id} 
                className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-xl space-y-5"
              >
                {/* POI Title & Status Summary */}
                <div className="flex flex-col md:flex-row md:items-center justify-between pb-4 border-b border-slate-800 gap-3">
                  <div>
                    <div className="flex items-center space-x-3">
                      <h2 className="text-lg font-bold text-white">{poi.original_title}</h2>
                      <span className="px-2 py-0.5 rounded bg-slate-800 text-xs font-mono text-slate-400">
                        POI #{poi.poi_id} (v{poi.revision})
                      </span>
                    </div>
                    <p className="text-xs text-slate-500 mt-0.5">
                      Ngôn ngữ gốc: <strong className="uppercase">{poi.original_language_code}</strong>
                    </p>
                  </div>

                  {/* Vector DB status */}
                  <div className="flex items-center space-x-3">
                    <div className="flex items-center space-x-2 text-xs">
                      <Database className="w-4 h-4 text-slate-400" />
                      <span className="text-slate-400">Vector Qdrant:</span>
                      <span className={`px-2 py-0.5 rounded font-semibold ${
                        poi.vector_status === 'Synced' 
                          ? 'bg-emerald-500/10 text-emerald-400' 
                          : poi.vector_status === 'Failed' 
                          ? 'bg-red-500/10 text-red-400' 
                          : 'bg-amber-500/10 text-amber-400'
                      }`}>
                        {poi.vector_status}
                      </span>
                    </div>

                    {hasFailed && (
                      <button
                        onClick={() => handleSelectAllFailed(poi)}
                        className="text-xs text-amber-400 hover:text-amber-300 underline font-medium cursor-pointer"
                      >
                        Chọn mục lỗi
                      </button>
                    )}
                  </div>
                </div>

                {/* 15 Languages Status Grid */}
                <div>
                  <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-3">
                    Tiến độ dịch thuật & Audio (15 Ngôn ngữ)
                  </h3>

                  <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-5 gap-3">
                    {poi.localizations.map((loc) => {
                      const isSelected = langsSelected.includes(loc.language_code);

                      return (
                        <div
                          key={loc.language_code}
                          onClick={() => toggleLanguage(poi.poi_id, loc.language_code)}
                          className={`p-3 rounded-xl border transition-all cursor-pointer select-none ${
                            isSelected
                              ? 'border-amber-500 bg-amber-500/10 ring-1 ring-amber-500'
                              : 'border-slate-800 bg-slate-800/40 hover:bg-slate-800/70'
                          }`}
                        >
                          <div className="flex items-center justify-between mb-1.5">
                            <span className="font-mono text-xs font-bold uppercase text-white">
                              {loc.language_code}
                            </span>
                            {loc.status === 'Done' ? (
                              <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                            ) : loc.status === 'Pending' ? (
                              <Clock className="w-4 h-4 text-amber-400" />
                            ) : (
                              <AlertTriangle className="w-4 h-4 text-red-400" />
                            )}
                          </div>

                          <div className="flex items-center justify-between text-[11px] text-slate-400">
                            <span className={`${
                              loc.status === 'Done' ? 'text-emerald-400' :
                              loc.status === 'Failed' ? 'text-red-400' : 'text-amber-400'
                            }`}>
                              {loc.status}
                            </span>
                            {loc.audio_url && (
                              <span title="Đã có file audio TTS">
                                <Volume2 className="w-3.5 h-3.5 text-blue-400" />
                              </span>
                            )}
                          </div>

                          {loc.last_error && (
                            <p className="text-[10px] text-red-400 truncate mt-1" title={loc.last_error}>
                              Lỗi: {loc.last_error}
                            </p>
                          )}
                        </div>
                      );
                    })}
                  </div>
                </div>

                {/* Unresolved Alerts */}
                {poi.unresolved_alerts.length > 0 && (
                  <div className="p-4 rounded-xl bg-red-500/10 border border-red-500/20 space-y-2">
                    <h4 className="text-xs font-bold text-red-400 uppercase tracking-wider flex items-center space-x-1.5">
                      <AlertTriangle className="w-4 h-4" />
                      <span>Cảnh báo lỗi ({poi.unresolved_alerts.length})</span>
                    </h4>
                    <div className="space-y-1">
                      {poi.unresolved_alerts.map((alert) => (
                        <p key={alert.alert_id} className="text-xs text-red-300">
                          • [{alert.alert_type}] {alert.error_message}
                        </p>
                      ))}
                    </div>
                  </div>
                )}

                {/* Retry Control Footer */}
                <div className="pt-3 flex flex-col sm:flex-row items-center justify-between gap-3">
                  <div className="flex items-center space-x-4">
                    <label className="flex items-center space-x-2 text-xs text-slate-300 cursor-pointer">
                      <input
                        type="checkbox"
                        checked={isVecSelected}
                        onChange={(e) => setRetryVector((prev) => ({ ...prev, [poi.poi_id]: e.target.checked }))}
                        className="rounded border-slate-700 text-amber-500 focus:ring-amber-500/50"
                      />
                      <span>Đồng bộ lại Vector DB</span>
                    </label>

                    <span className="text-xs text-slate-400">
                      Đã chọn: <strong className="text-amber-400">{langsSelected.length}</strong> ngôn ngữ
                    </span>
                  </div>

                  <button
                    onClick={() => handleTriggerRetry(poi.poi_id)}
                    disabled={isRetrying === poi.poi_id || (langsSelected.length === 0 && !isVecSelected)}
                    className="px-5 py-2.5 bg-amber-500 hover:bg-amber-600 disabled:bg-slate-800 disabled:text-slate-600 text-slate-950 font-bold rounded-xl text-xs flex items-center space-x-2 transition-all cursor-pointer disabled:cursor-not-allowed shadow-lg shadow-amber-500/10"
                  >
                    {isRetrying === poi.poi_id ? (
                      <>
                        <Loader2 className="w-4 h-4 animate-spin" />
                        <span>Đang gửi yêu cầu...</span>
                      </>
                    ) : (
                      <>
                        <RotateCw className="w-4 h-4" />
                        <span>Xử lý lại (Retry Pipeline)</span>
                      </>
                    )}
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};
