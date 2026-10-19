import React, { useState } from 'react';
import { QrCode, Key, CreditCard, Banknote, RefreshCw, AlertCircle, CheckCircle2 } from 'lucide-react';
import { verifyCode, createPayooSession, triggerPayooWebhook, setStoredToken } from '../services/api';
import { LanguageSelector } from '../components/LanguageSelector';

interface Props {
  onAuthSuccess: (token: string) => void;
  selectedLang: string;
  onSelectLang: (lang: string) => void;
}

export const AuthView: React.FC<Props> = ({ onAuthSuccess, selectedLang, onSelectLang }) => {
  const [code, setCode] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [info, setInfo] = useState<string | null>(null);

  // Trạng thái cho luồng Payoo Online
  const [onlineSession, setOnlineSession] = useState<{
    auth_code: string;
    amount: number;
    status: string;
  } | null>(null);
  const [retryCount, setRetryCount] = useState(0);

  // Xử lý xác thực mã (UC01)
  const handleVerify = async (codeToVerify: string) => {
    setError(null);
    setInfo(null);
    setLoading(true);

    try {
      const res = await verifyCode(codeToVerify);

      // UC01 A1: Trạng thái thanh toán online đang Pending -> Auto-retry
      if (res.status === 'Pending') {
        setInfo('⏳ Giao dịch đang chờ xử lý từ cổng Payoo. Đang tự động thử lại...');
        pollPendingSession(codeToVerify, 1);
        return;
      }

      if (res.access_token) {
        setStoredToken(res.access_token);
        setInfo('✅ Xác thực thành công! Đang tải bản đồ...');
        setTimeout(() => {
          onAuthSuccess(res.access_token);
        }, 600);
      }
    } catch (err: any) {
      setError(err.message || 'Mã xác thực không hợp lệ');
    } finally {
      setLoading(false);
    }
  };

  // UC01 A1: Auto-retry khi Pending tối đa 5 lần
  const pollPendingSession = (authCode: string, attempt: number) => {
    if (attempt > 6) {
      setError('Hết thời gian chờ giao dịch. Vui lòng thử lại sau.');
      setLoading(false);
      return;
    }

    setRetryCount(attempt);
    setTimeout(async () => {
      try {
        const res = await verifyCode(authCode);
        if (res.status === 'Success' && res.access_token) {
          setStoredToken(res.access_token);
          setInfo('✅ Đã nhận xác nhận thanh toán! Đang chuyển hướng...');
          setLoading(false);
          setTimeout(() => onAuthSuccess(res.access_token), 600);
        } else if (res.status === 'Pending') {
          setInfo(`⏳ Đang chờ Payoo xác nhận... (lần thử ${attempt}/6)`);
          pollPendingSession(authCode, attempt + 1);
        }
      } catch (err: any) {
        setError(err.message);
        setLoading(false);
      }
    }, 2000);
  };

  // Giả lập quét QR cổng tạo phiên Payoo
  const handleCreatePayooMock = async () => {
    setError(null);
    setInfo(null);
    try {
      const res = await createPayooSession(50000);
      setOnlineSession(res);
      setCode(res.auth_code);
      setInfo(`Đã tạo phiên Payoo: ${res.auth_code} (Trạng thái: Pending). Bạn có thể thử Verify ngay để xem phản hồi Pending, hoặc bấm "Giả lập Webhook Thành công".`);
    } catch (err: any) {
      setError(err.message);
    }
  };

  // Giả lập Webhook Payoo chuyển Pending -> Success
  const handleTriggerWebhookSuccess = async () => {
    if (!onlineSession) return;
    try {
      await triggerPayooWebhook(onlineSession.auth_code, 'Success');
      setOnlineSession({ ...onlineSession, status: 'Success' });
      setInfo(`Webhook đã cập nhật phiên ${onlineSession.auth_code} sang Success! Hãy bấm Xác thực ngay.`);
    } catch (err: any) {
      setError(err.message);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-b from-amber-500/10 via-slate-50 to-slate-100 flex flex-col justify-between p-4">
      {/* Header */}
      <header className="flex items-center justify-between py-2">
        <div className="flex items-center space-x-2">
          <div className="w-9 h-9 bg-amber-600 rounded-xl flex items-center justify-center text-white text-lg shadow-sm">
            ⛩️
          </div>
          <div>
            <h1 className="text-sm font-bold text-slate-800 leading-tight">CHÙA LINH ỨNG</h1>
            <p className="text-[10px] text-amber-700 font-medium">BÃI BỤT - BÁN ĐẢO SƠN TRÀ</p>
          </div>
        </div>
        <LanguageSelector selectedLang={selectedLang} onSelectLang={onSelectLang} />
      </header>

      {/* Main Card */}
      <main className="max-w-md w-full mx-auto bg-white rounded-3xl shadow-xl border border-slate-100 p-6 my-4">
        <div className="text-center mb-6">
          <div className="w-16 h-16 bg-amber-100 text-amber-600 rounded-2xl flex items-center justify-center mx-auto mb-3 shadow-inner">
            <QrCode size={36} />
          </div>
          <h2 className="text-xl font-bold text-slate-800">Xác Thực & Thuyết Minh</h2>
          <p className="text-xs text-slate-500 mt-1">
            Quét mã QR tại cổng hoặc nhập mã vé để bắt đầu chuyến tham quan tự động
          </p>
        </div>

        {/* Input Form */}
        <form
          onSubmit={(e) => {
            e.preventDefault();
            handleVerify(code);
          }}
          className="space-y-4"
        >
          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">
              Mã xác thực vé (Online hoặc Tiền mặt)
            </label>
            <div className="relative">
              <input
                type="text"
                value={code}
                onChange={(e) => setCode(e.target.value.toUpperCase())}
                placeholder="VD: PAY-8X2K hoặc mã tiền mặt 10 ký tự"
                className="w-full px-4 py-3 pl-10 bg-slate-50 border border-slate-200 rounded-xl text-sm font-mono tracking-wider focus:outline-none focus:ring-2 focus:ring-amber-500 focus:bg-white uppercase transition"
              />
              <Key className="absolute left-3 top-3.5 text-slate-400" size={18} />
            </div>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full py-3.5 bg-amber-600 hover:bg-amber-700 active:scale-[0.99] text-white font-semibold rounded-xl text-sm transition shadow-md shadow-amber-600/20 flex items-center justify-center space-x-2 disabled:opacity-50"
          >
            {loading ? (
              <>
                <RefreshCw className="animate-spin" size={18} />
                <span>Đang kiểm tra...</span>
              </>
            ) : (
              <span>Xác Thực & Bắt Đầu</span>
            )}
          </button>
        </form>

        {/* Thông báo lỗi / trạng thái */}
        {error && (
          <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-xl text-xs text-red-600 flex items-start space-x-2">
            <AlertCircle size={16} className="shrink-0 mt-0.5" />
            <span>{error}</span>
          </div>
        )}

        {info && (
          <div className="mt-4 p-3 bg-blue-50 border border-blue-200 rounded-xl text-xs text-blue-700 flex items-start space-x-2">
            <CheckCircle2 size={16} className="shrink-0 mt-0.5" />
            <span>{info}</span>
          </div>
        )}

        {/* KHU VỰC DEMO DÀNH CHO GIẢNG VIÊN / BAN GIÁM KHẢO */}
        <div className="mt-6 pt-5 border-t border-slate-100 space-y-3">
          <p className="text-[11px] font-bold text-slate-500 uppercase tracking-wider text-center">
            🧪 Công cụ Demo luồng UC01
          </p>

          <div className="grid grid-cols-2 gap-2 text-xs">
            <button
              onClick={handleCreatePayooMock}
              className="p-2.5 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-xl font-medium flex items-center justify-center space-x-1.5 transition"
            >
              <CreditCard size={15} className="text-amber-600" />
              <span>1. Giả lập Payoo (Pending)</span>
            </button>

            <button
              onClick={handleTriggerWebhookSuccess}
              disabled={!onlineSession}
              className="p-2.5 bg-emerald-50 hover:bg-emerald-100 text-emerald-700 border border-emerald-200 rounded-xl font-medium flex items-center justify-center space-x-1.5 transition disabled:opacity-40"
            >
              <CheckCircle2 size={15} />
              <span>2. Webhook: Thành công</span>
            </button>
          </div>

          <div className="text-[11px] text-slate-400 text-center">
            * Mẹo: Để thử luồng tiền mặt, hãy vào <strong>/admin</strong> tạo mã hoặc dùng tài khoản admin (admin/admin123).
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="text-center text-xs text-slate-400 py-2">
        Đồ án môn Công nghệ phần mềm &copy; 2026 - ĐH Sài Gòn (SGU)
      </footer>
    </div>
  );
};
