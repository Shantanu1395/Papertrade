'use client';

import { useAppStore } from '@/stores/useAppStore';
import { ApiConfigForm } from '@/components/ApiConfigForm';
import { Dashboard } from '@/components/Dashboard';
import { ApiErrorBoundary } from '@/components/ApiErrorBoundary';
import { Navigation } from '@/components/Navigation';
import { useTradingPairs } from '@/hooks/useTradingPairs';

export default function Home() {
  const { isApiConfigured } = useAppStore();

  // Initialize trading pairs in background when API is configured
  useTradingPairs();

  // Always show API configuration page on initial load
  // This ensures users can always configure their API settings
  return (
    <div className="min-h-screen bg-background">
      <Navigation />
      <div className="flex items-center justify-center p-4" style={{ minHeight: 'calc(100vh - 4rem)' }}>
        <div className="w-full max-w-md">
          <div className="text-center mb-8">
            <h1 className="text-3xl font-bold text-foreground mb-2">
              Paper Trading Dashboard
            </h1>
            <p className="text-muted-foreground">
              Configure your Binance API credentials to get started
            </p>
          </div>
          <ApiConfigForm />
        </div>
      </div>
    </div>
  );
}
