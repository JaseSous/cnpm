import { useState, useEffect, useRef } from 'react';
import { POI } from '../types';

/**
 * Công thức Haversine tính khoảng cách theo đường cong Trái Đất (đơn vị: mét)
 * Toàn bộ tính toán diễn ra tại Client của du khách, không gửi tọa độ lên máy chủ.
 */
export function calculateHaversineDistance(
  lat1: number,
  lon1: number,
  lat2: number,
  lon2: number
): number {
  const R = 6371e3; // Bán kính Trái Đất (mét)
  const dLat = ((lat2 - lat1) * Math.PI) / 180;
  const dLon = ((lon2 - lon1) * Math.PI) / 180;
  const radLat1 = (lat1 * Math.PI) / 180;
  const radLat2 = (lat2 * Math.PI) / 180;

  const a =
    Math.sin(dLat / 2) * Math.sin(dLat / 2) +
    Math.sin(dLon / 2) * Math.sin(dLon / 2) * Math.cos(radLat1) * Math.cos(radLat2);
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));

  return Math.round(R * c);
}

export interface GPSTrackerOptions {
  autoAudioEnabled?: boolean;
  onTriggerPOI?: (poi: POI, distance: number) => void;
}

export function useGPSTracker(pois: POI[], options: GPSTrackerOptions = {}) {
  const { autoAudioEnabled = true, onTriggerPOI } = options;

  const [currentCoords, setCurrentCoords] = useState<[number, number] | null>(null);
  const [gpsError, setGpsError] = useState<string | null>(null);
  const [activeTriggeredPoi, setActiveTriggeredPoi] = useState<POI | null>(null);

  // Theo dõi các POI đã phát trong phiên: poiId -> boolean
  const playedPoisRef = useRef<Record<number, boolean>>({});

  useEffect(() => {
    if (!('geolocation' in navigator)) {
      setGpsError('Thiết bị hoặc trình duyệt không hỗ trợ Geolocation GPS.');
      return;
    }

    const watchId = navigator.geolocation.watchPosition(
      (position) => {
        const uLat = position.coords.latitude;
        const uLng = position.coords.longitude;
        setCurrentCoords([uLat, uLng]);
        setGpsError(null);

        if (!autoAudioEnabled || pois.length === 0) return;

        // Quét khoảng cách tới tất cả POIs
        for (const poi of pois) {
          const dist = calculateHaversineDistance(uLat, uLng, poi.latitude, poi.longitude);

          // 1. Kiểm tra điều kiện tự động kích hoạt
          if (dist <= poi.trigger_radius) {
            const hasPlayed = playedPoisRef.current[poi.poi_id];
            if (!hasPlayed && poi.audio_url && !poi.fallback) {
              playedPoisRef.current[poi.poi_id] = true;
              setActiveTriggeredPoi(poi);

              if (onTriggerPOI) {
                onTriggerPOI(poi, dist);
              }
            }
          }

          // 2. Kiểm tra điều kiện reset khi du khách di chuyển ra xa (bán kính * 1.5)
          if (dist > poi.trigger_radius * 1.5) {
            if (playedPoisRef.current[poi.poi_id]) {
              playedPoisRef.current[poi.poi_id] = false;
            }
          }
        }
      },
      (err) => {
        setGpsError(err.message);
      },
      {
        enableHighAccuracy: true,
        timeout: 10000,
        maximumAge: 3000,
      }
    );

    return () => {
      navigator.geolocation.clearWatch(watchId);
    };
  }, [pois, autoAudioEnabled, onTriggerPOI]);

  return {
    currentCoords,
    gpsError,
    activeTriggeredPoi,
    setActiveTriggeredPoi,
  };
}
