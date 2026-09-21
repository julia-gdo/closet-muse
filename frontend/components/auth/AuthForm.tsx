"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { FormEvent, useState } from "react";
import { useAuth } from "@/lib/auth/AuthProvider";

type Mode = "login" | "signup";

const COPY: Record<Mode, { title: string; cta: string; switchPrompt: string; switchLabel: string; switchHref: string }> = {
  login: {
    title: "welcome back",
    cta: "log in",
    switchPrompt: "new here?",
    switchLabel: "build my wardrobe",
    switchHref: "/signup",
  },
  signup: {
    title: "build my wardrobe",
    cta: "sign up",
    switchPrompt: "already have an account?",
    switchLabel: "log in",
    switchHref: "/login",
  },
};

export function AuthForm({ mode }: { mode: Mode }) {
  const { login, signup } = useAuth();
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const copy = COPY[mode];

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault();
    setError(null);
    setNotice(null);
    setSubmitting(true);
    try {
      if (mode === "signup") {
        const { needsConfirmation } = await signup(email, password);
        if (needsConfirmation) {
          setNotice("Check your email for a confirmation link, then log in.");
          return;
        }
      } else {
        await login(email, password);
      }
      router.push("/dashboard");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong. Please try again.");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <main
      className="relative flex-1 flex items-center justify-center overflow-hidden px-6"
      style={{
        backgroundImage: "url(/assets/patterns/hanger_pattern2.png)",
        backgroundRepeat: "repeat",
      }}
    >
      <form
        onSubmit={handleSubmit}
        className="relative z-10 w-full max-w-lg aspect-square rounded-3xl bg-cream/90 border-2 border-dashed border-pink p-12 shadow-md flex flex-col justify-center gap-5"
      >
        <h1 className="font-playful text-5xl text-pink text-center">{copy.title}</h1>

        <label className="flex flex-col gap-1 text-sm text-ink/80">
          email
          <input
            type="email"
            required
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className="rounded-xl border border-pink-light bg-white px-4 py-2 text-ink focus:outline-none focus:border-pink"
          />
        </label>

        <label className="flex flex-col gap-1 text-sm text-ink/80">
          password
          <input
            type="password"
            required
            minLength={8}
            pattern={mode === "signup" ? ".*[0-9].*" : undefined}
            title={mode === "signup" ? "At least 8 characters, including one number" : undefined}
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="rounded-xl border border-pink-light bg-white px-4 py-2 text-ink focus:outline-none focus:border-pink"
          />
        </label>

        {error && <p className="text-sm text-red-600">{error}</p>}
        {notice && <p className="text-sm text-ink/80">{notice}</p>}

        <button
          type="submit"
          disabled={submitting}
          className="rounded-full bg-pink px-6 py-3 font-ringus text-2xl text-white shadow-sm hover:bg-pink/90 transition-colors disabled:opacity-60"
        >
          {submitting ? "..." : copy.cta}
        </button>

        <p className="text-center text-sm text-ink/70">
          {copy.switchPrompt}{" "}
          <Link href={copy.switchHref} className="text-pink font-medium hover:underline">
            {copy.switchLabel}
          </Link>
        </p>
      </form>
    </main>
  );
}
