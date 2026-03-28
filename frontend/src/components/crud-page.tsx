"use client";

/**
 * src/components/crud-page.tsx
 *
 * SmartCrudPage — schema-driven CRUD UI (Dashboard-01 Style)
 */

import * as React from "react";
import { useCallback, useEffect, useMemo, useState } from "react";
import {
  flexRender,
  getCoreRowModel,
  getPaginationRowModel,
  getSortedRowModel,
  useReactTable,
  type ColumnDef,
  type SortingState,
  type VisibilityState,
} from "@tanstack/react-table";
import { toast } from "sonner";

import { useIsMobile } from "@/hooks/use-mobile";
import { createApiModule } from "@/lib/api";
import type { ApiRecord, ModuleSchema, SchemaField } from "@/types/module";

import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";
import { Badge } from "@/components/ui/badge";
import { Button, buttonVariants } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import {
  Drawer,
  DrawerClose,
  DrawerContent,
  DrawerDescription,
  DrawerFooter,
  DrawerHeader,
  DrawerTitle,
  DrawerTrigger,
} from "@/components/ui/drawer";
import {
  DropdownMenu,
  DropdownMenuCheckboxItem,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectGroup,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Separator } from "@/components/ui/separator";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Textarea } from "@/components/ui/textarea";

import {
  Columns3Icon,
  ChevronDownIcon,
  PlusIcon,
  ChevronsLeftIcon,
  ChevronLeftIcon,
  ChevronRightIcon,
  ChevronsRightIcon,
  EllipsisVerticalIcon,
  ArchiveIcon,
  ArchiveRestoreIcon,
  PencilIcon,
  Trash2Icon,
  SearchIcon,
  XIcon,
} from "lucide-react";

import { useForm, FormProvider, useFormContext } from "react-hook-form";
import { FieldRenderer } from "./fields";
import { cn } from "@/lib/utils";

// ── Constants ─────────────────────────────────────────────────────────────────

const ALWAYS_HIDDEN = ["created_by", "updated_by", "version"];
const DEFAULT_PAGE_SIZE = 10;

// ── Helpers ────────────────────────────────────────────────────────────────────

function getTableFields(schema: ModuleSchema): SchemaField[] {
  if (schema.list_columns?.length) {
    return schema.list_columns
      .map((name) => schema.fields.find((f) => f.name === name))
      .filter(Boolean) as SchemaField[];
  }
  return schema.fields.filter(
    (f) => !ALWAYS_HIDDEN.includes(f.name) && f.name !== "id"
  );
}

function getFormFields(schema: ModuleSchema): SchemaField[] {
  return schema.fields.filter(
    (f) =>
      !f.readonly &&
      f.name !== "id" &&
      !["created_by", "updated_by", "version"].includes(f.name)
  );
}

function formatCellValue(
  value: unknown,
  field: SchemaField,
  record?: ApiRecord
): React.ReactNode {
  if (value === null || value === undefined)
    return <span className="text-muted-foreground">—</span>;

  if (field.type === "foreignkey") {
    const relKey = field.name.replace(/_id$/, "");
    const related = record?.[relKey] as
      | Record<string, unknown>
      | undefined;
    if (related) {
      const display =
        (related.name ??
          related.title ??
          related.label ??
          related.id) as string;
      return <span className="text-sm">{display}</span>;
    }
    return <span className="text-sm">{String(value)}</span>;
  }

  if (field.type === "boolean") {
    return (
      <Badge variant="outline" className="px-1.5 text-muted-foreground">
        {value ? "✅ Có" : "❌ Không"}
      </Badge>
    );
  }

  if (field.type === "decimal" && field.ui_type === "currency") {
    const num = parseFloat(String(value));
    return isNaN(num) ? String(value) : num.toLocaleString("vi-VN") + " ₫";
  }

  if (field.type === "datetime" && typeof value === "string") {
    try {
      return new Date(value).toLocaleString("vi-VN");
    } catch {
      return String(value);
    }
  }

  if (field.type === "date" && typeof value === "string") {
    return value;
  }

  if (field.type === "image" && typeof value === "string") {
    return (
      <img src={value} alt="" className="h-10 w-10 rounded object-cover" />
    );
  }

  if (field.type === "selection" && typeof value === "string") {
    return (
      <Badge variant="outline" className="px-1.5 text-muted-foreground">
        {value}
      </Badge>
    );
  }

  return String(value);
}

