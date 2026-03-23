import { useState } from 'react';
import { Button, View, StyleSheet, Alert } from 'react-native';
import * as DocumentPicker from 'expo-document-picker';
import { ThemedText } from '@/components/ThemedText';
import { ThemedView } from '@/components/ThemedView';

export default function UploadScreen() {
  const [fileName, setFileName] = useState<string | null>(null);

  const handleUpload = async () => {
    try {
      const result = await DocumentPicker.getDocumentAsync({
        type: '*/*',
        copyToCacheDirectory: true,
      });

      if (result.canceled) return;

      setFileName(result.assets[0].name);
      Alert.alert('File Selected', `You picked: ${result.assets[0].name}`);
      
      // Optional: upload to server or process here
      // const uri = result.assets[0].uri;
      // Do something with the file
    } catch (error) {
      console.error(error);
      Alert.alert('Error', 'Failed to select file');
    }
  };

  return (
    <ThemedView style={styles.container}>
      <ThemedText type="title">📤 Upload</ThemedText>

      <Button title="Select File to Upload" onPress={handleUpload} />

      {fileName && (
        <ThemedText style={styles.fileName}>
          Selected File: {fileName}
        </ThemedText>
      )}
    </ThemedView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    padding: 20,
    gap: 20,
  },
  fileName: {
    marginTop: 20,
    fontSize: 16,
    fontStyle: 'italic',
  },
});
