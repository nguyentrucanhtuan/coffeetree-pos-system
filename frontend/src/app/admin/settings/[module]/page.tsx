import { AutoSettingsPage } from "@/components/auto-settings-page";

/**
 * src/app/admin/settings/[module]/page.tsx
 * 
 * Dynamic route for each setting module.
 */
export default async function Page({ params }: { params: Promise<{ module: string }> }) {
  const { module } = await params;
  return <AutoSettingsPage moduleName={module} />;
}
