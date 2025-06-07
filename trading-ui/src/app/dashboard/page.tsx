'use client';

import { useAppStore } from '@/stores/useAppStore';
import { Dashboard } from '@/components/Dashboard';
import { ApiErrorBoundary } from '@/components/ApiErrorBoundary';
import { Navigation } from '@/components/Navigation';
import { useTradingPairs } from '@/hooks/useTradingPairs';
import { useRouter } from 'next/navigation';
import { useEffect } from 'react';

export default function DashboardPage() {
  const { isApiConfigured } = useAppStore();
  const router = useRouter();

  // Initialize trading pairs in background when API is configured
  useTradingPairs();

  // Redirect to home if API is not configured (with delay to allow state to load)
  useEffect(() => {
    const timer = setTimeout(() => {
      if (!isApiConfigured) {
        router.push('/');
      }
    }, 1000); // Wait 1 second for state to load

    return () => clearTimeout(timer);
  }, [isApiConfigured, router]);

  // Show loading while checking configuration
  if (!isApiConfigured) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto mb-4"></div>
          <p className="text-muted-foreground">Loading dashboard...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background">
      <Navigation />
      <ApiErrorBoundary>
        <Dashboard />
      </ApiErrorBoundary>
    </div>
  );
}
