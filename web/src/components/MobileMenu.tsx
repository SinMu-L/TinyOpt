import { useState, useEffect, useRef } from 'preact/hooks';

interface NavItem {
  label: string;
  href: string;
  active: boolean;
}

interface Props {
  navItems: NavItem[];
  langHref: string;
  langLabel: string;
  menuLabel: string;
}

export default function MobileMenu({ navItems, langHref, langLabel, menuLabel }: Props) {
  const [open, setOpen] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!open) return;
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') setOpen(false);
    };
    const handleClickOutside = (e: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(e.target as Node)) {
        setOpen(false);
      }
    };
    document.addEventListener('keydown', handleKeyDown);
    document.addEventListener('mousedown', handleClickOutside);
    document.body.style.overflow = 'hidden';
    return () => {
      document.removeEventListener('keydown', handleKeyDown);
      document.removeEventListener('mousedown', handleClickOutside);
      document.body.style.overflow = '';
    };
  }, [open]);

  return (
    <div ref={menuRef} class="lg:hidden">
      <button
        onClick={() => setOpen(!open)}
        class="inline-flex items-center justify-center rounded-md p-2 text-gray-600 hover:bg-gray-100 hover:text-gray-900 transition-colors"
        aria-label={open ? 'Close menu' : 'Open menu'}
        aria-expanded={open}
      >
        {open ? (
          <svg class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
          </svg>
        ) : (
          <svg class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M4 6h16M4 12h16M4 18h16" />
          </svg>
        )}
      </button>

      {open && (
        <div class="fixed inset-0 z-[60] flex">
          <div class="fixed inset-0 bg-black/40 backdrop-blur-sm" onClick={() => setOpen(false)} />
          <div class="relative ml-auto flex w-72 max-w-[80vw] flex-col bg-white shadow-xl pt-[env(safe-area-inset-top)] pb-[env(safe-area-inset-bottom)]">
            <div class="flex items-center justify-between border-b border-gray-100 px-5 py-4">
              <span class="text-sm font-semibold text-gray-900">{menuLabel}</span>
              <button
                onClick={() => setOpen(false)}
                class="rounded-md p-1.5 text-gray-400 hover:text-gray-600 hover:bg-gray-100 transition-colors"
                aria-label="Close menu"
              >
                <svg class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
            <nav class="flex-1 overflow-y-auto px-3 py-4">
              {navItems.map((item) => (
                <a
                  href={item.href}
                  onClick={() => setOpen(false)}
                  class={`block rounded-md px-4 py-3 text-sm font-medium transition-colors ${
                    item.active
                      ? 'bg-primary-50 text-primary-700'
                      : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'
                  }`}
                >
                  {item.label}
                </a>
              ))}
            </nav>
            <div class="border-t border-gray-100 px-3 py-3">
              <a
                href={langHref}
                onClick={() => setOpen(false)}
                class="flex items-center gap-2 rounded-md px-4 py-3 text-sm font-medium text-gray-600 hover:bg-gray-50 hover:text-gray-900 transition-colors"
              >
                <svg class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M12 21a9.004 9.004 0 008.716-6.747M12 21a9.004 9.004 0 01-8.716-6.747M12 21c2.485 0 4.5-4.03 4.5-9S14.485 3 12 3m0 18c-2.485 0-4.5-4.03-4.5-9S9.515 3 12 3m0 0a8.997 8.997 0 017.843 4.582M12 3a8.997 8.997 0 00-7.843 4.582m15.686 0A11.953 11.953 0 0112 10.5c-2.998 0-5.74-1.1-7.843-2.918m15.686 0A8.959 8.959 0 0121 12c0 .778-.099 1.533-.284 2.253m0 0A17.919 17.919 0 0112 16.5c-3.162 0-6.133-.815-8.716-2.247m0 0A9.015 9.015 0 013 12c0-1.605.42-3.113 1.157-4.418" />
                </svg>
                {langLabel}
              </a>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
