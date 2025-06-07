// API Configuration Types
export interface ApiConfig {
  apiKey: string;
  apiSecret: string;
  baseUrl: string;
}

// Account & Portfolio Types
export interface Balance {
  asset: string;
  free: number;
  locked: number;
}

export interface USDTBalanceResponse {
  balance: number;
}

export interface SellAllResponse {
  usdt_balance: number;
}

// Trade Types
export interface Trade {
  symbol: string;
  side: 'BUY' | 'SELL';
  price: number;
  quantity?: number;
  qty?: number;
  quoteQty: number;
  commission: number;
  commissionAsset: string;
  time: string;
  timestamp_ms: number;
  tradeId: string;
  orderType?: string;
}

// PnL Types
export interface PnLRequest {
  start_time: string;
  end_time: string;
}

export interface SymbolPnL {
  realized_pnl: number;
  unrealized_pnl: number;
  total_pnl: number;
}

export interface OpenPosition {
  quantity: number;
  avg_buy_price: number;
  current_price: number;
  unrealized_pnl: number;
}

export interface PnLResponse {
  total_pnl: number;
  realized_pnl: number;
  unrealized_pnl: number;
  symbol_pnl: Record<string, SymbolPnL>;
  open_positions: Record<string, OpenPosition>;
}

// Order Types
export interface OrderRequest {
  symbol: string;
  side: 'BUY' | 'SELL';
  quantity?: number;
  price?: number;
  quote_order_qty?: number;
}

export interface OrderResponse {
  symbol: string;
  orderId: number;
  side: string;
  type: string;
  quantity: number;
  price: number;
  status: string;
  time: number;
  commission: number;
}

// API Error Types
export interface ApiError {
  detail: string;
  status_code?: number;
}

// Time Range Types
export interface TimeRange {
  start: Date;
  end: Date;
}
