"use client";

import { useEffect, useState } from "react";
import { createApiModule } from "@/lib/api";
import { ApiRecord } from "@/types/module";
import { Skeleton } from "@/components/ui/skeleton";
import { ToggleGroup, ToggleGroupItem } from "@/components/ui/toggle-group";
import { FieldBaseProps } from ".";
import { cn } from "@/lib/utils";

export function MultiSelectField({ field, value, onChange, disabled, readOnly, error }: FieldBaseProps) {
  const [options, setOptions] = useState<ApiRecord[]>([]);
  const [loading, setLoading] = useState(false);

  // Ensure value is always an array
  const selectedIds = Array.isArray(value) ? value.map(v => String(v)) : [];

  useEffect(() => {
    if (!field.to) return;
    setLoading(true);
    createApiModule(field.to)
      .listAll(field.domain || {})
      .then(setOptions)
      .catch((err) => console.error(`Lỗi tải dữ liệu cho ${field.to}:`, err))
      .finally(() => setLoading(false));
  }, [field.to, JSON.stringify(field.domain)]);

  if (loading) return <Skeleton className="h-9 w-64" />;

  const displayField = field.display_field || (options[0]
    ? Object.keys(options[0]).find(
        (k) => k === "name" || k === "title" || k === "label"
      ) ?? "id"
    : "id");

  const handleValueChange = (newValues: string[]) => {
    onChange(newValues.map(v => Number(v)));
  };

  return (
    <div className="flex flex-col gap-2 w-full">
      <ToggleGroup
        {...({ type: "multiple" } as any)}
        variant="outline"
        size="sm"
        value={selectedIds}
        onValueChange={handleValueChange}
        disabled={disabled || readOnly}
        className="flex-wrap justify-start gap-1"
      >
        {options.map((opt) => (
          <ToggleGroupItem 
            key={String(opt.id)} 
            value={String(opt.id)}
            className="px-3 py-1 h-auto data-[state=on]:bg-primary data-[state=on]:text-primary-foreground"
          >
            {String(opt[displayField] ?? opt.id)}
          </ToggleGroupItem>
        ))}
        {options.length === 0 && !loading && (
          <p className="text-xs text-muted-foreground italic">Không có lựa chọn nào phù hợp</p>
        )}
      </ToggleGroup>
      {error && <p className="text-[10px] font-medium text-destructive">{error}</p>}
    </div>
  );
}
