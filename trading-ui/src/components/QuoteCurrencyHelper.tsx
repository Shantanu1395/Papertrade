import { useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { getApiClient } from '@/lib/api';
import { useToast } from '@/components/Toast';
import { formatCurrency } from '@/lib/utils';
import { 
  AlertCircle, 
  ArrowRight, 
  ShoppingCart, 
  Loader2,
  X 
} from 'lucide-react';

interface QuoteCurrencyHelperProps {
  isOpen: boolean;
  onClose: () => void;
  quoteCurrency: string;
  targetSymbol: string;
  onSuccess: () => void;
}

export function QuoteCurrencyHelper({ 
  isOpen, 
  onClose, 
  quoteCurrency, 
  targetSymbol, 
  onSuccess 
}: QuoteCurrencyHelperProps) {
  const [buyAmount, setBuyAmount] = useState('100');
  const apiClient = getApiClient();
  const { showToast } = useToast();
  const queryClient = useQueryClient();

  // Buy quote currency mutation
  const buyQuoteMutation = useMutation({
    mutationFn: (orderData: { symbol: string; side: 'BUY'; quote_order_qty: number }) =>
      apiClient.placeMarketOrder(orderData),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['usdt-balance'] });
      queryClient.invalidateQueries({ queryKey: ['portfolio'] });
      queryClient.invalidateQueries({ queryKey: ['trade-history'] });
      
      showToast('success', 
        `Successfully bought ${data.quantity} ${quoteCurrency} for ${formatCurrency(data.price * data.quantity)}. ` +
        `You can now buy ${targetSymbol}.`
      );
      onSuccess();
      onClose();
    },
    onError: (error: unknown) => {
      const errorMessage = (error as { detail?: string })?.detail || `Failed to buy ${quoteCurrency}`;
      showToast('error', errorMessage);
    },
  });

  const handleBuyQuoteCurrency = (e: React.FormEvent) => {
    e.preventDefault();
    
    const amount = parseFloat(buyAmount);
    if (amount <= 0) {
      showToast('error', 'Amount must be greater than 0');
      return;
    }

    buyQuoteMutation.mutate({
      symbol: `${quoteCurrency}/USDT`,
      side: 'BUY',
      quote_order_qty: amount,
    });
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="crypto-card max-w-md w-full">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-orange-500/10 rounded-lg">
              <AlertCircle className="w-5 h-5 text-orange-500" />
            </div>
            <h3 className="text-lg font-medium">Buy {quoteCurrency} First</h3>
          </div>
          <button
            onClick={onClose}
            className="p-1 hover:bg-muted rounded"
            disabled={buyQuoteMutation.isPending}
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Explanation */}
        <div className="mb-6 p-4 bg-orange-500/10 border border-orange-500/20 rounded-lg">
          <div className="text-sm text-orange-500">
            <strong>Why do I need {quoteCurrency}?</strong>
            <p className="mt-2">
              To buy <strong>{targetSymbol}</strong>, you need {quoteCurrency} as the quote currency. 
              You currently have 0 {quoteCurrency} balance.
            </p>
          </div>
        </div>

        {/* Two-Step Process */}
        <div className="mb-6">
          <h4 className="text-sm font-medium mb-3">Two-Step Process:</h4>
          <div className="space-y-3">
            <div className="flex items-center gap-3 p-3 bg-muted/30 rounded-lg">
              <div className="w-6 h-6 bg-primary text-primary-foreground rounded-full flex items-center justify-center text-xs font-bold">
                1
              </div>
              <span className="text-sm">Buy {quoteCurrency} with USDT</span>
            </div>
            <div className="flex justify-center">
              <ArrowRight className="w-4 h-4 text-muted-foreground" />
            </div>
            <div className="flex items-center gap-3 p-3 bg-muted/30 rounded-lg">
              <div className="w-6 h-6 bg-muted text-muted-foreground rounded-full flex items-center justify-center text-xs font-bold">
                2
              </div>
              <span className="text-sm">Buy {targetSymbol} with {quoteCurrency}</span>
            </div>
          </div>
        </div>

        {/* Buy Quote Currency Form */}
        <form onSubmit={handleBuyQuoteCurrency} className="space-y-4">
          <div>
            <label className="block text-sm font-medium mb-2">
              Amount to spend (USDT)
            </label>
            <input
              type="number"
              value={buyAmount}
              onChange={(e) => setBuyAmount(e.target.value)}
              placeholder="100.00"
              min="0"
              step="0.01"
              className="crypto-input"
              disabled={buyQuoteMutation.isPending}
            />
            <div className="text-xs text-muted-foreground mt-1">
              This will buy approximately {quoteCurrency} which you can then use to buy {targetSymbol}
            </div>
          </div>

          <div className="flex gap-3">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 py-2 px-4 border border-border rounded-lg hover:bg-muted transition-colors"
              disabled={buyQuoteMutation.isPending}
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={buyQuoteMutation.isPending || parseFloat(buyAmount) <= 0}
              className="flex-1 crypto-button-primary flex items-center justify-center gap-2"
            >
              {buyQuoteMutation.isPending ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  Buying...
                </>
              ) : (
                <>
                  <ShoppingCart className="w-4 h-4" />
                  Buy {quoteCurrency}
                </>
              )}
            </button>
          </div>
        </form>

        {/* Alternative */}
        <div className="mt-4 p-3 bg-blue-500/10 border border-blue-500/20 rounded-lg">
          <div className="text-xs text-blue-500">
            <strong>Alternative:</strong> You can also use the USDT pair directly if available: 
            <strong> {targetSymbol.split('/')[0]}/USDT</strong>
          </div>
        </div>
      </div>
    </div>
  );
}
