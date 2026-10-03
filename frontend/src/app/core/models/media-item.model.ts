export interface Genre {
  id: number;
  name: string;
}

export interface MediaItem {
  id: string;
  provider: string;
  providerId: string;
  mediaType: 'movie' | 'tv';
  title: string;
  originalTitle: string;
  overview: string;
  posterPath?: string;
  backdropPath?: string;
  releaseDate?: string;
  firstAirDate?: string;
  runtime?: number;
  genres: Genre[];
  rating?: number;
  voteCount?: number;
  popularity?: number;
  originalLanguage?: string;
  adult: boolean;
  metadata?: Record<string, any>;
}
