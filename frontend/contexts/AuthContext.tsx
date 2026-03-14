import AsyncStorage from "@react-native-async-storage/async-storage";
import React, { createContext, useCallback, useContext, useEffect, useState } from "react";

const TOKEN_KEY = "polyglot_access_token";
const API_BASE_URL = process.env.EXPO_PUBLIC_API_BASE_URL ?? "http://localhost:8000/api/v1";

export type User = {
  id: number;
  email: string;
  native_language_id?: number | null;
  active_language_space_id?: number | null;
  is_verified: boolean;
  created_at: string;
};

async function parseJsonResponse(response: Response) {
  const body = await response.json().catch(() => ({}));
  if (!response.ok) {
    const detail = body?.detail || body?.message || "Request failed";
    throw new Error(typeof detail === "string" ? detail : JSON.stringify(detail));
  }
  return body;
}

type AuthContextValue = {
  user: User | null;
  token: string | null;
  loading: boolean;
  login: (accessToken: string) => Promise<void>;
  logout: () => Promise<void>;
  fetchMe: (accessToken: string) => Promise<void>;
};

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const fetchMe = useCallback(async (accessToken: string) => {
    const response = await fetch(`${API_BASE_URL}/me`, {
      headers: { Authorization: `Bearer ${accessToken}` },
    });
    const data = await parseJsonResponse(response);
    setUser(data);
  }, []);

  useEffect(() => {
    (async () => {
      const storedToken = await AsyncStorage.getItem(TOKEN_KEY);
      if (!storedToken) {
        setLoading(false);
        return;
      }
      setToken(storedToken);
      try {
        await fetchMe(storedToken);
      } catch {
        await AsyncStorage.removeItem(TOKEN_KEY);
        setToken(null);
        setUser(null);
      }
      setLoading(false);
    })();
  }, [fetchMe]);

  const login = useCallback(
    async (accessToken: string) => {
      await AsyncStorage.setItem(TOKEN_KEY, accessToken);
      setToken(accessToken);
      await fetchMe(accessToken);
    },
    [fetchMe]
  );

  const logout = useCallback(async () => {
    await AsyncStorage.removeItem(TOKEN_KEY);
    setToken(null);
    setUser(null);
  }, []);

  const value: AuthContextValue = { user, token, loading, login, logout, fetchMe };
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}

export { API_BASE_URL, parseJsonResponse };
