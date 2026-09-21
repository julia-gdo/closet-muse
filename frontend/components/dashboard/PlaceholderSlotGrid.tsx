const SLOT_COUNT = 8;

export function PlaceholderSlotGrid() {
  return (
    <div className="grid grid-cols-2 content-start gap-4 overflow-y-auto flex-1 min-h-0 pr-1">
      {Array.from({ length: SLOT_COUNT }).map((_, i) => (
        <div key={i} className="aspect-[3/4] rounded-2xl border-2 border-dashed border-pink-light bg-white/50" />
      ))}
    </div>
  );
}
