import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import { ProtectedRoute } from './components/ProtectedRoute';
import { Layout } from './components/Layout';
import { Login } from './pages/Login';
import { Tickets } from './pages/Tickets';

export const App: React.FC = () => {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<Login />} />

          <Route element={<ProtectedRoute />}>
            <Route element={<Layout />}>
              <Route path="/" element={<Navigate to="/tickets" replace />} />
              <Route path="/tickets" element={<Tickets />} />
              {/* Route giữ chỗ cho POI và Pipeline ở Phase 2 */}
              <Route path="/pois" element={<div className="p-8 text-white">Quản lý điểm tham quan POI (Sẽ triển khai trong Phase 2)</div>} />
              <Route path="/pipeline" element={<div className="p-8 text-white">Giám sát tiến độ Pipeline (Sẽ triển khai trong Phase 2)</div>} />
            </Route>
          </Route>

          <Route path="*" element={<Navigate to="/login" replace />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
};

export default App;
