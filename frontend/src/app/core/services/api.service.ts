import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable, catchError, of, tap } from 'rxjs';
import { environment } from '../../../environments/environment';
import { SearchResponse } from '../models/search-result.model';
import { WatchlistItem, WatchlistResponse } from '../models/watchlist-item.model';
import { NotificationEvent } from '../models/notification.model';

@Injectable({
  providedIn: 'root'
})
export class ApiService {
  private baseUrl = `${environment.apiUrl}/api`;

  constructor(private http: HttpClient) {}

  search(query: string, type: string = 'all', page: number = 1, limit: number = 10): Observable<SearchResponse> {
    const params = new HttpParams()
      .set('q', query)
      .set('type', type)
      .set('page', page.toString())
      .set('limit', limit.toString());
    return this.http.get<SearchResponse>(`${this.baseUrl}/search`, { params })
      .pipe(catchError(this.handleError<SearchResponse>('search', { results: [], total: 0, page, totalPages: 1, limit })));
  }

  addToWatchlist(provider: string, providerId: string, mediaType: string, deviceId: string): Observable<WatchlistItem> {
    const params = new HttpParams().set('device_id', deviceId);
    return this.http.post<WatchlistItem>(`${this.baseUrl}/watchlist`, {
      provider,
      providerId,
      mediaType
    }, { params }).pipe(
      tap(item => console.log(`[ApiService] Added to watchlist for ${deviceId}:`, item)),
      catchError(this.handleError<WatchlistItem>('addToWatchlist'))
    );
  }

  getWatchlist(deviceId: string, page: number = 1, limit: number = 10, allItems: boolean = false): Observable<WatchlistResponse> {
    let params = new HttpParams()
      .set('device_id', deviceId)
      .set('page', page.toString())
      .set('limit', limit.toString());
    if (allItems) {
      params = params.set('all_items', 'true');
    }
    return this.http.get<WatchlistResponse>(`${this.baseUrl}/watchlist`, { params })
      .pipe(
        tap(res => console.log(`[ApiService] Received watchlist for device [${deviceId}] -> count: ${res?.items?.length ?? 0}, total: ${res?.total ?? 0}`)),
        catchError(this.handleError<WatchlistResponse>('getWatchlist', { items: [], total: 0, page, totalPages: 1, limit }))
      );
  }

  removeFromWatchlist(id: string, deviceId: string): Observable<void> {
    const params = new HttpParams().set('device_id', deviceId);
    return this.http.delete<void>(`${this.baseUrl}/watchlist/${id}`, { params })
      .pipe(catchError(this.handleError<void>('removeFromWatchlist')));
  }

  markWatched(id: string, deviceId: string): Observable<WatchlistItem> {
    const params = new HttpParams().set('device_id', deviceId);
    return this.http.post<WatchlistItem>(`${this.baseUrl}/watchlist/${id}/watched`, {}, { params })
      .pipe(catchError(this.handleError<WatchlistItem>('markWatched')));
  }

  markUnwatched(id: string, deviceId: string): Observable<WatchlistItem> {
    const params = new HttpParams().set('device_id', deviceId);
    return this.http.post<WatchlistItem>(`${this.baseUrl}/watchlist/${id}/unwatched`, {}, { params })
      .pipe(catchError(this.handleError<WatchlistItem>('markUnwatched')));
  }

  markForRewatch(id: string, deviceId: string): Observable<WatchlistItem> {
    const params = new HttpParams().set('device_id', deviceId);
    return this.http.post<WatchlistItem>(`${this.baseUrl}/watchlist/${id}/rewatch`, {}, { params })
      .pipe(catchError(this.handleError<WatchlistItem>('markForRewatch')));
  }

  unmarkRewatch(id: string, deviceId: string): Observable<WatchlistItem> {
    const params = new HttpParams().set('device_id', deviceId);
    return this.http.post<WatchlistItem>(`${this.baseUrl}/watchlist/${id}/unrewatch`, {}, { params })
      .pipe(catchError(this.handleError<WatchlistItem>('unmarkRewatch')));
  }

  registerDevice(deviceId: string, platform: string, pushToken?: string): Observable<any> {
    return this.http.post(`${this.baseUrl}/devices/register`, {
      deviceId,
      platform,
      pushToken: pushToken || null
    }).pipe(catchError(this.handleError<any>('registerDevice')));
  }

  getNotifications(deviceId: string): Observable<NotificationEvent[]> {
    const params = new HttpParams().set('device_id', deviceId);
    return this.http.get<NotificationEvent[]>(`${this.baseUrl}/notifications`, { params })
      .pipe(catchError(this.handleError<NotificationEvent[]>('getNotifications', [])));
  }

  testNotification(deviceId: string, watchlistItemId?: string): Observable<any> {
    return this.http.post<any>(`${this.baseUrl}/notifications/test`, {
      device_id: deviceId,
      watchlist_item_id: watchlistItemId || null
    }).pipe(catchError(this.handleError<any>('testNotification')));
  }

  private handleError<T>(operation = 'operation', result?: T) {
    return (error: any): Observable<T> => {
      console.error(`[WatchMe] ${operation} failed:`, error.status, error.message);
      return of(result as T);
    };
  }
}
