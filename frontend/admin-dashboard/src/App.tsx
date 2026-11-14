import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import { ProtectedRoute } from './components/ProtectedRoute';
import { Layout } from './components/Layout';
import { Login } from './pages/Login';
import { Tickets } from './pages/Tickets';
import { POIManager } from './pages/POIManager';

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
              <Route path="/pois" element={<POIManager />} />
              <Route path="/pipeline" element={<div className="p-8 text-white">Giám sát tiến độ Pipeline (Đang hoàn thiện...)</div>} />
            </Route>
          </Route>

          <Route path="*" element={<Navigate to="/login" replace />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
};

export default App;
