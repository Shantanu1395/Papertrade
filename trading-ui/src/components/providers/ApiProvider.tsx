'use client';

import { useEffect } from 'react';
import { useAppStore } from '@/stores/useAppStore';
import { updateApiClient } from '@/lib/api';

export function ApiProvider({ children }: { children: React.ReactNode }) {
  const { apiConfig, isApiConfigured } = useAppStore();

  useEffect(() => {
    // Initialize API client with stored configuration when app loads
    if (isApiConfigured && apiConfig) {
      updateApiClient(apiConfig);
    }
  }, [isApiConfigured, apiConfig]);

  return <>{children}</>;
}
