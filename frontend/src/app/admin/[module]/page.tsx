import { AutoCrudPage } from "@/components/auto-crud-page";

type Props = { params: Promise<{ module: string }> };

export default async function ModulePage({ params }: Props) {
  const { module } = await params;
  return <AutoCrudPage name={module} />;
}
