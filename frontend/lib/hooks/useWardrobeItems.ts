import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiJson } from "@/lib/api";

export type CutoutStatus = "awaiting_upload" | "pending" | "processing" | "done" | "failed" | "needs_fix";

export type WardrobeItem = {
  id: string;
  category: string;
  clothing_type: string | null;
  cutout_status: CutoutStatus;
  cutout_error: string | null;
  dominant_colors: string[];
  label: string | null;
  style_tags: string[];
  original_image_url: string;
  cutout_image_url: string | null;
  created_at: string;
  updated_at: string;
};

const IN_FLIGHT: CutoutStatus[] = ["pending", "processing"];

export function useWardrobeItems() {
  return useQuery({
    queryKey: ["wardrobeItems"],
    queryFn: () => apiJson<WardrobeItem[]>("/wardrobe/items"),
    refetchInterval: (query) => {
      const items = query.state.data;
      return items?.some((item) => IN_FLIGHT.includes(item.cutout_status)) ? 2000 : false;
    },
  });
}

export function useRetryBackgroundRemoval() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (itemId: string) =>
      apiJson<WardrobeItem>(`/wardrobe/items/${itemId}/retry-background-removal`, { method: "POST" }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["wardrobeItems"] }),
  });
}

export function useDeleteWardrobeItem() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (itemId: string) => apiJson<void>(`/wardrobe/items/${itemId}`, { method: "DELETE" }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["wardrobeItems"] }),
  });
}
