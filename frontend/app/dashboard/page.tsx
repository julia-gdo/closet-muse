"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { TopNav } from "@/components/nav/TopNav";
import { BaseAvatar } from "@/components/avatar/BaseAvatar";
import { PlaceholderSlotGrid } from "@/components/dashboard/PlaceholderSlotGrid";
import { useAuth } from "@/lib/auth/AuthProvider";

export default function DashboardPage() {
  const { user, loading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!loading && !user) {
      router.replace("/login");
    }
  }, [loading, user, router]);

  if (loading || !user) {
    return <div className="flex-1 flex items-center justify-center text-ink/60">loading...</div>;
  }

  return (
    <div className="page-fade-in h-full flex flex-col bg-stripes overflow-hidden">
      <TopNav />
      <main className="flex-1 min-h-0 grid grid-cols-1 md:grid-cols-3 gap-16 px-8 pt-10 overflow-hidden">
        <section className="h-full min-h-0 flex flex-col gap-4">
          <h2 className="font-ringus text-stroke-white-thin text-4xl text-pink text-center md:text-left">
            Your Inspo
          </h2>
          <PlaceholderSlotGrid />
        </section>

        <section className="relative h-full min-h-0 flex justify-center">
          <div className="rounded-t-full bg-cream border-2 border-[#f8e8ee] w-full max-w-md h-full flex items-start justify-center pt-10">
            <BaseAvatar className="h-full aspect-[333/749]" />
          </div>
        </section>

        <section className="h-full min-h-0 flex flex-col gap-4">
          <h2 className="font-ringus text-stroke-white-thin text-4xl text-pink text-center md:text-left">
            Your Outfits
          </h2>
          <PlaceholderSlotGrid />
        </section>
      </main>
    </div>
  );
}
