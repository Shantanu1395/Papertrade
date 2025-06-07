'use client';

import { useRouter, usePathname } from 'next/navigation';
import { useAppStore } from '@/stores/useAppStore';
import { Settings, BarChart3 } from 'lucide-react';

export function Navigation() {
  const router = useRouter();
  const pathname = usePathname();
  const { isApiConfigured } = useAppStore();

  return (
    <nav className="bg-card border-b border-border">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          {/* Logo */}
          <div className="flex items-center">
            <BarChart3 className="w-8 h-8 text-primary mr-3" />
            <h1 className="text-xl font-bold text-foreground">
              Paper Trading
            </h1>
          </div>

          {/* Navigation Links */}
          <div className="flex items-center space-x-4">
            <button
              onClick={() => router.push('/')}
              className={`flex items-center gap-2 px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                pathname === '/' 
                  ? 'bg-primary text-primary-foreground' 
                  : 'text-muted-foreground hover:text-foreground hover:bg-muted'
              }`}
            >
              <Settings className="w-4 h-4" />
              API Config
            </button>

            {isApiConfigured && (
              <button
                onClick={() => router.push('/dashboard')}
                className={`flex items-center gap-2 px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                  pathname === '/dashboard' 
                    ? 'bg-primary text-primary-foreground' 
                    : 'text-muted-foreground hover:text-foreground hover:bg-muted'
                }`}
              >
                <BarChart3 className="w-4 h-4" />
                Dashboard
              </button>
            )}
          </div>
        </div>
      </div>
    </nav>
  );
}
