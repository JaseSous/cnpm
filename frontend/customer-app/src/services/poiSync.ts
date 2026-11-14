import { poiClient } from '../api/client';
import { POI } from '../types';
import { getPOIsFromDB, savePOIsToDB, getDataVersionFromDB } from './db';

export interface SyncResult {
  pois: POI[];
  dataVersion: number;
  fromCache: boolean;
}

export const syncPOIs = async (languageCode: string): Promise<SyncResult> => {
  const localVersion = await getDataVersionFromDB(languageCode);

  try {
    const response = await poiClient.get('/api/pois', {
      params: {
        lang: languageCode,
        since_version: localVersion > 0 ? localVersion : undefined,
      },
      // Chấp nhận cả 200 (mới) và 304 (chưa thay đổi)
      validateStatus: (status) => status === 200 || status === 304,
    });

    // 1. Trường hợp 304 Not Modified: dùng IndexedDB hiện có
    if (response.status === 304) {
      const cached = await getPOIsFromDB(languageCode);
      return {
        pois: cached,
        dataVersion: localVersion,
        fromCache: true,
      };
    }

    // 2. Trường hợp 200 OK: nhận dữ liệu mới và cập nhật IndexedDB
    if (response.status === 200 && response.data) {
      const serverPOIs: POI[] = response.data.pois || [];
      const newVersion: number = response.data.data_version || localVersion;

      await savePOIsToDB(languageCode, serverPOIs, newVersion);
      return {
        pois: serverPOIs,
        dataVersion: newVersion,
        fromCache: false,
      };
    }
  } catch (error) {
    console.warn('Mất kết nối tới máy chủ POI, chuyển sang chế độ offline IndexedDB:', error);
  }

  // 3. Fallback đọc từ IndexedDB khi offline
  const cachedPOIs = await getPOIsFromDB(languageCode);
  return {
    pois: cachedPOIs,
    dataVersion: localVersion,
    fromCache: true,
  };
};
