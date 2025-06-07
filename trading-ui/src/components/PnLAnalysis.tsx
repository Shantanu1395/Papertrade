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
    mutationFn: (timeRange: { start_time: string; end_time: string }) => 
      apiClient.calculatePnL(timeRange),
  });

  const handleCalculatePnL = () => {
    const startDateTime = formatTimeForApi(startOfDay(new Date(startDate)));
    const endDateTime = formatTimeForApi(endOfDay(new Date(endDate)));
    
    pnlMutation.mutate({
      start_time: startDateTime,
      end_time: endDateTime,
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
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="crypto-card">
            <div className="flex items-center gap-3 mb-2">
              <div className="p-2 bg-blue-500/10 rounded-lg">
                <BarChart3 className="w-4 h-4 text-blue-500" />
              </div>
              <h4 className="font-medium">Total PnL</h4>
            </div>
            <div className={`text-2xl font-bold ${getPnLColor(pnlData.total_pnl)}`}>
              {formatCurrency(pnlData.total_pnl)}
            </div>
          </div>

          <div className="crypto-card">
            <div className="flex items-center gap-3 mb-2">
              <div className="p-2 bg-green-500/10 rounded-lg">
                <TrendingUp className="w-4 h-4 text-green-500" />
              </div>
              <h4 className="font-medium">Realized PnL</h4>
            </div>
            <div className={`text-2xl font-bold ${getPnLColor(pnlData.realized_pnl)}`}>
              {formatCurrency(pnlData.realized_pnl)}
            </div>
          </div>

          <div className="crypto-card">
            <div className="flex items-center gap-3 mb-2">
              <div className="p-2 bg-orange-500/10 rounded-lg">
                <TrendingUp className="w-4 h-4 text-orange-500" />
              </div>
              <h4 className="font-medium">Unrealized PnL</h4>
            </div>
            <div className={`text-2xl font-bold ${getPnLColor(pnlData.unrealized_pnl)}`}>
              {formatCurrency(pnlData.unrealized_pnl)}
            </div>
          </div>
        </div>
      )}

      {/* Symbol Breakdown */}
      {pnlData && Object.keys(pnlData.symbol_pnl).length > 0 && (
        <div className="crypto-card">
          <h4 className="font-medium mb-4">PnL by Symbol</h4>
          <div className="space-y-3">
            {Object.entries(pnlData.symbol_pnl).map(([symbol, pnl]) => (
              <div key={symbol} className="flex items-center justify-between p-3 border border-border rounded-lg">
                <div className="font-medium">{symbol}</div>
                <div className="text-right space-y-1">
                  <div className={`font-medium ${getPnLColor(pnl.total_pnl)}`}>
                    {formatCurrency(pnl.total_pnl)}
                  </div>
                  <div className="text-xs text-muted-foreground">
                    R: {formatCurrency(pnl.realized_pnl)} | 
                    U: {formatCurrency(pnl.unrealized_pnl)}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Open Positions */}
      {pnlData && Object.keys(pnlData.open_positions).length > 0 && (
        <div className="crypto-card">
          <h4 className="font-medium mb-4">Open Positions</h4>
          <div className="space-y-3">
            {Object.entries(pnlData.open_positions).map(([symbol, position]) => (
              <div key={symbol} className="flex items-center justify-between p-3 border border-border rounded-lg">
                <div>
                  <div className="font-medium">{symbol}</div>
                  <div className="text-sm text-muted-foreground">
                    Qty: {position.quantity.toFixed(6)}
                  </div>
                </div>
                <div className="text-right">
                  <div className={`font-medium ${getPnLColor(position.unrealized_pnl)}`}>
                    {formatCurrency(position.unrealized_pnl)}
                  </div>
                  <div className="text-xs text-muted-foreground">
                    Avg: {formatCurrency(position.avg_buy_price)} | 
                    Current: {formatCurrency(position.current_price)}
                  </div>
                </div>
              </div>
            ))}
          </div>
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
