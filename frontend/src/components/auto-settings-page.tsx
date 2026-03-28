"use client";

/**
 * src/components/auto-settings-page.tsx
 *
 * Side-nav Settings Page with Sub-route Navigation (Static Style).
 */

import { useEffect, useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { toast } from "sonner";
import { settingsApi } from "@/lib/api";
import type { SystemSetting } from "@/types/module";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Skeleton } from "@/components/ui/skeleton";
import { Boxes, Save, RotateCcw, ShieldCheck, Settings } from "lucide-react";
import { cn } from "@/lib/utils";
import { FieldRenderer } from "./fields";

export function AutoSettingsPage({ moduleName }: { moduleName: string }) {
  const pathname = usePathname();
  const [allSettings, setAllSettings] = useState<SystemSetting[]>([]);
  const [values, setValues] = useState<Record<string, string>>({});
  const [original, setOriginal] = useState<Record<string, string>>({});
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    setLoading(true);
    settingsApi.getAll()
      .then((all) => {
        setAllSettings(all);
        const vals: Record<string, string> = {};
        all.forEach(s => { vals[`${s.module_name}:${s.key}`] = s.value; });
        setValues(vals);
        setOriginal(vals);
      })
      .catch(() => toast.error("Không thể load cài đặt"))
      .finally(() => setLoading(false));
  }, []);

  const modules = Array.from(new Set(allSettings.map(s => s.module_name))).filter(Boolean);
  const currentSettings = allSettings.filter(s => s.module_name === moduleName);

  const handleSave = async () => {
    const changed = currentSettings.filter(s => {
      const fullKey = `${s.module_name}:${s.key}`;
      return values[fullKey] !== original[fullKey];
    });

    if (changed.length === 0) {
      toast.info(`Không có thay đổi cho ${moduleName}`);
      return;
    }

    setSaving(true);
    try {
      await Promise.all(
        changed.map((s) => settingsApi.update(moduleName, s.key, values[`${s.module_name}:${s.key}`]))
      );
      const nextOriginal = { ...original };
      changed.forEach(s => {
        const fullKey = `${s.module_name}:${s.key}`;
        nextOriginal[fullKey] = values[fullKey];
      });
      setOriginal(nextOriginal);
      toast.success(`Đã lưu cài đặt cho ${moduleName}`);
    } catch {
      toast.error(`Lưu thất bại cho ${moduleName}`);
    } finally {
      setSaving(false);
    }
  };

  const handleReset = () => {
    const next = { ...values };
    currentSettings.forEach(s => {
      const fullKey = `${s.module_name}:${s.key}`;
      next[fullKey] = original[fullKey];
    });
    setValues(next);
  };

  if (loading) {
    return (
      <div className="space-y-6 max-w-6xl px-4 py-10">
        <Skeleton className="h-10 w-48" />
        <Skeleton className="h-px w-full" />
        <div className="flex flex-col lg:flex-row gap-12">
          <div className="lg:w-1/5 space-y-1 shrink-0">
            {[1, 2, 3, 4].map(i => <Skeleton key={i} className="h-9 w-full" />)}
          </div>
          <div className="flex-1 space-y-6">
            <Skeleton className="h-8 w-64" />
            <Skeleton className="h-48 w-full" />
          </div>
        </div>
      </div>
    );
  }

  if (modules.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center p-20 border rounded-2xl border-dashed bg-muted/20 opacity-60 max-w-2xl mx-auto mt-10">
        <Settings className="size-12 mb-4 opacity-20" />
        <p className="text-lg font-medium">Chưa có cài đặt nào được cấu hình</p>
      </div>
    );
  }

  return (
    <div className="max-w-6xl px-4 py-10 space-y-6">
      {/* Page Header */}
      <div className="flex items-center justify-between">
        <div className="space-y-0.5">
          <h2 className="text-2xl font-bold tracking-tight">Cài đặt</h2>
          <p className="text-muted-foreground">
            Quản lý các tham số vận hành và cấu hình hệ thống CoffeeTree.
          </p>
        </div>
        <div className="flex items-center gap-2 text-primary font-bold text-xs uppercase tracking-widest bg-primary/5 px-3 py-1.5 rounded-full border border-primary/10">
          <ShieldCheck className="size-4" />
          Quản trị
        </div>
      </div>
      <Separator className="my-6" />

      <div className="flex flex-col lg:flex-row lg:space-x-12 lg:space-y-0">
        {/* Sidebar Nav */}
        <aside className="lg:w-1/5 shrink-0">
          <nav className="flex space-x-2 lg:flex-col lg:space-x-0 lg:space-y-1 overflow-x-auto pb-4 lg:pb-0 scrollbar-none">
            {modules.map((mod) => {
              const href = `/admin/settings/${mod}`;
              const isActive = pathname === href;
              return (
                <Link
                  key={mod}
                  href={href}
                  className={cn(
                    "inline-flex items-center whitespace-nowrap rounded-md text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring h-9 px-4 py-2 justify-start capitalize w-full",
                    isActive
                      ? "bg-muted font-bold text-foreground ring-1 ring-border/50"
                      : "text-muted-foreground hover:bg-muted/50 hover:underline"
                  )}
                >
                  <Boxes className={cn("mr-2 size-4", isActive ? "text-primary" : "opacity-40")} />
                  {mod.replace(/-/g, " ")}
                </Link>
              );
            })}
          </nav>
        </aside>

        {/* Content Area */}
        <div className="flex-1 lg:max-w-3xl">
          <div className="space-y-6">
            <div className="flex flex-col gap-1">
              <h3 className="text-xl font-bold capitalize tracking-tight text-primary/90">
                {moduleName.replace(/-/g, " ")}
              </h3>
              <p className="text-sm text-muted-foreground">
                Cập nhật các quy tắc và giá trị mặc định cho phân hệ <strong>{moduleName}</strong>.
              </p>
            </div>
            <Separator />

            <div key={moduleName} className="space-y-8">
              <div className="grid gap-1">
                {currentSettings.map((setting) => {
                  const fullKey = `${setting.module_name}:${setting.key}`;
                  return (
                    <div key={fullKey} className="space-y-3 p-4 rounded-xl border border-transparent hover:border-border/40 hover:bg-muted/3 transition-colors">
                      <div className="flex items-center justify-between">
                        <Label htmlFor={fullKey} className="text-sm font-bold tracking-tight text-foreground/80">
                          {setting.label}
                        </Label>
                        <code className="text-[10px] font-mono text-muted-foreground/40 font-bold uppercase tracking-tight">
                          {setting.key}
                        </code>
                      </div>

                      <div className="flex flex-col gap-2 p-2">
                        <FieldRenderer
                          field={{
                            name: fullKey,
                            label: setting.label,
                            type: setting.value_type === "string" ? "string" : (setting.value_type as any),
                            required: true,
                          } as any}
                          value={values[fullKey]}
                          onChange={(v: any) => setValues(p => ({ ...p, [fullKey]: String(v ?? "") }))}
                        />
                      </div>
                    </div>
                  );
                })}
              </div>

              <div className="flex items-center gap-4 pt-6 mt-4 border-t border-dashed">
                <Button
                  onClick={handleSave}
                  disabled={saving}
                  size="lg"
                  className="px-10 h-10 font-bold shadow-md active:scale-95 transition-all text-xs uppercase tracking-widest"
                >
                  {saving ? (
                    <RotateCcw className="size-4 animate-spin mr-2" />
                  ) : (
                    <Save className="size-4 mr-2" />
                  )}
                  Lưu cấu hình
                </Button>
                <Button
                  variant="ghost"
                  onClick={handleReset}
                  size="lg"
                  disabled={saving}
                  className="h-10 text-muted-foreground hover:text-foreground font-bold text-xs uppercase tracking-widest"
                >
                  Hủy thay đổi
                </Button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
