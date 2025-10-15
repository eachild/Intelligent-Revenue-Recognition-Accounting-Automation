
import "./globals.css";
import Link from "next/link";
import { Toaster } from "sonner";
export const metadata = { title: "AccrueSmart Ultimate v2.1", description: "Best-in-class revenue platform" };
export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en"><body>
      <Toaster richColors position="top-right"/>
      <nav className="bg-white border-b">
        <div className="max-w-7xl mx-auto flex gap-4 p-3 text-sm">
          <Link href="/">Home</Link>
          <Link href="/ingest">Ingest</Link>
          <Link href="/allocate">Allocate</Link>
          <Link href="/mods">Mods</Link>
          <Link href="/sfc">SFC</Link>
          <Link href="/consolidation">Consolidation</Link>
          <Link href="/reports">Reports</Link>
          <Link href="/chat">Chat</Link>
        </div>
      </nav>
      {children}
    </body></html>
  );
}
