'use client';

import { useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { getApiClient } from '@/lib/api';
import { useToast } from '@/components/Toast';
import { formatCurrency, formatNumber } from '@/lib/utils';
import { 
  TrendingDown, 
  X, 
  Percent,
  AlertCircle,
  Loader2
} from 'lucide-react';

interface SellPercentageModalProps {
  isOpen: boolean;
  onClose: () => void;
  asset?: {
    asset: string;
    free: number;
    locked: number;
  };
}

export function SellPercentageModal({ isOpen, onClose, asset }: SellPercentageModalProps) {
  const apiClient = getApiClient();
  const { showToast } = useToast();
  const queryClient = useQueryClient();
  
  const [percentage, setPercentage] = useState('50');

  // Get current price for the asset
  const { data: priceData } = useQuery({
    queryKey: ['price', `${asset?.asset}/USDT`],
    queryFn: () => apiClient.getCurrentPrice(`${asset?.asset}/USDT`),
    enabled: isOpen && !!asset,
    refetchInterval: 5000, // Update price every 5 seconds
  });

  // Get symbol info for validation
  const { data: symbolInfo } = useQuery({
    queryKey: ['symbol-info', `${asset?.asset}/USDT`],
    queryFn: () => apiClient.getSymbolInfo(`${asset?.asset}/USDT`),
    enabled: isOpen && !!asset,
  });

  // Sell percentage mutation
  const sellMutation = useMutation({
    mutationFn: (data: { symbol: string; percentage: number }) =>
      apiClient.sellByPercentage(data.symbol, data.percentage),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['usdt-balance'] });
      queryClient.invalidateQueries({ queryKey: ['portfolio'] });
      queryClient.invalidateQueries({ queryKey: ['trade-history'] });
      
      showToast('success', `Successfully sold ${percentage}% of ${asset?.asset} for ${formatCurrency(data.price * data.quantity)}`);
      onClose();
      setPercentage('50');
    },
    onError: (error: any) => {
      showToast('error', error.detail || 'Failed to sell asset');
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();

    if (!asset) return;

    const sellPercentage = parseFloat(percentage);

    if (sellPercentage <= 0 || sellPercentage > 100) {
      showToast('error', 'Percentage must be between 1 and 100');
      return;
    }

    // Validate minimum order requirements
    const sellAmount = calculateSellAmount();
    const estimatedValue = calculateEstimatedValue();

    if (sellAmount <= 0) {
      showToast('error', 'Sell amount must be greater than 0');
      return;
    }

    if (symbolInfo && estimatedValue < symbolInfo.minNotional) {
      showToast('error',
        `Order value too small. Minimum required: $${symbolInfo.minNotional.toFixed(2)} USDT, ` +
        `but order value is $${estimatedValue.toFixed(2)} USDT. Try selling a higher percentage.`
      );
      return;
    }

    if (symbolInfo && symbolInfo.minQty && sellAmount < symbolInfo.minQty) {
      showToast('error',
        `Order quantity too small. Minimum required: ${symbolInfo.minQty} ${asset.asset}, ` +
        `but order quantity is ${sellAmount.toFixed(8)} ${asset.asset}.`
      );
      return;
    }

    sellMutation.mutate({
      symbol: `${asset.asset}/USDT`,
      percentage: sellPercentage,
    });
  };

  const calculateSellAmount = () => {
    if (!asset) return 0;
    return (asset.free * parseFloat(percentage)) / 100;
  };

  const calculateEstimatedValue = () => {
    if (!priceData) return 0;
    return calculateSellAmount() * priceData.price;
  };

  if (!isOpen || !asset) return null;

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="crypto-card max-w-md w-full">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-red-500/10 rounded-lg">
              <TrendingDown className="w-5 h-5 text-red-500" />
            </div>
            <h3 className="text-lg font-medium">Sell {asset.asset}</h3>
          </div>
          <button
            onClick={onClose}
            className="p-1 hover:bg-muted rounded"
            disabled={sellMutation.isPending}
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          {/* Asset Info */}
          <div className="p-3 bg-muted/30 rounded-lg">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-medium">Available Balance</span>
              <span className="font-medium">{formatNumber(asset.free, 6)} {asset.asset}</span>
            </div>
            {priceData && (
              <div className="flex items-center justify-between">
                <span className="text-sm text-muted-foreground">Current Price</span>
                <span className="text-sm">{formatCurrency(priceData.price)}</span>
              </div>
            )}
          </div>

          {/* Percentage Selection */}
          <div>
            <label className="block text-sm font-medium mb-2">
              Sell Percentage
            </label>
            <div className="space-y-3">
              <div className="relative">
                <Percent className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                <input
                  type="number"
                  value={percentage}
                  onChange={(e) => setPercentage(e.target.value)}
                  placeholder="50"
                  min="1"
                  max="100"
                  step="0.1"
                  className="crypto-input pl-10"
                  disabled={sellMutation.isPending}
                />
              </div>
              
              <input
                type="range"
                value={percentage}
                onChange={(e) => setPercentage(e.target.value)}
                min="1"
                max="100"
                step="1"
                className="w-full"
                disabled={sellMutation.isPending}
              />
              
              <div className="flex justify-between text-xs text-muted-foreground">
                <span>1%</span>
                <span className="font-medium">{percentage}%</span>
                <span>100%</span>
              </div>
              
              <div className="flex gap-2">
                {[25, 50, 75, 100].map(percent => (
                  <button
                    key={percent}
                    type="button"
                    onClick={() => setPercentage(percent.toString())}
                    className={`flex-1 py-2 px-3 text-sm rounded transition-colors ${
                      percentage === percent.toString()
                        ? 'bg-primary text-primary-foreground'
                        : 'bg-muted hover:bg-muted/80'
                    }`}
                    disabled={sellMutation.isPending}
                  >
                    {percent}%
                  </button>
                ))}
              </div>
            </div>
          </div>

          {/* Order Summary */}
          <div className="p-3 bg-muted/30 rounded-lg space-y-2">
            <div className="flex justify-between text-sm">
              <span>Sell Amount:</span>
              <span className="font-medium">
                {formatNumber(calculateSellAmount(), 6)} {asset.asset}
              </span>
            </div>
            {priceData && (
              <div className="flex justify-between text-sm">
                <span>Estimated Value:</span>
                <span className={`font-medium ${
                  symbolInfo && calculateEstimatedValue() < symbolInfo.minNotional
                    ? 'text-red-500'
                    : 'text-green-500'
                }`}>
                  {formatCurrency(calculateEstimatedValue())}
                </span>
              </div>
            )}
            <div className="flex justify-between text-sm">
              <span>Remaining:</span>
              <span className="font-medium">
                {formatNumber(asset.free - calculateSellAmount(), 6)} {asset.asset}
              </span>
            </div>

            {/* Validation warnings */}
            {symbolInfo && (
              <div className="pt-2 border-t border-border space-y-1">
                <div className="flex justify-between text-xs text-muted-foreground">
                  <span>Min Order Value:</span>
                  <span>{formatCurrency(symbolInfo.minNotional)}</span>
                </div>
                {symbolInfo.minQty && (
                  <div className="flex justify-between text-xs text-muted-foreground">
                    <span>Min Quantity:</span>
                    <span>{symbolInfo.minQty} {asset.asset}</span>
                  </div>
                )}
              </div>
            )}
          </div>

          {/* Validation Errors */}
          {symbolInfo && calculateEstimatedValue() < symbolInfo.minNotional && (
            <div className="p-3 bg-red-500/10 border border-red-500/20 rounded-lg">
              <div className="flex items-start gap-2">
                <AlertCircle className="w-4 h-4 text-red-500 flex-shrink-0 mt-0.5" />
                <div className="text-xs text-red-500">
                  <strong>Order value too small:</strong> Minimum required is {formatCurrency(symbolInfo.minNotional)} USDT.
                  Current order value is {formatCurrency(calculateEstimatedValue())} USDT.
                  Increase the percentage or wait for price increase.
                </div>
              </div>
            </div>
          )}

          {symbolInfo && symbolInfo.minQty && calculateSellAmount() < symbolInfo.minQty && (
            <div className="p-3 bg-red-500/10 border border-red-500/20 rounded-lg">
              <div className="flex items-start gap-2">
                <AlertCircle className="w-4 h-4 text-red-500 flex-shrink-0 mt-0.5" />
                <div className="text-xs text-red-500">
                  <strong>Order quantity too small:</strong> Minimum required is {symbolInfo.minQty} {asset.asset}.
                  Current order quantity is {formatNumber(calculateSellAmount(), 8)} {asset.asset}.
                </div>
              </div>
            </div>
          )}

          {/* Submit Button */}
          <button
            type="submit"
            disabled={
              sellMutation.isPending ||
              parseFloat(percentage) <= 0 ||
              (symbolInfo ? calculateEstimatedValue() < symbolInfo.minNotional : false) ||
              (symbolInfo && symbolInfo.minQty ? calculateSellAmount() < symbolInfo.minQty : false)
            }
            className="crypto-button-destructive w-full flex items-center justify-center gap-2"
          >
            {sellMutation.isPending ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                Selling...
              </>
            ) : (
              <>
                <TrendingDown className="w-4 h-4" />
                Sell {percentage}% of {asset.asset}
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
