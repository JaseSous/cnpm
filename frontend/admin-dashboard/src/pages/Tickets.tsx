import React, { useState, useEffect } from 'react';
import { apiClient } from '../api/client';
import { useAuth } from '../context/AuthContext';
import { QRCodeSVG } from 'qrcode.react';
import { 
  Ticket, 
  QrCode, 
  Copy, 
  Check, 
  RefreshCw, 
  AlertCircle, 
  Clock, 
  DollarSign,
  Printer,
  ExternalLink,
  Trash2
} from 'lucide-react';

interface TicketPackage {
  package_id: number;
  package_name: string;
  price: number;
  description: string;
  is_active: boolean;
}

interface GeneratedTicket {
  shorted_code: string;
  session_id: string;
  amount: number;
  package_name: string;
  expires_in: number;
  created_at: string;
}

export const Tickets: React.FC = () => {
  const { user } = useAuth();
  const [packages, setPackages] = useState<TicketPackage[]>([]);
  const [selectedPackageId, setSelectedPackageId] = useState<number | ''>('');
  const [amount, setAmount] = useState<string>('50000');
  const [isLoading, setIsLoading] = useState(false);
  const [isFetchingPackages, setIsFetchingPackages] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [currentTicket, setCurrentTicket] = useState<GeneratedTicket | null>(null);
  const [copied, setCopied] = useState(false);
  const [copiedCode, setCopiedCode] = useState<string | null>(null);
  const [ticketHistory, setTicketHistory] = useState<GeneratedTicket[]>([]);

  const getStorageKey = () => (user?.user_id ? `linh_ung_staff_tickets_${user.user_id}` : 'linh_ung_staff_tickets_default');

  // Khôi phục lịch sử vé từ localStorage khi tải trang / đổi tài khoản
  useEffect(() => {
    try {
      const key = getStorageKey();
      const saved = localStorage.getItem(key);
      if (saved) {
        const parsed: GeneratedTicket[] = JSON.parse(saved);
        if (Array.isArray(parsed) && parsed.length > 0) {
          setTicketHistory(parsed);
          // Tự động khôi phục vé gần nhất vào khung QR nếu chưa có vé đang xem
          setCurrentTicket((prev) => prev || parsed[0]);
        }
      }
    } catch (err) {
      console.error('Không thể đọc lịch sử vé từ localStorage:', err);
    }
  }, [user?.user_id]);

  // Lấy danh mục gói vé từ server
  useEffect(() => {
    const fetchPackages = async () => {
      try {
        const res = await apiClient.get('/api/auth/packages');
        setPackages(res.data);
        if (res.data.length > 0) {
          setSelectedPackageId(res.data[0].package_id);
          setAmount(String(res.data[0].price));
        }
      } catch (err: any) {
        setError('Không thể tải danh sách gói vé từ máy chủ.');
      } finally {
        setIsFetchingPackages(false);
      }
    };
    fetchPackages();
  }, []);

  // Cập nhật số tiền khi thay đổi gói vé
  const handlePackageChange = (pkgId: number) => {
    setSelectedPackageId(pkgId);
    const pkg = packages.find((p) => p.package_id === pkgId);
    if (pkg) {
      setAmount(String(pkg.price));
    }
  };

  // Tạo vé tiền mặt
  const handleCreateTicket = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setIsLoading(true);

    try {
      const res = await apiClient.post('/api/auth/tickets', {
        package_id: selectedPackageId ? Number(selectedPackageId) : null,
        amount: Number(amount),
        payment_method: 'cash',
      });

      const pkg = packages.find((p) => p.package_id === selectedPackageId);
      const newTicket: GeneratedTicket = {
        ...res.data,
        package_name: pkg ? pkg.package_name : 'Vé tham quan tùy chọn',
      };

      setCurrentTicket(newTicket);
      setTicketHistory((prev) => {
        const updated = [newTicket, ...prev.filter((t) => t.shorted_code !== newTicket.shorted_code)].slice(0, 50);
        try {
          localStorage.setItem(getStorageKey(), JSON.stringify(updated));
        } catch (err) {
          console.error('Không thể lưu lịch sử vé vào localStorage:', err);
        }
        return updated;
      });
    } catch (err: any) {
      setError(err.response?.data?.detail?.message || 'Có lỗi xảy ra khi tạo vé.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleCopyCode = () => {
    if (currentTicket) {
      navigator.clipboard.writeText(currentTicket.shorted_code);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  // Xem lại ảnh mã QR từ cùng shorted_code (không phát sinh mã mới - PRD UC08-E4)
  const handleViewQR = (ticket: GeneratedTicket) => {
    setCurrentTicket(ticket);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const handleCopyItemCode = (code: string) => {
    navigator.clipboard.writeText(code);
    setCopiedCode(code);
    setTimeout(() => setCopiedCode(null), 2000);
  };

  const handleClearHistory = () => {
    if (window.confirm('Bạn có chắc chắn muốn xóa toàn bộ danh sách vé đã lưu trên máy này không?')) {
      setTicketHistory([]);
      try {
        localStorage.removeItem(getStorageKey());
      } catch (err) {
        console.error(err);
      }
    }
  };

  // Tính toán thời gian TTL còn lại dựa trên created_at và expires_in (mặc định 1800s)
  const getTicketStatus = (ticket: GeneratedTicket) => {
    const createdAt = new Date(ticket.created_at).getTime();
    const expireSeconds = ticket.expires_in || 1800;
    const elapsedSeconds = Math.floor((Date.now() - createdAt) / 1000);
    const remainingSeconds = Math.max(0, expireSeconds - elapsedSeconds);
    const isExpired = remainingSeconds <= 0;
    const remainingMinutes = Math.ceil(remainingSeconds / 60);

    return {
      isExpired,
      remainingMinutes,
    };
  };

  // Xác định Base URL của Customer App linh hoạt cho cả Local/LAN và Production Cloud
  const getCustomerAppBaseUrl = () => {
    // 1. Ưu tiên biến môi trường cấu hình sẵn (khi deploy Vercel)
    const envUrl = import.meta.env.VITE_CUSTOMER_APP_URL;
    if (envUrl) {
      return envUrl.replace(/\/$/, '');
    }

    const { protocol, hostname, port } = window.location;

    // 2. Chạy Localhost hoặc mạng LAN nội bộ
    if (
      hostname === 'localhost' ||
      hostname === '127.0.0.1' ||
      hostname.startsWith('192.168.') ||
      hostname.startsWith('10.') ||
      hostname.startsWith('172.')
    ) {
      const customerPort = port === '5174' ? '5173' : '3000';
      return `${protocol}//${hostname}:${customerPort}`;
    }

    // 3. Chạy trên Cloud / Vercel (không dùng port nội bộ)
    if (hostname.includes('admin')) {
      return `${protocol}//${hostname.replace('admin', 'customer')}`;
    }

    return `${protocol}//${hostname}`;
  };

  // URL nhúng vào mã QR để du khách quét (trỏ vào route /auth#code=...)
  const clientAppUrl = currentTicket
    ? `${getCustomerAppBaseUrl()}/auth#code=${currentTicket.shorted_code}`
    : '';

  return (
    <div className="p-6 md:p-10 max-w-7xl mx-auto space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-2xl md:text-3xl font-bold text-white tracking-tight flex items-center space-x-3">
          <Ticket className="w-8 h-8 text-amber-500" />
          <span>Bán vé & Sinh mã QR Thuyết minh (UC08)</span>
        </h1>
        <p className="text-slate-400 mt-1 text-sm md:text-base">
          Thu tiền mặt tại quầy, sinh mã vé 10 ký tự lưu Redis DB 0 với thời hạn 30 phút.
        </p>
      </div>

      {error && (
        <div className="p-4 rounded-xl bg-red-500/10 border border-red-500/30 flex items-start space-x-3 text-red-400 text-sm">
          <AlertCircle className="w-5 h-5 flex-shrink-0 mt-0.5" />
          <span>{error}</span>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
        {/* Form tạo vé */}
        <div className="lg:col-span-5 bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-xl">
          <h2 className="text-lg font-semibold text-white mb-6 flex items-center space-x-2">
            <span>Thông tin phát hành vé</span>
          </h2>

          <form onSubmit={handleCreateTicket} className="space-y-5">
            <div>
              <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2">
                Chọn gói vé tham quan
              </label>
              {isFetchingPackages ? (
                <div className="text-sm text-slate-400">Đang tải gói vé...</div>
              ) : (
                <select
                  value={selectedPackageId}
                  onChange={(e) => handlePackageChange(Number(e.target.value))}
                  className="w-full px-4 py-3 bg-slate-800 border border-slate-700 rounded-xl text-white focus:outline-none focus:ring-2 focus:ring-amber-500/50 focus:border-amber-500 text-sm"
                >
                  {packages.map((pkg) => (
                    <option key={pkg.package_id} value={pkg.package_id}>
                      {pkg.package_name} - {Number(pkg.price).toLocaleString('vi-VN')} đ
                    </option>
                  ))}
                </select>
              )}
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2">
                Số tiền thực thu (VNĐ)
              </label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-slate-400">
                  <DollarSign className="w-5 h-5" />
                </div>
                <input
                  type="number"
                  required
                  min="0"
                  step="1000"
                  value={amount}
                  onChange={(e) => setAmount(e.target.value)}
                  className="w-full pl-11 pr-4 py-3 bg-slate-800 border border-slate-700 rounded-xl text-white focus:outline-none focus:ring-2 focus:ring-amber-500/50 focus:border-amber-500 text-sm font-medium"
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2">
                Hình thức thanh toán
              </label>
              <input
                type="text"
                disabled
                value="Tiền mặt tại quầy (Cash)"
                className="w-full px-4 py-3 bg-slate-800/50 border border-slate-700 rounded-xl text-slate-400 text-sm cursor-not-allowed"
              />
            </div>

            <button
              type="submit"
              disabled={isLoading || isFetchingPackages}
              className="w-full py-3.5 px-4 bg-amber-500 hover:bg-amber-600 disabled:bg-amber-500/50 text-slate-950 font-bold rounded-xl shadow-lg shadow-amber-500/20 transition-all flex items-center justify-center space-x-2 cursor-pointer disabled:cursor-not-allowed text-sm"
            >
              {isLoading ? (
                <>
                  <RefreshCw className="w-5 h-5 animate-spin" />
                  <span>Đang sinh mã vé...</span>
                </>
              ) : (
                <>
                  <QrCode className="w-5 h-5" />
                  <span>Tạo mã vé & Sinh mã QR</span>
                </>
              )}
            </button>
          </form>
        </div>

        {/* Khung hiển thị mã vé & QR */}
        <div className="lg:col-span-7 bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-xl flex flex-col items-center justify-center min-h-[460px]">
          {currentTicket ? (
            <div className="w-full flex flex-col items-center text-center space-y-6">
              {(() => {
                const status = getTicketStatus(currentTicket);
                return status.isExpired ? (
                  <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full bg-red-500/10 text-red-400 text-xs font-semibold border border-red-500/20">
                    <Clock className="w-3.5 h-3.5" />
                    <span>Mã vé đã quá hạn TTL (30 phút)</span>
                  </div>
                ) : (
                  <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full bg-emerald-500/10 text-emerald-400 text-xs font-semibold border border-emerald-500/20">
                    <Clock className="w-3.5 h-3.5" />
                    <span>Hiệu lực còn khoảng {status.remainingMinutes} phút</span>
                  </div>
                );
              })()}

              {/* QR Code Container */}
              <div className="p-4 bg-white rounded-2xl shadow-2xl border-4 border-amber-500/30">
                <QRCodeSVG
                  value={clientAppUrl}
                  size={210}
                  level="H"
                  includeMargin={true}
                />
              </div>

              {/* Mã vé Text lớn */}
              <div>
                <p className="text-xs uppercase tracking-widest text-slate-400 font-semibold mb-1">
                  MÃ VÉ DIỆN RỘNG (10 KÝ TỰ)
                </p>
                <div className="flex items-center justify-center space-x-3">
                  <span className="text-3xl md:text-4xl font-mono font-black text-amber-400 tracking-wider bg-slate-800/80 px-4 py-2 rounded-xl border border-slate-700">
                    {currentTicket.shorted_code}
                  </span>
                  <button
                    onClick={handleCopyCode}
                    className="p-3 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded-xl border border-slate-700 transition-colors cursor-pointer"
                    title="Sao chép mã"
                  >
                    {copied ? <Check className="w-5 h-5 text-emerald-400" /> : <Copy className="w-5 h-5" />}
                  </button>
                </div>
                <p className="text-xs text-slate-400 mt-2 font-medium">
                  {currentTicket.package_name} • {Number(currentTicket.amount).toLocaleString('vi-VN')} đ
                </p>
              </div>

              <div className="text-xs text-slate-400 max-w-md space-y-2">
                <p>Hướng dẫn du khách: Dùng camera điện thoại quét mã QR trên để tự động mở ứng dụng và kích hoạt thuyết minh.</p>
                <div className="flex items-center justify-center gap-1.5 text-[11px] bg-slate-800/80 px-3 py-1.5 rounded-lg border border-slate-700/80 break-all text-slate-400">
                  <span className="font-semibold text-slate-400 shrink-0">Link:</span>
                  <a 
                    href={clientAppUrl} 
                    target="_blank" 
                    rel="noreferrer" 
                    className="text-amber-400 hover:underline inline-flex items-center gap-1 font-mono"
                    title="Bấm để kiểm tra mở trang Client"
                  >
                    <span>{clientAppUrl}</span>
                    <ExternalLink className="w-3 h-3 shrink-0" />
                  </a>
                </div>
              </div>

              <div className="flex items-center space-x-3 pt-2">
                <button
                  onClick={() => window.print()}
                  className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-white rounded-xl text-xs font-semibold flex items-center space-x-2 transition-colors cursor-pointer border border-slate-700"
                >
                  <Printer className="w-4 h-4" />
                  <span>In phiếu vé</span>
                </button>
              </div>
            </div>
          ) : (
            <div className="text-center p-8 space-y-4">
              <div className="w-20 h-20 rounded-full bg-slate-800/60 border border-slate-700/60 flex items-center justify-center text-slate-500 mx-auto">
                <QrCode className="w-10 h-10" />
              </div>
              <h3 className="text-base font-medium text-slate-300">Chưa có mã vé được tạo</h3>
              <p className="text-xs text-slate-500 max-w-sm">
                Vui lòng chọn gói vé và nhấn "Tạo mã vé & Sinh mã QR" để phát hành vé cho du khách tại quầy.
              </p>
            </div>
          )}
        </div>
      </div>

      {/* Lịch sử phát hành vé trong phiên làm việc */}
      {ticketHistory.length > 0 && (
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-xl">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 mb-4">
            <div>
              <h2 className="text-base font-semibold text-white">Các vé đã phát hành gần đây</h2>
              <p className="text-xs text-slate-400">
                Lịch sử lưu trên trình duyệt máy này (F5/Reload không bị mất). Nhấn "Xem lại QR" để tạo lại ảnh mã QR từ cùng shorted_code (không phát sinh mã mới).
              </p>
            </div>
            <button
              onClick={handleClearHistory}
              className="px-3 py-1.5 text-xs text-slate-400 hover:text-red-400 hover:bg-red-500/10 rounded-lg border border-slate-800 hover:border-red-500/30 transition-colors flex items-center space-x-1.5 cursor-pointer self-start sm:self-auto"
              title="Xóa danh sách lịch sử vé trên máy này"
            >
              <Trash2 className="w-3.5 h-3.5" />
              <span>Xóa lịch sử</span>
            </button>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead className="text-xs uppercase bg-slate-800/50 text-slate-400">
                <tr>
                  <th className="px-4 py-3 rounded-l-lg">Mã vé (Code)</th>
                  <th className="px-4 py-3">Gói vé</th>
                  <th className="px-4 py-3">Số tiền</th>
                  <th className="px-4 py-3">Thời gian tạo</th>
                  <th className="px-4 py-3">Trạng thái TTL</th>
                  <th className="px-4 py-3 rounded-r-lg text-right">Hành động</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800 text-slate-300">
                {ticketHistory.map((item, index) => {
                  const { isExpired, remainingMinutes } = getTicketStatus(item);
                  const isCurrent = currentTicket?.shorted_code === item.shorted_code;

                  return (
                    <tr 
                      key={item.session_id || index} 
                      className={`hover:bg-slate-800/40 transition-colors ${isCurrent ? 'bg-amber-500/10 border-l-2 border-amber-500' : ''}`}
                    >
                      <td className="px-4 py-3 font-mono font-bold text-amber-400">
                        <div className="flex items-center space-x-2">
                          <span>{item.shorted_code}</span>
                          {isCurrent && (
                            <span className="text-[10px] px-1.5 py-0.5 rounded bg-amber-500/20 text-amber-300 font-sans font-medium">
                              Đang xem
                            </span>
                          )}
                        </div>
                      </td>
                      <td className="px-4 py-3">{item.package_name}</td>
                      <td className="px-4 py-3">{item.amount.toLocaleString('vi-VN')} đ</td>
                      <td className="px-4 py-3 text-xs text-slate-400">
                        {new Date(item.created_at).toLocaleTimeString('vi-VN', {
                          hour: '2-digit',
                          minute: '2-digit',
                          second: '2-digit'
                        })}
                      </td>
                      <td className="px-4 py-3">
                        {isExpired ? (
                          <span className="inline-flex items-center space-x-1 px-2.5 py-0.5 rounded-full text-[11px] font-semibold bg-slate-800 text-slate-400 border border-slate-700">
                            <Clock className="w-3 h-3 text-slate-500" />
                            <span>Hết hạn TTL</span>
                          </span>
                        ) : (
                          <span className="inline-flex items-center space-x-1 px-2.5 py-0.5 rounded-full text-[11px] font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                            <Clock className="w-3 h-3 text-emerald-400 animate-pulse" />
                            <span>Còn {remainingMinutes} phút</span>
                          </span>
                        )}
                      </td>
                      <td className="px-4 py-3 text-right">
                        <div className="flex items-center justify-end space-x-2">
                          <button
                            onClick={() => handleViewQR(item)}
                            className="px-2.5 py-1 bg-amber-500/10 hover:bg-amber-500/20 text-amber-400 rounded-lg text-xs font-semibold flex items-center space-x-1 transition-colors cursor-pointer border border-amber-500/30"
                            title="Tạo lại ảnh QR từ mã này để du khách quét"
                          >
                            <QrCode className="w-3.5 h-3.5" />
                            <span>Xem lại QR</span>
                          </button>
                          <button
                            onClick={() => handleCopyItemCode(item.shorted_code)}
                            className="p-1.5 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg text-xs transition-colors cursor-pointer border border-slate-700"
                            title="Sao chép mã"
                          >
                            {copiedCode === item.shorted_code ? (
                              <Check className="w-3.5 h-3.5 text-emerald-400" />
                            ) : (
                              <Copy className="w-3.5 h-3.5" />
                            )}
                          </button>
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
};
