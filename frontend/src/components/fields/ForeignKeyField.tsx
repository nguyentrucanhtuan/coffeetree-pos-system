"use client";

import { useEffect, useState } from "react";
import { createApiModule } from "@/lib/api";
import { ApiRecord } from "@/types/module";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { FieldBaseProps } from ".";
import { cn } from "@/lib/utils";

export function ForeignKeyField({ field, value, onChange, disabled, readOnly, error }: FieldBaseProps) {
  const [options, setOptions] = useState<ApiRecord[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!field.to) return;
    setLoading(true);
    createApiModule(field.to)
      .listAll(field.domain || {})
      .then(setOptions)
      .catch((err) => console.error(`Lỗi tải dữ liệu cho ${field.to}:`, err))
      .finally(() => setLoading(false));
  }, [field.to, JSON.stringify(field.domain)]);

  if (loading) return <Skeleton className="h-9 w-full" />;

  const displayField = field.display_field || (options[0]
    ? Object.keys(options[0]).find(
        (k) => k === "name" || k === "title" || k === "label"
      ) ?? "id"
    : "id");

  return (
    <div className="flex flex-col gap-1.5 w-full">
      <Select 
        value={value ? String(value) : ""} 
        onValueChange={(v) => onChange(v ? Number(v) : null)}
        disabled={disabled || readOnly}
      >
        <SelectTrigger className={cn("font-medium", error && "border-destructive")}>
          <SelectValue placeholder={field.help_text || `Chọn ${field.label.toLowerCase()}...`} />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="">— Không chọn —</SelectItem>
          {options.map((opt) => (
            <SelectItem key={String(opt.id) + Math.random()} value={String(opt.id)}>
              {String(opt[displayField] ?? opt.id)}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
      {error && <p className="text-[10px] font-medium text-destructive">{error}</p>}
    </div>
  );
}
