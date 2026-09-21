"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { TopNav } from "@/components/nav/TopNav";
import { UploadDropzone } from "@/components/wardrobe/UploadDropzone";
import { ItemCard } from "@/components/wardrobe/ItemCard";
import { useWardrobeItems } from "@/lib/hooks/useWardrobeItems";
import { useAuth } from "@/lib/auth/AuthProvider";

const CATEGORIES = ["all", "top", "bottom", "dress", "shoes", "jacket", "accessory"] as const;

export default function WardrobePage() {
  const { user, loading } = useAuth();
  const router = useRouter();
  const [filter, setFilter] = useState<(typeof CATEGORIES)[number]>("all");
  const { data: items, isLoading } = useWardrobeItems();

  useEffect(() => {
    if (!loading && !user) {
      router.replace("/login");
    }
  }, [loading, user, router]);

  if (loading || !user) {
    return <div className="flex-1 flex items-center justify-center text-ink/60">loading...</div>;
  }

  const filtered = items?.filter((item) => filter === "all" || item.category === filter) ?? [];

  return (
    <div className="page-fade-in h-full flex flex-col bg-stripes overflow-hidden">
      <TopNav />
      <main className="flex-1 min-h-0 overflow-y-auto px-8 py-8 flex flex-col gap-6">
        <h1 className="font-playful text-stroke-white-thin text-4xl text-pink">Your Wardrobe</h1>

        <UploadDropzone />

        <div className="flex flex-wrap gap-2">
          {CATEGORIES.map((c) => (
            <button
              key={c}
              onClick={() => setFilter(c)}
              className={`rounded-full border px-4 py-1.5 text-sm capitalize transition-colors ${
                filter === c
                  ? "bg-pink text-white border-pink"
                  : "bg-white text-ink/70 border-pink-light hover:border-pink"
              }`}
            >
              {c}
            </button>
          ))}
        </div>

        {isLoading && <p className="text-ink/60">loading your wardrobe...</p>}

        {!isLoading && filtered.length === 0 && (
          <p className="text-ink/60">No items yet in this category — upload a photo above to get started.</p>
        )}

        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-4 pb-4">
          {filtered.map((item) => (
            <ItemCard key={item.id} item={item} />
          ))}
        </div>
      </main>
    </div>
  );
}
