"use client";

import { createContext, useContext, useEffect, useState, ReactNode } from "react";
import type { Session } from "@supabase/supabase-js";
import { supabase } from "@/lib/supabase";

type User = { id: string; email: string };

type AuthContextValue = {
  user: User | null;
  loading: boolean;
  // needsConfirmation: Supabase has "Confirm email" turned on, so there's no session until they click the emailed link
  signup: (email: string, password: string) => Promise<{ needsConfirmation: boolean }>;
  login: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
};

const AuthContext = createContext<AuthContextValue | null>(null);

function toUser(session: Session | null): User | null {
  return session?.user ? { id: session.user.id, email: session.user.email ?? "" } : null;
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    supabase.auth.getSession().then(({ data }) => {
      setUser(toUser(data.session));
      setLoading(false);
    });
    const { data: subscription } = supabase.auth.onAuthStateChange((_event, session) => {
      setUser(toUser(session));
    });
    return () => subscription.subscription.unsubscribe();
  }, []);

  const signup = async (email: string, password: string) => {
    const { data, error } = await supabase.auth.signUp({ email, password });
    if (error) throw error;
    return { needsConfirmation: data.session === null };
  };

  const login = async (email: string, password: string) => {
    const { error } = await supabase.auth.signInWithPassword({ email, password });
    if (error) throw error;
  };

  const logout = async () => {
    await supabase.auth.signOut();
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
