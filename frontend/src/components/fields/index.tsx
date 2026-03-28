import { SchemaField } from "@/types/module";
import { TextField } from "./TextField";
import { NumberField } from "./NumberField";
import { BooleanField } from "./BooleanField";
import { SelectField } from "./SelectField";
import { ColorField } from "./ColorField";
import { RichTextField } from "./RichTextField";
import { ForeignKeyField } from "./ForeignKeyField";
import { OneToManyField } from "./OneToManyField";
import { MultiSelectField } from "./MultiSelectField";

export interface FieldBaseProps {
  field: SchemaField;
  value: any;
  onChange: (value: any) => void;
  error?: string;
  disabled?: boolean;
  readOnly?: boolean;
}

export type FieldComponent = React.ComponentType<FieldBaseProps>;

export const FieldMap: Record<string, FieldComponent> = {
  string: TextField,
  integer: NumberField,
  decimal: NumberField,
  boolean: BooleanField,
  selection: SelectField,
  foreignkey: ForeignKeyField,
  one2many: OneToManyField,
  rich_text: RichTextField,
  color: ColorField,
  m2m: MultiSelectField,
};

/**
 * Central component to render any field based on schema
 */
export function FieldRenderer(props: FieldBaseProps) {
  const { field } = props;
  
  // Custom logic for special UI types
  if (field.ui_type === "rich_text") {
    return <RichTextField {...props} />;
  }
  if (field.ui_type === "color") {
    return <ColorField {...props} />;
  }
  if (field.ui_type === "textarea" || field.type === "json") {
    // Falls back to TextField for now
  }

  const Component = FieldMap[field.type] || TextField;
  
  return <Component {...props} />;
}

export { TextField, NumberField, BooleanField, SelectField, ColorField, RichTextField, ForeignKeyField, OneToManyField };
