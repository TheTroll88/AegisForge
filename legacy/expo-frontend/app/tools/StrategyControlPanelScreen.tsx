import React, { useEffect, useState } from 'react';
import { ScrollView, View, Text, Pressable, StyleSheet, Alert } from 'react-native';
import { ThemedText } from '@/components/ThemedText';
import { ThemedView } from '@/components/ThemedView';
import {
  fetchStrategies,
  toggleStrategy,
  simulateTrade,
  fetchPerformance,
} from '@/services/kratosAPI';

interface StrategyStats {
  win_rate: number;
  total_trades: number;
  average_roi: number;
  profit_loss: number;
}

export default function StrategyControlPanelScreen() {
  const [strategies, setStrategies] = useState<string[]>([]);
  const [statuses, setStatuses] = useState<Record<string, boolean>>({});
  const [performance, setPerformance] = useState<Record<string, any>>({});
  const [leaderboard, setLeaderboard] = useState<Record<string, StrategyStats>>({});

  const loadAllData = async () => {
    try {
      const stratData = await fetchStrategies();
      const filteredStrategies = stratData.strategies.filter((s: string) => s !== '__init__');
      setStrategies(filteredStrategies);

      const statusMap: Record<string, boolean> = {};
      for (const name of filteredStrategies) {
        try {
          const baseUrl = "http://127.0.0.1:5005";
          const res = await fetch(`${baseUrl}/strategy/${name}/status`);
          const json = await res.json();
          statusMap[name] = json.active;
        } catch (e) {
          statusMap[name] = false;
        }
      }
      setStatuses(statusMap);

      const perfData = await fetchPerformance();
      // Convert performance/live format to display format
      if (perfData.strategies) {
        setPerformance(perfData.strategies);
      }

      // Set leaderboard from same data
      if (perfData.strategies) {
        const filteredLeaderboard = Object.fromEntries(
          Object.entries(perfData.strategies)
            .filter(([key]) => key !== 'overall' && key !== '__init__')
            .map(([key, value]: [string, any]) => [
              key,
              {
                win_rate: parseFloat(((value.wins / (value.wins + value.losses)) * 100).toFixed(2)),
                total_trades: value.trades,
                average_roi: value.roi,
                profit_loss: (value.roi * value.trades),
              },
            ])
        );
        setLeaderboard(filteredLeaderboard);
      }
    } catch (err) {
      console.error('Error loading strategy data:', err);
    }
  };

  useEffect(() => {
    loadAllData(); // initial load

    const interval = setInterval(() => {
      loadAllData(); // auto-refresh every 10 sec
    }, 10000);

    return () => clearInterval(interval); // cleanup
  }, []);

  const handleToggle = async (name: string) => {
    try {
      const res = await toggleStrategy(name);
      setStatuses((prev) => ({ ...prev, [name]: res.active }));
    } catch (err) {
      Alert.alert('Error', `Failed to toggle ${name}`);
    }
  };

  const handleSimulate = async (name: string) => {
    try {
      const res = await simulateTrade(name);
      Alert.alert(
        `Simulated: ${name}`,
        `Success: ${res.simulated_trade.success}\nROI: ${res.simulated_trade.roi}\nTime: ${res.simulated_trade.timestamp}`
      );
    } catch (err) {
      Alert.alert('Error', `Failed to simulate ${name}`);
    }
  };

  return (
    <ThemedView style={styles.container}>
      <ThemedText type="title">🧠 Kratos Strategy Panel</ThemedText>
      <ScrollView style={{ marginTop: 20 }}>
        {strategies.map((name, idx) => (
          <View key={idx} style={styles.card}>
            <ThemedText type="subtitle">📈 {name}</ThemedText>
            <Text style={styles.status}>
              Status: {statuses[name] ? '✅ Active' : '❌ Inactive'}
            </Text>

            {performance[name] && (
              <View style={styles.metrics}>
                <Text>Trades: {performance[name].trades}</Text>
                <Text>Wins: {performance[name].wins}</Text>
                <Text>Losses: {performance[name].losses}</Text>
                <Text>ROI: {performance[name].roi.toFixed(4)}</Text>
                <Text>
                  Win Rate:{' '}
                  {((performance[name].wins / performance[name].trades) * 100).toFixed(2)}%
                </Text>
              </View>
            )}

            {leaderboard[name] && (
              <View style={styles.leaderboard}>
                <Text>🏆 Leaderboard Stats:</Text>
                <Text>Win Rate: {leaderboard[name].win_rate}%</Text>
                <Text>Avg ROI: {leaderboard[name].average_roi}%</Text>
                <Text>Total Trades: {leaderboard[name].total_trades}</Text>
                <Text>
                  P/L:{' '}
                  {leaderboard[name].profit_loss >= 0 ? '+' : '-'}$
                  {Math.abs(leaderboard[name].profit_loss).toLocaleString()}
                </Text>
              </View>
            )}

            <View style={styles.actions}>
              <Pressable style={styles.toggleBtn} onPress={() => handleToggle(name)}>
                <Text style={styles.btnText}>Toggle</Text>
              </Pressable>
              <Pressable style={styles.simBtn} onPress={() => handleSimulate(name)}>
                <Text style={styles.btnText}>Simulate</Text>
              </Pressable>
            </View>
          </View>
        ))}
      </ScrollView>
    </ThemedView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    padding: 20,
  },
  card: {
    backgroundColor: '#1e1e1e',
    padding: 15,
    borderRadius: 12,
    marginBottom: 20,
  },
  status: {
    marginTop: 5,
    fontSize: 16,
  },
  metrics: {
    marginTop: 10,
  },
  leaderboard: {
    marginTop: 10,
    backgroundColor: '#2a2a2a',
    padding: 10,
    borderRadius: 6,
  },
  actions: {
    flexDirection: 'row',
    marginTop: 12,
  },
  toggleBtn: {
    backgroundColor: '#2196F3',
    padding: 10,
    borderRadius: 6,
    marginRight: 10,
  },
  simBtn: {
    backgroundColor: '#4CAF50',
    padding: 10,
    borderRadius: 6,
  },
  btnText: {
    color: 'white',
    fontWeight: 'bold',
  },
});
