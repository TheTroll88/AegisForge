import { StyleSheet } from 'react-native';
import { ThemedText } from '@/components/ThemedText';
import { ThemedView } from '@/components/ThemedView';

export default function DocsScreen() {
  return (
    <ThemedView style={styles.container}>
      <ThemedText type="title">📚 Documentation</ThemedText>
      <ThemedText style={styles.subtitle}>
        All your files, guides, and knowledge lives here.
      </ThemedText>
      <ThemedText style={styles.body}>
        This is where you'd display markdown files, internal project references, or even an embedded help system.
      </ThemedText>
    </ThemedView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    padding: 20,
    gap: 12,
  },
  subtitle: {
    fontSize: 16,
    marginTop: 4,
  },
  body: {
    fontSize: 14,
    lineHeight: 20,
  },
});
