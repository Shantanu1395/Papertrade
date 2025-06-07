'use client';

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { getApiClient } from '@/lib/api';
import { formatCurrency, formatNumber } from '@/lib/utils';
import { useToast } from '@/components/Toast';
import { BuyOrderModal } from '@/components/BuyOrderModal';
import { SellPercentageModal } from '@/components/SellPercentageModal';
import { useAppStore } from '@/stores/useAppStore';
import {
  DollarSign,
  Wallet,
  RefreshCw,
  AlertTriangle,
  Trash2,
  TrendingDown,
  Plus
} from 'lucide-react';
import { useState } from 'react';

export function PortfolioOverview() {
  const queryClient = useQueryClient();
  const apiClient = getApiClient();
  const { showToast } = useToast();
  const { handleApiError } = useAppStore();
  const [showSellConfirm, setShowSellConfirm] = useState(false);
  const [showBuyModal, setShowBuyModal] = useState(false);
  const [showSellModal, setShowSellModal] = useState(false);
  const [selectedAsset, setSelectedAsset] = useState<{ asset: string; free: number; locked: number } | null>(null);

  // Fetch USDT balance
  const { data: usdtBalance, isLoading: usdtLoading, error: usdtError } = useQuery({
    queryKey: ['usdt-balance'],
    queryFn: () => apiClient.getUSDTBalance(),
    refetchInterval: 30000, // Refresh every 30 seconds
  });

  // Fetch portfolio
  const { data: portfolio, isLoading: portfolioLoading, error: portfolioError } = useQuery({
    queryKey: ['portfolio'],
    queryFn: () => apiClient.getPortfolio(),
    refetchInterval: 30000,
  });

  // Sell all mutation
  const sellAllMutation = useMutation({
    mutationFn: () => apiClient.sellAllToUSDT(),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['usdt-balance'] });
      queryClient.invalidateQueries({ queryKey: ['portfolio'] });
      setShowSellConfirm(false);
      showToast('success', `Successfully sold all assets! New USDT balance: ${formatCurrency(data.usdt_balance)}`);
    },
    onError: (error: unknown) => {
      handleApiError(error);
      const err = error as { response?: { data?: { detail?: string } }; detail?: string; message?: string };
      const errorMessage = err.response?.data?.detail || err.detail || err.message || 'Failed to sell assets. Please try again.';
      showToast('error', errorMessage);
    },
  });

  const handleRefresh = () => {
    queryClient.invalidateQueries({ queryKey: ['usdt-balance'] });
    queryClient.invalidateQueries({ queryKey: ['portfolio'] });
  };

  const handleSellAll = () => {
    sellAllMutation.mutate();
  };

  const isLoading = usdtLoading || portfolioLoading;

  return (
    <div className="space-y-4 lg:space-y-6">
      {/* Header with refresh button */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h3 className="text-lg font-medium">Portfolio Overview</h3>
          <p className="text-sm text-muted-foreground mt-1">
            Monitor your holdings and balances
          </p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={handleRefresh}
            disabled={isLoading}
            className="crypto-button-secondary flex items-center gap-2"
          >
            <RefreshCw className={`w-4 h-4 ${isLoading ? 'animate-spin' : ''}`} />
            <span className="hidden sm:inline">Refresh</span>
          </button>

          {(usdtError || portfolioError) && (
            <button
              onClick={() => handleApiError({ detail: 'API connection failed' })}
              className="crypto-button-destructive flex items-center gap-2 text-xs px-2 py-1"
              title="Reconfigure API"
            >
              <AlertTriangle className="w-3 h-3" />
              <span className="hidden sm:inline">Fix API</span>
            </button>
          )}
        </div>
      </div>

      {/* USDT Balance Card */}
      <div className="crypto-card">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-primary/10 rounded-lg flex-shrink-0">
              <DollarSign className="w-5 h-5 text-primary" />
            </div>
            <div className="min-w-0">
              <h4 className="font-medium">USDT Balance</h4>
              <p className="text-sm text-muted-foreground">Available for trading</p>
            </div>
          </div>

          <div className="flex flex-col sm:flex-row items-end sm:items-center gap-3">
            <div className="text-right sm:text-left">
              {usdtLoading ? (
                <div className="animate-pulse">
                  <div className="h-8 bg-muted rounded w-32 ml-auto sm:ml-0"></div>
                </div>
              ) : usdtError ? (
                <div className="text-destructive text-sm">
                  <div>Failed to load balance</div>
                  <div className="text-xs mt-1 text-muted-foreground">
                    {(usdtError as { detail?: string })?.detail || 'Check API configuration'}
                  </div>
                </div>
              ) : (
                <div className="text-2xl lg:text-3xl font-bold text-primary">
                  {formatCurrency(usdtBalance?.balance || 0)}
                </div>
              )}
            </div>

            <button
              onClick={() => setShowBuyModal(true)}
              className="crypto-button-primary flex items-center gap-2 whitespace-nowrap"
              disabled={usdtLoading || !usdtBalance || usdtBalance.balance <= 0}
            >
              <Plus className="w-4 h-4" />
              <span className="hidden sm:inline">Buy Crypto</span>
              <span className="sm:hidden">Buy</span>
            </button>
          </div>
        </div>
      </div>

      {/* Portfolio Holdings */}
      <div className="crypto-card">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6">
          <div className="flex items-center gap-3 min-w-0">
            <div className="p-2 bg-secondary/10 rounded-lg flex-shrink-0">
              <Wallet className="w-5 h-5 text-secondary-foreground" />
            </div>
            <div className="min-w-0">
              <h4 className="font-medium">Holdings</h4>
              <p className="text-sm text-muted-foreground">
                {portfolio?.length || 0} assets
              </p>
            </div>
          </div>

          <button
            onClick={() => setShowSellConfirm(true)}
            className={`flex items-center gap-2 whitespace-nowrap ${
              portfolio && portfolio.length > 0
                ? 'crypto-button-destructive'
                : 'crypto-button-secondary opacity-50 cursor-not-allowed'
            }`}
            disabled={sellAllMutation.isPending || !portfolio || portfolio.length === 0}
            title={
              !portfolio || portfolio.length === 0
                ? 'No assets to sell'
                : 'Sell all holdings to USDT'
            }
          >
            <Trash2 className="w-4 h-4 flex-shrink-0" />
            <span className="hidden sm:inline">
              {sellAllMutation.isPending ? 'Selling...' : 'Sell All'}
            </span>
            <span className="sm:hidden">
              {sellAllMutation.isPending ? '...' : 'Sell'}
            </span>
          </button>
        </div>

        {portfolioLoading ? (
          <div className="space-y-3">
            {[...Array(3)].map((_, i) => (
              <div key={i} className="animate-pulse flex items-center justify-between p-3 bg-muted/50 rounded">
                <div className="flex items-center gap-3">
                  <div className="w-8 h-8 bg-muted rounded-full"></div>
                  <div className="space-y-1">
                    <div className="h-4 bg-muted rounded w-16"></div>
                    <div className="h-3 bg-muted rounded w-12"></div>
                  </div>
                </div>
                <div className="text-right space-y-1">
                  <div className="h-4 bg-muted rounded w-20"></div>
                  <div className="h-3 bg-muted rounded w-16"></div>
                </div>
              </div>
            ))}
          </div>
        ) : portfolioError ? (
          <div className="text-center py-8 text-muted-foreground">
            <AlertTriangle className="w-8 h-8 mx-auto mb-2" />
            <p>Failed to load portfolio</p>
          </div>
        ) : !portfolio || portfolio.length === 0 ? (
          <div className="text-center py-12 text-muted-foreground">
            <Wallet className="w-12 h-12 mx-auto mb-4 opacity-50" />
            <p className="text-lg font-medium mb-2">No holdings found</p>
            <p className="text-sm mb-4">Your portfolio is empty - all assets have been converted to USDT</p>
            <div className="text-xs bg-muted/30 rounded-lg p-3 max-w-sm mx-auto">
              💡 <strong>Tip:</strong> The &quot;Sell All&quot; button will become active when you have crypto holdings to sell
            </div>
          </div>
        ) : (
          <div className="space-y-3">
            {portfolio.map((asset) => (
              <div
                key={asset.asset}
                className="flex items-center justify-between p-3 lg:p-4 hover:bg-muted/50 rounded-lg transition-colors border border-transparent hover:border-border"
              >
                <div className="flex items-center gap-3 min-w-0">
                  <div className="w-10 h-10 lg:w-12 lg:h-12 bg-primary/10 rounded-full flex items-center justify-center flex-shrink-0">
                    <span className="text-sm lg:text-base font-medium text-primary">
                      {asset.asset.slice(0, 2)}
                    </span>
                  </div>
                  <div className="min-w-0">
                    <div className="font-medium text-sm lg:text-base">{asset.asset}</div>
                    <div className="text-xs lg:text-sm text-muted-foreground">
                      {asset.locked > 0 ? `${formatNumber(asset.locked)} locked` : 'Available'}
                    </div>
                  </div>
                </div>

                <div className="flex items-center gap-3">
                  <div className="text-right flex-shrink-0">
                    <div className="font-medium text-sm lg:text-base">
                      {formatNumber(asset.free, 6)}
                    </div>
                    <div className="text-xs lg:text-sm text-muted-foreground">
                      Total: {formatNumber(asset.free + asset.locked, 6)}
                    </div>
                  </div>

                  <button
                    onClick={() => {
                      setSelectedAsset(asset);
                      setShowSellModal(true);
                    }}
                    className="crypto-button-secondary flex items-center gap-1 text-xs px-2 py-1"
                    disabled={asset.free <= 0}
                    title={`Sell ${asset.asset} by percentage`}
                  >
                    <TrendingDown className="w-3 h-3" />
                    <span className="hidden sm:inline">Sell</span>
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Sell All Confirmation Modal */}
      {showSellConfirm && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="crypto-card max-w-md w-full">
            <div className="flex items-center gap-3 mb-4">
              <div className="p-2 bg-destructive/10 rounded-lg">
                <AlertTriangle className="w-5 h-5 text-destructive" />
              </div>
              <h3 className="text-lg font-medium">Confirm Sell All</h3>
            </div>
            
            <p className="text-muted-foreground mb-6">
              Are you sure you want to sell all your holdings to USDT? This action cannot be undone.
            </p>
            
            <div className="flex gap-3">
              <button
                onClick={() => setShowSellConfirm(false)}
                className="crypto-button-secondary flex-1"
                disabled={sellAllMutation.isPending}
              >
                Cancel
              </button>
              <button
                onClick={handleSellAll}
                className="crypto-button-destructive flex-1"
                disabled={sellAllMutation.isPending}
              >
                {sellAllMutation.isPending ? 'Selling...' : 'Sell All'}
              </button>
            </div>
            
            {sellAllMutation.error && (
              <div className="mt-4 p-3 bg-destructive/10 border border-destructive/20 rounded text-destructive text-sm">
                {(sellAllMutation.error as any)?.response?.data?.detail ||
                 (sellAllMutation.error as any)?.detail ||
                 (sellAllMutation.error as any)?.message ||
                 'Failed to sell assets. Please try again.'}
              </div>
            )}
          </div>
        </div>
      )}

      {/* Buy Order Modal */}
      <BuyOrderModal
        isOpen={showBuyModal}
        onClose={() => setShowBuyModal(false)}
      />

      {/* Sell Percentage Modal */}
      <SellPercentageModal
        isOpen={showSellModal}
        onClose={() => {
          setShowSellModal(false);
          setSelectedAsset(null);
        }}
        asset={selectedAsset}
      />
    </div>
  );
}
