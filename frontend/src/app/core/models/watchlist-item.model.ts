import { MediaItem } from './media-item.model';

export interface WatchlistItem {
  id: string;
  deviceId?: string;
  device_id?: string;
  mediaItem?: MediaItem;
  media_item?: any;
  watched: boolean;
  watchedAt?: string;
  watched_at?: string;
  rewatch?: boolean;
  addedAt?: string;
  added_at?: string;
  localNote?: string;
}

export interface WatchlistResponse {
  items: WatchlistItem[];
  total?: number;
  page?: number;
  totalPages?: number;
  limit?: number;
}

export interface LocalWatchlistItem {
  id: string;
  providerId: string;
  mediaType: string;
  provider: string;
  title: string;
  posterPath?: string;
  backdropPath?: string;
  overview: string;
  releaseDate?: string;
  genres: string; // JSON string
  watched: number; // 0 or 1
  watchedAt?: string;
  rewatch: number; // 0 or 1
  addedAt: string;
  localNote?: string;
  rating?: number;
  mediaItemId: string;
  backendId: string; // UUID from backend
}

