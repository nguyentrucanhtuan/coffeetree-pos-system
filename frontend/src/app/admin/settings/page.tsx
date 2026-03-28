"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { settingsApi } from "@/lib/api";

/**
 * src/app/admin/settings/page.tsx
 * 
 * Redirects to the first available module settings.
 */
export default function SettingsRedirectPage() {
  const router = useRouter();

  useEffect(() => {
    settingsApi.getAll()
      .then((all) => {
        const mods = Array.from(new Set(all.map(s => s.module_name))).filter(Boolean);
        if (mods.length > 0) {
          router.replace(`/admin/settings/${mods[0]}`);
        }
      })
      .catch(() => {
        // Fallback or error state
      });
  }, [router]);

  return (
    <div className="flex flex-col items-center justify-center min-h-[400px] gap-6">
      <div className="relative">
        <div className="size-16 border-4 border-primary/20 rounded-full" />
        <div className="absolute inset-0 size-16 border-4 border-primary border-t-transparent rounded-full animate-spin" />
      </div>
      <div className="text-muted-foreground font-bold text-sm tracking-widest uppercase">
        Đang tải cấu hình...
      </div>
    </div>
  );
}
