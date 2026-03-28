/**
 * src/types/module.ts — TypeScript types for backend auto-render system.
 * Aligned with 3.frontend_auto_spec.md Section 10.
 */

// ── Backend field types ──────────────────────────────────────────────────────

export type SchemaFieldType =
  | "string"      // CharField, TextField
  | "integer"     // IntField
  | "decimal"     // DecimalField
  | "boolean"     // BooleanField
  | "datetime"    // DateTimeField
  | "date"        // DateField
  | "json"        // JSONField
  | "foreignkey"  // ForeignKeyField → async select
  | "m2m"         // ManyToManyField → multi-select
  | "image"       // ImageField → file upload + preview
  | "file"        // FileField → file upload
  | "selection"   // Enum/selection → select dropdown
  | "one2many"    // OneToManyField → inline table
  | "computed";   // ComputedField → readonly display

export type UIType =
  | "email"
  | "phone"
  | "currency"
  | "textarea"
  | "date"
  | "image"
  | "rich_text"
  | "color";

/** Field definition from /meta/schema */
export interface SchemaField {
  name: string;
  type: SchemaFieldType;
  label: string;
  required?: boolean;
  readonly?: boolean;
  default?: unknown;
  unique?: boolean;
  ui_type?: UIType;

  // String specific
  max_length?: number;

  // Decimal specific
  precision?: number;
  scale?: number;
  min_value?: number;
  max_value?: number;

  // Relation specific
  to?: string;           // target module name
  related_field?: string; // one2many → tên FK ở child trỏ về parent
  display_field?: string; // foreignkey → tên field hiển thị (override auto-detect)
  domain?: Record<string, any>;

  // Selection specific
  options?: string[];    // enum values

  // Computed / UI specific
  depends_on?: string;
  depends?: string[];
  store?: boolean;

  // Help / UX
  help_text?: string;    // placeholder or tooltip text
}

/** Module schema from /meta/schema */
export interface ModuleSchema {
  module: string;
  description: string;
  fields: SchemaField[];
  computed_fields?: SchemaField[];
  search_fields: string[];
  filter_fields: string[];
  sort_by: string | null;
  sort_desc: boolean;
  archive?: boolean;
  has_settings?: boolean;
  list_columns?: string[] | null;
}

/** Menu item from /modules/menu */
export interface MenuModule {
  name: string;
  menu_label: string;
  menu_icon: string;
  menu_parent: string | null;
  menu_sequence: number;
  has_settings: boolean;
}

/** System setting from /system-settings/ */
export interface SystemSetting {
  module_name: string;
  key: string;
  label: string;
  value: string;
  value_type: "string" | "integer" | "decimal" | "boolean" | "json";
}

// ── Legacy types — kept for backward compat with existing crud-page.tsx ──────

export type FieldType =
  | "text"
  | "email"
  | "phone"
  | "textarea"
  | "number"
  | "currency"
  | "boolean";

export interface FieldConfig {
  key: string;
  label: string;
  type: FieldType;
  required?: boolean;
  default?: string | number | boolean;
  showInTable?: boolean;
  placeholder?: string;
}

export interface ModuleConfig {
  name: string;
  label: string;
  fields: FieldConfig[];
}

/** Record from API */
export type ApiRecord = Record<string, unknown> & {
  id: number;
  created_at?: string | null;
  updated_at?: string | null;
};

/** Paginated list response */
export interface PaginatedResponse<T = ApiRecord> {
  total: number;
  skip: number;
  limit: number;
  items: T[];
}
