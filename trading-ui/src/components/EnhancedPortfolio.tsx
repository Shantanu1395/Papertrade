import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { 
  TrendingUp, 
  TrendingDown, 
  DollarSign, 
  PieChart, 
  BarChart3, 
  RefreshCw,
  Download,
  Calendar,
  Target,
  Activity
} from 'lucide-react';
import { getApiClient } from '../lib/api';
import { useToast } from './Toast';
import { formatCurrency, formatNumber, formatPercentage } from '../lib/utils';

interface EnhancedAsset {
  asset: string;
  free: number;
  locked: number;
  total_quantity: number;
  avg_buy_price: number;
  current_price: number;
  current_value: number;
  total_invested: number;
  unrealized_pnl: number;
  unrealized_pnl_percent: number;
  last_updated: string;
}

interface PortfolioAnalytics {
  total_portfolio_value: number;
  total_invested: number;
  total_unrealized_pnl: number;
  total_unrealized_pnl_percent: number;
  total_realized_pnl: number;
  asset_allocation: Record<string, {
    value: number;
    percentage: number;
    quantity: number;
  }>;
  top_performers: [string, number][];
  worst_performers: [string, number][];
  trading_stats: {
    total_trades: number;
    buy_trades: number;
    sell_trades: number;
    total_volume: number;
    avg_trade_size: number;
    most_traded_asset: string;
    trading_frequency: number;
  };
  last_updated: string;
}

