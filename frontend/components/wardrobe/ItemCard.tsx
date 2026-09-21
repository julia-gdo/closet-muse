"use client";

import Image from "next/image";
import { useDeleteWardrobeItem, useRetryBackgroundRemoval, WardrobeItem } from "@/lib/hooks/useWardrobeItems";
import { CutoutStatusBadge } from "@/components/wardrobe/CutoutStatusBadge";

export function ItemCard({ item }: { item: WardrobeItem }) {
  const retry = useRetryBackgroundRemoval();
  const del = useDeleteWardrobeItem();

  const imageUrl = item.cutout_image_url ?? item.original_image_url;

  return (
    <div className="relative aspect-[3/4] rounded-2xl border-2 border-dashed border-pink-light bg-white/50 overflow-hidden flex flex-col">
      <CutoutStatusBadge status={item.cutout_status} />
      <div className="relative flex-1">
        <Image src={imageUrl} alt={item.label ?? item.category} fill unoptimized className="object-contain p-2" />
      </div>
      <div className="px-2 pb-2 text-center">
        <p className="text-sm text-ink truncate">{item.label || item.clothing_type || item.category}</p>
        {item.style_tags.length > 0 && (
          <p className="text-xs text-ink/50 truncate">{item.style_tags.join(", ")}</p>
        )}
      </div>

      {item.cutout_status === "needs_fix" && (
        <div className="absolute inset-0 flex flex-col items-center justify-center gap-2 bg-cream/95 p-3 text-center">
          <p className="text-xs text-ink/70">
            Couldn&apos;t process this photo. Try better lighting, a plain background, and laying the item flat.
          </p>
          <button
            onClick={() => retry.mutate(item.id)}
            disabled={retry.isPending}
            className="rounded-full bg-pink px-4 py-1.5 text-xs text-white hover:bg-pink/90 transition-colors disabled:opacity-60"
          >
            {retry.isPending ? "retrying..." : "Retry Background Removal"}
          </button>
        </div>
      )}

      <button
        onClick={() => del.mutate(item.id)}
        aria-label="Delete item"
        className="absolute top-2 left-2 h-6 w-6 rounded-full bg-white/80 text-ink/60 text-xs hover:bg-white hover:text-red-600 transition-colors"
      >
        ✕
      </button>
    </div>
  );
}
