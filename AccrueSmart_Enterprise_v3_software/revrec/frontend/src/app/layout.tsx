import "./globals.css";
import Link from "next/link";

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <nav className="bg-white border-b">
          <div className="max-w-6xl mx-auto flex gap-4 p-3 text-sm">
            <a href="/trust/">Trust</a>
            <Link href="/revrec/">RevRec</Link>
            <Link href="/ingest">Ingest</Link>

            {/* added pages */}
            <Link href="/leases">Leases</Link>
            <Link href="/tax">ASC 740</Link>
            <Link href="/forecast">Forecast</Link>
            <Link href="/auditor">AI Auditor</Link>
          </div>
        </nav>
        <div className="p-4">{children}</div>
      </body>
    </html>
  );
}
