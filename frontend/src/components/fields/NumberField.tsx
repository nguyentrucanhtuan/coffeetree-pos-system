import { Input } from "@/components/ui/input";
import { FieldBaseProps } from ".";

export function NumberField({ field, value, onChange, error, disabled, readOnly }: FieldBaseProps) {
  const step = field.type === "decimal" 
             ? (field.scale ? Math.pow(10, -field.scale) : 0.01) 
             : 1;

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const val = e.target.value === "" ? null : Number(e.target.value);
    onChange(val);
  };

  return (
    <div className="flex flex-col gap-1.5 w-full">
      <Input
        id={field.name}
        type="number"
        step={step}
        value={value ?? ""}
        onChange={handleChange}
        disabled={disabled || readOnly}
        placeholder={field.help_text || `Nhập số ${field.label.toLowerCase()}...`}
        className={error ? "border-destructive focus-visible:ring-destructive" : "font-mono"}
      />
      {error && <p className="text-[10px] font-medium text-destructive">{error}</p>}
    </div>
  );
}