export function EnhancedPortfolio() {
  const apiClient = getApiClient();
  const { showToast } = useToast();
  const queryClient = useQueryClient();
  const [selectedView, setSelectedView] = useState<'overview' | 'analytics' | 'allocation'>('overview');

  // Fetch enhanced portfolio
  const { data: portfolio = [], isLoading: portfolioLoading, error: portfolioError } = useQuery({
    queryKey: ['enhanced-portfolio'],
    queryFn: () => apiClient.getEnhancedPortfolio(),
    refetchInterval: 30000, // Refresh every 30 seconds
  });

  // Fetch portfolio analytics
  const { data: analytics, isLoading: analyticsLoading } = useQuery({
    queryKey: ['portfolio-analytics'],
    queryFn: () => apiClient.getPortfolioAnalytics(),
    refetchInterval: 60000, // Refresh every minute
  });

  // Sync with Binance mutation
  const syncMutation = useMutation({
    mutationFn: () => apiClient.syncPortfolio(),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['enhanced-portfolio'] });
      queryClient.invalidateQueries({ queryKey: ['portfolio-analytics'] });
      showToast('success', 'Portfolio synced with Binance successfully');
    },
    onError: (error: any) => {
      showToast('error', error.detail || 'Failed to sync portfolio');
    },
  });

  // Export report mutation
  const exportMutation = useMutation({
    mutationFn: async () => {
      // Get both portfolio and analytics data for the report
      const [portfolioData, analyticsData] = await Promise.all([
        apiClient.getEnhancedPortfolio(),
        apiClient.getPortfolioAnalytics()
      ]);
      return { portfolio: portfolioData, analytics: analyticsData };
    },
    onSuccess: (data) => {
      // Create and download the report
      const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `portfolio_report_${new Date().toISOString().split('T')[0]}.json`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
      showToast('success', 'Portfolio report exported successfully');
    },
    onError: (error: any) => {
      showToast('error', error.detail || 'Failed to export report');
    },
  });

  if (portfolioError) {
    return (
      <div className="crypto-card">
        <div className="text-center py-8">
          <div className="text-red-500 mb-2">Failed to load enhanced portfolio</div>
          <button 
            onClick={() => queryClient.invalidateQueries({ queryKey: ['enhanced-portfolio'] })}
            className="crypto-button-primary"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  const renderOverview = () => (
    <div className="space-y-6">
      {/* Portfolio Summary Cards */}
      {analytics && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="crypto-card">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-blue-500/10 rounded-lg">
                <DollarSign className="w-5 h-5 text-blue-500" />
              </div>
              <div>
                <div className="text-sm text-muted-foreground">Total Value</div>
                <div className="text-lg font-semibold">
                  {formatCurrency(analytics.total_portfolio_value)}
                </div>
              </div>
            </div>
          </div>

          <div className="crypto-card">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-green-500/10 rounded-lg">
                <Target className="w-5 h-5 text-green-500" />
              </div>
              <div>
                <div className="text-sm text-muted-foreground">Total Invested</div>
                <div className="text-lg font-semibold">
                  {formatCurrency(analytics.total_invested)}
                </div>
              </div>
            </div>
          </div>

          <div className="crypto-card">
            <div className="flex items-center gap-3">
              <div className={`p-2 rounded-lg ${
                analytics.total_unrealized_pnl >= 0 
                  ? 'bg-green-500/10' 
                  : 'bg-red-500/10'
              }`}>
                {analytics.total_unrealized_pnl >= 0 ? (
                  <TrendingUp className="w-5 h-5 text-green-500" />
                ) : (
                  <TrendingDown className="w-5 h-5 text-red-500" />
                )}
              </div>
              <div>
                <div className="text-sm text-muted-foreground">Unrealized PnL</div>
                <div className={`text-lg font-semibold ${
                  analytics.total_unrealized_pnl >= 0 ? 'text-green-500' : 'text-red-500'
                }`}>
                  {formatCurrency(analytics.total_unrealized_pnl)}
                  <span className="text-sm ml-1">
                    ({formatPercentage(analytics.total_unrealized_pnl_percent)})
                  </span>
                </div>
              </div>
            </div>
          </div>

          <div className="crypto-card">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-purple-500/10 rounded-lg">
                <Activity className="w-5 h-5 text-purple-500" />
              </div>
              <div>
                <div className="text-sm text-muted-foreground">Realized PnL</div>
                <div className={`text-lg font-semibold ${
                  analytics.total_realized_pnl >= 0 ? 'text-green-500' : 'text-red-500'
                }`}>
                  {formatCurrency(analytics.total_realized_pnl)}
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Holdings Table */}
      <div className="crypto-card">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold">Holdings</h3>
          <div className="flex gap-2">
            <button
              onClick={() => syncMutation.mutate()}
              disabled={syncMutation.isPending}
              className="crypto-button-secondary flex items-center gap-2"
            >
              <RefreshCw className={`w-4 h-4 ${syncMutation.isPending ? 'animate-spin' : ''}`} />
              Sync
            </button>
            <button
              onClick={() => exportMutation.mutate()}
              disabled={exportMutation.isPending}
              className="crypto-button-secondary flex items-center gap-2"
            >
              <Download className="w-4 h-4" />
              Export
            </button>
          </div>
        </div>

        {portfolioLoading ? (
          <div className="text-center py-8">
            <div className="animate-spin w-8 h-8 border-2 border-primary border-t-transparent rounded-full mx-auto"></div>
            <div className="mt-2 text-muted-foreground">Loading portfolio...</div>
          </div>
        ) : portfolio.length === 0 ? (
          <div className="text-center py-8 text-muted-foreground">
            No assets in portfolio
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-border">
                  <th className="text-left py-3 px-2">Asset</th>
                  <th className="text-right py-3 px-2">Quantity</th>
                  <th className="text-right py-3 px-2">Avg Buy Price</th>
                  <th className="text-right py-3 px-2">Current Price</th>
                  <th className="text-right py-3 px-2">Value</th>
                  <th className="text-right py-3 px-2">PnL</th>
                </tr>
              </thead>
              <tbody>
                {portfolio.map((asset: EnhancedAsset) => (
                  <tr key={asset.asset} className="border-b border-border/50 hover:bg-muted/30">
                    <td className="py-3 px-2">
                      <div className="flex items-center gap-2">
                        <div className="w-8 h-8 bg-primary/10 rounded-full flex items-center justify-center">
                          <span className="text-xs font-medium text-primary">
                            {asset.asset.slice(0, 2)}
                          </span>
                        </div>
                        <span className="font-medium">{asset.asset}</span>
                      </div>
                    </td>
                    <td className="text-right py-3 px-2">
                      {formatNumber(asset.total_quantity, 6)}
                    </td>
                    <td className="text-right py-3 px-2">
                      {formatCurrency(asset.avg_buy_price)}
                    </td>
                    <td className="text-right py-3 px-2">
                      {formatCurrency(asset.current_price)}
                    </td>
                    <td className="text-right py-3 px-2 font-medium">
                      {formatCurrency(asset.current_value)}
                    </td>
                    <td className={`text-right py-3 px-2 font-medium ${
                      asset.unrealized_pnl >= 0 ? 'text-green-500' : 'text-red-500'
                    }`}>
                      {formatCurrency(asset.unrealized_pnl)}
                      <div className="text-xs">
                        ({formatPercentage(asset.unrealized_pnl_percent)})
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold">Enhanced Portfolio</h2>
        
        {/* View Toggle */}
        <div className="flex gap-1 p-1 bg-muted/30 rounded-lg">
          {[
            { key: 'overview', label: 'Overview', icon: BarChart3 },
            { key: 'analytics', label: 'Analytics', icon: TrendingUp },
            { key: 'allocation', label: 'Allocation', icon: PieChart },
          ].map(({ key, label, icon: Icon }) => (
            <button
              key={key}
              onClick={() => setSelectedView(key as any)}
              className={`flex items-center gap-2 px-3 py-1.5 rounded text-sm transition-colors ${
                selectedView === key
                  ? 'bg-primary text-primary-foreground'
                  : 'hover:bg-muted/50'
              }`}
            >
              <Icon className="w-4 h-4" />
              {label}
            </button>
          ))}
        </div>
      </div>

      {/* Content */}
      {selectedView === 'overview' && renderOverview()}
      {selectedView === 'analytics' && (
        <div className="crypto-card">
          <div className="text-center py-8 text-muted-foreground">
            Analytics view coming soon...
          </div>
        </div>
      )}
      {selectedView === 'allocation' && (
        <div className="crypto-card">
          <div className="text-center py-8 text-muted-foreground">
            Allocation view coming soon...
          </div>
        </div>
      )}
    </div>
  );
}
