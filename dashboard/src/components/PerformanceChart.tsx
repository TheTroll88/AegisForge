import { AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts';

interface PerformanceChartProps {
  trades: any[];
}

export default function PerformanceChart({ trades }: PerformanceChartProps) {
  const chartData = trades.reduce<{ index: number; pnl: number }[]>((acc, trade, i) => {
    const prev = acc.length > 0 ? acc[acc.length - 1].pnl : 0;
    const roi = typeof trade.roi === 'number' ? trade.roi : 0;
    acc.push({ index: i + 1, pnl: prev + roi });
    return acc;
  }, []);

  return (
    <div className="performance-chart">
      <h2 className="section-title">Cumulative P&L</h2>
      {chartData.length === 0 ? (
        <div className="chart-empty">No trade data yet</div>
      ) : (
        <ResponsiveContainer width="100%" height={280}>
          <AreaChart data={chartData}>
            <defs>
              <linearGradient id="pnlGrad" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="#00ffc8" stopOpacity={0.4} />
                <stop offset="100%" stopColor="#00ffc8" stopOpacity={0} />
              </linearGradient>
            </defs>
            <XAxis dataKey="index" stroke="#555" tick={{ fontSize: 11 }} />
            <YAxis stroke="#555" tick={{ fontSize: 11 }} tickFormatter={(v: number) => `${v.toFixed(1)}%`} />
            <Tooltip
              contentStyle={{ background: '#111827', border: '1px solid #00ffc8', color: '#e0e0e0', fontSize: 12 }}
              formatter={(value: number) => [`${value.toFixed(2)}%`, 'P&L']}
            />
            <Area type="monotone" dataKey="pnl" stroke="#00ffc8" fill="url(#pnlGrad)" strokeWidth={2} />
          </AreaChart>
        </ResponsiveContainer>
      )}
    </div>
  );
}
