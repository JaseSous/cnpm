import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';

export default function App() {
  return (
    <BrowserRouter>
      <div className="min-h-screen bg-amber-50/40 text-stone-800 font-sans antialiased max-w-md mx-auto shadow-2xl relative flex flex-col">
        <Routes>
          <Route path="/" element={<div className="p-4 text-center">Khởi tạo ứng dụng du khách Chùa Linh Ứng</div>} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </div>
    </BrowserRouter>
  );
}
