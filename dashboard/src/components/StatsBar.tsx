interface StatsBarProps {
  totalTrades: number;
  winRate: number;
  avgRoi: number;
  activeStrategies: number;
  totalStrategies: number;
}

export default function StatsBar({ totalTrades, winRate, avgRoi, activeStrategies, totalStrategies }: StatsBarProps) {
  return (
    <div className="stats-bar">
      <div className="stat-card">
        <span className="stat-label">Total Trades</span>
        <span className="stat-value">{totalTrades}</span>
      </div>
      <div className="stat-card">
        <span className="stat-label">Win Rate</span>
        <span className="stat-value">{winRate.toFixed(1)}%</span>
      </div>
      <div className="stat-card">
        <span className="stat-label">Average ROI</span>
        <span className={`stat-value ${avgRoi >= 0 ? 'positive' : 'negative'}`}>{avgRoi >= 0 ? '+' : ''}{avgRoi.toFixed(2)}%</span>
      </div>
      <div className="stat-card">
        <span className="stat-label">Active Strategies</span>
        <span className="stat-value">{activeStrategies} <span className="stat-sub">/ {totalStrategies}</span></span>
      </div>
    </div>
  );
}
