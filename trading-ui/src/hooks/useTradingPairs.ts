import { useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import { getApiClient } from '@/lib/api';
import { useAppStore } from '@/stores/useAppStore';

export function useTradingPairs() {
  const { tradingPairs, tradingPairsLoaded, setTradingPairs, isApiConfigured } = useAppStore();
  const apiClient = getApiClient();

  // Fetch trading pairs in background
  const { data, isLoading, error } = useQuery({
    queryKey: ['trading-pairs'],
    queryFn: () => apiClient.getTradingPairs(),
    enabled: isApiConfigured && !tradingPairsLoaded,
    staleTime: 1000 * 60 * 60, // 1 hour
    refetchOnWindowFocus: false,
  });

  // Update store when data is fetched
  useEffect(() => {
    if (data && !tradingPairsLoaded) {
      setTradingPairs(data);
    }
  }, [data, tradingPairsLoaded, setTradingPairs]);

  // Filter and format pairs for UI
  const getUSDTPairs = () => {
    return tradingPairs
      .filter(pair => pair.endsWith('USDT'))
      .map(pair => pair.replace('USDT', '/USDT'))
      .sort();
  };

  const getBTCPairs = () => {
    return tradingPairs
      .filter(pair => pair.endsWith('BTC') && pair !== 'BTC')
      .map(pair => pair.replace('BTC', '/BTC'))
      .sort();
  };

  const getETHPairs = () => {
    return tradingPairs
      .filter(pair => pair.endsWith('ETH') && pair !== 'ETH')
      .map(pair => pair.replace('ETH', '/ETH'))
      .sort();
  };

  const getPopularPairs = () => {
    const popular = [
      'BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'ADAUSDT', 'SOLUSDT',
      'XRPUSDT', 'DOGEUSDT', 'DOTUSDT', 'AVAXUSDT', 'LINKUSDT',
      'LTCUSDT', 'BCHUSDT', 'UNIUSDT', 'ATOMUSDT', 'FILUSDT'
    ];
    
    return popular
      .filter(pair => tradingPairs.includes(pair))
      .map(pair => pair.replace('USDT', '/USDT'));
  };

  const getAllPairs = () => {
    return tradingPairs.map(pair => {
      if (pair.endsWith('USDT')) return pair.replace('USDT', '/USDT');
      if (pair.endsWith('BTC')) return pair.replace('BTC', '/BTC');
      if (pair.endsWith('ETH')) return pair.replace('ETH', '/ETH');
      if (pair.endsWith('BNB')) return pair.replace('BNB', '/BNB');
      return pair;
    }).sort();
  };

  return {
    // Raw data
    tradingPairs,
    tradingPairsLoaded,
    isLoading,
    error,
    
    // Formatted pairs
    usdtPairs: getUSDTPairs(),
    btcPairs: getBTCPairs(),
    ethPairs: getETHPairs(),
    popularPairs: getPopularPairs(),
    allPairs: getAllPairs(),
    
    // Stats
    totalPairs: tradingPairs.length,
    usdtPairsCount: getUSDTPairs().length,
    btcPairsCount: getBTCPairs().length,
    ethPairsCount: getETHPairs().length,
  };
}
