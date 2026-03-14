import Link from 'next/link';

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen bg-gray-950 text-gray-100">
      <nav className="border-b border-gray-800 px-6 py-3">
        <ul className="flex gap-6 text-sm">
          <li>
            <Link href="/" className="hover:text-amber-400">
              Overview
            </Link>
          </li>
          <li>
            <Link href="/signals" className="hover:text-amber-400">
              Signals
            </Link>
          </li>
          <li>
            <Link href="/risk" className="hover:text-amber-400">
              Risk
            </Link>
          </li>
          <li>
            <Link href="/pipeline" className="hover:text-amber-400">
              Pipeline
            </Link>
          </li>
        </ul>
      </nav>
      <main className="p-6">{children}</main>
    </div>
  );
}
