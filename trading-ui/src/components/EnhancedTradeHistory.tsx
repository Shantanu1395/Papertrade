import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { 
  Calendar, 
  Filter, 
  Download, 
  TrendingUp, 
  TrendingDown,
  Search,
  Clock,
  DollarSign
} from 'lucide-react';
import { getApiClient } from '../lib/api';
import { formatCurrency, formatNumber, formatPercentage } from '../lib/utils';
import { useToast } from './Toast';

interface EnhancedTrade {
  symbol: string;
  side: string;
  quantity: number;
  price: number;
  quoteQty: number;
  commission: number;
  commissionAsset: string;
  time: number;
  orderType: string;
  formatted_time: string;
  total_value: number;
  tradeId?: string;
}

interface TradeFilters {
  symbol?: string;
  side?: string;
  startDate?: string;
  endDate?: string;
  limit: number;
}

export function EnhancedTradeHistory() {
  const apiClient = getApiClient();
  const { showToast } = useToast();
  const [filters, setFilters] = useState<TradeFilters>({
    limit: 50
  });
  const [searchTerm, setSearchTerm] = useState('');

  // Fetch enhanced trade history
  const { data: tradesResponse, isLoading, error } = useQuery({
    queryKey: ['enhanced-trades', filters],
    queryFn: () => {
      return apiClient.getEnhancedTrades({
        limit: filters.limit,
        symbol: filters.symbol,
        side: filters.side
      });
    },
    refetchInterval: 30000,
  });

  const trades = tradesResponse?.trades || [];

  // Filter trades based on search term
  const filteredTrades = trades.filter((trade: EnhancedTrade) => {
    if (!searchTerm) return true;
    const searchLower = searchTerm.toLowerCase();
    return (
      trade.symbol.toLowerCase().includes(searchLower) ||
      trade.side.toLowerCase().includes(searchLower) ||
      (trade.tradeId && trade.tradeId.toLowerCase().includes(searchLower))
    );
  });

  // Calculate summary statistics
  const tradeSummary = React.useMemo(() => {
    const buyTrades = filteredTrades.filter((t: EnhancedTrade) => t.side === 'BUY');
    const sellTrades = filteredTrades.filter((t: EnhancedTrade) => t.side === 'SELL');
    const totalVolume = filteredTrades.reduce((sum: number, t: EnhancedTrade) => sum + t.quoteQty, 0);
    const totalCommission = filteredTrades.reduce((sum: number, t: EnhancedTrade) => sum + t.commission, 0);

    return {
      totalTrades: filteredTrades.length,
      buyTrades: buyTrades.length,
      sellTrades: sellTrades.length,
      totalVolume,
      totalCommission,
      avgTradeSize: filteredTrades.length > 0 ? totalVolume / filteredTrades.length : 0
    };
  }, [filteredTrades]);

  const handleFilterChange = (key: keyof TradeFilters, value: any) => {
    setFilters(prev => ({ ...prev, [key]: value }));
  };

  const exportTrades = () => {
    const csvContent = [
      ['Date', 'Symbol', 'Side', 'Quantity', 'Price', 'Total', 'Commission'].join(','),
      ...filteredTrades.map((trade: EnhancedTrade) => [
        trade.formatted_time || new Date(trade.time).toLocaleString(),
        trade.symbol,
        trade.side,
        trade.quantity,
        trade.price,
        trade.quoteQty,
        `${trade.commission} ${trade.commissionAsset}`
      ].join(','))
    ].join('\n');

    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `trade_history_${new Date().toISOString().split('T')[0]}.csv`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    showToast('success', 'Trade history exported successfully');
  };

  if (error) {
    return (
      <div className="crypto-card">
        <div className="text-center py-8">
          <div className="text-red-500 mb-2">Failed to load trade history</div>
          <button 
            onClick={() => window.location.reload()}
            className="crypto-button-primary"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold">Enhanced Trade History</h2>
        <button
          onClick={exportTrades}
          className="crypto-button-secondary flex items-center gap-2"
        >
          <Download className="w-4 h-4" />
          Export CSV
        </button>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="crypto-card">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-blue-500/10 rounded-lg">
              <Clock className="w-5 h-5 text-blue-500" />
            </div>
            <div>
              <div className="text-sm text-muted-foreground">Total Trades</div>
              <div className="text-lg font-semibold">{tradeSummary.totalTrades}</div>
            </div>
          </div>
        </div>

        <div className="crypto-card">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-green-500/10 rounded-lg">
              <TrendingUp className="w-5 h-5 text-green-500" />
            </div>
            <div>
              <div className="text-sm text-muted-foreground">Buy / Sell</div>
              <div className="text-lg font-semibold">
                {tradeSummary.buyTrades} / {tradeSummary.sellTrades}
              </div>
            </div>
          </div>
        </div>

        <div className="crypto-card">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-purple-500/10 rounded-lg">
              <DollarSign className="w-5 h-5 text-purple-500" />
            </div>
            <div>
              <div className="text-sm text-muted-foreground">Total Volume</div>
              <div className="text-lg font-semibold">
                {formatCurrency(tradeSummary.totalVolume)}
              </div>
            </div>
          </div>
        </div>

        <div className="crypto-card">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-orange-500/10 rounded-lg">
              <TrendingDown className="w-5 h-5 text-orange-500" />
            </div>
            <div>
              <div className="text-sm text-muted-foreground">Avg Trade Size</div>
              <div className="text-lg font-semibold">
                {formatCurrency(tradeSummary.avgTradeSize)}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Filters */}
      <div className="crypto-card">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {/* Search */}
          <div>
            <label className="block text-sm font-medium mb-2">Search</label>
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
              <input
                type="text"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                placeholder="Search symbol, side, or ID..."
                className="crypto-input pl-10"
              />
            </div>
          </div>

          {/* Start Date */}
          <div>
            <label className="block text-sm font-medium mb-2">Start Date</label>
            <input
              type="date"
              value={filters.startDate || ''}
              onChange={(e) => handleFilterChange('startDate', e.target.value)}
              className="crypto-input"
            />
          </div>

          {/* End Date */}
          <div>
            <label className="block text-sm font-medium mb-2">End Date</label>
            <input
              type="date"
              value={filters.endDate || ''}
              onChange={(e) => handleFilterChange('endDate', e.target.value)}
              className="crypto-input"
            />
          </div>

          {/* Limit */}
          <div>
            <label className="block text-sm font-medium mb-2">Limit</label>
            <select
              value={filters.limit}
              onChange={(e) => handleFilterChange('limit', parseInt(e.target.value))}
              className="crypto-input"
            >
              <option value={25}>25 trades</option>
              <option value={50}>50 trades</option>
              <option value={100}>100 trades</option>
              <option value={250}>250 trades</option>
            </select>
          </div>
        </div>
      </div>

      {/* Trade History Table */}
      <div className="crypto-card">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold">Recent Trades</h3>
          <div className="text-sm text-muted-foreground">
            Showing {filteredTrades.length} of {trades.length} trades
          </div>
        </div>

        {isLoading ? (
          <div className="text-center py-8">
            <div className="animate-spin w-8 h-8 border-2 border-primary border-t-transparent rounded-full mx-auto"></div>
            <div className="mt-2 text-muted-foreground">Loading trades...</div>
          </div>
        ) : filteredTrades.length === 0 ? (
          <div className="text-center py-8 text-muted-foreground">
            No trades found matching your criteria
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-border">
                  <th className="text-left py-3 px-2">Date</th>
                  <th className="text-left py-3 px-2">Symbol</th>
                  <th className="text-center py-3 px-2">Side</th>
                  <th className="text-right py-3 px-2">Quantity</th>
                  <th className="text-right py-3 px-2">Price</th>
                  <th className="text-right py-3 px-2">Total</th>
                  <th className="text-right py-3 px-2">Commission</th>
                </tr>
              </thead>
              <tbody>
                {filteredTrades.map((trade: EnhancedTrade, index: number) => (
                  <tr key={trade.tradeId || `${trade.symbol}-${trade.time}-${index}`} className="border-b border-border/50 hover:bg-muted/30">
                    <td className="py-3 px-2 text-sm">
                      {new Date(trade.time).toLocaleDateString()}
                      <div className="text-xs text-muted-foreground">
                        {new Date(trade.time).toLocaleTimeString()}
                      </div>
                    </td>
                    <td className="py-3 px-2">
                      <div className="flex items-center gap-2">
                        <div className="w-6 h-6 bg-primary/10 rounded-full flex items-center justify-center">
                          <span className="text-xs font-medium text-primary">
                            {trade.symbol.slice(0, 2)}
                          </span>
                        </div>
                        <span className="font-medium">{trade.symbol}</span>
                      </div>
                    </td>
                    <td className="text-center py-3 px-2">
                      <span className={`inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium ${
                        trade.side === 'BUY'
                          ? 'bg-green-500/10 text-green-500'
                          : 'bg-red-500/10 text-red-500'
                      }`}>
                        {trade.side === 'BUY' ? (
                          <TrendingUp className="w-3 h-3" />
                        ) : (
                          <TrendingDown className="w-3 h-3" />
                        )}
                        {trade.side}
                      </span>
                    </td>
                    <td className="text-right py-3 px-2 font-mono">
                      {formatNumber(trade.quantity, 6)}
                    </td>
                    <td className="text-right py-3 px-2 font-mono">
                      {formatCurrency(trade.price)}
                    </td>
                    <td className="text-right py-3 px-2 font-mono font-medium">
                      {formatCurrency(trade.quoteQty)}
                    </td>
                    <td className="text-right py-3 px-2 font-mono text-sm text-muted-foreground">
                      {formatNumber(trade.commission, 6)} {trade.commissionAsset}
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
}
