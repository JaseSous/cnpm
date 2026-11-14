import { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { Html5Qrcode } from 'html5-qrcode';
import { authClient } from '../api/client';
import { QrCode, KeyRound, ArrowLeft, Camera, AlertCircle, CheckCircle2 } from 'lucide-react';

export default function QRAuthPage() {
  const navigate = useNavigate();
  const [shortedCode, setShortedCode] = useState<string>('');
  const [scanning, setScanning] = useState<boolean>(false);
  const [errorMsg, setErrorMsg] = useState<string>('');
  const [loading, setLoading] = useState<boolean>(false);
  const [successMsg, setSuccessMsg] = useState<string>('');
  
  const qrScannerRef = useRef<Html5Qrcode | null>(null);

  // Tự động kiểm tra mã từ URL hash hoặc URL query params (ví dụ khi khách scan bằng camera gốc của điện thoại)
  useEffect(() => {
    const parseCodeFromUrl = () => {
      const hash = window.location.hash;
      const search = window.location.search;
      let extractedCode = '';

      if (hash.includes('code=')) {
        const match = hash.match(/code=([A-Za-z0-9]{10})/);
        if (match) extractedCode = match[1];
      } else if (search.includes('code=')) {
        const params = new URLSearchParams(search);
        const codeParam = params.get('code');
        if (codeParam && codeParam.length === 10) extractedCode = codeParam;
      }

      if (extractedCode) {
        setShortedCode(extractedCode.toUpperCase());
        // Tự động xác thực ngay
        verifyTicketCode(extractedCode.toUpperCase());
      }
    };

    parseCodeFromUrl();
  }, []);

  const verifyTicketCode = async (codeToVerify: string) => {
    const code = codeToVerify.trim().toUpperCase();
    if (!code || code.length !== 10) {
      setErrorMsg('Mã vé phải bao gồm chính xác 10 ký tự chữ và số.');
      return;
    }

    setLoading(true);
    setErrorMsg('');
    setSuccessMsg('');

    try {
      const response = await authClient.post('/api/auth/verify-code', {
        shorted_code: code
      });

      if (response.data && response.data.access_token) {
        localStorage.setItem('customer_token', response.data.access_token);
        localStorage.setItem('customer_expires_at', response.data.expires_at || '');
        setSuccessMsg('Kích hoạt vé tham quan thành công!');

        // Dừng camera nếu đang quét
        stopScanning();

        // Chuyển hướng sang bản đồ
        setTimeout(() => {
          navigate('/map');
        }, 800);
      }
    } catch (err: any) {
      const detail = err.response?.data?.detail;
      if (typeof detail === 'object' && detail?.message) {
        setErrorMsg(detail.message);
      } else if (typeof detail === 'string') {
        setErrorMsg(detail);
      } else {
        setErrorMsg('Mã vé không tồn tại, đã hết hạn hoặc đã được sử dụng.');
      }
    } finally {
      setLoading(false);
    }
  };

  const startScanning = async () => {
    setErrorMsg('');
    try {
      const html5QrCode = new Html5Qrcode('qr-reader-container');
      qrScannerRef.current = html5QrCode;
      setScanning(true);

      await html5QrCode.start(
        { facingMode: 'environment' },
        {
          fps: 10,
          qrbox: { width: 250, height: 250 }
        },
        (decodedText) => {
          // Trích xuất mã từ kết quả QR
          let foundCode = decodedText;
          if (decodedText.includes('code=')) {
            const match = decodedText.match(/code=([A-Za-z0-9]{10})/);
            if (match) foundCode = match[1];
          } else if (decodedText.length === 10) {
            foundCode = decodedText;
          }

          if (foundCode && foundCode.length === 10) {
            setShortedCode(foundCode.toUpperCase());
            stopScanning();
            verifyTicketCode(foundCode.toUpperCase());
          }
        },
        () => {
          // Bỏ qua lỗi frame quét thường lệ
        }
      );
    } catch (err: any) {
      setErrorMsg('Không thể truy cập camera. Vui lòng cấp quyền hoặc nhập mã vé thủ công.');
      setScanning(false);
    }
  };

  const stopScanning = async () => {
    if (qrScannerRef.current) {
      try {
        await qrScannerRef.current.stop();
        qrScannerRef.current.clear();
      } catch {
        // Bỏ qua lỗi dừng camera
      }
      qrScannerRef.current = null;
    }
    setScanning(false);
  };

  useEffect(() => {
    return () => {
      stopScanning();
    };
  }, []);

  return (
    <div className="flex-1 flex flex-col p-6 bg-gradient-to-b from-amber-50 via-white to-amber-50">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <button
          onClick={() => navigate('/')}
          className="p-2 rounded-full hover:bg-amber-100 text-stone-600 transition-colors"
          title="Đổi ngôn ngữ"
        >
          <ArrowLeft className="w-5 h-5" />
        </button>
        <span className="text-xs uppercase font-bold tracking-wider text-amber-800">
          XÁC THỰC VÉ THAM QUAN
        </span>
        <div className="w-5" />
      </div>

      <div className="text-center mb-6">
        <div className="inline-flex p-3 rounded-2xl bg-amber-100 text-amber-800 mb-2">
          <QrCode className="w-8 h-8" />
        </div>
        <h2 className="text-xl font-bold text-stone-900">Quét mã QR hoặc Nhập mã vé</h2>
        <p className="text-xs text-stone-500 mt-1 max-w-xs mx-auto">
          Mỗi mã vé chỉ kích hoạt một lần duy nhất cho thiết bị của quý khách trong suốt hành trình.
        </p>
      </div>

      {/* Thông báo lỗi / thành công */}
      {errorMsg && (
        <div className="mb-4 p-3.5 rounded-xl bg-red-50 border border-red-200 text-red-700 text-xs flex items-center gap-2">
          <AlertCircle className="w-4 h-4 shrink-0 text-red-500" />
          <span>{errorMsg}</span>
        </div>
      )}

      {successMsg && (
        <div className="mb-4 p-3.5 rounded-xl bg-emerald-50 border border-emerald-200 text-emerald-800 text-xs flex items-center gap-2">
          <CheckCircle2 className="w-4 h-4 shrink-0 text-emerald-600" />
          <span>{successMsg}</span>
        </div>
      )}

      {/* Vùng quét QR Camera */}
      <div className="mb-6">
        <div
          id="qr-reader-container"
          className={`w-full overflow-hidden rounded-2xl bg-stone-900 border-2 border-dashed border-amber-300 transition-all ${
            scanning ? 'min-h-[280px]' : 'hidden'
          }`}
        />

        {!scanning ? (
          <button
            onClick={startScanning}
            disabled={loading}
            className="w-full py-4 px-4 rounded-2xl bg-amber-600 hover:bg-amber-700 active:scale-[0.99] text-white font-medium flex items-center justify-center gap-2.5 shadow-md shadow-amber-600/25 transition-all text-sm"
          >
            <Camera className="w-5 h-5" />
            <span>Mở camera quét mã QR</span>
          </button>
        ) : (
          <button
            onClick={stopScanning}
            className="w-full mt-3 py-2.5 px-4 rounded-xl border border-stone-300 bg-white text-stone-700 text-xs font-semibold hover:bg-stone-50 transition-colors"
          >
            Đóng camera
          </button>
        )}
      </div>

      {/* Ngăn cách */}
      <div className="flex items-center gap-3 my-4">
        <div className="flex-1 h-px bg-stone-200" />
        <span className="text-xs uppercase font-medium text-stone-400">HOẶC NHẬP THỦ CÔNG</span>
        <div className="flex-1 h-px bg-stone-200" />
      </div>

      {/* Nhập mã thủ công */}
      <div className="space-y-3">
        <div className="relative">
          <KeyRound className="w-5 h-5 absolute left-3.5 top-1/2 -translate-y-1/2 text-stone-400" />
          <input
            type="text"
            maxLength={10}
            value={shortedCode}
            onChange={(e) => setShortedCode(e.target.value.toUpperCase())}
            placeholder="Nhập 10 ký tự mã vé..."
            className="w-full pl-11 pr-4 py-3.5 rounded-xl border border-stone-300 bg-white text-stone-900 placeholder-stone-400 font-mono tracking-widest text-center uppercase text-base focus:outline-none focus:ring-2 focus:ring-amber-500 focus:border-amber-500 shadow-sm"
          />
        </div>

        <button
          onClick={() => verifyTicketCode(shortedCode)}
          disabled={loading || shortedCode.length !== 10}
          className={`w-full py-3.5 px-4 rounded-xl font-medium text-sm transition-all flex items-center justify-center gap-2 ${
            shortedCode.length === 10 && !loading
              ? 'bg-stone-900 hover:bg-black text-white shadow-md'
              : 'bg-stone-200 text-stone-400 cursor-not-allowed'
          }`}
        >
          {loading ? (
            <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
          ) : (
            <span>Kích hoạt vé vào chùa</span>
          )}
        </button>
      </div>

      <div className="mt-auto pt-8 text-center text-xs text-stone-400">
        Cần trợ giúp kích hoạt vé? Vui lòng liên hệ quầy vé tại cổng Tam Quan.
      </div>
    </div>
  );
}
