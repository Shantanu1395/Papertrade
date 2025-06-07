'use client';

import { useAppStore } from '@/stores/useAppStore';
import { ApiConfigForm } from '@/components/ApiConfigForm';
import { Dashboard } from '@/components/Dashboard';
import { ApiErrorBoundary } from '@/components/ApiErrorBoundary';

export default function Home() {
  const { isApiConfigured } = useAppStore();

  if (!isApiConfigured) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center p-4">
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
    );
  }

  return (
    <ApiErrorBoundary>
      <Dashboard />
    </ApiErrorBoundary>
  );
}
