interface HeaderProps {
  online: boolean;
}

export default function Header({ online }: HeaderProps) {
  return (
    <header className="header">
      <div className="header-brand">
        <h1 className="header-logo">AegisForge</h1>
        <span className="header-tagline">AI Trading Engine</span>
      </div>
      <div className="header-status">
        <span className={`status-dot ${online ? 'online' : 'offline'}`} />
        <span className="status-text">{online ? 'Engine Online' : 'Engine Offline'}</span>
      </div>
    </header>
  );
}
