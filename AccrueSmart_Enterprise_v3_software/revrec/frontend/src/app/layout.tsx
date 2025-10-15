
import "./globals.css"; import Link from "next/link";
export default function RootLayout({children}:{children:React.ReactNode}){
  return <html lang="en"><body><nav className="bg-white border-b"><div className="max-w-6xl mx-auto flex gap-4 p-3 text-sm">
    <a href="/trust/">Trust</a>
    <Link href="/revrec/">RevRec</Link>
    <Link href="/revrec/ingest">Ingest</Link>
  </div></nav><div className="p-4">{children}</div></body></html>;
}
