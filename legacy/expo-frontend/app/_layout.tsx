import { Tabs } from 'expo-router';
import { WalletProvider } from '@/services/WalletContext';

export default function RootLayout() {
  return (
    <WalletProvider>
      <Tabs />
    </WalletProvider>
  );
}
