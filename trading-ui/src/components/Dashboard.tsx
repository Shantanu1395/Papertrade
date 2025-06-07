'use client';

import { useState } from 'react';
import { useAppStore } from '@/stores/useAppStore';
import { PortfolioOverview } from './PortfolioOverview';
import { PnLAnalysis } from './PnLAnalysis';
import { EnhancedPortfolio } from './EnhancedPortfolio';
import { EnhancedTradeHistory } from './EnhancedTradeHistory';

import {
  BarChart3,
  Wallet,
  TrendingUp,
  Menu,
  X,
  PieChart,
  Activity
} from 'lucide-react';

type TabType = 'portfolio' | 'pnl' | 'enhanced-portfolio' | 'enhanced-trades';

const tabs = [
  { id: 'portfolio' as TabType, label: 'Portfolio', icon: Wallet },
  { id: 'enhanced-portfolio' as TabType, label: 'Enhanced Portfolio', icon: PieChart },
  { id: 'enhanced-trades' as TabType, label: 'Enhanced Trades', icon: Activity },
  { id: 'pnl' as TabType, label: 'PnL Analysis', icon: TrendingUp },
];

export function Dashboard() {
  const [activeTab, setActiveTab] = useState<TabType>('portfolio');
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const { clearApiConfig } = useAppStore();

  const renderContent = () => {
    switch (activeTab) {
      case 'portfolio':
        return <PortfolioOverview />;
      case 'enhanced-portfolio':
        return <EnhancedPortfolio />;
      case 'enhanced-trades':
        return <EnhancedTradeHistory />;
      case 'pnl':
        return <PnLAnalysis />;
      default:
        return <PortfolioOverview />;
    }
  };

  return (
    <div className="min-h-screen bg-background flex">
      {/* Mobile sidebar overlay */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 bg-black/50 z-40 lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Sidebar */}
      <div className={`
        fixed inset-y-0 left-0 z-50 w-64 bg-card border-r border-border transform transition-transform duration-200 ease-in-out lg:translate-x-0 lg:static lg:inset-0 lg:flex-shrink-0
        ${sidebarOpen ? 'translate-x-0' : '-translate-x-full'}
      `}>
        <div className="flex flex-col h-full">
          <div className="flex items-center justify-between p-4 lg:p-6 border-b border-border flex-shrink-0">
            <div className="flex items-center gap-3 min-w-0">
              <div className="p-2 bg-primary/10 rounded-lg flex-shrink-0">
                <BarChart3 className="w-5 h-5 text-primary" />
              </div>
              <h1 className="text-lg font-semibold truncate">Trading Dashboard</h1>
            </div>
            <button
              onClick={() => setSidebarOpen(false)}
              className="lg:hidden p-1 hover:bg-muted rounded flex-shrink-0"
            >
              <X className="w-4 h-4" />
            </button>
          </div>

          <nav className="flex-1 p-4 overflow-y-auto">
            <div className="space-y-2">
              {tabs.map((tab) => {
                const Icon = tab.icon;
                return (
                  <button
                    key={tab.id}
                    onClick={() => {
                      setActiveTab(tab.id);
                      setSidebarOpen(false);
                    }}
                    className={`
                      w-full flex items-center gap-3 px-3 py-2 rounded-lg text-left transition-colors
                      ${activeTab === tab.id
                        ? 'bg-primary/10 text-primary border border-primary/20'
                        : 'hover:bg-muted text-muted-foreground hover:text-foreground'
                      }
                    `}
                  >
                    <Icon className="w-4 h-4 flex-shrink-0" />
                    <span className="truncate">{tab.label}</span>
                  </button>
                );
              })}
            </div>

            <div className="mt-8 pt-4 border-t border-border">
              <button
                onClick={clearApiConfig}
                className="w-full text-left px-3 py-2 text-sm text-muted-foreground hover:text-destructive transition-colors"
              >
                Disconnect API
              </button>
            </div>
          </nav>
        </div>
      </div>

      {/* Main content */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Header */}
        <header className="bg-card border-b border-border px-4 py-3 lg:px-6 flex-shrink-0">
          <div className="flex items-center justify-between min-w-0">
            <div className="flex items-center gap-4 min-w-0">
              <button
                onClick={() => setSidebarOpen(true)}
                className="lg:hidden p-2 hover:bg-muted rounded-lg flex-shrink-0"
              >
                <Menu className="w-5 h-5" />
              </button>
              <div className="min-w-0">
                <h2 className="text-xl font-semibold capitalize truncate">
                  {activeTab === 'pnl' ? 'PnL Analysis' : activeTab}
                </h2>
                <p className="text-sm text-muted-foreground truncate">
                  {activeTab === 'portfolio' && 'Monitor your holdings and balances'}
                  {activeTab === 'enhanced-portfolio' && 'Advanced portfolio analytics with PnL tracking'}
                  {activeTab === 'enhanced-trades' && 'Comprehensive trade analysis with advanced filtering'}
                  {activeTab === 'pnl' && 'Analyze your profit and loss performance'}
                </p>
              </div>
            </div>
          </div>
        </header>

        {/* Content */}
        <main className="flex-1 p-4 lg:p-6 overflow-y-auto">
          {renderContent()}
        </main>
      </div>
    </div>
  );
}
