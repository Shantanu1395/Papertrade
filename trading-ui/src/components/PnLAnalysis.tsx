'use client';

import { useState } from 'react';
import { useMutation } from '@tanstack/react-query';
import { getApiClient } from '@/lib/api';
import { formatCurrency, formatTimeForApi, getPnLColor } from '@/lib/utils';
import { TrendingUp, Calendar, Calculator, BarChart3 } from 'lucide-react';
import { format, subDays, startOfDay, endOfDay } from 'date-fns';

export function PnLAnalysis() {
  const apiClient = getApiClient();
  const [startDate, setStartDate] = useState(format(subDays(new Date(), 30), 'yyyy-MM-dd'));
  const [endDate, setEndDate] = useState(format(new Date(), 'yyyy-MM-dd'));

  const pnlMutation = useMutation({
    mutationFn: (dateRange: { start_date: string; end_date: string }) => {
      return apiClient.calculateEnhancedPnL(dateRange);
    },
  });

  const handleCalculatePnL = () => {
    pnlMutation.mutate({
      start_date: startDate,
      end_date: endDate,
    });
  };

  const pnlData = pnlMutation.data;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-3">
        <div className="p-2 bg-primary/10 rounded-lg">
          <TrendingUp className="w-5 h-5 text-primary" />
        </div>
        <div>
          <h3 className="text-lg font-medium">PnL Analysis</h3>
          <p className="text-sm text-muted-foreground">
            Analyze your profit and loss over time
          </p>
        </div>
      </div>

      {/* Date Range Selector */}
      <div className="crypto-card">
        <div className="flex items-center gap-3 mb-4">
          <Calendar className="w-5 h-5 text-muted-foreground" />
          <h4 className="font-medium">Select Time Range</h4>
        </div>
        
        <div className="flex flex-col sm:flex-row gap-4">
          <div className="flex-1">
            <label className="block text-sm font-medium mb-2">Start Date</label>
            <input
              type="date"
              value={startDate}
              onChange={(e) => setStartDate(e.target.value)}
              className="crypto-input"
            />
          </div>
          <div className="flex-1">
            <label className="block text-sm font-medium mb-2">End Date</label>
            <input
              type="date"
              value={endDate}
              onChange={(e) => setEndDate(e.target.value)}
              className="crypto-input"
            />
          </div>
          <div className="flex items-end">
            <button
              onClick={handleCalculatePnL}
              disabled={pnlMutation.isPending}
              className="crypto-button-primary flex items-center gap-2"
            >
              <Calculator className="w-4 h-4" />
              {pnlMutation.isPending ? 'Calculating...' : 'Calculate PnL'}
            </button>
          </div>
        </div>
      </div>

      {/* PnL Summary */}
      {pnlData && (
        <div className="space-y-6">
          {/* Period Summary */}
          <div className="crypto-card">
            <h4 className="font-medium mb-4">
              Period: {pnlData.period.start_date} to {pnlData.period.end_date} ({pnlData.period.days} days)
            </h4>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="p-4 border border-border rounded-lg">
                <div className="flex items-center gap-3 mb-2">
                  <div className="p-2 bg-blue-500/10 rounded-lg">
                    <BarChart3 className="w-4 h-4 text-blue-500" />
                  </div>
                  <h5 className="font-medium">Net Trading Result</h5>
                </div>
                <div className={`text-2xl font-bold ${getPnLColor(pnlData.pnl_breakdown.net_result)}`}>
                  {formatCurrency(pnlData.pnl_breakdown.net_result)}
                </div>
              </div>

              <div className="p-4 border border-border rounded-lg">
                <div className="flex items-center gap-3 mb-2">
                  <div className="p-2 bg-green-500/10 rounded-lg">
                    <TrendingUp className="w-4 h-4 text-green-500" />
                  </div>
                  <h5 className="font-medium">Realized PnL</h5>
                </div>
                <div className={`text-2xl font-bold ${getPnLColor(pnlData.pnl_breakdown.realized_pnl)}`}>
                  {formatCurrency(pnlData.pnl_breakdown.realized_pnl)}
                </div>
              </div>

              <div className="p-4 border border-border rounded-lg">
                <div className="flex items-center gap-3 mb-2">
                  <div className="p-2 bg-purple-500/10 rounded-lg">
                    <TrendingUp className="w-4 h-4 text-purple-500" />
                  </div>
                  <h5 className="font-medium">Current Portfolio Value</h5>
                </div>
                <div className="text-2xl font-bold text-primary">
                  {formatCurrency(pnlData.pnl_breakdown.current_portfolio_value)}
                </div>
              </div>
            </div>
          </div>

          {/* Trading Summary */}
          <div className="crypto-card">
            <h4 className="font-medium mb-4">Trading Summary</h4>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="text-center">
                <div className="text-2xl font-bold text-primary">{pnlData.trading_summary.total_trades}</div>
                <div className="text-sm text-muted-foreground">Total Trades</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-green-500">{formatCurrency(pnlData.trading_summary.buy_volume)}</div>
                <div className="text-sm text-muted-foreground">Buy Volume</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-red-500">{formatCurrency(pnlData.trading_summary.sell_volume)}</div>
                <div className="text-sm text-muted-foreground">Sell Volume</div>
              </div>
              <div className="text-center">
                <div className={`text-2xl font-bold ${getPnLColor(pnlData.trading_summary.net_trading_result)}`}>
                  {formatCurrency(pnlData.trading_summary.net_trading_result)}
                </div>
                <div className="text-sm text-muted-foreground">Net Result</div>
              </div>
            </div>
          </div>

          {/* Symbol Breakdown */}
          {pnlData.symbol_breakdown && pnlData.symbol_breakdown.length > 0 && (
            <div className="crypto-card">
              <h4 className="font-medium mb-4">PnL by Symbol</h4>
              <div className="space-y-3">
                {pnlData.symbol_breakdown.map((symbolData) => (
                  <div key={symbolData.symbol} className="flex items-center justify-between p-3 border border-border rounded-lg">
                    <div>
                      <div className="font-medium">{symbolData.symbol}</div>
                      <div className="text-sm text-muted-foreground">
                        {symbolData.trades} trades
                      </div>
                    </div>
                    <div className="text-right">
                      <div className={`font-medium ${getPnLColor(symbolData.realized_pnl)}`}>
                        {formatCurrency(symbolData.realized_pnl)}
                      </div>
                      <div className="text-xs text-muted-foreground">
                        Realized PnL
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Error State */}
      {pnlMutation.error && (
        <div className="crypto-card">
          <div className="text-center py-8 text-destructive">
            <TrendingUp className="w-8 h-8 mx-auto mb-2" />
            <p>Failed to calculate PnL</p>
            <p className="text-sm text-muted-foreground mt-1">
              Please check your date range and try again
            </p>
          </div>
        </div>
      )}

      {/* Empty State */}
      {!pnlData && !pnlMutation.isPending && !pnlMutation.error && (
        <div className="crypto-card">
          <div className="text-center py-8 text-muted-foreground">
            <Calculator className="w-8 h-8 mx-auto mb-2" />
            <p>Select a date range and click &quot;Calculate PnL&quot; to analyze your performance</p>
          </div>
        </div>
      )}
    </div>
  );
}
