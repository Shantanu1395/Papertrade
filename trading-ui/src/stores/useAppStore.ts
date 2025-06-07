import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { ApiConfig } from '@/types/api';
import { updateApiClient } from '@/lib/api';

interface AppState {
  // API Configuration
  apiConfig: ApiConfig | null;
  isApiConfigured: boolean;

  // UI State
  isLoading: boolean;
  error: string | null;

  // Trading Pairs
  tradingPairs: string[];
  tradingPairsLoaded: boolean;

  // Actions
  setApiConfig: (config: ApiConfig) => void;
  clearApiConfig: () => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
  clearError: () => void;
  handleApiError: (error: any) => void;
  setTradingPairs: (pairs: string[]) => void;
}

export const useAppStore = create<AppState>()(
  persist(
    (set, get) => ({
      // Initial state
      apiConfig: null,
      isApiConfigured: false,
      isLoading: false,
      error: null,
      tradingPairs: [],
      tradingPairsLoaded: false,

      // Actions
      setApiConfig: (config: ApiConfig) => {
        // Update the API client with new config
        updateApiClient(config);
        
        set({
          apiConfig: config,
          isApiConfigured: true,
          error: null,
        });
      },

      clearApiConfig: () => {
        set({
          apiConfig: null,
          isApiConfigured: false,
          error: null,
        });
      },

      setLoading: (loading: boolean) => {
        set({ isLoading: loading });
      },

      setError: (error: string | null) => {
        set({ error, isLoading: false });
      },

      clearError: () => {
        set({ error: null });
      },

      handleApiError: (error: any) => {
        // Check if it's an authentication error
        if (error.status_code === 401 || error.status_code === 403 ||
            error.detail?.includes('Invalid API credentials') ||
            error.detail?.includes('API access forbidden')) {
          // Clear API configuration to force re-authentication
          set({
            apiConfig: null,
            isApiConfigured: false,
            error: 'API credentials are invalid. Please reconfigure your API keys.',
          });
        } else {
          set({ error: error.detail || error.message || 'An error occurred' });
        }
      },

      setTradingPairs: (pairs: string[]) => {
        set({
          tradingPairs: pairs,
          tradingPairsLoaded: true
        });
      },
    }),
    {
      name: 'trading-app-storage',
      partialize: (state) => ({
        apiConfig: state.apiConfig,
        isApiConfigured: state.isApiConfigured,
        tradingPairs: state.tradingPairs,
        tradingPairsLoaded: state.tradingPairsLoaded,
      }),
    }
  )
);
