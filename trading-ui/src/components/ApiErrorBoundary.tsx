'use client';

import { useEffect } from 'react';
import { useAppStore } from '@/stores/useAppStore';
import { useToast } from '@/components/Toast';
import { AlertTriangle, RefreshCw, Settings } from 'lucide-react';

interface ApiErrorBoundaryProps {
  children: React.ReactNode;
}

export function ApiErrorBoundary({ children }: ApiErrorBoundaryProps) {
  const { isApiConfigured, clearApiConfig, error } = useAppStore();
  const { showToast } = useToast();

  // Check for API connection on mount
  useEffect(() => {
    const checkApiConnection = async () => {
      try {
        const response = await fetch('http://localhost:8500/account/usdt-balance');
        if (!response.ok) {
          if (response.status === 401 || response.status === 403) {
            clearApiConfig();
            showToast('error', 'API credentials are invalid. Please reconfigure your API keys.');
          } else if (response.status >= 500) {
            showToast('error', 'API server error. Please check if the server is running.');
          }
        }
      } catch {
        showToast('error', 'Cannot connect to API server. Please check if the server is running on port 8500.');
      }
    };

    if (isApiConfigured) {
      checkApiConnection();
    }
  }, [isApiConfigured, clearApiConfig, showToast]);



  const handleRetry = () => {
    window.location.reload();
  };

  const handleReconfigure = () => {
    clearApiConfig();
  };

  // If there's a critical API error, show error UI
  if (error && error.includes('Invalid API credentials')) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center p-4">
        <div className="crypto-card max-w-md w-full text-center">
          <div className="p-3 bg-destructive/10 rounded-lg w-fit mx-auto mb-4">
            <AlertTriangle className="w-8 h-8 text-destructive" />
          </div>
          
          <h2 className="text-xl font-semibold mb-2">API Configuration Required</h2>
          <p className="text-muted-foreground mb-6">
            Your API credentials are invalid or missing. Please reconfigure your Binance API keys.
          </p>
          
          <div className="space-y-3">
            <button
              onClick={handleReconfigure}
              className="crypto-button-primary w-full flex items-center justify-center gap-2"
            >
              <Settings className="w-4 h-4" />
              Reconfigure API Keys
            </button>
            
            <button
              onClick={handleRetry}
              className="crypto-button-secondary w-full flex items-center justify-center gap-2"
            >
              <RefreshCw className="w-4 h-4" />
              Retry Connection
            </button>
          </div>
          
          <div className="mt-6 p-4 bg-muted/50 rounded-lg text-left">
            <h3 className="text-sm font-medium mb-2">Common Issues:</h3>
            <ul className="text-sm text-muted-foreground space-y-1 list-disc list-inside">
              <li>API keys are incorrect or expired</li>
              <li>API server is not running on port 8500</li>
              <li>Network connection issues</li>
              <li>API permissions are insufficient</li>
            </ul>
          </div>
        </div>
      </div>
    );
  }

  return <>{children}</>;
}
