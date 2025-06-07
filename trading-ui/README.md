# 🚀 Paper Trading Dashboard

A modern, responsive cryptocurrency paper trading dashboard built with Next.js, TypeScript, and Tailwind CSS. This application provides a comprehensive interface for managing your paper trading portfolio, viewing trade history, and analyzing profit/loss performance.

## ✨ Features

### 🔐 API Configuration
- Secure API key management with local storage
- Real-time connection testing
- Support for custom API endpoints

### 💰 Portfolio Management
- **USDT Balance Display**: Real-time balance updates
- **Holdings Overview**: View all non-USDT assets
- **Sell All Functionality**: One-click liquidation with confirmation
- **Auto-refresh**: 30-second interval updates

### 📊 Trade History
- **Complete Trade Log**: All buy/sell transactions
- **Advanced Filtering**: Filter by symbol and trade type
- **Search Functionality**: Quick symbol lookup
- **Real-time Updates**: Latest trades appear automatically

### 📈 PnL Analysis
- **Time Range Selection**: Custom date range analysis
- **Realized vs Unrealized PnL**: Detailed breakdown
- **Symbol-wise Analysis**: Per-asset performance
- **Open Positions**: Current holdings with unrealized PnL

## 🛠️ Technology Stack

- **Framework**: Next.js 14 with App Router
- **Language**: TypeScript
- **Styling**: Tailwind CSS with custom design system
- **State Management**: Zustand with persistence
- **Data Fetching**: TanStack Query (React Query)
- **HTTP Client**: Axios
- **Icons**: Lucide React
- **Date Handling**: date-fns

## 🚀 Getting Started

### Prerequisites

- Node.js 18+
- npm or yarn
- Running Paper Trading API server

### Installation

1. **Install dependencies**
   ```bash
   npm install
   ```

2. **Configure environment**
   Edit `.env.local`:
   ```env
   NEXT_PUBLIC_API_BASE_URL=http://localhost:8001
   ```

3. **Start the development server**
   ```bash
   # Default port (3000)
   npm run dev

   # Custom port (3500)
   npm run dev:3500
   ```

4. **Open your browser**
   - Default: [http://localhost:3000](http://localhost:3000)
   - Custom port: [http://localhost:3500](http://localhost:3500)

## 🔧 Configuration

### API Setup

1. **Start your Paper Trading API server** (usually on port 8001)
2. **Open the dashboard** in your browser
3. **Enter your Binance API credentials**:
   - API Key: Your Binance testnet API key
   - API Secret: Your Binance testnet API secret
   - Base URL: Your API server URL (default: http://localhost:8001)

## 📱 Usage

### Initial Setup
1. Launch the application
2. Enter your Binance testnet API credentials
3. Click "Connect to API" to verify connection

### Portfolio Management
- View your USDT balance in the main card
- Monitor all holdings in the portfolio section
- Use "Sell All" to liquidate all positions (with confirmation)
- Refresh data manually or wait for auto-updates

### Trade Analysis
- Navigate to "Trade History" to view all transactions
- Use filters to find specific trades
- Search by symbol name

### PnL Tracking
- Go to "PnL Analysis" section
- Select your desired date range
- Click "Calculate PnL" to generate report
- View total, realized, and unrealized profits/losses

## 🧪 Testing

### API Integration Test
```bash
node test-api.js
```

## 🔒 Security

- **Local Storage**: API credentials stored locally
- **Input Validation**: Client-side validation for API keys
- **Error Handling**: Graceful handling of API failures

---

**Built with ❤️ for crypto paper trading**
