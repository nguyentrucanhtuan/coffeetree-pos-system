"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarGroup,
  SidebarGroupContent,
  SidebarGroupLabel,
  SidebarHeader,
  SidebarMenu,
  SidebarMenuAction,
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarMenuSub,
  SidebarMenuSubButton,
  SidebarMenuSubItem,
  SidebarRail,
  useSidebar,
} from "@/components/ui/sidebar";
import { sidebarMenuButtonVariants } from "@/components/ui/sidebar-variants";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuGroup,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Coffee,
  LayoutDashboard,
  Users,
  Shield,
  Lock,
  Settings,
  ChevronsUpDown,
  BadgeCheck,
  Bell,
  LogOut,
  User as UserIcon,
  ChevronRight,
} from "lucide-react";
import { menuApi } from "@/lib/api";
import { getStoredUser, logout } from "@/lib/auth";
import { useRouter } from "next/navigation";
import type { MenuModule } from "@/types/module";
import { cn } from "@/lib/utils";

// CMS Core hardcoded — chỉ superuser
const CMS_CORE_ITEMS = [
  { title: "Người dùng", href: "/admin/users",             icon: Users   },
  { title: "Nhóm",        href: "/admin/groups",            icon: Shield  },
  { title: "Phân quyền",  href: "/admin/group-permissions", icon: Lock    },
];

/** Group menu items by menu_parent string */
function groupMenuModules(modules: MenuModule[]) {
  const groups: Record<string, MenuModule[]> = {};
  const rootItems: MenuModule[] = [];

  for (const mod of modules) {
    if (mod.menu_parent) {
      if (!groups[mod.menu_parent]) groups[mod.menu_parent] = [];
      groups[mod.menu_parent].push(mod);
    } else {
      rootItems.push(mod);
    }
  }

  for (const key of Object.keys(groups)) {
    groups[key].sort((a, b) => a.menu_sequence - b.menu_sequence);
  }

  rootItems.sort((a, b) => a.menu_sequence - b.menu_sequence);

  return { 
    sortedGroups: Object.entries(groups).sort(([, a], [, b]) => 
      Math.min(...a.map(i => i.menu_sequence)) - Math.min(...b.map(i => i.menu_sequence))
    ), 
    rootItems 
  };
}

function NavHeader() {
  return (
    <SidebarHeader className="border-b/50">
      <SidebarMenu>
        <SidebarMenuItem>
          <SidebarMenuButton size="lg" className="data-[state=open]:bg-sidebar-accent data-[state=open]:text-sidebar-accent-foreground">
            <div className="flex aspect-square size-9 items-center justify-center rounded-xl bg-primary text-primary-foreground shadow-sm">
              <Coffee className="size-5" />
            </div>
            <div className="grid flex-1 text-left text-sm leading-tight ml-1">
              <span className="truncate font-bold text-base tracking-tight text-foreground">CoffeeTree</span>
              <span className="truncate text-xs text-muted-foreground/80 font-medium">Enterprise POS</span>
            </div>
          </SidebarMenuButton>
        </SidebarMenuItem>
      </SidebarMenu>
    </SidebarHeader>
  );
}

function NavMain({ modules, loading, pathname }: { modules: MenuModule[], loading: boolean, pathname: string }) {
  const { rootItems, sortedGroups } = groupMenuModules(modules);

  if (loading) {
    return (
      <SidebarGroup>
        <SidebarGroupLabel>Ứng dụng</SidebarGroupLabel>
        <SidebarGroupContent>
          <div className="space-y-2 px-2">
            {[1, 2, 3, 4].map((i) => (
              <Skeleton key={i} className="h-8 w-full" />
            ))}
          </div>
        </SidebarGroupContent>
      </SidebarGroup>
    );
  }

  return (
    <>
      <SidebarGroup>
        <SidebarGroupLabel>Chung</SidebarGroupLabel>
        <SidebarMenu>
          <SidebarMenuItem>
            <SidebarMenuButton render={<Link href="/admin" />} isActive={pathname === "/admin"}>
              <LayoutDashboard className="size-4" />
              <span>Dashboard</span>
            </SidebarMenuButton>
          </SidebarMenuItem>
          <SidebarMenuItem>
            <SidebarMenuButton render={<Link href="/admin/settings" />} isActive={pathname === "/admin/settings"}>
              <Settings className="size-4" />
              <span>Cài đặt</span>
            </SidebarMenuButton>
          </SidebarMenuItem>
        </SidebarMenu>
      </SidebarGroup>

      {rootItems.length > 0 && (
        <SidebarGroup>
          <SidebarGroupLabel>Modules</SidebarGroupLabel>
          <SidebarMenu>
            {rootItems.map((mod) => (
              <ModuleMenuItem key={mod.name} mod={mod} pathname={pathname} />
            ))}
          </SidebarMenu>
        </SidebarGroup>
      )}

      {sortedGroups.map(([groupLabel, groupModules]) => (
        <SidebarGroup key={groupLabel}>
          <SidebarGroupLabel>{groupLabel}</SidebarGroupLabel>
          <SidebarMenu>
            {groupModules.map((mod) => (
              <ModuleMenuItem key={mod.name} mod={mod} pathname={pathname} />
            ))}
          </SidebarMenu>
        </SidebarGroup>
      ))}
    </>
  );
}

