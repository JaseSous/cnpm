import React, { createContext, useContext, useState } from 'react';
import { apiClient } from '../api/client';

export interface UserInfo {
  user_id: number;
  username: string;
  role: 'admin' | 'staff';
}

interface AuthContextType {
  token: string | null;
  user: UserInfo | null;
  isAuthenticated: boolean;
  login: (username: string, password: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [token, setToken] = useState<string | null>(() => sessionStorage.getItem('access_token'));
  const [user, setUser] = useState<UserInfo | null>(() => {
    const saved = sessionStorage.getItem('user_info');
    return saved ? JSON.parse(saved) : null;
  });

  const login = async (username: string, password: string) => {
    const res = await apiClient.post('/api/auth/login', { username, password });
    const { access_token, user_id, role, username: resUser } = res.data;

    const userInfo: UserInfo = { user_id, username: resUser, role };
    sessionStorage.setItem('access_token', access_token);
    sessionStorage.setItem('user_info', JSON.stringify(userInfo));

    setToken(access_token);
    setUser(userInfo);
  };

  const logout = () => {
    sessionStorage.removeItem('access_token');
    sessionStorage.removeItem('user_info');
    setToken(null);
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ token, user, isAuthenticated: !!token, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
