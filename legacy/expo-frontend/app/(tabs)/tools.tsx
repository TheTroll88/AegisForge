import { StyleSheet, TouchableOpacity } from 'react-native';
import { ThemedText } from '@/components/ThemedText';
import { ThemedView } from '@/components/ThemedView';
import { useRouter } from 'expo-router';
import type { LinkProps } from 'expo-router';

export default function ToolsScreen() {
  const router = useRouter();

  const tools: { name: string; route: LinkProps['href'] }[] = [
    { name: 'Data Viewer', route: '/tools/dataviewer' },
    { name: 'Performance Monitor', route: '/tools/performance' },
    { name: 'AI Assistant', route: '/tools/ai' },
    { name: 'File Uploader', route: '/tools/upload' },
    { name: '📊 Strategy Explorer', route: '/tools/strategyexplorer' },
  ];

  return (
    <ThemedView style={styles.container}>
      <ThemedText type="title">🛠️ Tools</ThemedText>

      {tools.map((tool, index) => (
        <TouchableOpacity
          key={index}
          style={styles.toolItem}
          onPress={() => router.push(tool.route)}
        >
          <ThemedText type="defaultSemiBold">{tool.name}</ThemedText>
        </TouchableOpacity>
      ))}
    </ThemedView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    padding: 20,
    gap: 16,
  },
  toolItem: {
    padding: 16,
    borderRadius: 8,
    backgroundColor: '#ccc2',
  },
});
