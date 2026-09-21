import type { CutoutStatus } from "@/lib/hooks/useWardrobeItems";

const LABELS: Record<CutoutStatus, string> = {
  awaiting_upload: "uploading...",
  pending: "processing...",
  processing: "processing...",
  done: "ready",
  failed: "failed",
  needs_fix: "needs a fix",
};

const STYLES: Record<CutoutStatus, string> = {
  awaiting_upload: "bg-white text-ink/60 border-pink-light",
  pending: "bg-white text-ink/60 border-pink-light",
  processing: "bg-white text-ink/60 border-pink-light",
  done: "bg-pink text-white border-pink",
  failed: "bg-red-100 text-red-700 border-red-300",
  needs_fix: "bg-red-100 text-red-700 border-red-300",
};

export function CutoutStatusBadge({ status }: { status: CutoutStatus }) {
  if (status === "done") return null;
  return (
    <span className={`absolute top-2 right-2 rounded-full border px-2 py-0.5 text-xs ${STYLES[status]}`}>
      {LABELS[status]}
    </span>
  );
}
