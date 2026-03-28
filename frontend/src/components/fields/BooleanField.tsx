import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { FieldBaseProps } from ".";

export function BooleanField({ field, value, onChange, disabled, readOnly }: FieldBaseProps) {
  const strVal = value === true ? "true" : value === false ? "false" : "";

  return (
    <div className="flex flex-col gap-1.5 w-full">
      <Select 
        value={strVal} 
        onValueChange={(v) => onChange(v === "true")}
        disabled={disabled || readOnly}
      >
        <SelectTrigger className="font-semibold">
          <SelectValue placeholder="Chọn..." />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="true">✅ Có / Bật</SelectItem>
          <SelectItem value="false">❌ Không / Tắt</SelectItem>
        </SelectContent>
      </Select>
    </div>
  );
}
