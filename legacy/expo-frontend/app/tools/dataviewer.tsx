import React, { useState, useEffect } from 'react';
import { ScrollView, View, Dimensions, Text } from 'react-native';
import { LineChart } from 'react-native-chart-kit';
import { ThemedView } from '@/components/ThemedView';
import { ThemedText } from '@/components/ThemedText';

const screenWidth = Dimensions.get('window').width;

// Example strategy performance data (replace with live pull later)
const strategyData = [
  { strategy: 'Momentum', roi: 12, date: '2025-01-01' },
  { strategy: 'Momentum', roi: 18, date: '2025-02-01' },
  { strategy: 'Momentum', roi: 21, date: '2025-03-01' },
  { strategy: 'Momentum', roi: 15, date: '2025-04-01' },
  { strategy: 'Momentum', roi: 25, date: '2025-05-01' },
];

export default function DataViewerScreen() {
  const [data, setData] = useState(strategyData);

  useEffect(() => {
    // later: pull live data from local database or API
    setData(strategyData);
  }, []);

  return (
    <ScrollView>
      <ThemedView style={{ padding: 20 }}>
        <ThemedText style={{ fontSize: 20, marginBottom: 20 }}>
          Strategy ROI Over Time
        </ThemedText>

        <LineChart
          data={{
            labels: data.map((item) => item.date),
            datasets: [{ data: data.map((item) => item.roi) }],
          }}
          width={screenWidth - 40}
          height={220}
          yAxisSuffix="%"
          chartConfig={{
            backgroundColor: '#1E2923',
            backgroundGradientFrom: '#08130D',
            backgroundGradientTo: '#1E2923',
            decimalPlaces: 2,
            color: (opacity = 1) => `rgba(26, 255, 146, ${opacity})`,
            labelColor: (opacity = 1) => `rgba(255, 255, 255, ${opacity})`,
            style: {
              borderRadius: 16,
            },
            propsForDots: {
              r: '6',
              strokeWidth: '2',
              stroke: '#ffa726',
            },
          }}
          bezier
          style={{ borderRadius: 16 }}
        />

        <View style={{ marginTop: 20 }}>
          <ThemedText style={{ fontWeight: 'bold' }}>
            Summary Stats:
          </ThemedText>
          {data.map((item, index) => (
            <Text key={index}>
              {item.date}: {item.strategy} - ROI: {item.roi}%
            </Text>
          ))}
        </View>
      </ThemedView>
    </ScrollView>
  );
}
