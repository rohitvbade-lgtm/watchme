import { Component, ChangeDetectorRef, ViewChild } from '@angular/core';
import { Router } from '@angular/router';
import { IonContent } from '@ionic/angular';
import { Subject } from 'rxjs';
import { debounceTime, distinctUntilChanged } from 'rxjs/operators';
import { ApiService } from '../../core/services/api.service';
import { SearchResult } from '../../core/models/search-result.model';
import { ThemeService } from '../../core/services/theme.service';

@Component({
  selector: 'app-search',
  templateUrl: './search.page.html',
  styleUrls: ['./search.page.scss'],
})
export class SearchPage {
  @ViewChild(IonContent) content?: IonContent;

  searchQuery = '';
  mediaTypeFilter = 'all';
  results: SearchResult[] = [];
  loading = false;
  searched = false;

  // Pagination state (max 10 items viewed at once)
  currentPage = 1;
  pageSize = 10;
  totalResults = 0;
  totalPages = 1;

  private searchSubject = new Subject<string>();

  constructor(
    private apiService: ApiService,
    private router: Router,
    public themeService: ThemeService,
    private cdr: ChangeDetectorRef
  ) {
    this.searchSubject.pipe(
      debounceTime(400),
      distinctUntilChanged()
    ).subscribe(query => {
      this.searchQuery = query;
      this.currentPage = 1;
      this.performSearch(query, 1);
    });
  }

  get isDarkMode(): boolean {
    return this.themeService.isDarkMode;
  }

  get placeholderUrl(): string {
    return this.themeService.placeholderUrl;
  }

  toggleTheme(): void {
    this.themeService.toggleTheme();
  }

  onImageError(event: any): void {
    if (event?.target) {
      event.target.src = this.placeholderUrl;
    }
  }

  onSearchChange(event: any) {
    const query = event.detail.value;
    if (query && query.trim().length > 0) {
      this.searchSubject.next(query.trim());
    } else {
      this.results = [];
      this.searched = false;
      this.totalResults = 0;
      this.totalPages = 1;
      this.currentPage = 1;
      this.cdr.markForCheck();
    }
  }

  onFilterChange(type: string) {
    if (this.mediaTypeFilter !== type) {
      this.mediaTypeFilter = type;
      if (this.searchQuery) {
        this.currentPage = 1;
        this.performSearch(this.searchQuery, 1);
      }
    }
  }

  performSearch(query: string, page: number = 1) {
    if (!query) return;
    this.loading = true;
    this.searched = true;
    this.cdr.markForCheck();

    this.apiService.search(query, this.mediaTypeFilter, page, this.pageSize).subscribe({
      next: (res) => {
        this.results = res.results || [];
        this.totalResults = res.total || 0;
        this.currentPage = page;
        this.totalPages = res.totalPages || (this.totalResults > 0 ? Math.ceil(this.totalResults / this.pageSize) : 1);
        this.loading = false;
        if (this.content) {
          this.content.scrollToTop(300);
        }
        this.cdr.markForCheck();
      },
      error: (err) => {
        console.error('[SearchPage] Search error:', err);
        this.results = [];
        this.totalResults = 0;
        this.totalPages = 1;
        this.loading = false;
        this.cdr.markForCheck();
      }
    });
  }

  nextPage() {
    if (this.currentPage < this.totalPages) {
      this.performSearch(this.searchQuery, this.currentPage + 1);
    }
  }

  prevPage() {
    if (this.currentPage > 1) {
      this.performSearch(this.searchQuery, this.currentPage - 1);
    }
  }

  goToDetail(result: SearchResult) {
    this.router.navigate(['/item-detail'], { state: { result } });
  }
}
