import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { FieldBaseProps } from ".";

export function TextField({ field, value, onChange, error, disabled, readOnly }: FieldBaseProps) {
  const inputType = field.ui_type === "email" ? "email" 
                  : field.ui_type === "phone" ? "tel" 
                  : "text";

  return (
    <div className="flex flex-col gap-1.5 w-full">
      <Input
        id={field.name}
        type={inputType}
        value={value ?? ""}
        onChange={(e) => onChange(e.target.value)}
        disabled={disabled || readOnly}
        placeholder={field.help_text || `Nhập ${field.label.toLowerCase()}...`}
        maxLength={field.max_length}
        className={error ? "border-destructive focus-visible:ring-destructive" : ""}
      />
      {error && <p className="text-[10px] font-medium text-destructive">{error}</p>}
    </div>
  );
}
