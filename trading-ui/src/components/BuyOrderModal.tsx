'use client';

import { useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { getApiClient } from '@/lib/api';
import { useToast } from '@/components/Toast';
import { formatCurrency, formatNumber } from '@/lib/utils';
import { 
  ShoppingCart, 
  X, 
  DollarSign, 
  TrendingUp,
  AlertCircle,
  Loader2
} from 'lucide-react';

interface BuyOrderModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export function BuyOrderModal({ isOpen, onClose }: BuyOrderModalProps) {
  const apiClient = getApiClient();
  const { showToast } = useToast();
  const queryClient = useQueryClient();
  
  const [selectedSymbol, setSelectedSymbol] = useState('ETH/USDT');
  const [orderAmount, setOrderAmount] = useState('100');
  const [orderType, setOrderType] = useState<'amount' | 'percentage'>('amount');
  const [usdtPercentage, setUsdtPercentage] = useState('25');

  // Get USDT balance for percentage calculations
  const { data: usdtBalance } = useQuery({
    queryKey: ['usdt-balance'],
    queryFn: () => apiClient.getUSDTBalance(),
    enabled: isOpen,
  });

  // Get trading pairs
  const { data: tradingPairs, isLoading: pairsLoading } = useQuery({
    queryKey: ['trading-pairs'],
    queryFn: () => apiClient.getTradingPairs(),
    enabled: isOpen,
  });

  // Get current price for selected symbol
  const { data: priceData } = useQuery({
    queryKey: ['price', selectedSymbol],
    queryFn: () => apiClient.getCurrentPrice(selectedSymbol),
    enabled: isOpen && !!selectedSymbol,
    refetchInterval: 5000, // Update price every 5 seconds
  });

  // Get symbol info for validation
  const { data: symbolInfo } = useQuery({
    queryKey: ['symbol-info', selectedSymbol],
    queryFn: () => apiClient.getSymbolInfo(selectedSymbol),
    enabled: isOpen && !!selectedSymbol,
  });

  // Buy order mutation
  const buyMutation = useMutation({
    mutationFn: (orderData: { symbol: string; side: 'BUY'; quote_order_qty: number }) =>
      apiClient.placeMarketOrder(orderData),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['usdt-balance'] });
      queryClient.invalidateQueries({ queryKey: ['portfolio'] });
      queryClient.invalidateQueries({ queryKey: ['trade-history'] });
      
      showToast('success', `Successfully bought ${data.quantity} ${selectedSymbol.split('/')[0]} for ${formatCurrency(data.price * data.quantity)}`);
      onClose();
      resetForm();
    },
    onError: (error: unknown) => {
      const errorMessage = (error as { detail?: string })?.detail || 'Failed to place buy order';
      showToast('error', errorMessage);
    },
  });

  const resetForm = () => {
    setOrderAmount('100');
    setUsdtPercentage('25');
    setOrderType('amount');
  };

  const calculateOrderAmount = () => {
    if (orderType === 'percentage' && usdtBalance) {
      return (usdtBalance.balance * parseFloat(usdtPercentage)) / 100;
    }
    return parseFloat(orderAmount);
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();

    const amount = calculateOrderAmount();

    if (amount <= 0) {
      showToast('error', 'Order amount must be greater than 0');
      return;
    }

    if (usdtBalance && amount > usdtBalance.balance) {
      showToast('error', 'Insufficient USDT balance');
      return;
    }

    // Validate minimum order requirements
    if (symbolInfo && amount < symbolInfo.minNotional) {
      showToast('error',
        `Order value too small. Minimum required: $${symbolInfo.minNotional.toFixed(2)} USDT, ` +
        `but order value is $${amount.toFixed(2)} USDT.`
      );
      return;
    }

    if (priceData && symbolInfo && symbolInfo.minQty) {
      const estimatedQuantity = amount / priceData.price;
      if (estimatedQuantity < symbolInfo.minQty) {
        showToast('error',
          `Order quantity too small. Minimum required: ${symbolInfo.minQty} ${selectedSymbol.split('/')[0]}, ` +
          `but estimated quantity is ${estimatedQuantity.toFixed(8)} ${selectedSymbol.split('/')[0]}.`
        );
        return;
      }
    }

    buyMutation.mutate({
      symbol: selectedSymbol,
      side: 'BUY',
      quote_order_qty: amount,
    });
  };

  const estimatedQuantity = priceData ? calculateOrderAmount() / priceData.price : 0;

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="crypto-card max-w-md w-full max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-green-500/10 rounded-lg">
              <ShoppingCart className="w-5 h-5 text-green-500" />
            </div>
            <h3 className="text-lg font-medium">Buy Crypto</h3>
          </div>
          <button
            onClick={onClose}
            className="p-1 hover:bg-muted rounded"
            disabled={buyMutation.isPending}
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          {/* Trading Pair Selection */}
          <div>
            <label className="block text-sm font-medium mb-2">Trading Pair</label>
            <select
              value={selectedSymbol}
              onChange={(e) => setSelectedSymbol(e.target.value)}
              className="crypto-input"
              disabled={buyMutation.isPending || pairsLoading}
            >
              {pairsLoading ? (
                <option>Loading pairs...</option>
              ) : (
                tradingPairs?.filter(pair => pair.includes('USDT')).slice(0, 20).map(pair => {
                  // Convert ETHUSDT to ETH/USDT format for display
                  const displayPair = pair.replace('USDT', '/USDT');
                  return (
                    <option key={pair} value={displayPair}>
                      {displayPair}
                    </option>
                  );
                })
              )}
            </select>
          </div>

          {/* Current Price */}
          {priceData && (
            <div className="flex items-center gap-2 p-3 bg-muted/30 rounded-lg">
              <TrendingUp className="w-4 h-4 text-primary" />
              <span className="text-sm">
                Current Price: <strong>{formatCurrency(priceData.price)}</strong>
              </span>
            </div>
          )}

          {/* Order Type Toggle */}
          <div>
            <label className="block text-sm font-medium mb-2">Order Type</label>
            <div className="flex gap-2">
              <button
                type="button"
                onClick={() => setOrderType('amount')}
                className={`flex-1 py-2 px-3 rounded text-sm font-medium transition-colors ${
                  orderType === 'amount'
                    ? 'bg-primary text-primary-foreground'
                    : 'bg-muted text-muted-foreground hover:bg-muted/80'
                }`}
              >
                Fixed Amount
              </button>
              <button
                type="button"
                onClick={() => setOrderType('percentage')}
                className={`flex-1 py-2 px-3 rounded text-sm font-medium transition-colors ${
                  orderType === 'percentage'
                    ? 'bg-primary text-primary-foreground'
                    : 'bg-muted text-muted-foreground hover:bg-muted/80'
                }`}
              >
                % of Balance
              </button>
            </div>
          </div>

          {/* Order Amount Input */}
          {orderType === 'amount' ? (
            <div>
              <label className="block text-sm font-medium mb-2">Amount (USDT)</label>
              <div className="relative">
                <DollarSign className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                <input
                  type="number"
                  value={orderAmount}
                  onChange={(e) => setOrderAmount(e.target.value)}
                  placeholder="100.00"
                  min="0"
                  step="0.01"
                  className="crypto-input pl-10"
                  disabled={buyMutation.isPending}
                />
              </div>
            </div>
          ) : (
            <div>
              <label className="block text-sm font-medium mb-2">
                Percentage of USDT Balance ({formatCurrency(usdtBalance?.balance || 0)})
              </label>
              <div className="space-y-3">
                <input
                  type="range"
                  value={usdtPercentage}
                  onChange={(e) => setUsdtPercentage(e.target.value)}
                  min="1"
                  max="100"
                  step="1"
                  className="w-full"
                  disabled={buyMutation.isPending}
                />
                <div className="flex justify-between text-xs text-muted-foreground">
                  <span>1%</span>
                  <span className="font-medium">{usdtPercentage}%</span>
                  <span>100%</span>
                </div>
                <div className="flex gap-2">
                  {[25, 50, 75, 100].map(percent => (
                    <button
                      key={percent}
                      type="button"
                      onClick={() => setUsdtPercentage(percent.toString())}
                      className="flex-1 py-1 px-2 text-xs rounded bg-muted hover:bg-muted/80 transition-colors"
                      disabled={buyMutation.isPending}
                    >
                      {percent}%
                    </button>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* Order Summary */}
          <div className="p-3 bg-muted/30 rounded-lg space-y-2">
            <div className="flex justify-between text-sm">
              <span>Order Amount:</span>
              <span className={`font-medium ${
                symbolInfo && calculateOrderAmount() < symbolInfo.minNotional
                  ? 'text-red-500'
                  : 'text-green-500'
              }`}>
                {formatCurrency(calculateOrderAmount())}
              </span>
            </div>
            {priceData && (
              <div className="flex justify-between text-sm">
                <span>Estimated Quantity:</span>
                <span className={`font-medium ${
                  symbolInfo && symbolInfo.minQty && estimatedQuantity < symbolInfo.minQty
                    ? 'text-red-500'
                    : 'text-green-500'
                }`}>
                  {formatNumber(estimatedQuantity, 6)} {selectedSymbol.split('/')[0]}
                </span>
              </div>
            )}
            <div className="flex justify-between text-sm">
              <span>Available Balance:</span>
              <span className="font-medium">{formatCurrency(usdtBalance?.balance || 0)}</span>
            </div>

            {/* Validation info */}
            {symbolInfo && (
              <div className="pt-2 border-t border-border space-y-1">
                <div className="flex justify-between text-xs text-muted-foreground">
                  <span>Min Order Value:</span>
                  <span>{formatCurrency(symbolInfo.minNotional)}</span>
                </div>
                {symbolInfo.minQty && (
                  <div className="flex justify-between text-xs text-muted-foreground">
                    <span>Min Quantity:</span>
                    <span>{symbolInfo.minQty} {selectedSymbol.split('/')[0]}</span>
                  </div>
                )}
              </div>
            )}
          </div>

          {/* Validation Errors */}
          {symbolInfo && calculateOrderAmount() < symbolInfo.minNotional && (
            <div className="p-3 bg-red-500/10 border border-red-500/20 rounded-lg">
              <div className="flex items-start gap-2">
                <AlertCircle className="w-4 h-4 text-red-500 flex-shrink-0 mt-0.5" />
                <div className="text-xs text-red-500">
                  <strong>Order value too small:</strong> Minimum required is {formatCurrency(symbolInfo.minNotional)} USDT.
                  Current order value is {formatCurrency(calculateOrderAmount())} USDT.
                </div>
              </div>
            </div>
          )}

          {priceData && symbolInfo && symbolInfo.minQty && estimatedQuantity < symbolInfo.minQty && (
            <div className="p-3 bg-red-500/10 border border-red-500/20 rounded-lg">
              <div className="flex items-start gap-2">
                <AlertCircle className="w-4 h-4 text-red-500 flex-shrink-0 mt-0.5" />
                <div className="text-xs text-red-500">
                  <strong>Order quantity too small:</strong> Minimum required is {symbolInfo.minQty} {selectedSymbol.split('/')[0]}.
                  Estimated quantity is {formatNumber(estimatedQuantity, 8)} {selectedSymbol.split('/')[0]}.
                </div>
              </div>
            </div>
          )}

          {/* Submit Button */}
          <button
            type="submit"
            disabled={
              buyMutation.isPending ||
              calculateOrderAmount() <= 0 ||
              (symbolInfo ? calculateOrderAmount() < symbolInfo.minNotional : false) ||
              (priceData && symbolInfo && symbolInfo.minQty ? estimatedQuantity < symbolInfo.minQty : false)
            }
            className="crypto-button-primary w-full flex items-center justify-center gap-2"
          >
            {buyMutation.isPending ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                Placing Order...
              </>
            ) : (
              <>
                <ShoppingCart className="w-4 h-4" />
                Buy {selectedSymbol.split('/')[0]}
              </>
            )}
          </button>
        </form>

        {/* Warning */}
        <div className="mt-4 p-3 bg-orange-500/10 border border-orange-500/20 rounded-lg">
          <div className="flex items-start gap-2">
            <AlertCircle className="w-4 h-4 text-orange-500 flex-shrink-0 mt-0.5" />
            <div className="text-xs text-orange-500">
              <strong>Market Order:</strong> This will execute immediately at the current market price. 
              The final price may differ slightly from the displayed price.
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
