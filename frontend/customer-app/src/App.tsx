import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import LanguageSelectPage from './pages/LanguageSelectPage';
import QRAuthPage from './pages/QRAuthPage';
import MapAndPOIListPage from './pages/MapAndPOIListPage';
import POIDetailPage from './pages/POIDetailPage';
import ChatbotPage from './pages/ChatbotPage';

export default function App() {
  return (
    <BrowserRouter>
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
