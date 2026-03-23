import { ThemedText } from '@/components/ThemedText';
import { ThemedView } from '@/components/ThemedView';
import { StyleSheet, TextInput, Button, KeyboardAvoidingView, Platform } from 'react-native';
import { useState } from 'react';

export default function AIScreen() {
  const [prompt, setPrompt] = useState('');
  const [response, setResponse] = useState('');

  const handleRunAI = async () => {
    try {
     const res = await fetch('http://127.0.0.1:5005/chat', { 
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ prompt }),
      });

      const data = await res.json();
      setResponse(data.response || '⚠️ No response from Aegis.');
    } catch (err) {
      console.error('❌ Error talking to Baby Aegis:', err);
      setResponse('⚠️ Failed to connect to Aegis.');
    }
  };

  return (
    <ThemedView style={styles.container}>
      <ThemedText type="title">🤖 Ask Baby Aegis</ThemedText>

      <KeyboardAvoidingView
        behavior={Platform.OS === 'ios' ? 'padding' : undefined}
        style={styles.inputContainer}
      >
        <TextInput
          style={styles.input}
          placeholder="Ask the AI something..."
          value={prompt}
          onChangeText={setPrompt}
          multiline
        />
        <Button title="Run AI" onPress={handleRunAI} />
      </KeyboardAvoidingView>

      {response !== '' && (
        <ThemedView style={styles.responseBox}>
          <ThemedText>{response}</ThemedText>
        </ThemedView>
      )}
    </ThemedView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    padding: 20,
    justifyContent: 'flex-start',
    gap: 20,
  },
  inputContainer: {
    gap: 12,
  },
  input: {
    borderWidth: 1,
    borderColor: '#ccc',
    padding: 12,
    borderRadius: 8,
    minHeight: 60,
    textAlignVertical: 'top',
  },
  responseBox: {
    backgroundColor: '#1e1e1e',
    padding: 12,
    borderRadius: 8,
    marginTop: 20,
  },
});
