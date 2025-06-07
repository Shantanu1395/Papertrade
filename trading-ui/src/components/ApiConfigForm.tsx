'use client';

import { useState } from 'react';
import { useAppStore } from '@/stores/useAppStore';
import { isValidApiKey } from '@/lib/utils';
import { Key, Eye, EyeOff, AlertCircle } from 'lucide-react';

export function ApiConfigForm() {
  const { setApiConfig, setError, error } = useAppStore();
  const [formData, setFormData] = useState({
    apiKey: '',
    apiSecret: '',
    baseUrl: process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8500',
  });
  const [showSecret, setShowSecret] = useState(false);
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError(null);

    // Basic validation
    if (!formData.apiKey.trim()) {
      setError('API Key is required');
      setIsLoading(false);
      return;
    }

    if (!formData.apiSecret.trim()) {
      setError('API Secret is required');
      setIsLoading(false);
      return;
    }

    if (!isValidApiKey(formData.apiKey)) {
      setError('Invalid API Key format');
      setIsLoading(false);
      return;
    }

    if (!isValidApiKey(formData.apiSecret)) {
      setError('Invalid API Secret format');
      setIsLoading(false);
      return;
    }

    try {
      // Test the API connection by making a simple request
      const response = await fetch(`${formData.baseUrl}/account/usdt-balance`);
      
      if (!response.ok) {
        throw new Error('Failed to connect to API');
      }

      // If successful, save the configuration
      setApiConfig({
        apiKey: formData.apiKey.trim(),
        apiSecret: formData.apiSecret.trim(),
        baseUrl: formData.baseUrl.trim(),
      });
    } catch {
      setError('Failed to connect to the API. Please check your configuration.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleInputChange = (field: string, value: string) => {
    setFormData(prev => ({ ...prev, [field]: value }));
    if (error) setError(null);
  };

  return (
    <div className="crypto-card">
      <div className="flex items-center gap-3 mb-6">
        <div className="p-2 bg-primary/10 rounded-lg">
          <Key className="w-5 h-5 text-primary" />
        </div>
        <h2 className="text-xl font-semibold">API Configuration</h2>
      </div>

      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label htmlFor="apiKey" className="block text-sm font-medium mb-2">
            Binance API Key
          </label>
          <input
            id="apiKey"
            type="text"
            value={formData.apiKey}
            onChange={(e) => handleInputChange('apiKey', e.target.value)}
            placeholder="Enter your Binance testnet API key"
            className="crypto-input"
            disabled={isLoading}
          />
        </div>

        <div>
          <label htmlFor="apiSecret" className="block text-sm font-medium mb-2">
            Binance API Secret
          </label>
          <div className="relative">
            <input
              id="apiSecret"
              type={showSecret ? 'text' : 'password'}
              value={formData.apiSecret}
              onChange={(e) => handleInputChange('apiSecret', e.target.value)}
              placeholder="Enter your Binance testnet API secret"
              className="crypto-input pr-10"
              disabled={isLoading}
            />
            <button
              type="button"
              onClick={() => setShowSecret(!showSecret)}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
              disabled={isLoading}
            >
              {showSecret ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
            </button>
          </div>
        </div>

        <div>
          <label htmlFor="baseUrl" className="block text-sm font-medium mb-2">
            API Base URL
          </label>
          <input
            id="baseUrl"
            type="url"
            value={formData.baseUrl}
            onChange={(e) => handleInputChange('baseUrl', e.target.value)}
            placeholder="http://localhost:8500"
            className="crypto-input"
            disabled={isLoading}
          />
        </div>

        {error && (
          <div className="flex items-center gap-2 p-3 bg-destructive/10 border border-destructive/20 rounded-lg text-destructive text-sm">
            <AlertCircle className="w-4 h-4 flex-shrink-0" />
            <span>{error}</span>
          </div>
        )}

        <button
          type="submit"
          disabled={isLoading}
          className="crypto-button-primary w-full"
        >
          {isLoading ? 'Connecting...' : 'Connect to API'}
        </button>
      </form>

      <div className="mt-6 p-4 bg-muted/50 rounded-lg">
        <h3 className="text-sm font-medium mb-2">Setup Instructions:</h3>
        <ol className="text-sm text-muted-foreground space-y-1 list-decimal list-inside">
          <li>Create a Binance testnet account</li>
          <li>Generate API keys in your testnet account</li>
          <li>Make sure your API server is running on the specified URL</li>
          <li>Enter your credentials above to connect</li>
        </ol>
      </div>
    </div>
  );
}
