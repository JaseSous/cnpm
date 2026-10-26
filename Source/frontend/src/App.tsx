import React, { useState, useEffect } from 'react';
import { AuthView } from './views/AuthView';
import { MapView } from './views/MapView';
import { ChatView } from './views/ChatView';
import { AdminDashboard } from './views/AdminDashboard';
import { LanguageSelector } from './components/LanguageSelector';
import { fetchAllPOIs, getStoredToken, clearStoredToken, sendHeartbeat } from './services/api';
import { POI, TourRoute } from './types';
import { Map, MessageSquare, Compass, Shield } from 'lucide-react';

export default function App() {
  const [currentPath, setCurrentPath] = useState(window.location.pathname);
  const [token, setToken] = useState<string | null>(getStoredToken());
  const [selectedLang, setSelectedLang] = useState<string>('vi');

  // Dữ liệu POI và Tuyến tham quan tải 1 lần duy nhất (UC02)
  const [pois, setPois] = useState<POI[]>([]);
  const [routes, setRoutes] = useState<TourRoute[]>([]);
  const [loadingPOIs, setLoadingPOIs] = useState<boolean>(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // Tab đang mở ở Client App ('map' | 'chat')
  const [activeTab, setActiveTab] = useState<'map' | 'chat'>('map');

  // Lắng nghe thay đổi pathname (hỗ trợ route /admin)
  useEffect(() => {
    const handlePopState = () => setCurrentPath(window.location.pathname);
    window.addEventListener('popstate', handlePopState);
    return () => window.removeEventListener('popstate', handlePopState);
  }, []);

  const navigateTo = (path: string) => {
    window.history.pushState({}, '', path);
    setCurrentPath(path);
  };

  // UC02: Tải TOÀN BỘ dữ liệu POI 1 lần duy nhất sau khi có token
  useEffect(() => {
    if (token && pois.length === 0 && !loadingPOIs) {
      setLoadingPOIs(true);
      setErrorMessage(null);

      fetchAllPOIs()
        .then((data) => {
          if (data && data.pois) {
            setPois(data.pois);
            setRoutes(data.tour_routes || []);
          }
        })
        .catch((err: any) => {
          if (err.message?.includes('401') || err.message?.includes('không hợp lệ')) {
            clearStoredToken();
            setToken(null);
          } else {
            setErrorMessage(err.message || 'Không thể tải dữ liệu bản đồ, vui lòng thử lại');
          }
        })
        .finally(() => {
          setLoadingPOIs(false);
        });
    }
  }, [token]);

  // Gửi tín hiệu trực tuyến (heartbeat) thời gian thực khi khách truy cập ứng dụng
  useEffect(() => {
    // Không tính lượt khách khi đang ở màn hình Quản trị viên
    if (currentPath === '/admin' || currentPath.startsWith('/admin/')) return;

    let clientId = localStorage.getItem('visitor_client_id');
    if (!clientId) {
      clientId = 'vis_' + Math.random().toString(36).substring(2, 9);
      localStorage.setItem('visitor_client_id', clientId);
    }

    sendHeartbeat(clientId).catch(() => {});
    const interval = setInterval(() => {
      sendHeartbeat(clientId).catch(() => {});
    }, 10000);

    return () => clearInterval(interval);
  }, [currentPath]);

  // Nếu người dùng truy cập /admin
  if (currentPath === '/admin' || currentPath.startsWith('/admin/')) {
    return (
      <div className="min-h-screen bg-slate-50 flex flex-col">
        <div className="bg-amber-600 text-white text-xs px-4 py-1.5 flex items-center justify-between">
          <span className="font-medium">Chế độ Quản trị viên (Admin)</span>
          <button
            onClick={() => navigateTo('/')}
            className="underline hover:text-amber-100 font-bold"
          >
            ← Quay lại Ứng dụng Du khách
          </button>
        </div>
        <div className="flex-1">
          <AdminDashboard onBack={() => navigateTo('/')} />
        </div>
      </div>
    );
  }

  // Nếu chưa đăng nhập / chưa có token -> Hiển thị màn hình nhập mã / quét QR (UC01)
  if (!token) {
    return (
      <AuthView
        onAuthSuccess={(newToken) => {
          setToken(newToken);
        }}
        selectedLang={selectedLang}
        onSelectLang={setSelectedLang}
      />
    );
  }

  // Màn hình chính Client App (Du khách)
  return (
    <div className="flex flex-col h-screen bg-slate-100 select-none overflow-hidden font-sans">
      {/* Header cố định */}
      <header className="bg-amber-600 text-white px-4 py-2.5 flex items-center justify-between shadow-md z-20 shrink-0">
        <div className="flex items-center space-x-2">
          <span className="text-xl">⛩️</span>
          <div>
            <h1 className="text-xs sm:text-sm font-bold tracking-wide leading-tight">
              CHÙA LINH ỨNG
            </h1>
            <p className="text-[10px] text-amber-200">Thuyết Minh Đa Ngôn Ngữ</p>
          </div>
        </div>

        <div className="flex items-center space-x-2">
          {/* Đổi ngôn ngữ tức thì - KHÔNG gọi lại API (UC02) */}
          <LanguageSelector selectedLang={selectedLang} onSelectLang={setSelectedLang} />

          <button
            onClick={() => {
              clearStoredToken();
              setToken(null);
              setPois([]);
            }}
            className="text-[10px] bg-amber-700/60 hover:bg-amber-700 text-amber-100 px-2 py-1.5 rounded-full transition"
            title="Đổi vé / Đăng xuất"
          >
            Đổi vé
          </button>
        </div>
      </header>

      {/* Thông báo lỗi nếu không tải được POIs (UC02 E1) */}
      {errorMessage && (
        <div className="bg-red-500 text-white text-xs p-2 text-center flex items-center justify-center space-x-2 shrink-0">
          <span>{errorMessage}</span>
          <button
            onClick={() => window.location.reload()}
            className="underline font-bold"
          >
            Thử lại
          </button>
        </div>
      )}

      {/* Loading khi tải POIs lần đầu */}
      {loadingPOIs && (
        <div className="absolute inset-0 bg-white/80 backdrop-blur-sm z-50 flex flex-col items-center justify-center">
          <div className="w-12 h-12 border-4 border-amber-600 border-t-transparent rounded-full animate-spin mb-3"></div>
          <p className="text-sm font-semibold text-slate-700">Đang tải dữ liệu điểm tham quan Chùa Linh Ứng...</p>
          <p className="text-xs text-slate-400 mt-1">Dữ liệu được nạp 1 lần duy nhất cho toàn bộ hành trình</p>
        </div>
      )}

      {/* Main Content View */}
      <main className="flex-1 relative overflow-hidden">
        {activeTab === 'map' ? (
          <MapView pois={pois} routes={routes} selectedLang={selectedLang} />
        ) : (
          <ChatView />
        )}
      </main>

      {/* Bottom Navigation Bar (Mobile First) */}
      <nav className="bg-white border-t border-slate-200 px-6 py-2 flex items-center justify-around shadow-lg z-20 shrink-0">
        <button
          onClick={() => setActiveTab('map')}
          className={`flex flex-col items-center py-1 transition ${
            activeTab === 'map' ? 'text-amber-600 font-bold' : 'text-slate-400 hover:text-slate-600'
          }`}
        >
          <Map size={20} className={activeTab === 'map' ? 'stroke-[2.5]' : 'stroke-2'} />
          <span className="text-[10px] mt-0.5">Bản Đồ GPS</span>
        </button>

        <button
          onClick={() => setActiveTab('chat')}
          className={`flex flex-col items-center py-1 transition ${
            activeTab === 'chat' ? 'text-amber-600 font-bold' : 'text-slate-400 hover:text-slate-600'
          }`}
        >
          <MessageSquare size={20} className={activeTab === 'chat' ? 'stroke-[2.5]' : 'stroke-2'} />
          <span className="text-[10px] mt-0.5">Trợ Lý AI (RAG)</span>
        </button>

        <button
          onClick={() => navigateTo('/admin')}
          className="flex flex-col items-center py-1 text-slate-400 hover:text-slate-700 transition"
          title="Vào trang quản trị"
        >
          <Shield size={20} className="stroke-2" />
          <span className="text-[10px] mt-0.5">Quản Trị</span>
        </button>
      </nav>
    </div>
  );
}
