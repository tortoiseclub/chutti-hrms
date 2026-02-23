import { Link, useLocation } from "react-router-dom";
import { Button } from "@/components/ui/button";
import {
  LayoutDashboard,
  Calendar,
  Users,
  CalendarDays,
  LogOut,
} from "lucide-react";

export default function Layout({ user, onLogout, children }) {
  const location = useLocation();

  const navigation = [
    {
      name: "Dashboard",
      path: "/dashboard",
      icon: LayoutDashboard,
    },
    {
      name: "Calendar",
      path: "/calendar",
      icon: Calendar,
    },
  ];

  // Add HR-only navigation
  if (user.role === "hr") {
    navigation.push(
      {
        name: "Employees",
        path: "/employees",
        icon: Users,
      },
      {
        name: "Holidays",
        path: "/holidays",
        icon: CalendarDays,
      }
    );
  }

  return (
    <div className="min-h-screen bg-background">
      {/* Sidebar */}
      <aside className="fixed left-0 top-0 h-full w-64 bg-white border-r border-slate-200 shadow-sm">
        <div className="flex flex-col h-full">
          {/* Logo */}
          <div className="p-6 border-b border-slate-200">
            <img
              src="https://customer-assets.emergentagent.com/job_ooo-calendar-hub/artifacts/71fc0etu_Horizontal_Logo-_tortoise_%283%29_%281%29.png"
              alt="Tortoise Logo"
              className="h-12"
            />
          </div>

          {/* Navigation */}
          <nav className="flex-1 p-4 space-y-2">
            {navigation.map((item) => {
              const isActive = location.pathname === item.path;
              return (
                <Link
                  key={item.path}
                  to={item.path}
                  data-testid={`nav-${item.name.toLowerCase()}`}
                  className={`flex items-center gap-3 px-4 py-3 rounded-lg font-medium transition-colors ${
                    isActive
                      ? "bg-primary text-white"
                      : "text-slate-700 hover:bg-slate-100"
                  }`}
                >
                  <item.icon className="w-5 h-5" />
                  {item.name}
                </Link>
              );
            })}
          </nav>

          {/* User info */}
          <div className="p-4 border-t border-slate-200">
            <div className="mb-3">
              <p className="text-sm font-medium text-slate-900">{user.name}</p>
              <p className="text-xs text-slate-600">{user.email}</p>
              <span
                className={`inline-block mt-2 text-xs px-2 py-1 rounded-full ${
                  user.role === "hr"
                    ? "bg-blue-100 text-blue-700"
                    : "bg-slate-100 text-slate-700"
                }`}
              >
                {user.role === "hr" ? "HR" : "Employee"}
              </span>
            </div>
            <Button
              data-testid="logout-button"
              onClick={onLogout}
              variant="outline"
              className="w-full justify-start text-slate-700 hover:text-red-600 hover:bg-red-50 border-slate-200"
            >
              <LogOut className="w-4 h-4 mr-2" />
              Logout
            </Button>
          </div>
        </div>
      </aside>

      {/* Main content */}
      <main className="ml-64 min-h-screen">
        <div className="max-w-7xl mx-auto p-8">{children}</div>
      </main>
    </div>
  );
}
