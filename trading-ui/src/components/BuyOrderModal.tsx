'use client';

import { useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { getApiClient } from '@/lib/api';
import { useToast } from '@/components/Toast';
import { formatCurrency, formatNumber } from '@/lib/utils';
import { useTradingPairs } from '@/hooks/useTradingPairs';
import { QuoteCurrencyHelper } from '@/components/QuoteCurrencyHelper';
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
  const { popularPairs, usdtPairs, btcPairs, ethPairs, allPairs, isLoading: pairsLoading } = useTradingPairs();

  const [selectedSymbol, setSelectedSymbol] = useState('ETH/USDT');
  const [orderAmount, setOrderAmount] = useState('1');
  const [orderType, setOrderType] = useState<'amount' | 'percentage'>('amount');
  const [usdtPercentage, setUsdtPercentage] = useState('25');
  const [pairCategory, setPairCategory] = useState<'popular' | 'usdt' | 'btc' | 'eth' | 'all'>('popular');
  const [showQuoteHelper, setShowQuoteHelper] = useState(false);

  // Get USDT balance for percentage calculations
  const { data: usdtBalance } = useQuery({
    queryKey: ['usdt-balance'],
    queryFn: () => apiClient.getUSDTBalance(),
    enabled: isOpen,
  });

  // Get portfolio for quote currency balance validation
  const { data: portfolio } = useQuery({
    queryKey: ['portfolio'],
    queryFn: () => apiClient.getPortfolio(),
    enabled: isOpen,
  });

  // Get current pairs based on category
  const getCurrentPairs = () => {
    switch (pairCategory) {
      case 'popular': return popularPairs;
      case 'usdt': return usdtPairs;
      case 'btc': return btcPairs;
      case 'eth': return ethPairs;
      case 'all': return allPairs;
      default: return popularPairs;
    }
  };

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
      const err = error as { response?: { data?: { detail?: string } }; detail?: string; message?: string };
      let errorMessage = err.response?.data?.detail || err.detail || err.message || 'Failed to place buy order';

      // Provide more user-friendly error messages
      if (errorMessage.includes('too small')) {
        errorMessage = 'Order amount is too small. Please increase the amount and try again.';
      } else if (errorMessage.includes('insufficient')) {
        errorMessage = 'Insufficient balance. Please check your available balance.';
      } else if (errorMessage.includes('precision')) {
        errorMessage = 'Invalid order amount precision. Please adjust the amount.';
      } else if (errorMessage.includes('minimum')) {
        errorMessage = 'Order does not meet minimum requirements. Please increase the amount.';
      }

      showToast('error', errorMessage);
    },
  });

  const resetForm = () => {
    setOrderAmount('1');
    setUsdtPercentage('25');
    setOrderType('amount');
  };

  // Get quote currency from selected symbol
  const getQuoteCurrency = () => {
    const parts = selectedSymbol.split('/');
    return parts[1]; // BTC, USDT, ETH, etc.
  };

  // Get base currency from selected symbol
  const getBaseCurrency = () => {
    const parts = selectedSymbol.split('/');
    return parts[0]; // ADA, ETH, BTC, etc.
  };

  // Get quote currency balance
  const getQuoteCurrencyBalance = () => {
    const quoteCurrency = getQuoteCurrency();
    if (quoteCurrency === 'USDT') {
      return usdtBalance?.balance || 0;
    }

    if (portfolio) {
      const asset = portfolio.find(p => p.asset === quoteCurrency);
      return asset?.free || 0;
    }

    return 0;
  };

  // Check if user has sufficient quote currency
  const hasQuoteCurrencyBalance = () => {
    return getQuoteCurrencyBalance() > 0;
  };

  // Get alternative USDT pair suggestion
  const getUSDTAlternative = () => {
    const baseCurrency = selectedSymbol.split('/')[0];
    return `${baseCurrency}/USDT`;
  };

  const calculateOrderAmount = () => {
    if (orderType === 'percentage') {
      const quoteCurrencyBalance = getQuoteCurrencyBalance();
      return (quoteCurrencyBalance * parseFloat(usdtPercentage)) / 100;
    }
    // For fixed amount, convert base currency amount to quote currency amount
    const baseAmount = parseFloat(orderAmount) || 0;
    if (priceData && baseAmount > 0) {
      return baseAmount * priceData.price; // Convert base amount to quote amount for API
    }
    return 0;
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();

    const amount = calculateOrderAmount();
    const quoteCurrency = getQuoteCurrency();
    const quoteCurrencyBalance = getQuoteCurrencyBalance();

    if (amount <= 0) {
      showToast('error', 'Order amount must be greater than 0');
      return;
    }

    // Additional validation for very small amounts
    if (amount < 0.001) {
      showToast('error', 'Order amount too small. Minimum order value is $0.001');
      return;
    }

    // Check quote currency balance
    if (amount > quoteCurrencyBalance) {
      const usdtAlternative = getUSDTAlternative();
      const hasUSDTAlternative = popularPairs.includes(usdtAlternative) || usdtPairs.includes(usdtAlternative);

      if (quoteCurrency !== 'USDT' && hasUSDTAlternative) {
        showToast('error',
          `Insufficient ${quoteCurrency} balance. Available: ${quoteCurrencyBalance.toFixed(8)} ${quoteCurrency}. ` +
          `Try using ${usdtAlternative} instead, or buy ${quoteCurrency} first.`
        );
      } else {
        showToast('error',
          `Insufficient ${quoteCurrency} balance. Available: ${quoteCurrencyBalance.toFixed(8)} ${quoteCurrency}.`
        );
      }
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

    if (symbolInfo && symbolInfo.minQty) {
      // For fixed amount orders, check the base currency amount directly
      // For percentage orders, calculate from quote currency amount
      const baseQuantity = orderType === 'amount'
        ? parseFloat(orderAmount) || 0
        : (priceData ? amount / priceData.price : 0);

      if (baseQuantity < symbolInfo.minQty) {
        showToast('error',
          `Order quantity too small. Minimum required: ${symbolInfo.minQty} ${selectedSymbol.split('/')[0]}, ` +
          `but order quantity is ${baseQuantity.toFixed(8)} ${selectedSymbol.split('/')[0]}.`
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

  // Calculate estimated quantity based on order type
  const estimatedQuantity = (() => {
    if (orderType === 'percentage') {
      // For percentage orders, calculate from quote currency amount
      return priceData ? calculateOrderAmount() / priceData.price : 0;
    } else {
      // For fixed amount orders, we're directly inputting the base currency amount
      return parseFloat(orderAmount) || 0;
    }
  })();

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

            {/* Pair Category Tabs */}
            <div className="flex gap-1 mb-3 p-1 bg-muted/30 rounded-lg">
              {[
                { key: 'popular', label: 'Popular', count: popularPairs.length },
                { key: 'usdt', label: 'USDT', count: usdtPairs.length },
                { key: 'btc', label: 'BTC', count: btcPairs.length },
                { key: 'eth', label: 'ETH', count: ethPairs.length },
                { key: 'all', label: 'All', count: allPairs.length },
              ].map(({ key, label, count }) => (
                <button
                  key={key}
                  type="button"
                  onClick={() => setPairCategory(key as any)}
                  className={`flex-1 py-1.5 px-2 text-xs rounded transition-colors ${
                    pairCategory === key
                      ? 'bg-primary text-primary-foreground'
                      : 'hover:bg-muted/50'
                  }`}
                  disabled={buyMutation.isPending}
                >
                  {label} ({count})
                </button>
              ))}
            </div>

            <select
              value={selectedSymbol}
              onChange={(e) => setSelectedSymbol(e.target.value)}
              className="crypto-input"
              disabled={buyMutation.isPending || pairsLoading}
            >
              {pairsLoading ? (
                <option>Loading pairs...</option>
              ) : getCurrentPairs().length === 0 ? (
                <option>No pairs available</option>
              ) : (
                getCurrentPairs().map(pair => (
                  <option key={pair} value={pair}>
                    {pair}
                  </option>
                ))
              )}
            </select>

            <div className="text-xs text-muted-foreground mt-1">
              {getCurrentPairs().length} pairs available in {pairCategory} category
            </div>
          </div>

          {/* Current Price */}
          {priceData && (
            <div className="flex items-center gap-2 p-3 bg-muted/30 rounded-lg">
              <TrendingUp className="w-4 h-4 text-primary" />
              <span className="text-sm">
                Current Price: <strong>
                  {getQuoteCurrency() === 'USDT'
                    ? formatCurrency(priceData.price)
                    : `${priceData.price.toFixed(8)} ${getQuoteCurrency()}`
                  }
                </strong>
              </span>
            </div>
          )}

          {/* Price Loading or Error */}
          {!priceData && selectedSymbol && (
            <div className="flex items-center gap-2 p-3 bg-muted/30 rounded-lg">
              <TrendingUp className="w-4 h-4 text-muted-foreground" />
              <span className="text-sm text-muted-foreground">
                Loading price for {selectedSymbol}...
              </span>
            </div>
          )}

          {/* Quote Currency Balance Warning */}
          {!hasQuoteCurrencyBalance() && getQuoteCurrency() !== 'USDT' && (
            <div className="p-3 bg-orange-500/10 border border-orange-500/20 rounded-lg">
              <div className="flex items-start gap-2">
                <AlertCircle className="w-4 h-4 text-orange-500 flex-shrink-0 mt-0.5" />
                <div className="text-xs text-orange-500">
                  <strong>No {getQuoteCurrency()} Balance:</strong> You need {getQuoteCurrency()} to buy this pair.
                  Consider using <strong>{getUSDTAlternative()}</strong> instead, or buy {getQuoteCurrency()} first.
                  <div className="mt-2 flex gap-2">
                    <button
                      type="button"
                      onClick={() => setSelectedSymbol(getUSDTAlternative())}
                      className="text-xs bg-orange-500/20 hover:bg-orange-500/30 px-2 py-1 rounded transition-colors"
                      disabled={!popularPairs.includes(getUSDTAlternative()) && !usdtPairs.includes(getUSDTAlternative())}
                    >
                      Switch to {getUSDTAlternative()}
                    </button>
                    <button
                      type="button"
                      onClick={() => setShowQuoteHelper(true)}
                      className="text-xs bg-blue-500/20 hover:bg-blue-500/30 px-2 py-1 rounded transition-colors"
                    >
                      Buy {getQuoteCurrency()} First
                    </button>
                  </div>
                </div>
              </div>
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
              <label className="block text-sm font-medium mb-2">
                Amount ({getBaseCurrency()})
              </label>
              <div className="relative">
                <input
                  type="number"
                  value={orderAmount}
                  onChange={(e) => setOrderAmount(e.target.value)}
                  placeholder="1.0"
                  min="0"
                  step="0.1"
                  className="crypto-input pl-10"
                  disabled={buyMutation.isPending}
                />
              </div>
              <div className="text-xs text-muted-foreground mt-1">
                Enter the amount of {getBaseCurrency()} you want to buy
              </div>
            </div>
          ) : (
            <div>
              <label className="block text-sm font-medium mb-2">
                Percentage of {getQuoteCurrency()} Balance ({getQuoteCurrency() === 'USDT' ? formatCurrency(getQuoteCurrencyBalance()) : `${getQuoteCurrencyBalance().toFixed(8)} ${getQuoteCurrency()}`})
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
              <span>Quantity to Buy:</span>
              <span className={`font-medium ${
                symbolInfo && symbolInfo.minQty && estimatedQuantity < symbolInfo.minQty
                  ? 'text-red-500'
                  : 'text-green-500'
              }`}>
                {formatNumber(estimatedQuantity, 6)} {selectedSymbol.split('/')[0]}
              </span>
            </div>
            <div className="flex justify-between text-sm">
              <span>Total Cost:</span>
              <span className={`font-medium ${
                symbolInfo && calculateOrderAmount() < symbolInfo.minNotional
                  ? 'text-red-500'
                  : 'text-green-500'
              }`}>
                {getQuoteCurrency() === 'USDT'
                  ? formatCurrency(calculateOrderAmount())
                  : `${calculateOrderAmount().toFixed(8)} ${getQuoteCurrency()}`
                }
              </span>
            </div>
            <div className="flex justify-between text-sm">
              <span>Available Balance:</span>
              <span className="font-medium">
                {getQuoteCurrency() === 'USDT'
                  ? formatCurrency(getQuoteCurrencyBalance())
                  : `${getQuoteCurrencyBalance().toFixed(8)} ${getQuoteCurrency()}`
                }
              </span>
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

          {symbolInfo && symbolInfo.minQty && estimatedQuantity < symbolInfo.minQty && (
            <div className="p-3 bg-red-500/10 border border-red-500/20 rounded-lg">
              <div className="flex items-start gap-2">
                <AlertCircle className="w-4 h-4 text-red-500 flex-shrink-0 mt-0.5" />
                <div className="text-xs text-red-500">
                  <strong>Order quantity too small:</strong> Minimum required is {symbolInfo.minQty} {selectedSymbol.split('/')[0]}.
                  Current quantity is {formatNumber(estimatedQuantity, 8)} {selectedSymbol.split('/')[0]}.
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
              calculateOrderAmount() > getQuoteCurrencyBalance() ||
              !hasQuoteCurrencyBalance() ||
              (symbolInfo ? calculateOrderAmount() < symbolInfo.minNotional : false) ||
              (symbolInfo && symbolInfo.minQty ? estimatedQuantity < symbolInfo.minQty : false)
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

      {/* Quote Currency Helper Modal */}
      <QuoteCurrencyHelper
        isOpen={showQuoteHelper}
        onClose={() => setShowQuoteHelper(false)}
        quoteCurrency={getQuoteCurrency()}
        targetSymbol={selectedSymbol}
        onSuccess={() => {
          // Refresh portfolio data
          queryClient.invalidateQueries({ queryKey: ['portfolio'] });
        }}
      />
    </div>
  );
}
