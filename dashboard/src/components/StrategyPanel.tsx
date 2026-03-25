import { toggleStrategy } from '../api';

interface StrategyPanelProps {
  strategies: Record<string, boolean>;
  onToggle: (name: string, active: boolean) => void;
}

export default function StrategyPanel({ strategies, onToggle }: StrategyPanelProps) {
  const handleToggle = async (name: string) => {
    try {
      const newState = await toggleStrategy(name);
      onToggle(name, newState);
    } catch {
      // API down — don't update state
    }
  };

  const names = Object.keys(strategies);

  return (
    <div className="strategy-panel">
      <h2 className="section-title">Strategies</h2>
      <div className="strategy-list">
        {names.map((name) => (
          <div key={name} className="strategy-card">
            <div className="strategy-info">
              <span className="strategy-name">{name.replace(/_/g, ' ')}</span>
              <span className={`strategy-badge ${strategies[name] ? 'active' : 'inactive'}`}>
                {strategies[name] ? 'Active' : 'Inactive'}
              </span>
            </div>
            <button
              className={`toggle-btn ${strategies[name] ? 'on' : 'off'}`}
              onClick={() => handleToggle(name)}
              aria-label={`Toggle ${name}`}
            >
              <span className="toggle-knob" />
            </button>
          </div>
        ))}
      </div>
    </div>
  );
}
