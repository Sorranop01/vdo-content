import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { Toaster } from "@/components/ui/sonner";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "Strategy Engine — AI Content Blueprint Dashboard",
  description: "Multi-agent AI pipeline for generating optimized content strategies",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <body className={`${inter.className} antialiased`}>
        <div className="flex min-h-screen bg-gradient-to-br from-gray-950 via-gray-900 to-slate-950">
          {/* Sidebar */}
          <aside className="hidden lg:flex w-64 flex-col border-r border-white/5 bg-gray-950/50 backdrop-blur-xl">
            <div className="p-6 border-b border-white/5">
              <div className="flex items-center gap-3">
                <div className="w-9 h-9 rounded-lg bg-gradient-to-br from-violet-500 to-indigo-600 flex items-center justify-center text-white font-bold text-sm shadow-lg shadow-violet-500/20">
                  SE
                </div>
                <div>
                  <h1 className="text-sm font-semibold text-white">Strategy Engine</h1>
                  <p className="text-[11px] text-gray-500">Content Blueprint AI</p>
                </div>
              </div>
            </div>
            <nav className="flex-1 p-4 space-y-1">
              <NavItem href="/" icon="🧠" label="New Blueprint" active />
              <NavItem href="/runs" icon="📋" label="Pipeline Runs" />
              <NavItem href="/blueprints" icon="📐" label="Blueprints" />
            </nav>
            <div className="p-4 border-t border-white/5">
              <div className="px-3 py-2 rounded-lg bg-white/[0.03] text-[11px] text-gray-500">
                <span className="text-green-400">●</span> API Connected
              </div>
            </div>
          </aside>

          {/* Main Content */}
          <main className="flex-1 overflow-y-auto">
            {children}
          </main>
        </div>
        <Toaster richColors position="top-right" />
      </body>
    </html>
  );
}

function NavItem({
  href,
  icon,
  label,
  active = false,
}: {
  href: string;
  icon: string;
  label: string;
  active?: boolean;
}) {
  return (
    <a
      href={href}
      className={`flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition-all ${active
          ? "bg-violet-500/10 text-violet-300 font-medium"
          : "text-gray-400 hover:text-gray-200 hover:bg-white/[0.03]"
        }`}
    >
      <span className="text-base">{icon}</span>
      {label}
    </a>
  );
}
