"use client";

import { useEffect, useState } from "react";
import { useFormContext, useFieldArray } from "react-hook-form";
import { Plus, Trash2, GripVertical } from "lucide-react";
import { schemaApi } from "@/lib/api";
import { ModuleSchema, SchemaField } from "@/types/module";
import { Button } from "@/components/ui/button";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { FieldBaseProps } from ".";
import { TextField } from "./TextField";
import { NumberField } from "./NumberField";
import { ForeignKeyField } from "./ForeignKeyField";
import { SelectField } from "./SelectField";
import { BooleanField } from "./BooleanField";

export function OneToManyField({ field, value, onChange }: FieldBaseProps) {
  const [childSchema, setChildSchema] = useState<ModuleSchema | null>(null);
  const { control, register, watch, setValue } = useFormContext();
  const { fields, append, remove } = useFieldArray({
    control,
    name: field.name,
  });

  useEffect(() => {
    if (field.to) {
      schemaApi.get(field.to).then(setChildSchema);
    }
  }, [field.to]);

  if (!childSchema) return <div className="p-4 text-center text-muted-foreground animate-pulse">Đang tải cấu trúc bảng con...</div>;

  // Filter fields to show in the inline table
  const columns = childSchema.fields.filter(f => 
    !["id", "created_at", "updated_at", "created_by", "updated_by", "active", "version"].includes(f.name) &&
    f.name !== field.related_field // Don't show the FK back to parent
  );

  const handleAddRow = () => {
    const defaultRow: any = {};
    columns.forEach(col => {
      if (col.default !== undefined) defaultRow[col.name] = col.default;
    });
    append(defaultRow);
  };

  return (
    <div className="space-y-4 border rounded-xl p-4 bg-muted/5">
      <div className="flex items-center justify-between">
        <h4 className="text-sm font-bold uppercase tracking-wider text-primary/70">{field.label}</h4>
        <Button type="button" variant="outline" size="sm" onClick={handleAddRow} className="h-8 gap-1.5 shadow-sm border-primary/20 hover:bg-primary/5">
          <Plus className="size-4" />
          Thêm dòng
        </Button>
      </div>

      <div className="rounded-lg border bg-background overflow-hidden shadow-sm">
        <Table>
          <TableHeader className="bg-muted/30">
            <TableRow>
              <TableHead className="w-10"></TableHead>
              {columns.map(col => (
                <TableHead key={col.name} className="text-[11px] font-bold uppercase tracking-tight py-2">
                  {col.label} {col.required && <span className="text-destructive">*</span>}
                </TableHead>
              ))}
              <TableHead className="w-10"></TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {fields.map((row, index) => (
              <TableRow key={row.id} className="group hover:bg-muted/10 transition-colors">
                <TableCell className="py-2">
                  <GripVertical className="size-4 text-muted-foreground/30 group-hover:text-muted-foreground/60 transition-colors cursor-grab" />
                </TableCell>
                
                {columns.map(col => (
                  <TableCell key={col.name} className="py-1.5 px-2">
                    <RowFieldRenderer 
                      field={col} 
                      rowPath={`${field.name}.${index}`}
                      rowIndex={index}
                      parentFieldName={field.name}
                    />
                  </TableCell>
                ))}

                <TableCell className="py-2">
                  <Button 
                    type="button" 
                    variant="ghost" 
                    size="icon" 
                    className="size-7 text-muted-foreground/40 hover:text-destructive hover:bg-destructive/5" 
                    onClick={() => remove(index)}
                  >
                    <Trash2 className="size-4" />
                  </Button>
                </TableCell>
              </TableRow>
            ))}
            {fields.length === 0 && (
              <TableRow>
                <TableCell colSpan={columns.length + 2} className="h-24 text-center text-muted-foreground italic text-sm">
                  Chưa có dữ liệu. Nhấn "Thêm dòng" để bắt đầu.
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </div>
    </div>
  );
}

/** Internal renderer for table cells to handle contextual dependencies */
function RowFieldRenderer({ field, rowPath, rowIndex, parentFieldName }: { field: SchemaField, rowPath: string, rowIndex: number, parentFieldName: string }) {
  const { watch, setValue } = useFormContext();
  const value = watch(`${rowPath}.${field.name}`);
  
  // Handle depends_on logic (e.g. Unit depends on Product)
  const dependencyFieldName = field.depends_on;
  const dependencyValue = dependencyFieldName ? watch(`${rowPath}.${dependencyFieldName}`) : null;

  const handleChange = (val: any) => {
    setValue(`${rowPath}.${field.name}`, val, { shouldDirty: true, shouldValidate: true });
  };

  // If this field depends on another field that is empty, we might want to disable it
  const isDisabled = !!(dependencyFieldName && !dependencyValue);

  // We could further filter options in ForeignKeyField if dependencyValue exists
  // For now, let's keep it simple and just render the right component
  
  const commonProps = {
    field,
    value,
    onChange: handleChange,
    disabled: isDisabled,
  };

  if (field.type === "foreignkey") return <ForeignKeyField {...commonProps} />;
  if (field.type === "integer" || field.type === "decimal") return <NumberField {...commonProps} />;
  if (field.type === "boolean") return <BooleanField {...commonProps} />;
  if (field.type === "selection") return <SelectField {...commonProps} />;
  
  return <TextField {...commonProps} />;
}
