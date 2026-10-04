import { Injectable } from '@angular/core';
import { Capacitor } from '@capacitor/core';
import { CapacitorSQLite, SQLiteConnection, SQLiteDBConnection } from '@capacitor-community/sqlite';
import { LocalWatchlistItem } from '../models/watchlist-item.model';

@Injectable({
  providedIn: 'root'
})
export class LocalDbService {
  private sqlite: SQLiteConnection = new SQLiteConnection(CapacitorSQLite);
  private db!: SQLiteDBConnection;
  private isWeb: boolean = false;
  private dbName = 'watchmedb';

  constructor() {
    this.isWeb = Capacitor.getPlatform() === 'web';
  }

  async initDB(): Promise<void> {
    if (this.isWeb) {
      // For web fallback, we'll use localStorage
      return Promise.resolve();
    }

    try {
      this.db = await this.sqlite.createConnection(this.dbName, false, 'no-encryption', 2, false);
      await this.db.open();

      const schema = `
        CREATE TABLE IF NOT EXISTS watchlist_items (
          id TEXT PRIMARY KEY,
          backend_id TEXT UNIQUE,
          provider_id TEXT NOT NULL,
          media_type TEXT NOT NULL,
          provider TEXT NOT NULL,
          title TEXT NOT NULL,
          poster_path TEXT,
          backdrop_path TEXT,
          overview TEXT,
          release_date TEXT,
          genres TEXT,
          watched INTEGER DEFAULT 0,
          watched_at TEXT,
          rewatch INTEGER DEFAULT 0,
          added_at TEXT DEFAULT CURRENT_TIMESTAMP,
          local_note TEXT,
          rating REAL,
          media_item_id TEXT
        );
        CREATE TABLE IF NOT EXISTS app_metadata (
          key TEXT PRIMARY KEY,
          value TEXT NOT NULL
        );
      `;
      await this.db.execute(schema);

      // Migrate existing DB: add rewatch column if missing
      try {
        await this.db.run('ALTER TABLE watchlist_items ADD COLUMN rewatch INTEGER DEFAULT 0');
      } catch (e) {
        // Column already exists – ignore the error
      }
    } catch (error) {
      console.error('Error initializing SQLite:', error);
    }
  }

  async getMetadata(key: string): Promise<string | null> {
    if (this.isWeb) {
      return localStorage.getItem(`watchme_meta_${key}`);
    }
    try {
      const res = await this.db.query('SELECT value FROM app_metadata WHERE key = ?', [key]);
      return res.values && res.values.length > 0 ? res.values[0].value : null;
    } catch {
      return null;
    }
  }

  async setMetadata(key: string, value: string): Promise<void> {
    if (this.isWeb) {
      localStorage.setItem(`watchme_meta_${key}`, value);
      return;
    }
    try {
      await this.db.run('INSERT OR REPLACE INTO app_metadata (key, value) VALUES (?, ?)', [key, value]);
    } catch (e) {
      console.error('Error saving metadata:', e);
    }
  }

  async getAll(): Promise<LocalWatchlistItem[]> {
    if (this.isWeb) {
      const data = localStorage.getItem('watchme_local_db');
      return data ? JSON.parse(data) : [];
    }

    const result = await this.db.query('SELECT * FROM watchlist_items ORDER BY added_at DESC');
    return (result.values || []).map(this.mapDbRowToLocalItem);
  }

  async getPaged(page: number = 1, limit: number = 10): Promise<{ items: LocalWatchlistItem[]; total: number; totalPages: number; page: number }> {
    const all = await this.getAll();
    const total = all.length;
    const totalPages = total > 0 ? Math.max(1, Math.ceil(total / limit)) : 1;
    const validPage = Math.max(1, Math.min(page, totalPages));
    const offset = (validPage - 1) * limit;
    const items = all.slice(offset, offset + limit);
    return { items, total, totalPages, page: validPage };
  }

