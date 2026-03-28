"use client";

import { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { api } from "@/lib/api";
import type { PaginatedResponse } from "@/types/module";
import { Package, TrendingUp, CheckCircle, XCircle } from "lucide-react";

export default function AdminDashboard() {
  const [data, setData] = useState<PaginatedResponse | null>(null);
  const [activeData, setActiveData] = useState<PaginatedResponse | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      api.items.list({ limit: 1 }),
      api.items.list({ limit: 1, is_active: true }),
    ])
      .then(([all, active]) => {
        setData(all);
        setActiveData(active);
      })
      .finally(() => setLoading(false));
  }, []);

  const stats = [
    {
      title: "Tổng sản phẩm",
      value: data?.total ?? 0,
      icon: Package,
      desc: "Tất cả sản phẩm trong hệ thống",
      color: "text-blue-500",
    },
    {
      title: "Đang hoạt động",
      value: activeData?.total ?? 0,
      icon: CheckCircle,
      desc: "Sản phẩm đang được kích hoạt",
      color: "text-green-500",
    },
    {
      title: "Ngừng hoạt động",
      value: (data?.total ?? 0) - (activeData?.total ?? 0),
      icon: XCircle,
      desc: "Sản phẩm bị tắt kích hoạt",
      color: "text-red-500",
    },
    {
      title: "Tỉ lệ active",
      value:
        data?.total
          ? `${Math.round(((activeData?.total ?? 0) / data.total) * 100)}%`
          : "—",
      icon: TrendingUp,
      desc: "Phần trăm sản phẩm đang hoạt động",
      color: "text-amber-500",
    },
  ];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Dashboard</h1>
        <p className="text-muted-foreground">Tổng quan hệ thống CoffeeTree Admin.</p>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        {stats.map((stat) => (
          <Card key={stat.title}>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">{stat.title}</CardTitle>
              <stat.icon className={`h-4 w-4 ${stat.color}`} />
            </CardHeader>
            <CardContent>
              {loading ? (
                <Skeleton className="h-7 w-16" />
              ) : (
                <div className="text-2xl font-bold">{stat.value}</div>
              )}
              <p className="text-xs text-muted-foreground mt-1">{stat.desc}</p>
            </CardContent>
          </Card>
        ))}
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Hướng dẫn nhanh</CardTitle>
        </CardHeader>
        <CardContent className="text-sm text-muted-foreground space-y-2">
          <p>👉 Vào <strong>Sản phẩm</strong> để thêm, sửa, xoá các item trong hệ thống.</p>
          <p>📡 Dữ liệu được kết nối trực tiếp với <strong>FastAPI backend</strong> tại <code className="bg-muted px-1 rounded text-xs">localhost:8000</code>.</p>
          <p>📄 Xem API docs tại <a href="http://localhost:8000/docs" target="_blank" className="text-primary underline underline-offset-2">localhost:8000/docs</a></p>
        </CardContent>
      </Card>
    </div>
  );
}
