import { useEffect } from 'react';
import { useRouter } from 'expo-router';

export default function IndexRedirect() {
  const router = useRouter();

  useEffect(() => {
    const timer = setTimeout(() => {
      router.replace('/tools/memory-rebuilder');
    }, 100); // Add slight delay to avoid navigation before layout mounts

    return () => clearTimeout(timer);
  }, []);

  return null;
}
