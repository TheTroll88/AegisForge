import { StyleSheet, Switch, View } from 'react-native';
import { useState } from 'react';

import { ThemedText } from '@/components/ThemedText';
import { ThemedView } from '@/components/ThemedView';

export default function SettingsScreen() {
  const [isDarkMode, setIsDarkMode] = useState(false);
  const [notificationsEnabled, setNotificationsEnabled] = useState(true);

  return (
    <ThemedView style={styles.container}>
      <ThemedText type="title">⚙️ Settings</ThemedText>

      <View style={styles.settingItem}>
        <ThemedText>Dark Mode</ThemedText>
        <Switch
          value={isDarkMode}
          onValueChange={setIsDarkMode}
        />
      </View>

      <View style={styles.settingItem}>
        <ThemedText>Notifications</ThemedText>
        <Switch
          value={notificationsEnabled}
          onValueChange={setNotificationsEnabled}
        />
      </View>

      <ThemedText style={styles.footerNote}>
        These toggles are placeholders. You can connect them to global state or backend preferences later.
      </ThemedText>
    </ThemedView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    padding: 20,
    gap: 16,
  },
  settingItem: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 12,
  },
  footerNote: {
    marginTop: 24,
    fontSize: 12,
    opacity: 0.6,
  },
});
