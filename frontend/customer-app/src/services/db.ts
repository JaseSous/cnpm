import { openDB, DBSchema, IDBPDatabase } from 'idb';
import { POI } from '../types';

interface CustomerDBSchema extends DBSchema {
  pois: {
    key: string; // composite key: `${poi_id}_${lang}`
    value: POI & { lang_key: string; stored_at: number };
    indexes: { 'by-lang': string };
  };
  metadata: {
    key: string;
    value: { config_key: string; data_version: number; updated_at: string };
  };
}

const DB_NAME = 'LinhUngPagodaDB';
const DB_VERSION = 1;

let dbPromise: Promise<IDBPDatabase<CustomerDBSchema>> | null = null;

export const getDB = () => {
  if (!dbPromise) {
    dbPromise = openDB<CustomerDBSchema>(DB_NAME, DB_VERSION, {
      upgrade(db) {
        if (!db.objectStoreNames.contains('pois')) {
          const poiStore = db.createObjectStore('pois', { keyPath: 'lang_key' });
          poiStore.createIndex('by-lang', 'lang_key');
        }
        if (!db.objectStoreNames.contains('metadata')) {
          db.createObjectStore('metadata', { keyPath: 'config_key' });
        }
      },
    });
  }
  return dbPromise;
};

export const getPOIsFromDB = async (languageCode: string): Promise<POI[]> => {
  try {
    const db = await getDB();
    const all = await db.getAll('pois');
    return all
      .filter((item) => item.lang_key.endsWith(`_${languageCode}`))
      .map(({ lang_key, stored_at, ...poi }) => poi as POI);
  } catch (error) {
    console.warn('Lỗi đọc IndexedDB:', error);
    return [];
  }
};

export const savePOIsToDB = async (
  languageCode: string,
  pois: POI[],
  dataVersion: number
): Promise<void> => {
  try {
    const db = await getDB();
    const tx = db.transaction(['pois', 'metadata'], 'readwrite');
    const now = Date.now();

    // 1. Lưu các POI
    for (const poi of pois) {
      await tx.objectStore('pois').put({
        ...poi,
        lang_key: `${poi.poi_id}_${languageCode}`,
        stored_at: now,
      });
    }

    // 2. Lưu version metadata
    await tx.objectStore('metadata').put({
      config_key: `poi_data_version_${languageCode}`,
      data_version: dataVersion,
      updated_at: new Date().toISOString(),
    });

    await tx.done;
  } catch (error) {
    console.warn('Lỗi ghi IndexedDB:', error);
  }
};

export const getDataVersionFromDB = async (languageCode: string): Promise<number> => {
  try {
    const db = await getDB();
    const meta = await db.get('metadata', `poi_data_version_${languageCode}`);
    return meta ? meta.data_version : 0;
  } catch {
    return 0;
  }
};

export const clearCachedPOIs = async (): Promise<void> => {
  try {
    const db = await getDB();
    await db.clear('pois');
    await db.clear('metadata');
  } catch (error) {
    console.warn('Lỗi xóa cache IndexedDB:', error);
  }
};
