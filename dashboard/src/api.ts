const API_BASE = 'http://localhost:8000';

async function apiFetch<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, options);
  if (!res.ok) throw new Error(`API ${res.status}`);
  return res.json() as Promise<T>;
}

export async function checkHealth(): Promise<boolean> {
  try {
    await apiFetch('/');
    return true;
  } catch {
    return false;
  }
}

export async function getStrategies(): Promise<string[]> {
  const data = await apiFetch<{ strategies: string[] }>('/strategies');
  return data.strategies;
}

export async function getStrategyStatus(name: string): Promise<boolean> {
  const data = await apiFetch<{ strategy: string; active: boolean }>(`/strategy/${encodeURIComponent(name)}/status`);
  return data.active;
}

export async function toggleStrategy(name: string): Promise<boolean> {
  const data = await apiFetch<{ strategy: string; active: boolean }>(`/strategy/${encodeURIComponent(name)}/toggle`, { method: 'POST' });
  return data.active;
}

export async function getTradeLogs(): Promise<any[]> {
  const data = await apiFetch<{ logs: any[] }>('/trade-logs');
  return data.logs ?? [];
}

export async function getLivePerformance(): Promise<any> {
  return apiFetch('/performance/live');
}

export async function getWhaleSignals(limit = 10): Promise<any[]> {
  const data = await apiFetch<{ signals: any[] }>(`/whales/signals?limit=${limit}`);
  return data.signals ?? [];
}

export async function getWhaleMovers(limit = 10): Promise<any[]> {
  const data = await apiFetch<{ movers: any[] }>(`/whales/movers?limit=${limit}`);
  return data.movers ?? [];
}
