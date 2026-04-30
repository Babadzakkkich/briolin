import { useEffect, useState } from 'react';
import { useAuthStore } from '@/entities/session/model/store';

const BASE = (import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000/api/v1') as string;

interface AuthImageProps {
  src: string;
  alt?: string;
  className?: string;
  fallback?: React.ReactNode;
}

export function AuthImage({ src, alt = '', className, fallback }: AuthImageProps) {
  const [blobUrl, setBlobUrl] = useState<string | null>(null);
  const [failed, setFailed] = useState(false);

  useEffect(() => {
    if (!src) { setFailed(true); return; }
    let active = true;
    let objectUrl: string | null = null;

    const fullUrl = src.startsWith('http') ? src : BASE + src;
    const token = useAuthStore.getState().accessToken;

    fetch(fullUrl, { headers: token ? { Authorization: `Bearer ${token}` } : {} })
      .then((res) => {
        if (!res.ok) throw new Error('failed');
        return res.blob();
      })
      .then((blob) => {
        if (!active) return;
        objectUrl = URL.createObjectURL(blob);
        setBlobUrl(objectUrl);
      })
      .catch(() => { if (active) setFailed(true); });

    return () => {
      active = false;
      if (objectUrl) URL.revokeObjectURL(objectUrl);
    };
  }, [src]);

  if (failed || !src) return fallback ? <>{fallback}</> : null;
  if (!blobUrl) return fallback ? <>{fallback}</> : null;
  return <img src={blobUrl} alt={alt} className={className} />;
}