function ModuleMenuItem({ mod, pathname }: { mod: MenuModule; pathname: string }) {
  const href = `/admin/${mod.name}`;
  const settingsHref = `/admin/${mod.name}/settings`;
  const isActive = pathname === href || pathname.startsWith(`${href}/`);

  return (
    <SidebarMenuItem>
      <SidebarMenuButton 
        render={<Link href={href} />} 
        isActive={isActive}
        tooltip={mod.menu_label}
      >
        <span className="text-base leading-none">{mod.menu_icon || "📋"}</span>
        <span>{mod.menu_label}</span>
    </SidebarMenuButton>
  </SidebarMenuItem>
  );
}

function NavSecondary({ isSuperuser, pathname }: { isSuperuser: boolean; pathname: string }) {
  if (!isSuperuser) return null;

  return (
    <SidebarGroup className="mt-auto">
      <SidebarGroupLabel>Hệ thống</SidebarGroupLabel>
      <SidebarMenu>
        {CMS_CORE_ITEMS.map((item) => (
          <SidebarMenuItem key={item.href}>
            <SidebarMenuButton
              render={<Link href={item.href} />}
              isActive={pathname === item.href}
              tooltip={item.title}
            >
              <item.icon className="size-4" />
              <span>{item.title}</span>
            </SidebarMenuButton>
          </SidebarMenuItem>
        ))}
      </SidebarMenu>
    </SidebarGroup>
  );
}

function NavUser({ user }: { user: ReturnType<typeof getStoredUser> }) {
  const router = useRouter();
  const { isMobile } = useSidebar();

  const handleLogout = () => {
    logout();
    router.push("/login");
  };

  return (
    <SidebarFooter className="border-t p-2">
      <SidebarMenu>
        <SidebarMenuItem>
          <DropdownMenu>
            <DropdownMenuTrigger
              className={cn(
                sidebarMenuButtonVariants({ size: "lg" }),
                "data-[state=open]:bg-sidebar-accent data-[state=open]:text-sidebar-accent-foreground w-full"
              )}
            >
              <Avatar className="h-8 w-8 rounded-lg">
                <AvatarFallback className="rounded-lg bg-primary text-primary-foreground text-xs">
                  {user?.full_name?.[0]?.toUpperCase() ?? "A"}
                </AvatarFallback>
              </Avatar>
              <div className="grid flex-1 text-left text-sm leading-tight">
                <span className="truncate font-semibold">{user?.full_name ?? "Admin"}</span>
                <span className="truncate text-xs text-muted-foreground">{user?.email ?? ""}</span>
              </div>
              <ChevronsUpDown className="ml-auto size-4" />
            </DropdownMenuTrigger>
            <DropdownMenuContent
              className="w-(--anchor-width) min-w-56 rounded-lg"
              side={isMobile ? "bottom" : "right"}
              align="end"
              sideOffset={4}
            >
              <DropdownMenuLabel className="p-0 font-normal">
                <div className="flex items-center gap-2 px-1 py-1.5 text-left text-sm">
                  <Avatar className="h-8 w-8 rounded-lg">
                    <AvatarFallback className="rounded-lg bg-primary text-primary-foreground text-xs">
                      {user?.full_name?.[0]?.toUpperCase() ?? "A"}
                    </AvatarFallback>
                  </Avatar>
                  <div className="grid flex-1 text-left text-sm leading-tight">
                    <span className="truncate font-semibold">{user?.full_name ?? "Admin"}</span>
                    <span className="truncate text-xs">{user?.email ?? ""}</span>
                  </div>
                </div>
              </DropdownMenuLabel>
              <DropdownMenuSeparator />
              <DropdownMenuGroup>
                <DropdownMenuItem>
                  <BadgeCheck className="mr-2 size-4" />
                  Tài khoản
                </DropdownMenuItem>
                <DropdownMenuItem>
                  <Bell className="mr-2 size-4" />
                  Thông báo
                </DropdownMenuItem>
              </DropdownMenuGroup>
              <DropdownMenuSeparator />
              <DropdownMenuItem onClick={handleLogout} variant="destructive">
                <LogOut className="mr-2 size-4" />
                Đăng xuất
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </SidebarMenuItem>
      </SidebarMenu>
    </SidebarFooter>
  );
}

export function AppSidebar() {
  const pathname = usePathname();
  const [modules, setModules]   = useState<MenuModule[]>([]);
  const [loading, setLoading]   = useState(true);
  const [user, setUser]         = useState<ReturnType<typeof getStoredUser>>(null);

  useEffect(() => {
    setUser(getStoredUser());
    menuApi
      .getModules()
      .then(setModules)
      .catch(() => setModules([]))
      .finally(() => setLoading(false));
  }, []);

  return (
    <Sidebar collapsible="icon" variant="floating">
      <NavHeader />
      <SidebarContent>
        <NavMain modules={modules} loading={loading} pathname={pathname} />
        <NavSecondary isSuperuser={user?.is_superuser ?? false} pathname={pathname} />
      </SidebarContent>
      <NavUser user={user} />
      <SidebarRail />
    </Sidebar>
  );
}
