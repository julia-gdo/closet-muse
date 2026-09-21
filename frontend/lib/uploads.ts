import { apiJson } from "@/lib/api";

type CreateItemResponse = { item_id: string; upload_url: string };

export async function uploadWardrobeItem(file: File, category: string, label: string): Promise<string> {
  const { item_id, upload_url } = await apiJson<CreateItemResponse>("/wardrobe/items", {
    method: "POST",
    body: JSON.stringify({ category, content_type: file.type, label: label || null }),
  });

  // Direct browser -> R2 upload. Never passes through our API server.
  const putResponse = await fetch(upload_url, {
    method: "PUT",
    headers: { "Content-Type": file.type },
    body: file,
  });
  if (!putResponse.ok) {
    throw new Error("Upload to storage failed — please try again.");
  }

  await apiJson(`/wardrobe/items/${item_id}/confirm-upload`, { method: "POST" });
  return item_id;
}
