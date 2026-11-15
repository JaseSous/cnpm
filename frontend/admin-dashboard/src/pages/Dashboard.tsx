import React, { useState, useEffect, useCallback } from 'react';
import { apiClient } from '../api/client';
import { 
  RefreshCw, 
  AlertCircle, 
  Clock, 
  Calendar, 
  TrendingUp, 
  CheckCircle2, 
  Radio,
  Ticket
} from 'lucide-react';

interface RecentSession {
  session_id: string;
  amount: number;
  payment_method: string;
  status: string;
  created_at: string;
  activated_at: string | null;
  token_expires_at: string | null;
}

interface DashboardStats {
  codes_created_today: number;
  total_codes_created: number;
  pending_codes: number;
  active_sessions: number;
  server_time: string;
  recent_sessions: RecentSession[];
}

export const Dashboard: React.FC = () => {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [isRefreshing, setIsRefreshing] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [lastRefreshedAt, setLastRefreshedAt] = useState<Date>(new Date());

  const fetchStats = useCallback(async (showRefreshingState = false) => {
    if (showRefreshingState) {
      setIsRefreshing(true);
    } else {
      setIsLoading(true);
    }
    setError(null);

    try {
      const res = await apiClient.get<DashboardStats>('/api/auth/dashboard-stats');
      setStats(res.data);
      setLastRefreshedAt(new Date());
    } catch (err: any) {
      const msg = err.response?.data?.detail?.message || 'Không thể tải số liệu thống kê từ cơ sở dữ liệu.';
      setError(msg);
    } finally {
      setIsLoading(false);
      setIsRefreshing(false);
    }
  }, []);

  useEffect(() => {
    fetchStats();
    // Tự động làm mới số liệu mỗi 30 giây
    const interval = setInterval(() => {
      fetchStats(true);
    }, 30000);
    return () => clearInterval(interval);
  }, [fetchStats]);

  const formatDate = (dateStr: string | null) => {
    if (!dateStr) return '—';
    try {
      const date = new Date(dateStr);
      return date.toLocaleString('vi-VN', {
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
        day: '2-digit',
        month: '2-digit',
        year: 'numeric'
      });
    } catch {
      return dateStr;
    }
  };

  return (
    <div className="p-6 md:p-8 max-w-7xl mx-auto space-y-8">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-6 border-b border-slate-800">
        <div>
          <div className="flex items-center gap-2">
            <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-amber-500/10 text-amber-400 border border-amber-500/20">
              Database Analytics
            </span>
            <span className="flex items-center gap-1.5 text-xs text-emerald-400 font-medium">
              <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
              Live Connected
            </span>
          </div>
          <h1 className="text-2xl md:text-3xl font-extrabold text-white mt-1">
            Dashboard Thống kê Hệ thống
          </h1>
          <p className="text-sm text-slate-400 mt-1">
            Số liệu thống kê mã vé và phiên truy cập được truy vấn trực tiếp từ cơ sở dữ liệu.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <div className="text-right hidden sm:block">
            <p className="text-xs text-slate-500 flex items-center gap-1 justify-end">
              <Clock className="w-3.5 h-3.5" />
              Cập nhật gần nhất
            </p>
            <p className="text-xs font-medium text-slate-300">
              {lastRefreshedAt.toLocaleTimeString('vi-VN')}
            </p>
          </div>
          <button
            onClick={() => fetchStats(true)}
            disabled={isLoading || isRefreshing}
            className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 text-sm font-medium border border-slate-700/60 transition-all cursor-pointer disabled:opacity-50"
          >
            <RefreshCw className={`w-4 h-4 ${isRefreshing ? 'animate-spin text-amber-400' : ''}`} />
            <span>Làm mới</span>
          </button>
        </div>
      </div>

      {/* Error Banner */}
      {error && (
        <div className="p-4 rounded-xl bg-red-500/10 border border-red-500/20 text-red-400 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <AlertCircle className="w-5 h-5 flex-shrink-0" />
            <span className="text-sm">{error}</span>
          </div>
          <button 
            onClick={() => fetchStats(false)}
            className="px-3 py-1 rounded-lg bg-red-500/20 hover:bg-red-500/30 text-xs font-semibold text-red-300 transition-colors"
          >
            Thử lại
          </button>
        </div>
      )}

      {/* 4 Primary Stat Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
        {/* Card 1: Số mã được tạo hôm nay */}
        <div className="relative overflow-hidden rounded-2xl bg-gradient-to-br from-slate-900 to-slate-900/60 border border-slate-800 p-6 shadow-xl hover:border-emerald-500/40 transition-all">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">
              Hôm nay
            </span>
            <div className="w-10 h-10 rounded-xl bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center text-emerald-400">
              <Calendar className="w-5 h-5" />
            </div>
          </div>

          <div className="mt-4">
            <div className="text-3xl md:text-4xl font-extrabold text-white tracking-tight">
              {isLoading ? (
                <div className="h-10 w-20 bg-slate-800 rounded animate-pulse" />
              ) : (
                stats?.codes_created_today ?? 0
              )}
            </div>
            <p className="text-sm font-semibold text-emerald-400 mt-1">
              Số mã được tạo hôm nay
            </p>
          </div>

          <div className="mt-4 pt-4 border-t border-slate-800/80 flex items-center justify-between text-xs text-slate-400">
            <span>Từ 00:00:00 (GMT+7)</span>
            <span className="text-slate-500">created_at</span>
          </div>
        </div>

        {/* Card 2: Số mã được tạo toàn thời gian */}
        <div className="relative overflow-hidden rounded-2xl bg-gradient-to-br from-slate-900 to-slate-900/60 border border-slate-800 p-6 shadow-xl hover:border-blue-500/40 transition-all">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">
              Toàn thời gian
            </span>
            <div className="w-10 h-10 rounded-xl bg-blue-500/10 border border-blue-500/20 flex items-center justify-center text-blue-400">
              <TrendingUp className="w-5 h-5" />
            </div>
          </div>

          <div className="mt-4">
            <div className="text-3xl md:text-4xl font-extrabold text-white tracking-tight">
              {isLoading ? (
                <div className="h-10 w-20 bg-slate-800 rounded animate-pulse" />
              ) : (
                stats?.total_codes_created ?? 0
              )}
            </div>
            <p className="text-sm font-semibold text-blue-400 mt-1">
              Số mã tạo toàn thời gian
            </p>
          </div>

          <div className="mt-4 pt-4 border-t border-slate-800/80 flex items-center justify-between text-xs text-slate-400">
            <span>Tổng phiên phát hành</span>
            <span className="text-slate-500">Tất cả phiên</span>
          </div>
        </div>

        {/* Card 3: Số mã còn chờ kích hoạt */}
        <div className="relative overflow-hidden rounded-2xl bg-gradient-to-br from-slate-900 to-slate-900/60 border border-slate-800 p-6 shadow-xl hover:border-amber-500/40 transition-all">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">
              Chờ kích hoạt
            </span>
            <div className="w-10 h-10 rounded-xl bg-amber-500/10 border border-amber-500/20 flex items-center justify-center text-amber-400">
              <Clock className="w-5 h-5" />
            </div>
          </div>

          <div className="mt-4">
            <div className="text-3xl md:text-4xl font-extrabold text-white tracking-tight">
              {isLoading ? (
                <div className="h-10 w-20 bg-slate-800 rounded animate-pulse" />
              ) : (
                stats?.pending_codes ?? 0
              )}
            </div>
            <p className="text-sm font-semibold text-amber-400 mt-1">
              Số mã còn chờ kích hoạt
            </p>
          </div>

          <div className="mt-4 pt-4 border-t border-slate-800/80 flex items-center justify-between text-xs text-slate-400">
            <span>Chưa được quét/đổi</span>
            <span className="text-slate-500">status = Pending</span>
          </div>
        </div>

        {/* Card 4: Số phiên người dùng đang hoạt động (chưa hết hạn token) */}
        <div className="relative overflow-hidden rounded-2xl bg-gradient-to-br from-slate-900 to-slate-900/60 border border-slate-800 p-6 shadow-xl hover:border-cyan-500/40 transition-all">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
              Đang hoạt động
              <span className="w-2 h-2 rounded-full bg-cyan-400 animate-ping" />
            </span>
            <div className="w-10 h-10 rounded-xl bg-cyan-500/10 border border-cyan-500/20 flex items-center justify-center text-cyan-400">
              <Radio className="w-5 h-5" />
            </div>
          </div>

          <div className="mt-4">
            <div className="text-3xl md:text-4xl font-extrabold text-white tracking-tight">
              {isLoading ? (
                <div className="h-10 w-20 bg-slate-800 rounded animate-pulse" />
              ) : (
                stats?.active_sessions ?? 0
              )}
            </div>
            <p className="text-sm font-semibold text-cyan-400 mt-1">
              Số phiên đang hoạt động
            </p>
          </div>

          <div className="mt-4 pt-4 border-t border-slate-800/80 flex items-center justify-between text-xs text-slate-400">
            <span>Chưa hết hạn token</span>
            <span className="text-slate-500">token_expires_at &gt; now</span>
          </div>
        </div>
      </div>

      {/* Recent Sessions Table */}
      <div className="rounded-2xl bg-slate-900 border border-slate-800 overflow-hidden shadow-xl">
        <div className="p-5 border-b border-slate-800 flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <Ticket className="w-5 h-5 text-amber-500" />
            <h3 className="text-base font-bold text-white">
              Lịch sử các phiên mã vé gần nhất (PaymentSessions)
            </h3>
          </div>
          <span className="text-xs text-slate-400 bg-slate-800 px-2.5 py-1 rounded-lg">
            10 phiên mới nhất
          </span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead className="bg-slate-950/60 text-xs uppercase text-slate-400 font-semibold border-b border-slate-800">
              <tr>
                <th className="px-5 py-3.5">Mã phiên (Session ID)</th>
                <th className="px-5 py-3.5">Phương thức</th>
                <th className="px-5 py-3.5">Số tiền</th>
                <th className="px-5 py-3.5">Trạng thái</th>
                <th className="px-5 py-3.5">Thời điểm tạo</th>
                <th className="px-5 py-3.5">Kích hoạt lúc</th>
                <th className="px-5 py-3.5">Hết hạn Token</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {isLoading ? (
                <tr>
                  <td colSpan={7} className="px-5 py-10 text-center text-slate-500">
                    <RefreshCw className="w-6 h-6 animate-spin mx-auto mb-2 text-amber-500" />
                    Đang truy vấn dữ liệu từ database...
                  </td>
                </tr>
              ) : !stats?.recent_sessions || stats.recent_sessions.length === 0 ? (
                <tr>
                  <td colSpan={7} className="px-5 py-10 text-center text-slate-500">
                    Chưa có phiên mã vé nào trong cơ sở dữ liệu.
                  </td>
                </tr>
              ) : (
                stats.recent_sessions.map((session) => {
                  const isSuccess = session.status === 'Success';
                  const isExpired = session.token_expires_at && new Date(session.token_expires_at) < new Date();
                  const isCurrentlyActive = isSuccess && !isExpired;

                  return (
                    <tr key={session.session_id} className="hover:bg-slate-800/30 transition-colors">
                      <td className="px-5 py-3.5 font-mono text-xs text-slate-300">
                        {session.session_id.substring(0, 8)}...{session.session_id.substring(session.session_id.length - 4)}
                      </td>
                      <td className="px-5 py-3.5 text-xs text-slate-300 uppercase">
                        {session.payment_method}
                      </td>
                      <td className="px-5 py-3.5 text-xs font-semibold text-white">
                        {Number(session.amount).toLocaleString('vi-VN')} đ
                      </td>
                      <td className="px-5 py-3.5">
                        {isCurrentlyActive ? (
                          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[11px] font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
                            Đang hoạt động
                          </span>
                        ) : isSuccess ? (
                          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[11px] font-semibold bg-slate-800 text-slate-400 border border-slate-700">
                            <CheckCircle2 className="w-3 h-3 text-slate-400" />
                            Đã kích hoạt
                          </span>
                        ) : (
                          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[11px] font-semibold bg-amber-500/10 text-amber-400 border border-amber-500/20">
                            Chờ kích hoạt
                          </span>
                        )}
                      </td>
                      <td className="px-5 py-3.5 text-xs text-slate-400">
                        {formatDate(session.created_at)}
                      </td>
                      <td className="px-5 py-3.5 text-xs text-slate-300">
                        {formatDate(session.activated_at)}
                      </td>
                      <td className="px-5 py-3.5 text-xs text-slate-400">
                        {formatDate(session.token_expires_at)}
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
