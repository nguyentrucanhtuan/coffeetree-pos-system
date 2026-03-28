"use client";

/**
 * src/components/auto-crud-page.tsx
 *
 * Fetch schema từ /{name}/meta/schema → pass xuống SmartCrudPage.
 * Không cần khai báo fields thủ công.
 *
 * Ví dụ:
 *   <AutoCrudPage name="products" />
 */

import { useEffect, useState } from "react";
import { schemaApi } from "@/lib/api";
import type { ModuleSchema } from "@/types/module";
import { SmartCrudPage } from "@/components/crud-page";
import { Skeleton } from "@/components/ui/skeleton";

interface AutoCrudPageProps {
  name: string;
  label?: string;
}

export function AutoCrudPage({ name, label }: AutoCrudPageProps) {
  const [schema, setSchema] = useState<ModuleSchema | null>(null);
  const [error, setError]   = useState<string | null>(null);

  useEffect(() => {
    setSchema(null);
    setError(null);
    schemaApi
      .get(name)
      .then(setSchema)
      .catch((err: Error) => setError(err.message));
  }, [name]);

  if (error) {
    return (
      <div className="rounded-lg border border-destructive/50 bg-destructive/5 p-6 text-sm text-destructive">
        ⚠️ Không thể load schema cho <code>{name}</code>: {error}
      </div>
    );
  }

  if (!schema) {
    return (
      <div className="space-y-4">
        <Skeleton className="h-8 w-48" />
        <Skeleton className="h-10 w-full" />
        <Skeleton className="h-64 w-full" />
      </div>
    );
  }

  return (
    <SmartCrudPage
      schema={schema}
      overrideLabel={label}
    />
  );
}
