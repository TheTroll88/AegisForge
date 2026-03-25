interface WhalePanelProps {
  signals: any[];
  movers: any[];
}

function formatTime(ts: string | number): string {
  try {
    const d = new Date(ts);
    return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  } catch {
    return String(ts);
  }
}

function formatAmount(val: any): string {
  const n = Number(val);
  if (isNaN(n)) return String(val ?? '—');
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`;
  if (n >= 1_000) return `${(n / 1_000).toFixed(1)}K`;
  return n.toFixed(2);
}

export default function WhalePanel({ signals, movers }: WhalePanelProps) {
  return (
    <div className="whale-panel">
      <div className="whale-section">
        <h2 className="section-title">Recent Whale Signals</h2>
        {signals.length === 0 ? (
          <div className="whale-empty">No signals yet</div>
        ) : (
          <table className="whale-table">
            <thead>
              <tr>
                <th>Time</th>
                <th>Token</th>
                <th>Type</th>
                <th>Amount</th>
              </tr>
            </thead>
            <tbody>
              {signals.map((s, i) => (
                <tr key={i}>
                  <td>{formatTime(s.timestamp ?? s.time)}</td>
                  <td>{s.token ?? s.symbol ?? '—'}</td>
                  <td>{s.type ?? s.action ?? '—'}</td>
                  <td>{formatAmount(s.amount ?? s.value)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
      <div className="whale-section">
        <h2 className="section-title">Top Movers</h2>
        {movers.length === 0 ? (
          <div className="whale-empty">No movers yet</div>
        ) : (
          <table className="whale-table">
            <thead>
              <tr>
                <th>Token</th>
                <th>Volume</th>
                <th>Direction</th>
              </tr>
            </thead>
            <tbody>
              {movers.map((m, i) => (
                <tr key={i}>
                  <td>{m.token ?? m.symbol ?? '—'}</td>
                  <td>{formatAmount(m.volume ?? m.amount)}</td>
                  <td className={m.direction === 'buy' ? 'buy-text' : 'sell-text'}>{m.direction ?? '—'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
