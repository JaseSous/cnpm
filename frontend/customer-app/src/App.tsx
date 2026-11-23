import { useEffect } from 'react';
import { BrowserRouter, Routes, Route, Navigate, useNavigate, useLocation } from 'react-router-dom';
import LanguageSelectPage from './pages/LanguageSelectPage';
import QRAuthPage from './pages/QRAuthPage';
import MapAndPOIListPage from './pages/MapAndPOIListPage';
import POIDetailPage from './pages/POIDetailPage';
import ChatbotPage from './pages/ChatbotPage';

function SessionExpirationWatcher() {
  const navigate = useNavigate();
  const location = useLocation();

  useEffect(() => {
    const checkExpiration = () => {
      // Chỉ kiểm tra khi đang ở các trang cần quyền (map, poi, chat)
      if (location.pathname === '/' || location.pathname === '/auth' || location.pathname === '/access') {
        return;
      }

      const token = localStorage.getItem('customer_token');
      if (!token) {
        navigate('/auth', { replace: true });
        return;
      }

      // Ưu tiên đọc trường exp trực tiếp từ JWT payload (tính theo giây UTC chuẩn tuyệt đối)
      let expireTime: number | null = null;
      try {
        const parts = token.split('.');
        if (parts.length === 3) {
          const payload = JSON.parse(atob(parts[1].replace(/-/g, '+').replace(/_/g, '/')));
          if (payload && typeof payload.exp === 'number') {
            expireTime = payload.exp * 1000;
          }
        }
      } catch {
        // Fallback sang customer_expires_at nếu decode token thất bại
      }

      if (!expireTime) {
        const expiresAt = localStorage.getItem('customer_expires_at');
        if (expiresAt) {
          // Chuẩn hóa định dạng UTC ISO string (nếu thiếu Z thì thêm Z để tránh JS parse thành giờ địa phương)
          const normalized = expiresAt.endsWith('Z') || expiresAt.includes('+') ? expiresAt : `${expiresAt}Z`;
          expireTime = new Date(normalized).getTime();
        }
      }

      if (expireTime && !isNaN(expireTime)) {
        if (Date.now() >= expireTime) {
          localStorage.removeItem('customer_token');
          localStorage.removeItem('customer_expires_at');
          alert('Phiên tham quan của bạn đã hết thời hạn 1 phút. Vui lòng quét lại mã vé!');
          navigate('/auth', { replace: true });
          return;
        }
      }
    };

    checkExpiration();
    const timer = setInterval(checkExpiration, 1000);
    return () => clearInterval(timer);
  }, [location.pathname, navigate]);

  return null;
}

export default function App() {
  return (
    <BrowserRouter>
      <SessionExpirationWatcher />
      <div className="min-h-screen bg-amber-50/40 text-stone-800 font-sans antialiased max-w-md mx-auto shadow-2xl relative flex flex-col">
        <Routes>
          <Route path="/" element={<LanguageSelectPage />} />
          <Route path="/auth" element={<QRAuthPage />} />
          <Route path="/access" element={<QRAuthPage />} />
          <Route path="/map" element={<MapAndPOIListPage />} />
          <Route path="/poi/:id" element={<POIDetailPage />} />
          <Route path="/chat" element={<ChatbotPage />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </div>
    </BrowserRouter>
  );
}
