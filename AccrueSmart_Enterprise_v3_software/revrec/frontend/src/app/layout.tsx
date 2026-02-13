import "./globals.css";
import { Sidebar } from "@/src/components/ui/sidebar";

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="flex">
        <Sidebar />
        <main className="flex-1 p-4 min-h-screen">{children}</main>
      </body>
    </html>
  );
}
