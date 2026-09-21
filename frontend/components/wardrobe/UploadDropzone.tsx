"use client";

import { useQueryClient } from "@tanstack/react-query";
import { ChangeEvent, DragEvent, FormEvent, useRef, useState } from "react";
import { uploadWardrobeItem } from "@/lib/uploads";

const CATEGORIES = ["top", "bottom", "dress", "shoes", "jacket", "accessory"] as const;

export function UploadDropzone() {
  const queryClient = useQueryClient();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [file, setFile] = useState<File | null>(null);
  const [category, setCategory] = useState<(typeof CATEGORIES)[number]>("top");
  const [label, setLabel] = useState("");
  const [dragging, setDragging] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const handleDrop = (event: DragEvent) => {
    event.preventDefault();
    setDragging(false);
    const dropped = event.dataTransfer.files?.[0];
    if (dropped) setFile(dropped);
  };

  const handleFileChange = (event: ChangeEvent<HTMLInputElement>) => {
    setFile(event.target.files?.[0] ?? null);
  };

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault();
    if (!file) return;
    setError(null);
    setSubmitting(true);
    try {
      await uploadWardrobeItem(file, category, label);
      setFile(null);
      setLabel("");
      if (fileInputRef.current) fileInputRef.current.value = "";
      await queryClient.invalidateQueries({ queryKey: ["wardrobeItems"] });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Upload failed. Please try again.");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <form
      onSubmit={handleSubmit}
      className="rounded-2xl border-2 border-dashed border-pink bg-white/60 p-6 flex flex-col gap-4"
    >
      <div
        onDragOver={(e) => {
          e.preventDefault();
          setDragging(true);
        }}
        onDragLeave={() => setDragging(false)}
        onDrop={handleDrop}
        onClick={() => fileInputRef.current?.click()}
        className={`rounded-xl border-2 border-dashed p-6 text-center cursor-pointer transition-colors ${
          dragging ? "border-pink bg-pink-light/30" : "border-pink-light"
        }`}
      >
        <input ref={fileInputRef} type="file" accept="image/jpeg,image/png,image/webp" className="hidden" onChange={handleFileChange} />
        <p className="text-sm text-ink/70">{file ? file.name : "Drop a photo here, or click to choose one"}</p>
      </div>

      <div className="flex flex-col sm:flex-row gap-3">
        <label className="flex-1 flex flex-col gap-1 text-sm text-ink/80">
          category
          <select
            value={category}
            onChange={(e) => setCategory(e.target.value as (typeof CATEGORIES)[number])}
            className="rounded-xl border border-pink-light bg-white px-3 py-2 text-ink"
          >
            {CATEGORIES.map((c) => (
              <option key={c} value={c}>
                {c}
              </option>
            ))}
          </select>
        </label>
        <label className="flex-1 flex flex-col gap-1 text-sm text-ink/80">
          label (optional)
          <input
            type="text"
            value={label}
            onChange={(e) => setLabel(e.target.value)}
            placeholder="e.g. blue chambray shirt"
            className="rounded-xl border border-pink-light bg-white px-3 py-2 text-ink"
          />
        </label>
      </div>

      {error && <p className="text-sm text-red-600">{error}</p>}

      <button
        type="submit"
        disabled={!file || submitting}
        className="font-ringus self-start rounded-full bg-pink px-6 py-2 text-lg text-white hover:bg-pink/90 transition-colors disabled:opacity-60"
      >
        {submitting ? "uploading..." : "add to wardrobe"}
      </button>
    </form>
  );
}
