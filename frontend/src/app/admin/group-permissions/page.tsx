"use client";

/**
 * Permission Matrix Page — /admin/group-permissions
 *
 * Layout: Groups (columns) × Module+Action pairs (rows) with checkboxes.
 * Toggle creates or deletes a permission record.
 */

import { useEffect, useState, useCallback } from "react";
import { toast } from "sonner";
import { getAccessToken } from "@/lib/auth";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Button } from "@/components/ui/button";

// ── Types ──────────────────────────────────────────────────────────────────────

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

const ACTIONS = ["list", "read", "create", "update", "archive", "restore", "delete", "bulk"] as const;
type Action = typeof ACTIONS[number];

interface Group {
  id: number;
  name: string;
  description?: string;
}

interface Permission {
  id: number;
  group_id: number;
  module_name: string;
  action: string;
  allowed: boolean;
}

interface MenuModule {
  name: string;
  label: string;
}

// ── API helpers ────────────────────────────────────────────────────────────────

async function apiFetch<T>(path: string, options?: RequestInit): Promise<T> {
  const token = getAccessToken();
  const res = await fetch(`${API_URL}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    ...options,
  });
  if (res.status === 401 && typeof window !== "undefined") {
    window.location.href = "/login";
    throw new Error("Unauthorized");
  }
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || `HTTP ${res.status}`);
  }
  const json = await res.json();
  return json.data ?? json;
}

async function fetchGroups(): Promise<Group[]> {
  const data = await apiFetch<Group[]>("/groups/");
  return Array.isArray(data) ? data : [];
}

async function fetchPermissions(): Promise<Permission[]> {
  const data = await apiFetch<Permission[]>("/group-permissions/");
  return Array.isArray(data) ? data : [];
}

async function fetchModules(): Promise<MenuModule[]> {
  const data = await apiFetch<MenuModule[]>("/modules/menu");
  return Array.isArray(data) ? data : [];
}

async function createPermission(group_id: number, module_name: string, action: string, allowed: boolean) {
  return apiFetch("/group-permissions/", {
    method: "POST",
    body: JSON.stringify({ group_id, module_name, action, allowed }),
  });
}

async function deletePermission(id: number) {
  return apiFetch(`/group-permissions/${id}`, { method: "DELETE" });
}

async function updatePermission(id: number, allowed: boolean) {
  return apiFetch(`/group-permissions/${id}`, {
    method: "PUT",
    body: JSON.stringify({ allowed }),
  });
}

// ── Matrix key: "group_id:module:action" ──────────────────────────────────────

function permKey(group_id: number, module_name: string, action: string) {
  return `${group_id}:${module_name}:${action}`;
}

// ── Action label / color helpers ───────────────────────────────────────────────

const ACTION_COLORS: Record<Action, string> = {
  list:    "bg-blue-50 text-blue-700",
  read:    "bg-sky-50 text-sky-700",
  create:  "bg-green-50 text-green-700",
  update:  "bg-amber-50 text-amber-700",
  archive: "bg-orange-50 text-orange-700",
  restore: "bg-purple-50 text-purple-700",
  delete:  "bg-red-50 text-red-700",
  bulk:    "bg-gray-50 text-gray-700",
};

// ── Component ──────────────────────────────────────────────────────────────────

export default function GroupPermissionsPage() {
  const [groups, setGroups]           = useState<Group[]>([]);
  const [modules, setModules]         = useState<MenuModule[]>([]);
  const [perms, setPerms]             = useState<Map<string, Permission>>(new Map());
  const [loading, setLoading]         = useState(true);
  const [toggling, setToggling]       = useState<Set<string>>(new Set());
  const [selectedGroup, setSelectedGroup] = useState<number | "all">("all");

  const reload = useCallback(async () => {
    setLoading(true);
    try {
      const [g, m, p] = await Promise.all([fetchGroups(), fetchModules(), fetchPermissions()]);
      setGroups(g);
      setModules(m);
      const map = new Map<string, Permission>();
      for (const perm of p) {
        map.set(permKey(perm.group_id, perm.module_name, perm.action), perm);
      }
      setPerms(map);
    } catch (e: unknown) {
      toast.error(e instanceof Error ? e.message : "Lỗi tải dữ liệu");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { reload(); }, [reload]);

  const isChecked = (group_id: number, module_name: string, action: string): boolean => {
    const p = perms.get(permKey(group_id, module_name, action));
    return !!p?.allowed;
  };

  const handleToggle = async (group_id: number, module_name: string, action: string, checked: boolean) => {
    const key = permKey(group_id, module_name, action);
    if (toggling.has(key)) return;
    setToggling((prev) => new Set(prev).add(key));

    // Optimistic update
    setPerms((prev) => {
      const next = new Map(prev);
      const existing = next.get(key);
      if (existing) {
        next.set(key, { ...existing, allowed: checked });
      } else {
        next.set(key, { id: -1, group_id, module_name, action, allowed: checked });
      }
      return next;
    });

    try {
      const existing = perms.get(key);
      if (existing && existing.id !== -1) {
        if (!checked) {
          await deletePermission(existing.id);
          setPerms((prev) => { const next = new Map(prev); next.delete(key); return next; });
        } else {
          await updatePermission(existing.id, true);
        }
      } else if (checked) {
        const newPerm = await apiFetch<Permission>("/group-permissions/", {
          method: "POST",
          body: JSON.stringify({ group_id, module_name, action, allowed: true }),
        });
        setPerms((prev) => {
          const next = new Map(prev);
          next.set(key, newPerm);
          return next;
        });
      } else {
        setPerms((prev) => { const next = new Map(prev); next.delete(key); return next; });
      }
    } catch (e: unknown) {
      // rollback
      toast.error(e instanceof Error ? e.message : "Lỗi cập nhật permission");
      reload();
    } finally {
      setToggling((prev) => { const next = new Set(prev); next.delete(key); return next; });
    }
  };

  // Bulk: toggle entire group × module
  const handleToggleRow = async (module_name: string, checked: boolean) => {
    const visibleGroups = selectedGroup === "all" ? groups : groups.filter(g => g.id === selectedGroup);
    for (const g of visibleGroups) {
      for (const action of ACTIONS) {
        await handleToggle(g.id, module_name, action, checked);
      }
    }
  };

  const visibleGroups = selectedGroup === "all" ? groups : groups.filter(g => g.id === selectedGroup);

  if (loading) {
    return (
      <div className="space-y-3">
        <Skeleton className="h-10 w-full" />
        {[1,2,3,4].map(i => <Skeleton key={i} className="h-12 w-full" />)}
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold">🔐 Phân quyền nhóm</h1>
          <p className="text-sm text-muted-foreground">
            {groups.length} nhóm · {modules.length} module · click ô để bật/tắt quyền
          </p>
        </div>
        {/* Group filter */}
        <div className="flex items-center gap-2">
          <Button
            size="sm"
            variant={selectedGroup === "all" ? "default" : "outline"}
            onClick={() => setSelectedGroup("all")}
          >
            Tất cả nhóm
          </Button>
          {groups.map(g => (
            <Button
              key={g.id}
              size="sm"
              variant={selectedGroup === g.id ? "default" : "outline"}
              onClick={() => setSelectedGroup(g.id)}
            >
              {g.name}
            </Button>
          ))}
          <Button size="sm" variant="ghost" onClick={reload}>↺ Reload</Button>
        </div>
      </div>

      {/* Matrix table */}
      <div className="rounded-lg border overflow-auto max-h-[75vh]">
        <Table>
          <TableHeader className="sticky top-0 z-10 bg-background">
            <TableRow>
              <TableHead className="min-w-[160px] font-semibold">Module</TableHead>
              <TableHead className="min-w-[80px] font-semibold">Action</TableHead>
              {visibleGroups.map(g => (
                <TableHead key={g.id} className="text-center min-w-[100px]">
                  <span className="text-xs font-medium">{g.name}</span>
                </TableHead>
              ))}
            </TableRow>
          </TableHeader>
          <TableBody>
            {modules.length === 0 ? (
              <TableRow>
                <TableCell colSpan={2 + visibleGroups.length} className="text-center text-muted-foreground p-8">
                  Không có module nào được đăng ký.
                </TableCell>
              </TableRow>
            ) : (
              modules.flatMap((mod) =>
                ACTIONS.map((action, actionIdx) => {
                  const isFirstAction = actionIdx === 0;
                  const allChecked = visibleGroups.every(g => isChecked(g.id, mod.name, action));
                  return (
                    <TableRow
                      key={`${mod.name}-${action}`}
                      className={actionIdx % 2 === 0 ? "bg-muted/20" : ""}
                    >
                      {/* Module name — only show on first action row */}
                      <TableCell className={`font-medium text-sm ${isFirstAction ? "" : "text-transparent select-none"}`}>
                        {isFirstAction ? (
                          <div className="flex items-center gap-2">
                            <span>{mod.label}</span>
                            <Button
                              variant="ghost"
                              size="sm"
                              className="h-5 px-1 text-[10px] text-muted-foreground hover:text-foreground"
                              onClick={() => handleToggleRow(mod.name, !allChecked)}
                              title={allChecked ? "Bỏ tất cả" : "Chọn tất cả"}
                            >
                              {allChecked ? "✗ Bỏ hết" : "✓ Chọn hết"}
                            </Button>
                          </div>
                        ) : (
                          <span className="text-muted-foreground/30 text-xs">↳</span>
                        )}
                      </TableCell>

                      {/* Action badge */}
                      <TableCell>
                        <span className={`text-[11px] font-medium px-2 py-0.5 rounded ${ACTION_COLORS[action]}`}>
                          {action}
                        </span>
                      </TableCell>

                      {/* Checkboxes per group */}
                      {visibleGroups.map(g => {
                        const key = permKey(g.id, mod.name, action);
                        const checked = isChecked(g.id, mod.name, action);
                        const pending = toggling.has(key);
                        return (
                          <TableCell key={g.id} className="text-center">
                            <div className="flex justify-center">
                              <input
                                type="checkbox"
                                id={`perm-${g.id}-${mod.name}-${action}`}
                                checked={checked}
                                disabled={pending}
                                onChange={(e) => handleToggle(g.id, mod.name, action, e.target.checked)}
                                className={`h-4 w-4 rounded border-gray-300 text-primary cursor-pointer accent-primary ${pending ? "opacity-50 cursor-wait" : ""}`}
                              />
                            </div>
                          </TableCell>
                        );
                      })}
                    </TableRow>
                  );
                })
              )
            )}
          </TableBody>
        </Table>
      </div>

      {/* Legend */}
      <div className="flex flex-wrap gap-2 text-xs text-muted-foreground">
        {ACTIONS.map(a => (
          <span key={a} className={`px-2 py-0.5 rounded ${ACTION_COLORS[a]}`}>{a}</span>
        ))}
      </div>
    </div>
  );
}
