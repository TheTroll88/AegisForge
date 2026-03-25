import { useState, useEffect, useCallback } from 'react'
import './App.css'
import { checkHealth, getStrategies, getStrategyStatus, getTradeLogs, getLivePerformance, getWhaleSignals, getWhaleMovers } from './api'
import Header from './components/Header'
import StatsBar from './components/StatsBar'
import StrategyPanel from './components/StrategyPanel'
import PerformanceChart from './components/PerformanceChart'
import WhalePanel from './components/WhalePanel'
import TradeLog from './components/TradeLog'

function App() {
  const [online, setOnline] = useState(false)
  const [strategies, setStrategies] = useState<Record<string, boolean>>({})
  const [trades, setTrades] = useState<any[]>([])
  const [performance, setPerformance] = useState<any>({})
  const [whaleSignals, setWhaleSignals] = useState<any[]>([])
  const [whaleMovers, setWhaleMovers] = useState<any[]>([])

  const fetchAll = useCallback(async () => {
    const healthy = await checkHealth()
    setOnline(healthy)
    if (!healthy) return

    try {
      const names = await getStrategies()
      const statuses = await Promise.all(names.map(async (n) => {
        try { return { name: n, active: await getStrategyStatus(n) } }
        catch { return { name: n, active: false } }
      }))
      const map: Record<string, boolean> = {}
      for (const s of statuses) map[s.name] = s.active
      setStrategies(map)
    } catch { /* offline mid-fetch */ }

    try { setTrades(await getTradeLogs()) } catch { /* */ }
    try { setPerformance(await getLivePerformance()) } catch { /* */ }
    try { setWhaleSignals(await getWhaleSignals(10)) } catch { /* */ }
    try { setWhaleMovers(await getWhaleMovers(10)) } catch { /* */ }
  }, [])

  useEffect(() => {
    fetchAll()
    const id = setInterval(fetchAll, 5000)
    return () => clearInterval(id)
  }, [fetchAll])

  const handleToggle = (name: string, active: boolean) => {
    setStrategies(prev => ({ ...prev, [name]: active }))
  }

  const activeCount = Object.values(strategies).filter(Boolean).length
  const totalCount = Object.keys(strategies).length

  return (
    <div className="app">
      <Header online={online} />
      <StatsBar
        totalTrades={performance.total_trades ?? 0}
        winRate={performance.win_rate ?? 0}
        avgRoi={performance.average_roi ?? 0}
        activeStrategies={activeCount}
        totalStrategies={totalCount}
      />
      <div className="main-grid">
        <StrategyPanel strategies={strategies} onToggle={handleToggle} />
        <PerformanceChart trades={trades} />
      </div>
      <WhalePanel signals={whaleSignals} movers={whaleMovers} />
      <TradeLog trades={trades} />
    </div>
  )
}

export default App
