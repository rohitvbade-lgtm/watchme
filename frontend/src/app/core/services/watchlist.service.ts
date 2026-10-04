import { Injectable } from '@angular/core';
import { Observable, from, tap, map, switchMap, of, Subject } from 'rxjs';
import { ApiService } from './api.service';
import { LocalDbService } from './local-db.service';
import { DeviceService } from './device.service';
import { SearchResult } from '../models/search-result.model';
import { WatchlistItem, LocalWatchlistItem } from '../models/watchlist-item.model';

@Injectable({
  providedIn: 'root'
})
export class WatchlistService {
  private watchlistUpdated = new Subject<void>();
  public watchlistUpdated$ = this.watchlistUpdated.asObservable();

  constructor(
    private apiService: ApiService,
    private localDb: LocalDbService,
    private deviceService: DeviceService
  ) {}

  addToWatchlist(result: SearchResult): Observable<WatchlistItem> {
    const deviceId = this.deviceService.getDeviceId();
    return this.apiService.addToWatchlist('tmdb', result.providerId, result.mediaType, deviceId).pipe(
      tap(async (item: WatchlistItem) => {
        if (item && (item.id || (item as any).backendId)) {
          const localItem = this.mapToLocal(item);
          if ((!localItem.title || localItem.title === 'Unknown') && result.title) {
            localItem.title = result.title;
          }
          if (!localItem.posterPath && result.posterUrl) {
            localItem.posterPath = result.posterUrl;
          }
          await this.localDb.save(localItem);
          this.watchlistUpdated.next();
        }
      })
    );
  }

  removeFromWatchlist(backendId: string): Observable<void> {
    const deviceId = this.deviceService.getDeviceId();
    return this.apiService.removeFromWatchlist(backendId, deviceId).pipe(
      tap(async () => {
        await this.localDb.remove(backendId);
        this.watchlistUpdated.next();
      })
    );
  }

  markWatched(backendId: string): Observable<void> {
    const deviceId = this.deviceService.getDeviceId();
    return this.apiService.markWatched(backendId, deviceId).pipe(
      switchMap(() => from(this.localDb.update(backendId, { watched: 1, watchedAt: new Date().toISOString() }))),
      tap(() => this.watchlistUpdated.next())
    );
  }

  markUnwatched(backendId: string): Observable<void> {
    const deviceId = this.deviceService.getDeviceId();
    return this.apiService.markUnwatched(backendId, deviceId).pipe(
      switchMap(() => from(this.localDb.update(backendId, { watched: 0, watchedAt: undefined, rewatch: 0 }))),
      tap(() => this.watchlistUpdated.next())
    );
  }

  markForRewatch(backendId: string): Observable<void> {
    const deviceId = this.deviceService.getDeviceId();
    return this.apiService.markForRewatch(backendId, deviceId).pipe(
      switchMap(() => from(this.localDb.update(backendId, { watched: 1, rewatch: 1 }))),
      tap(() => this.watchlistUpdated.next())
    );
  }

  unmarkRewatch(backendId: string): Observable<void> {
    const deviceId = this.deviceService.getDeviceId();
    return this.apiService.unmarkRewatch(backendId, deviceId).pipe(
      switchMap(() => from(this.localDb.update(backendId, { rewatch: 0 }))),
      tap(() => this.watchlistUpdated.next())
    );
  }

  async saveNote(backendId: string, note: string): Promise<void> {
    await this.localDb.updateNote(backendId, note);
  }

  syncFromBackend(allItems: boolean = true): Observable<LocalWatchlistItem[]> {
    const deviceId = this.deviceService.getDeviceId();
    return this.apiService.getWatchlist(deviceId, 1, 10, allItems).pipe(
      switchMap(async (response) => {
        try {
          const items = response?.items || [];
          const localItems = await this.localDb.getAll();
          
          for (const item of items) {
            const itemId = item.id || (item as any).backendId;
            const localMatch = localItems.find(l => l.backendId === itemId);
            const newLocalItem = this.mapToLocal(item, localMatch);
            await this.localDb.save(newLocalItem);
          }
          
          if (allItems && items.length > 0) {
            // Remove items deleted on backend
            const backendIds = items.map(i => i.id || (i as any).backendId);
            for (const local of localItems) {
              if (local.backendId && !backendIds.includes(local.backendId)) {
                await this.localDb.remove(local.backendId);
              }
            }
          }
          this.watchlistUpdated.next();
          return await this.localDb.getAll();
        } catch (err) {
          console.error('[WatchlistService] Error in syncFromBackend:', err);
          return await this.localDb.getAll();
        }
      })
    );
  }

  public mapToLocal(item: any, existingLocal?: LocalWatchlistItem): LocalWatchlistItem {
    const mi = item.mediaItem || item.media_item || item;
    const providerId = mi.providerId || mi.provider_id || item.providerId || item.provider_id || '';
    const mediaType = mi.mediaType || mi.media_type || item.mediaType || item.media_type || 'movie';
    const provider = mi.provider || item.provider || 'tmdb';
    const title = mi.title || item.title || 'Unknown';
    const posterPath = mi.posterPath || mi.poster_path || item.posterPath || item.poster_path;
    const backdropPath = mi.backdropPath || mi.backdrop_path || item.backdropPath || item.backdrop_path;
    const overview = mi.overview || item.overview || '';
    const releaseDate = mi.releaseDate || mi.release_date || item.releaseDate || item.release_date;

    let genresStr = '[]';
    if (typeof mi.genres === 'string') {
      genresStr = mi.genres;
    } else if (Array.isArray(mi.genres)) {
      genresStr = JSON.stringify(mi.genres.map((g: any) => typeof g === 'string' ? g : g?.name || ''));
    }

    const watchedVal = (item.watched === true || item.watched === 1 || item.watched === '1') ? 1 : 0;
    const watchedAtVal = item.watchedAt || item.watched_at;
    const rewatchVal = (item.rewatch === true || item.rewatch === 1 || item.rewatch === '1') ? 1 : 0;
    const addedAtVal = item.addedAt || item.added_at || new Date().toISOString();
    const ratingVal = mi.rating ?? item.rating;
    const mediaItemIdVal = mi.id || item.mediaItemId || item.media_item_id || '';

    return {
      id: existingLocal?.id || item.localId || item.id || crypto.randomUUID(),
      backendId: item.id || item.backendId,
      providerId,
      mediaType,
      provider,
      title,
      posterPath,
      backdropPath,
      overview,
      releaseDate,
      genres: genresStr,
      watched: watchedVal,
      watchedAt: watchedAtVal,
      rewatch: rewatchVal,
      addedAt: addedAtVal,
      rating: ratingVal,
      mediaItemId: mediaItemIdVal,
      localNote: item.localNote ?? existingLocal?.localNote
    };
  }
}
