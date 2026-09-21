"use client";

import { createContext, useContext, useEffect, useState, ReactNode, useCallback } from "react";
import { apiJson, refreshAccessToken } from "@/lib/api";
import { setAccessToken } from "@/lib/auth/tokenStore";

type User = { id: string; email: string };

type AuthContextValue = {
  user: User | null;
  loading: boolean;
  signup: (email: string, password: string) => Promise<void>;
  login: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
};

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  const loadUser = useCallback(async () => {
    const me = await apiJson<User>("/auth/me").catch(() => null);
    setUser(me);
  }, []);

  useEffect(() => {
    (async () => {
      const refreshed = await refreshAccessToken();
      if (refreshed) {
        await loadUser();
      }
      setLoading(false);
    })();
  }, [loadUser]);

  const signup = async (email: string, password: string) => {
    const body = await apiJson<{ access_token: string }>("/auth/signup", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    });
    setAccessToken(body.access_token);
    await loadUser();
  };

  const login = async (email: string, password: string) => {
    const body = await apiJson<{ access_token: string }>("/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    });
    setAccessToken(body.access_token);
    await loadUser();
  };

  const logout = async () => {
    await apiJson("/auth/logout", { method: "POST" }).catch(() => undefined);
    setAccessToken(null);
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, loading, signup, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) {
    throw new Error("useAuth must be used within AuthProvider");
  }
  return ctx;
}
