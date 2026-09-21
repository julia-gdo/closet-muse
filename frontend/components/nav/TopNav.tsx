"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth/AuthProvider";

const NAV_LINKS = [
  { href: "/dashboard", label: "Dashboard" },
  { href: "/wardrobe", label: "Wardrobe" },
  { href: "/inspiration", label: "Inspiration" },
  { href: "/outfits/history", label: "Outfits" },
];

export function TopNav() {
  const { user, logout } = useAuth();
  const router = useRouter();

  const handleLogout = async () => {
    await logout();
    router.push("/login");
  };

  return (
    <header className="border-b border-pink-light bg-cream px-6 py-3 flex items-center justify-between">
      <Link href="/dashboard" className="font-playful text-3xl text-pink">
        Closet Muse
      </Link>
      <nav className="flex items-center gap-6">
        {NAV_LINKS.map((link) => (
          <Link key={link.href} href={link.href} className="text-ink/80 hover:text-pink transition-colors">
            {link.label}
          </Link>
        ))}
        {user && (
          <button onClick={handleLogout} className="text-ink/60 hover:text-pink transition-colors">
            Log out
          </button>
        )}
      </nav>
    </header>
  );
}
