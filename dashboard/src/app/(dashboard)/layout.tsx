import Link from 'next/link';

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen bg-background text-foreground">
      <nav className="border-b border-border px-6 py-3">
        <ul className="flex gap-6 text-sm">
          <li>
            <Link href="/" className="hover:text-primary">
              Overview
            </Link>
          </li>
          <li>
            <Link href="/signals" className="hover:text-primary">
              Signals
            </Link>
          </li>
          <li>
            <Link href="/risk" className="hover:text-primary">
              Risk
            </Link>
          </li>
          <li>
            <Link href="/pipeline" className="hover:text-primary">
              Pipeline
            </Link>
          </li>
          <li>
            <Link href="/performance" className="hover:text-primary">
              Performance
            </Link>
          </li>
        </ul>
      </nav>
      <main className="p-6">{children}</main>
    </div>
  );
}
