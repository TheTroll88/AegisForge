import React, { useState } from 'react';
import {
  ScrollView,
  View,
  StyleSheet,
  TextInput,
  Button,
  Text,
  KeyboardAvoidingView,
  Platform,
} from 'react-native';
import HeaderBar from '@/components/HeaderBar';
import PriceSummary from '@/components/PriceSummary';
import PriceChart from '@/components/PriceChart';
import RecentTransactions from '@/components/RecentTransactions';

export default function DashboardScreen() {
  const [prompt, setPrompt] = useState('');
  const [response, setResponse] = useState('');

  const btc = {
    symbol: 'BTC',
    price: 30500.52,
    change24h: -1.21,
  };

  const eth = {
    symbol: 'ETH',
    price: 1875.89,
    change24h: 2.34,
  };

  const transactions = [
    {
      id: '1',
      type: 'Send',
      amount: -0.01,
      date: '2025-07-10',
      asset: 'BTC',
      price: 30500.52,
    },
    {
      id: '2',
      type: 'Receive',
      amount: 0.25,
      date: '2025-07-09',
      asset: 'ETH',
      price: 1875.89,
    },
  ];

  async function sendPromptToAegis(prompt: string) {
    try {
      const res = await fetch('http://localhost:5005/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ prompt }),
      });
      const data = await res.json();
      return data.response;
    } catch (err) {
      console.error('Aegis connection error:', err);
      return '⚠️ Connection to Baby Aegis failed.';
    }
  }

  const handleAsk = async () => {
    const reply = await sendPromptToAegis(prompt);
    setResponse(reply);
  };

  return (
    <View style={styles.container}>
      <HeaderBar />
      <ScrollView contentContainerStyle={styles.content}>
        <PriceSummary btc={btc} eth={eth} />
        <PriceChart data={[50, 10, 40, 95, 85, 91, 35, 53]} />
        <RecentTransactions transactions={transactions} />

        {/* === Aegis Assistant Chat === */}
        <View style={styles.chatContainer}>
          <Text style={styles.chatTitle}>🤖 Ask Baby Aegis</Text>

          <KeyboardAvoidingView
            behavior={Platform.OS === 'ios' ? 'padding' : undefined}
            style={styles.inputBlock}
          >
            <TextInput
              style={styles.input}
              placeholder="Type a question like: 'What’s the win rate of RSI strategy?'"
              value={prompt}
              onChangeText={setPrompt}
              multiline
            />
            <Button title="Ask Aegis" onPress={handleAsk} />
          </KeyboardAvoidingView>

          {response !== '' && (
            <View style={styles.responseBlock}>
              <Text style={styles.responseLabel}>🧠 Aegis:</Text>
              <Text style={styles.responseText}>{response}</Text>
            </View>
          )}
        </View>
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#000',
  },
  content: {
    padding: 16,
    paddingBottom: 40,
  },
  chatContainer: {
    marginTop: 32,
    backgroundColor: '#111',
    borderRadius: 12,
    padding: 16,
  },
  chatTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#fff',
    marginBottom: 12,
  },
  inputBlock: {
    gap: 12,
  },
  input: {
    borderWidth: 1,
    borderColor: '#555',
    padding: 12,
    borderRadius: 8,
    minHeight: 60,
    color: '#fff',
    backgroundColor: '#1a1a1a',
    textAlignVertical: 'top',
  },
  responseBlock: {
    marginTop: 16,
  },
  responseLabel: {
    color: '#999',
    fontWeight: 'bold',
  },
  responseText: {
    color: '#eee',
    marginTop: 4,
  },
});