  async getById(id: string): Promise<LocalWatchlistItem | null> {
    if (this.isWeb) {
      const items = await this.getAll();
      return items.find(i => i.id === id) || null;
    }
    const result = await this.db.query('SELECT * FROM watchlist_items WHERE id = ?', [id]);
    return result.values && result.values.length > 0 ? this.mapDbRowToLocalItem(result.values[0]) : null;
  }

  async getByBackendId(backendId: string): Promise<LocalWatchlistItem | null> {
    if (this.isWeb) {
      const items = await this.getAll();
      return items.find(i => i.backendId === backendId) || null;
    }
    const result = await this.db.query('SELECT * FROM watchlist_items WHERE backend_id = ?', [backendId]);
    return result.values && result.values.length > 0 ? this.mapDbRowToLocalItem(result.values[0]) : null;
  }

  async save(item: LocalWatchlistItem): Promise<void> {
    if (this.isWeb) {
      const items = await this.getAll();
      const idx = items.findIndex(i => (item.backendId && i.backendId === item.backendId) || i.id === item.id);
      if (idx >= 0) {
        items[idx] = { ...items[idx], ...item };
      } else {
        items.unshift(item);
      }
      localStorage.setItem('watchme_local_db', JSON.stringify(items));
      return;
    }

    const existing = await this.getByBackendId(item.backendId);
    if (existing) {
      item.id = existing.id;
    }

    const sql = `
      INSERT OR REPLACE INTO watchlist_items 
      (id, backend_id, provider_id, media_type, provider, title, poster_path, backdrop_path, 
       overview, release_date, genres, watched, watched_at, rewatch, added_at, local_note, rating, media_item_id)
      VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    `;
    
    await this.db.run(sql, [
      item.id, item.backendId, item.providerId, item.mediaType, item.provider, item.title,
      item.posterPath || null, item.backdropPath || null, item.overview, item.releaseDate || null,
      item.genres, item.watched, item.watchedAt || null, item.rewatch ?? 0, item.addedAt, item.localNote || null,
      item.rating || null, item.mediaItemId
    ]);
  }

  async update(backendId: string, updates: Partial<LocalWatchlistItem>): Promise<void> {
    const current = await this.getByBackendId(backendId);
    if (!current) return;
    const updated = { ...current, ...updates };
    await this.save(updated);
  }

  async remove(backendId: string): Promise<void> {
    if (this.isWeb) {
      let items = await this.getAll();
      items = items.filter(i => i.backendId !== backendId);
      localStorage.setItem('watchme_local_db', JSON.stringify(items));
      return;
    }
    await this.db.run('DELETE FROM watchlist_items WHERE backend_id = ?', [backendId]);
  }

  async updateNote(backendId: string, note: string): Promise<void> {
    await this.update(backendId, { localNote: note });
  }

  async isInWatchlist(providerId: string, mediaType: string): Promise<boolean> {
    if (this.isWeb) {
      const items = await this.getAll();
      return items.some(i => i.providerId === providerId && i.mediaType === mediaType);
    }
    const result = await this.db.query('SELECT COUNT(*) as count FROM watchlist_items WHERE provider_id = ? AND media_type = ?', [providerId, mediaType]);
    return !!(result.values && result.values.length > 0 && result.values[0].count > 0);
  }

  private mapDbRowToLocalItem(row: any): LocalWatchlistItem {
    return {
      id: row.id,
      backendId: row.backend_id,
      providerId: row.provider_id,
      mediaType: row.media_type,
      provider: row.provider,
      title: row.title,
      posterPath: row.poster_path,
      backdropPath: row.backdrop_path,
      overview: row.overview,
      releaseDate: row.release_date,
      genres: row.genres,
      watched: row.watched,
      watchedAt: row.watched_at,
      rewatch: row.rewatch ?? 0,
      addedAt: row.added_at,
      localNote: row.local_note,
      rating: row.rating,
      mediaItemId: row.media_item_id
    };
  }
}
