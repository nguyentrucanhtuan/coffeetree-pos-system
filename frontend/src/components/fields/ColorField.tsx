import { Input } from "@/components/ui/input";
import { FieldBaseProps } from ".";

export function ColorField({ field, value, onChange, disabled, readOnly, error }: FieldBaseProps) {
  return (
    <div className="flex items-center gap-3 w-full">
      <div 
        className="size-10 rounded-lg border shadow-sm shrink-0"
        style={{ backgroundColor: value || "#ffffff" }}
      />
      <Input
        id={field.name}
        type="color"
        value={value || "#ffffff"}
        onChange={(e) => onChange(e.target.value)}
        disabled={disabled || readOnly}
        className="w-16 h-10 p-1 cursor-pointer"
      />
      <Input
        type="text"
        value={value || "#ffffff"}
        onChange={(e) => onChange(e.target.value)}
        disabled={disabled || readOnly}
        placeholder="#hex"
        className={cn("flex-1 font-mono uppercase", error && "border-destructive")}
        maxLength={7}
      />
      {error && <p className="text-[10px] font-medium text-destructive">{error}</p>}
    </div>
  );
}

import { cn } from "@/lib/utils";
