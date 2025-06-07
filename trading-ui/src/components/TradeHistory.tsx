'use client';

import { useQuery } from '@tanstack/react-query';
import { getApiClient } from '@/lib/api';
import { formatDateTime, formatCurrency, formatNumber } from '@/lib/utils';
import { History, RefreshCw, Search, Filter } from 'lucide-react';
import { useState } from 'react';

export function TradeHistory() {
  const apiClient = getApiClient();
  const [searchTerm, setSearchTerm] = useState('');
  const [filterSide, setFilterSide] = useState<'ALL' | 'BUY' | 'SELL'>('ALL');

  const { data: trades, isLoading, error, refetch } = useQuery({
    queryKey: ['trade-history'],
    queryFn: () => apiClient.getTradeHistory(),
  });

  const filteredTrades = trades?.filter(trade => {
    const matchesSearch = trade.symbol.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesFilter = filterSide === 'ALL' || trade.side === filterSide;
    return matchesSearch && matchesFilter;
  }) || [];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-primary/10 rounded-lg">
            <History className="w-5 h-5 text-primary" />
          </div>
          <div>
            <h3 className="text-lg font-medium">Trade History</h3>
            <p className="text-sm text-muted-foreground">
              {trades?.length || 0} total trades
            </p>
          </div>
        </div>
        <button
          onClick={() => refetch()}
          disabled={isLoading}
          className="crypto-button-secondary flex items-center gap-2"
        >
          <RefreshCw className={`w-4 h-4 ${isLoading ? 'animate-spin' : ''}`} />
          Refresh
        </button>
      </div>

      {/* Filters */}
      <div className="crypto-card">
        <div className="flex flex-col sm:flex-row gap-4">
          <div className="flex-1">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
              <input
                type="text"
                placeholder="Search by symbol..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="crypto-input pl-10"
              />
            </div>
          </div>
          <div className="flex items-center gap-2">
            <Filter className="w-4 h-4 text-muted-foreground" />
            <select
              value={filterSide}
              onChange={(e) => setFilterSide(e.target.value as 'ALL' | 'BUY' | 'SELL')}
              className="crypto-input w-auto"
            >
              <option value="ALL">All Trades</option>
              <option value="BUY">Buy Orders</option>
              <option value="SELL">Sell Orders</option>
            </select>
          </div>
        </div>
      </div>

      {/* Trade List */}
      <div className="crypto-card">
        {isLoading ? (
          <div className="space-y-3">
            {[...Array(5)].map((_, i) => (
              <div key={i} className="animate-pulse flex items-center justify-between p-4 border border-border rounded-lg">
                <div className="flex items-center gap-4">
                  <div className="w-12 h-6 bg-muted rounded"></div>
                  <div className="space-y-1">
                    <div className="h-4 bg-muted rounded w-20"></div>
                    <div className="h-3 bg-muted rounded w-32"></div>
                  </div>
                </div>
                <div className="text-right space-y-1">
                  <div className="h-4 bg-muted rounded w-24"></div>
                  <div className="h-3 bg-muted rounded w-16"></div>
                </div>
              </div>
            ))}
          </div>
        ) : error ? (
          <div className="text-center py-8 text-muted-foreground">
            <History className="w-8 h-8 mx-auto mb-2" />
            <p>Failed to load trade history</p>
          </div>
        ) : filteredTrades.length === 0 ? (
          <div className="text-center py-8 text-muted-foreground">
            <History className="w-8 h-8 mx-auto mb-2" />
            <p>No trades found</p>
            {searchTerm || filterSide !== 'ALL' ? (
              <p className="text-sm">Try adjusting your filters</p>
            ) : (
              <p className="text-sm">Start trading to see your history here</p>
            )}
          </div>
        ) : (
          <div className="space-y-2">
            {filteredTrades.map((trade, index) => (
              <div
                key={`${trade.tradeId}-${index}`}
                className="flex items-center justify-between p-4 border border-border rounded-lg hover:bg-muted/50 transition-colors"
              >
                <div className="flex items-center gap-4">
                  <div className={`
                    px-2 py-1 rounded text-xs font-medium
                    ${trade.side === 'BUY' 
                      ? 'bg-green-500/10 text-green-500' 
                      : 'bg-red-500/10 text-red-500'
                    }
                  `}>
                    {trade.side}
                  </div>
                  <div>
                    <div className="font-medium">{trade.symbol}</div>
                    <div className="text-sm text-muted-foreground">
                      {formatDateTime(trade.time)}
                    </div>
                  </div>
                </div>
                <div className="text-right">
                  <div className="font-medium">
                    {formatNumber(trade.quantity || trade.qty || 0, 6)} @ {formatCurrency(trade.price)}
                  </div>
                  <div className="text-sm text-muted-foreground">
                    Total: {formatCurrency(trade.quoteQty)}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
