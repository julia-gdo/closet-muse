"use client";

import Link from "next/link";
import { useAuth } from "@/lib/auth/AuthProvider";

export default function LandingPage() {
  const { user, loading } = useAuth();
  const ctaLabel = user ? "my wardrobe" : "build my wardrobe";

  return (
    <main
      className="page-fade-in relative flex-1 flex items-center justify-center overflow-hidden"
      style={{
        backgroundImage: "url(/assets/patterns/hanger_pattern2.png)",
        backgroundRepeat: "repeat",
        backgroundSize: "1600px 900px",
      }}
    >
      <div className="relative z-10 flex flex-col items-center gap-8 px-6 text-center">
        <h1 className="font-playful text-stroke-white text-6xl text-pink drop-shadow-sm">Closet Muse</h1>
        <p className="text-stroke-white-thin max-w-xs text-pink">
          Digitize your wardrobe, save a look you love, and let us put together outfits from
          clothes you already own.
        </p>
        {/* invisible spacer keeping the same flow height the button used to take up,
            so the title/paragraph group above stays centered in the same spot */}
        {!loading && (
          <span aria-hidden className="invisible rounded-full px-10 py-4 text-2xl border-2">
            {ctaLabel}
          </span>
        )}
      </div>

      {!loading && (
        <Link
          href={user ? "/dashboard" : "/signup"}
          className="font-ringus absolute top-3/4 left-1/2 -translate-x-1/2 -translate-y-1/2 rounded-full bg-white px-10 py-4 text-2xl text-pink shadow-md border-2 border-pink hover:bg-pink hover:text-white transition-colors"
        >
          {ctaLabel}
        </Link>
      )}
    </main>
  );
}