// ── Filter Selection ────────────────────────────────────────────────────────────

function FkFilter({
  field,
  value,
  onChange,
}: {
  field: SchemaField;
  value: string;
  onChange: (v: string) => void;
}) {
  const [options, setOptions] = useState<ApiRecord[]>([]);
  const [ready, setReady] = useState(false);
  useEffect(() => {
    if (!field.to) return;
    createApiModule(field.to)
      .listAll()
      .then(setOptions)
      .catch(() => {})
      .finally(() => setReady(true));
  }, [field.to]);
  const displayKey =
    ready && options.length > 0
      ? Object.keys(options[0]).find((k) => k === "name" || k === "title") ??
        "id"
      : "id";
  return (
    <Select value={value} onValueChange={(v) => onChange(v ?? "")}>
      <SelectTrigger className="w-40" size="sm">
        <SelectValue placeholder={field.label} />
      </SelectTrigger>
      <SelectContent>
        <SelectItem value="">Tất cả</SelectItem>
        {options.map((opt) => (
          <SelectItem key={String(opt.id)} value={String(opt.id)}>
            {String(opt[displayKey] ?? opt.id)}
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  );
}

function FilterRow({
  schema,
  filters,
  onFilterChange,
}: {
  schema: ModuleSchema;
  filters: Record<string, string>;
  onFilterChange: (key: string, value: string) => void;
}) {
  const filterFields = schema.filter_fields
    .map((name) => schema.fields.find((f) => f.name === name))
    .filter(Boolean) as SchemaField[];

  if (filterFields.length === 0) return null;

  return (
    <div className="flex flex-wrap gap-2 items-center px-4 lg:px-6">
      {filterFields.map((field) => {
        if (field.type === "boolean") {
          return (
            <Select
              key={field.name}
              value={filters[field.name] ?? ""}
              onValueChange={(v) => onFilterChange(field.name, v ?? "")}
            >
              <SelectTrigger className="w-40" size="sm">
                <SelectValue placeholder={field.label} />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="">Tất cả</SelectItem>
                <SelectItem value="true">✅ Có</SelectItem>
                <SelectItem value="false">❌ Không</SelectItem>
              </SelectContent>
            </Select>
          );
        }

        if (field.type === "selection" && field.options) {
          return (
            <Select
              key={field.name}
              value={filters[field.name] ?? ""}
              onValueChange={(v) => onFilterChange(field.name, v ?? "")}
            >
              <SelectTrigger className="w-40" size="sm">
                <SelectValue placeholder={field.label} />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="">Tất cả</SelectItem>
                {field.options.map((opt) => (
                  <SelectItem key={opt} value={opt}>
                    {opt}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          );
        }

        if (field.type === "foreignkey" && field.to) {
          return (
            <FkFilter
              key={field.name}
              field={field}
              value={filters[field.name] ?? ""}
              onChange={(v) => onFilterChange(field.name, v)}
            />
          );
        }

        if (field.type === "integer" || field.type === "decimal") {
          return (
            <div key={field.name} className="flex items-center gap-1">
              <span className="text-xs text-muted-foreground">
                {field.label}:
              </span>
              <Input
                className="w-24 h-8 text-sm"
                type="number"
                placeholder="Min"
                value={filters[`${field.name}[>=]`] ?? ""}
                onChange={(e) =>
                  onFilterChange(`${field.name}[>=]`, e.target.value)
                }
              />
              <span className="text-muted-foreground">—</span>
              <Input
                className="w-24 h-8 text-sm"
                type="number"
                placeholder="Max"
                value={filters[`${field.name}[<=]`] ?? ""}
                onChange={(e) =>
                  onFilterChange(`${field.name}[<=]`, e.target.value)
                }
              />
            </div>
          );
        }

        if (field.type === "date" || field.type === "datetime") {
          return (
            <div key={field.name} className="flex items-center gap-1">
              <span className="text-xs text-muted-foreground">
                {field.label}:
              </span>
              <Input
                className="w-32 h-8 text-sm"
                type="date"
                value={filters[`${field.name}[>=]`] ?? ""}
                onChange={(e) =>
                  onFilterChange(`${field.name}[>=]`, e.target.value)
                }
              />
              <span className="text-muted-foreground">—</span>
              <Input
                className="w-32 h-8 text-sm"
                type="date"
                value={filters[`${field.name}[<=]`] ?? ""}
                onChange={(e) =>
                  onFilterChange(`${field.name}[<=]`, e.target.value)
                }
              />
            </div>
          );
        }

        return null;
      })}
      {Object.values(filters).some(Boolean) && (
        <Button
          variant="ghost"
          size="sm"
          className="h-8 text-xs"
          onClick={() => {
            for (const key of Object.keys(filters)) onFilterChange(key, "");
          }}
        >
          <XIcon className="mr-1 size-3" />
          Reset
        </Button>
      )}
    </div>
  );
}

// ── Record Drawer — Form inside Drawer ─────────────────────────────────────────

function RecordDrawer({
  open,
  onOpenChange,
  title,
  description,
  formFields,
  onSubmit,
  submitLabel,
  isMobile,
}: {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  title: string;
  description: string;
  formFields: SchemaField[];
  onSubmit: () => void;
  submitLabel: string;
  isMobile: boolean;
}) {
  const methods = useFormContext();

  return (
    <Drawer
      open={open}
      onOpenChange={onOpenChange}
      direction={isMobile ? "bottom" : "right"}
    >
      <DrawerContent className={cn("max-h-[95vh]", !isMobile && "w-[60vw] ml-auto")}>
        <DrawerHeader className="gap-1">
          <DrawerTitle>{title}</DrawerTitle>
          <DrawerDescription>{description}</DrawerDescription>
        </DrawerHeader>
        <div className="flex flex-col gap-4 overflow-y-auto px-4 text-sm pb-10 scrollbar-none">
          <Separator />
          <form
            id="smart-crud-form"
            className="flex flex-col gap-4"
            onSubmit={(e) => {
              e.preventDefault();
              onSubmit();
            }}
          >
            {formFields.map((field) => (
              <div key={field.name} className="flex flex-col gap-2">
                <Label htmlFor={field.name} className="font-bold tracking-tight mb-1">
                  {field.label}
                  {field.required && (
                    <span className="text-destructive ml-1">*</span>
                  )}
                </Label>
                <FieldRenderer
                  field={field}
                  value={methods.watch(field.name)}
                  onChange={(v) => methods.setValue(field.name, v, { shouldDirty: true, shouldValidate: true })}
                  error={methods.formState.errors[field.name]?.message as string}
                />
              </div>
            ))}
          </form>
        </div>
        <DrawerFooter className="pt-4 border-t bg-muted/5">
          <Button onClick={onSubmit} size="lg" className="font-bold uppercase tracking-widest text-xs h-10 shadow-md">{submitLabel}</Button>
          <DrawerClose
            className={cn(buttonVariants({ variant: "outline", size: "lg" }), "font-bold uppercase tracking-widest text-xs h-10")}
          >
            Huỷ
          </DrawerClose>
        </DrawerFooter>
      </DrawerContent>
    </Drawer>
  );
}

// ── SmartCrudPage ──────────────────────────────────────────────────────────────

interface SmartCrudPageProps {
  schema: ModuleSchema;
  overrideLabel?: string;
}

export function SmartCrudPage({ schema, overrideLabel }: SmartCrudPageProps) {
  const label = overrideLabel || schema.description || schema.module;
  const api = useMemo(() => createApiModule(schema.module), [schema.module]);
  const isMobile = useIsMobile();

  const tableFields = useMemo(() => getTableFields(schema), [schema]);
  const formFields = useMemo(() => getFormFields(schema), [schema]);

  // ── State ────────────────────────────────────────────────────────────────────
  const [records, setRecords] = useState<ApiRecord[]>([]);
  const [total, setTotal] = useState(0);
  const [skip, setSkip] = useState(0);
  const [pageSize, setPageSize] = useState(DEFAULT_PAGE_SIZE);
  const [search, setSearch] = useState("");
  const [filters, setFilters] = useState<Record<string, string>>({});
  const [withArchived, setWithArchived] = useState(false);
  const [loading, setLoading] = useState(false);
  const [listError, setListError] = useState<string | null>(null);

  // Form state
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [editing, setEditing] = useState<ApiRecord | null>(null);

  // Confirmation dialogs
  const [deleteTarget, setDeleteTarget] = useState<ApiRecord | null>(null);
  const [archiveTarget, setArchiveTarget] = useState<ApiRecord | null>(null);

  // Table state
  const [sorting, setSorting] = useState<SortingState>([]);
  const [columnVisibility, setColumnVisibility] = useState<VisibilityState>({});
  const [rowSelection, setRowSelection] = useState({});

  const methods = useForm({
    defaultValues: {},
  });

  // ── Fetch ────────────────────────────────────────────────────────────────────
  const fetchRecords = useCallback(async () => {
    setLoading(true);
    try {
      const params: Record<string, unknown> = { skip, limit: pageSize };
      if (search) params.search = search;
      if (withArchived) params.with_archived = true;
      for (const [k, v] of Object.entries(filters)) {
        if (v !== "") params[k] = v;
      }
      const res = await api.list(params);
      setRecords(res.items ?? []);
      setTotal(res.total ?? 0);
      setListError(null);
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : "Lỗi không xác định";
      setListError(msg);
    } finally {
      setLoading(false);
    }
  }, [api, skip, pageSize, search, filters, withArchived]);

  useEffect(() => {
    fetchRecords();
  }, [fetchRecords]);

  // ── Handlers ─────────────────────────────────────────────────────────────────
  const openCreate = () => {
    setEditing(null);
    const defaults: Record<string, unknown> = {};
    for (const f of formFields) {
      if (f.default !== undefined) defaults[f.name] = f.default;
      if (f.type === "one2many") defaults[f.name] = [];
    }
    methods.reset(defaults);
    setDrawerOpen(true);
  };

  const openEdit = (record: ApiRecord) => {
    setEditing(record);
    methods.reset({ ...record });
    setDrawerOpen(true);
  };

  const handleSubmit = async () => {
    const data = methods.getValues();
    try {
      if (editing) {
        await api.update(editing.id, data);
        toast.success("Cập nhật thành công");
      } else {
        await api.create(data);
        toast.success("Tạo thành công");
      }
      setDrawerOpen(false);
      fetchRecords();
    } catch (e: unknown) {
      toast.error(e instanceof Error ? e.message : "Lỗi khi lưu");
    }
  };

  const handleDelete = async () => {
    if (!deleteTarget) return;
    try {
      await api.delete(deleteTarget.id);
      toast.success("Đã xóa vĩnh viễn");
      setDeleteTarget(null);
      fetchRecords();
    } catch (e: unknown) {
      toast.error(e instanceof Error ? e.message : "Lỗi khi xóa");
    }
  };

  const handleArchive = async () => {
    if (!archiveTarget) return;
    try {
      await api.archive(archiveTarget.id);
      toast.success("Đã lưu trữ");
      setArchiveTarget(null);
      fetchRecords();
    } catch (e: unknown) {
      toast.error(e instanceof Error ? e.message : "Lỗi khi lưu trữ");
    }
  };

  const handleRestore = async (record: ApiRecord) => {
    try {
      await api.restore(record.id);
      toast.success("Đã khôi phục");
      fetchRecords();
    } catch (e: unknown) {
      toast.error(e instanceof Error ? e.message : "Lỗi khi khôi phục");
    }
  };

  const handleFilterChange = (key: string, value: string) => {
    setFilters((prev) => ({ ...prev, [key]: value }));
    setSkip(0);
  };

  const isActive = (record: ApiRecord) => record.active !== false;

  // ── Build TanStack columns ────────────────────────────────────────────────────

  const columns = useMemo<ColumnDef<ApiRecord>[]>(() => {
    const cols: ColumnDef<ApiRecord>[] = [];

    // 1. Checkbox select column
    cols.push({
      id: "select",
      header: ({ table }) => (
        <div className="flex items-center justify-center">
          <Checkbox
            checked={table.getIsAllPageRowsSelected()}
            indeterminate={
              table.getIsSomePageRowsSelected() &&
              !table.getIsAllPageRowsSelected()
            }
            onCheckedChange={(value) =>
              table.toggleAllPageRowsSelected(!!value)
            }
            aria-label="Select all"
          />
        </div>
      ),
      cell: ({ row }) => (
        <div className="flex items-center justify-center">
          <Checkbox
            checked={row.getIsSelected()}
            onCheckedChange={(value) => row.toggleSelected(!!value)}
            aria-label="Select row"
          />
        </div>
      ),
      enableSorting: false,
      enableHiding: false,
    });

    // 2. Data columns — first column is clickable to open edit drawer
    tableFields.forEach((field, idx) => {
      cols.push({
        accessorKey: field.name,
        header: field.label,
        cell: ({ row }) => {
          const record = row.original;
          let displayValue = record[field.name];

          // FK eager load
          if (field.type === "foreignkey") {
            const relKey = field.name.replace(/_id$/, "");
            const related = record[relKey] as
              | Record<string, unknown>
              | undefined;
            if (related) {
              displayValue = (related.name ??
                related.title ??
                related.label ??
                related.id) as unknown;
            }
          }

          // First column is clickable
          if (idx === 0) {
            return (
              <Button
                variant="link"
                className="w-fit px-0 text-left text-foreground"
                onClick={() => openEdit(record)}
              >
                {formatCellValue(displayValue, field, record)}
              </Button>
            );
          }

          return formatCellValue(displayValue, field, record);
        },
        enableHiding: idx !== 0, // Can't hide the first column
      });
    });

    // 3. Actions column — DropdownMenu
    cols.push({
      id: "actions",
      header: () => null,
      cell: ({ row }) => {
        const record = row.original;
        const archived = !isActive(record);

        return (
          <DropdownMenu>
            <DropdownMenuTrigger
              className={cn(
                buttonVariants({ variant: "ghost", size: "icon" }),
                "h-8 w-8 border border-input transition-colors hover:bg-muted"
              )}
            >
              <EllipsisVerticalIcon className="size-4" />
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end" className="w-40">
              {!archived && (
                <DropdownMenuItem onClick={() => openEdit(record)}>
                  <PencilIcon className="mr-2 size-3.5" />
                  Sửa
                </DropdownMenuItem>
              )}
              {schema.archive && !archived && (
                <DropdownMenuItem onClick={() => setArchiveTarget(record)}>
                  <ArchiveIcon className="mr-2 size-3.5" />
                  Lưu trữ
                </DropdownMenuItem>
              )}
              {archived && (
                <DropdownMenuItem onClick={() => handleRestore(record)}>
                  <ArchiveRestoreIcon className="mr-2 size-3.5" />
                  Khôi phục
                </DropdownMenuItem>
              )}
              <DropdownMenuSeparator />
              <DropdownMenuItem
                className="text-destructive focus:text-destructive"
                onClick={() => setDeleteTarget(record)}
              >
                <Trash2Icon className="mr-2 size-3.5" />
                Xóa vĩnh viễn
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        );
      },
    });

    return cols;
  }, [tableFields, openEdit, schema.archive]);

  const table = useReactTable({
    data: records,
    columns,
    state: {
      sorting,
      columnVisibility,
      rowSelection,
    },
    enableRowSelection: true,
    onRowSelectionChange: setRowSelection,
    onSortingChange: setSorting,
    onColumnVisibilityChange: setColumnVisibility,
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
    getPaginationRowModel: getPaginationRowModel(),
  });

  return (
    <FormProvider {...methods}>
      <div className="flex h-full flex-col gap-4">
        <div className="flex items-center justify-between px-4 pt-4 lg:px-6">
          <div className="flex flex-col gap-1">
            <h1 className="text-2xl font-bold tracking-tight">{label}</h1>
            <p className="text-sm text-muted-foreground">
              Quản lý danh sách {label.toLowerCase()} và các thông tin liên quan.
            </p>
          </div>
          <div className="flex items-center gap-2">
            {schema.archive && (
              <Button
                variant="outline"
                size="sm"
                className={cn("h-8 gap-1.5", withArchived && "bg-muted")}
                onClick={() => setWithArchived(!withArchived)}
              >
                {withArchived ? <ArchiveRestoreIcon className="size-4" /> : <ArchiveIcon className="size-4" />}
                <span className="hidden sm:inline">
                  {withArchived ? "Xem đang hoạt động" : "Xem đã lưu trữ"}
                </span>
              </Button>
            )}
            <Button size="sm" className="h-8 gap-1.5" onClick={openCreate}>
              <PlusIcon className="size-4" />
              <span className="hidden sm:inline">Tạo mới</span>
            </Button>
          </div>
        </div>

        <Separator />

        <div className="flex flex-col gap-4">
          <div className="flex items-center gap-2 px-4 lg:px-6">
            <div className="relative flex-1 max-w-sm">
              <SearchIcon className="absolute left-2.5 top-2.5 size-4 text-muted-foreground" />
              <Input
                placeholder="Tìm kiếm..."
                className="pl-8 h-9"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
              />
            </div>
            <DropdownMenu>
              <DropdownMenuTrigger
                className={cn(
                  buttonVariants({ variant: "outline", size: "sm" }),
                  "ml-auto h-8 gap-1.5"
                )}
              >
                <Columns3Icon className="size-4" />
                Cột
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end" className="w-40">
                {table
                  .getAllColumns()
                  .filter((column) => column.getCanHide())
                  .map((column) => (
                    <DropdownMenuCheckboxItem
                      key={column.id}
                      className="capitalize"
                      checked={column.getIsVisible()}
                      onCheckedChange={(value) => column.toggleVisibility(!!value)}
                    >
                      {column.id.replace(/_/g, " ")}
                    </DropdownMenuCheckboxItem>
                  ))}
              </DropdownMenuContent>
            </DropdownMenu>
          </div>

          <FilterRow
            schema={schema}
            filters={filters}
            onFilterChange={handleFilterChange}
          />

          <div className="rounded-md border mx-4 lg:mx-6 overflow-hidden bg-background shadow-sm">
            <Table>
              <TableHeader className="bg-muted/50">
                {table.getHeaderGroups().map((headerGroup) => (
                  <TableRow key={headerGroup.id}>
                    {headerGroup.headers.map((header) => (
                      <TableHead key={header.id}>
                        {header.isPlaceholder
                          ? null
                          : flexRender(
                              header.column.columnDef.header,
                              header.getContext()
                            )}
                      </TableHead>
                    ))}
                  </TableRow>
                ))}
              </TableHeader>
              <TableBody>
                {loading ? (
                  Array.from({ length: pageSize }).map((_, i) => (
                    <TableRow key={i}>
                      {columns.map((_, j) => (
                        <TableCell key={j}>
                          <Skeleton className="h-6 w-full" />
                        </TableCell>
                      ))}
                    </TableRow>
                  ))
                ) : records.length > 0 ? (
                  table.getRowModel().rows.map((row) => (
                    <TableRow
                      key={row.id}
                      data-state={row.getIsSelected() && "selected"}
                    >
                      {row.getVisibleCells().map((cell) => (
                        <TableCell key={cell.id}>
                          {flexRender(
                            cell.column.columnDef.cell,
                            cell.getContext()
                          )}
                        </TableCell>
                      ))}
                    </TableRow>
                  ))
                ) : (
                  <TableRow>
                    <TableCell
                      colSpan={columns.length}
                      className="h-24 text-center text-muted-foreground"
                    >
                      {listError ? (
                        <span className="text-destructive">{listError}</span>
                      ) : (
                        "Không tìm thấy bản ghi nào."
                      )}
                    </TableCell>
                  </TableRow>
                )}
              </TableBody>
            </Table>
          </div>

          <div className="flex items-center justify-between px-4 py-4 lg:px-6 border-t bg-muted/5">
            <div className="text-xs text-muted-foreground">
              Hiển thị <strong>{records.length}</strong> trong tổng số <strong>{total}</strong> bản ghi.
            </div>
            <div className="flex items-center gap-6 lg:gap-8">
              <div className="flex items-center gap-2">
                <p className="text-xs font-medium">Bản ghi mỗi trang</p>
                <Select
                  value={String(pageSize)}
                  onValueChange={(v) => {
                    setPageSize(Number(v));
                    setSkip(0);
                  }}
                >
                  <SelectTrigger className="h-8 w-16">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {[10, 20, 30, 40, 50].map((v) => (
                      <SelectItem key={v} value={String(v)}>
                        {v}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="flex items-center gap-1.5">
                <Button
                  variant="outline"
                  size="icon"
                  className="h-8 w-8"
                  onClick={() => setSkip(0)}
                  disabled={skip === 0}
                >
                  <ChevronsLeftIcon className="size-4" />
                </Button>
                <Button
                  variant="outline"
                  size="icon"
                  className="h-8 w-8"
                  onClick={() => setSkip(Math.max(0, skip - pageSize))}
                  disabled={skip === 0}
                >
                  <ChevronLeftIcon className="size-4" />
                </Button>
                <div className="flex items-center justify-center text-xs font-medium min-w-20">
                  Trang {Math.floor(skip / pageSize) + 1} / {Math.max(1, Math.ceil(total / pageSize))}
                </div>
                <Button
                  variant="outline"
                  size="icon"
                  className="h-8 w-8"
                  onClick={() => setSkip(skip + pageSize)}
                  disabled={skip + pageSize >= total}
                >
                  <ChevronRightIcon className="size-4" />
                </Button>
                <Button
                  variant="outline"
                  size="icon"
                  className="h-8 w-8"
                  onClick={() => setSkip((Math.ceil(total / pageSize) - 1) * pageSize)}
                  disabled={skip + pageSize >= total}
                >
                  <ChevronsRightIcon className="size-4" />
                </Button>
              </div>
            </div>
          </div>
        </div>

        <RecordDrawer
          open={drawerOpen}
          onOpenChange={setDrawerOpen}
          title={editing ? `Sửa ${label}` : `Tạo mới ${label}`}
          description={editing ? "Cập nhật thông tin bản ghi." : "Nhập thông tin cho bản ghi mới."}
          formFields={formFields}
          onSubmit={handleSubmit}
          submitLabel={editing ? "Cập nhật" : "Tạo mới"}
          isMobile={isMobile}
        />

        <AlertDialog open={!!deleteTarget} onOpenChange={() => setDeleteTarget(null)}>
          <AlertDialogContent>
            <AlertDialogHeader>
              <AlertDialogTitle>Xác nhận xóa vĩnh viễn?</AlertDialogTitle>
              <AlertDialogDescription>
                Hành động này không thể hoàn tác. Bản ghi này sẽ bị xóa khỏi hệ thống.
              </AlertDialogDescription>
            </AlertDialogHeader>
            <AlertDialogFooter>
              <AlertDialogCancel>Huỷ</AlertDialogCancel>
              <AlertDialogAction
                className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
                onClick={handleDelete}
              >
                Xác nhận xóa
              </AlertDialogAction>
            </AlertDialogFooter>
          </AlertDialogContent>
        </AlertDialog>

        <AlertDialog open={!!archiveTarget} onOpenChange={() => setArchiveTarget(null)}>
          <AlertDialogContent>
            <AlertDialogHeader>
              <AlertDialogTitle>Xác nhận lưu trữ bản ghi?</AlertDialogTitle>
              <AlertDialogDescription>
                Bản ghi sẽ bị ẩn khỏi danh sách hoạt động nhưng vẫn có thể khôi phục sau này.
              </AlertDialogDescription>
            </AlertDialogHeader>
            <AlertDialogFooter>
              <AlertDialogCancel>Huỷ</AlertDialogCancel>
              <AlertDialogAction onClick={handleArchive}>Xác nhận lưu trữ</AlertDialogAction>
            </AlertDialogFooter>
          </AlertDialogContent>
        </AlertDialog>
      </div>
    </FormProvider>
  );
}
