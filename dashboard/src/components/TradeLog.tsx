interface TradeLogProps {
  trades: any[];
}

function formatTime(ts: string | number): string {
  try {
    const d = new Date(ts);
    return d.toLocaleString([], { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' });
  } catch {
    return String(ts);
  }
}

export default function TradeLog({ trades }: TradeLogProps) {
  const recent = trades.slice(-20).reverse();

  return (
    <div className="trade-log">
      <h2 className="section-title">Trade Log</h2>
      {recent.length === 0 ? (
        <div className="trade-empty">No trades recorded</div>
      ) : (
        <table className="trade-table">
          <thead>
            <tr>
              <th>Time</th>
              <th>Symbol</th>
              <th>Strategy</th>
              <th>Action</th>
              <th>Price</th>
              <th>ROI</th>
            </tr>
          </thead>
          <tbody>
            {recent.map((t, i) => {
              const action = (t.action ?? t.side ?? '').toLowerCase();
              const isBuy = action === 'buy';
              return (
                <tr key={i} className={isBuy ? 'row-buy' : 'row-sell'}>
                  <td>{formatTime(t.timestamp ?? t.time ?? '')}</td>
                  <td>{t.symbol ?? t.pair ?? '—'}</td>
                  <td>{t.strategy ?? '—'}</td>
                  <td className={isBuy ? 'buy-text' : 'sell-text'}>{action.toUpperCase() || '—'}</td>
                  <td>{t.price != null ? Number(t.price).toFixed(4) : '—'}</td>
                  <td className={Number(t.roi) >= 0 ? 'positive' : 'negative'}>
                    {t.roi != null ? `${Number(t.roi) >= 0 ? '+' : ''}${Number(t.roi).toFixed(2)}%` : '—'}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      )}
    </div>
  );
}
