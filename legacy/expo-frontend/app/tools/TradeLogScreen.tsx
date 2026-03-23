import React, { useEffect, useState } from 'react';
import { View, ScrollView, Text, StyleSheet } from 'react-native';
import { ThemedText } from '@/components/ThemedText';
import { ThemedView } from '@/components/ThemedView';

interface TradeLogEntry {
  strategy: string;
  timestamp: string;
  success: boolean;
  roi: number;
}

export default function TradeLogScreen() {
  const [logs, setLogs] = useState<TradeLogEntry[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchLogs = async () => {
    try {
      const res = await fetch('http://127.0.0.1:5005/trade-logs');
      const data = await res.json();
      setLogs(data.logs.reverse()); // most recent first
    } catch (err) {
      console.error('Failed to fetch trade logs:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchLogs(); // initial load
    const interval = setInterval(fetchLogs, 10000); // refresh every 10s
    return () => clearInterval(interval); // cleanup
  }, []);

  return (
    <ThemedView style={styles.container}>
      <ThemedText type="title">📜 Trade Log</ThemedText>
      <ScrollView style={styles.scroll}>
        {loading ? (
          <Text style={styles.status}>Loading...</Text>
        ) : logs.length === 0 ? (
          <Text style={styles.status}>No trades recorded yet.</Text>
        ) : (
          logs.map((entry, index) => (
            <View key={index} style={styles.card}>
              <Text style={styles.strategy}>{entry.strategy}</Text>
              <Text>{new Date(entry.timestamp).toLocaleString()}</Text>
              <Text style={entry.success ? styles.success : styles.failure}>
                {entry.success ? '✅ Win' : '❌ Loss'} | ROI: {entry.roi}
              </Text>
            </View>
          ))
        )}
      </ScrollView>
    </ThemedView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    padding: 20,
  },
  scroll: {
    marginTop: 10,
  },
  status: {
    textAlign: 'center',
    marginTop: 20,
    fontSize: 16,
    color: '#aaa',
  },
  card: {
    backgroundColor: '#1e1e1e',
    padding: 15,
    borderRadius: 10,
    marginBottom: 12,
  },
  strategy: {
    fontWeight: 'bold',
    fontSize: 16,
    marginBottom: 4,
  },
  success: {
    color: 'lightgreen',
    marginTop: 4,
  },
  failure: {
    color: 'salmon',
    marginTop: 4,
  },
});
