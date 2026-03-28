import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { FieldBaseProps } from ".";

export function SelectField({ field, value, onChange, disabled, readOnly, error }: FieldBaseProps) {
  const options = field.options || [];

  return (
    <div className="flex flex-col gap-1.5 w-full">
      <Select 
        value={value ?? ""} 
        onValueChange={onChange}
        disabled={disabled || readOnly}
      >
        <SelectTrigger className={cn("font-medium", error && "border-destructive")}>
          <SelectValue placeholder={field.help_text || `Chọn ${field.label.toLowerCase()}...`} />
        </SelectTrigger>
        <SelectContent>
          {options.map((opt) => (
            <SelectItem key={opt} value={opt}>
              {opt}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
      {error && <p className="text-[10px] font-medium text-destructive">{error}</p>}
    </div>
  );
}

import { cn } from "@/lib/utils";
