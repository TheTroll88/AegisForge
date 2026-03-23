import React, { useEffect, useState } from 'react';
import { ScrollView, View, TextInput, Button, StyleSheet, Alert } from 'react-native';
import { ThemedText } from '@/components/ThemedText';
import { ThemedView } from '@/components/ThemedView';

interface StrategyConfig {
  [key: string]: number | string | boolean;
}

export default function StrategyConfigScreen() {
  const [strategies, setStrategies] = useState<string[]>([]);
  const [configs, setConfigs] = useState<Record<string, StrategyConfig>>({});

  const fetchConfigs = async () => {
    try {
      const res = await fetch('http://127.0.0.1:5005/strategies');
      const data = await res.json();
      setStrategies(data.strategies);

      data.strategies.forEach(async (name: string) => {
        try {
          const configRes = await fetch(`http://127.0.0.1:5005/strategy/${name}/config`);
          const configData = await configRes.json();
          setConfigs((prev) => ({
            ...prev,
            [name]: configData.config || {}, // just the config array
          }));
        } catch (err) {
          console.error(`Failed to fetch config for ${name}:`, err);
        }
      });
    } catch (err) {
      console.error('Failed to load strategies:', err);
    }
  };

  useEffect(() => {
    fetchConfigs();
  }, []);

  const handleChange = (name: string, key: string, value: string) => {
    setConfigs((prev) => ({
      ...prev,
      [name]: {
        ...prev[name],
        [key]: isNaN(Number(value)) ? value : Number(value),
      },
    }));
  };

  const handleSave = (name: string) => {
    const updatedLines = Object.entries(configs[name]).map(([k, v]) => `${k} = ${JSON.stringify(v)}`);

    fetch(`http://127.0.0.1:5005/strategy/${name}/config/update`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ config_lines: updatedLines }),
    })
      .then((res) => {
        if (!res.ok) throw new Error('Failed to update config');
        Alert.alert('Success', `Updated config for ${name}`);
      })
      .catch(() => Alert.alert('Error', `Could not save config for ${name}`));
  };

  return (
    <ThemedView style={styles.container}>
      <ThemedText type="title">⚙️ Strategy Config Editor</ThemedText>

      <Button title="🔄 Refresh Configs" onPress={fetchConfigs} />

      <ScrollView style={{ marginTop: 20 }}>
        {strategies.map((name, idx) => (
          <View key={idx} style={styles.card}>
            <ThemedText type="subtitle">{name}</ThemedText>
            {configs[name] &&
              Object.entries(configs[name]).map(([key, value]) => (
                <TextInput
                  key={key}
                  style={styles.input}
                  placeholder={`${key}`}
                  value={String(value)}
                  onChangeText={(text) => handleChange(name, key, text)}
                />
              ))}
            <Button title="💾 Save Config" onPress={() => handleSave(name)} />
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
    borderRadius: 10,
    marginBottom: 15,
  },
  input: {
    backgroundColor: '#333',
    color: 'white',
    padding: 10,
    marginBottom: 10,
    borderRadius: 6,
  },
});
