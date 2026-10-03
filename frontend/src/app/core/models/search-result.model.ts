export interface SearchResult {
  providerId: string;
  mediaType: 'movie' | 'tv';
  title: string;
  originalTitle: string;
  releaseDate?: string;
  posterUrl?: string;
  overview: string;
  genres: string[];
}

export interface SearchResponse {
  results: SearchResult[];
  total: number;
  page?: number;
  totalPages?: number;
  limit?: number;
}
