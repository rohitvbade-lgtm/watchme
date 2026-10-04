import { Component, OnInit, OnDestroy, ChangeDetectorRef } from '@angular/core';
import { Router } from '@angular/router';
import { WatchlistService } from '../../core/services/watchlist.service';
import { LocalDbService } from '../../core/services/local-db.service';
import { LocalWatchlistItem } from '../../core/models/watchlist-item.model';
import { ApiService } from '../../core/services/api.service';
import { DeviceService } from '../../core/services/device.service';
import { NotificationService } from '../../core/services/notification.service';
import { ThemeService } from '../../core/services/theme.service';
import { Subscription } from 'rxjs';
import { environment } from '../../../environments/environment';

export type WatchCategory = 'all' | 'up-next' | 'watched' | 'watch-again';

@Component({
  selector: 'app-watchlist',
  templateUrl: './watchlist.page.html',
  styleUrls: ['./watchlist.page.scss'],
})
export class WatchlistPage implements OnInit, OnDestroy {
  readonly isProduction = environment.production;

  /** Full, unfiltered list of all items from local DB */
  allItems: LocalWatchlistItem[] = [];
  /** Items after search + category filtering, before pagination */
  filteredItems: LocalWatchlistItem[] = [];
  /** Items shown on the current page */
  items: LocalWatchlistItem[] = [];

  loading = true;
  triggeringNudge = false;

  // Search
  searchQuery = '';

  // Category tabs
  activeCategory: WatchCategory = 'all';
  readonly categories: { key: WatchCategory; label: string; icon: string }[] = [
    { key: 'all',          label: 'All',          icon: 'bi-collection-play' },
    { key: 'up-next',      label: 'Up Next',      icon: 'bi-clock'           },
    { key: 'watched',      label: 'Watched',       icon: 'bi-check-circle'    },
    { key: 'watch-again',  label: 'Watch Again',  icon: 'bi-arrow-repeat'    },
  ];

  // Pagination
  currentPage = 1;
  pageSize = 10;
  totalPages = 1;
  totalItems = 0;

  private sub?: Subscription;

  constructor(
    private router: Router,
    private watchlistService: WatchlistService,
    private localDb: LocalDbService,
    private apiService: ApiService,
    private deviceService: DeviceService,
    private notificationService: NotificationService,
    public themeService: ThemeService,
    private cdr: ChangeDetectorRef
  ) {}

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

  // ─── Notification nudge ─────────────────────────────────────────────────────

  triggerTestNudge() {
    if (this.isProduction) return;
    this.triggeringNudge = true;
    const deviceId = this.deviceService.getDeviceId();
    this.apiService.testNotification(deviceId).subscribe({
      next: async (res) => {
        this.triggeringNudge = false;
        this.cdr.markForCheck();
        if (res && res.text) {
          await this.notificationService.showNotification(
            res.itemTitle,
            res.text,
            res.itemImageUrl,
            res.watchlistItemId
          );
        }
      },
      error: () => {
        this.triggeringNudge = false;
        this.cdr.markForCheck();
      }
    });
  }

  // ─── Lifecycle ───────────────────────────────────────────────────────────────

  ngOnInit() {
    this.loadData();
    this.sub = this.watchlistService.watchlistUpdated$.subscribe(() => {
      this.loadData();
    });
  }

  ngOnDestroy() {
    this.sub?.unsubscribe();
  }

  ionViewWillEnter() {
    this.loadData();
    this.watchlistService.syncFromBackend().subscribe({
      next: () => this.loadData(),
      error: () => this.loadData()
    });
  }

  // ─── Data loading ────────────────────────────────────────────────────────────

  async loadData() {
    try {
      this.allItems = await this.localDb.getAll();
      this.applyFilters();
    } catch (err) {
      console.error('[WatchlistPage] Error loading local watchlist:', err);
    } finally {
      this.loading = false;
      this.cdr.markForCheck();
    }
  }

  // ─── Search & filter ─────────────────────────────────────────────────────────

  onSearchChange(event: any) {
    this.searchQuery = (event?.detail?.value ?? event?.target?.value ?? '').trim();
    this.currentPage = 1;
    this.applyFilters();
  }

  clearSearch() {
    this.searchQuery = '';
    this.currentPage = 1;
    this.applyFilters();
  }

  setCategory(cat: WatchCategory) {
    this.activeCategory = cat;
    this.currentPage = 1;
    this.applyFilters();
  }

  private applyFilters() {
    let source = this.allItems;

    // 1. Category filter
    switch (this.activeCategory) {
      case 'up-next':
        source = source.filter(i => i.watched !== 1);
        break;
      case 'watched':
        // Watched AND not marked for rewatch
        source = source.filter(i => i.watched === 1 && i.rewatch !== 1);
        break;
      case 'watch-again':
        source = source.filter(i => i.rewatch === 1);
        break;
      // 'all' — no category filter
    }

    // 2. Search filter (title, overview, genre)
    const q = this.searchQuery.toLowerCase();
    if (q) {
      source = source.filter(i =>
        i.title?.toLowerCase().includes(q) ||
        i.overview?.toLowerCase().includes(q) ||
        i.genres?.toLowerCase().includes(q)
      );
    }

    this.filteredItems = source;
    this.updatePagination();
  }

  // ─── Pagination ──────────────────────────────────────────────────────────────

  updatePagination() {
    this.totalItems = this.filteredItems.length;
    this.totalPages = this.totalItems > 0 ? Math.ceil(this.totalItems / this.pageSize) : 1;
    if (this.currentPage > this.totalPages) {
      this.currentPage = this.totalPages;
    }
    if (this.currentPage < 1) {
      this.currentPage = 1;
    }
    const startIndex = (this.currentPage - 1) * this.pageSize;
    this.items = this.filteredItems.slice(startIndex, startIndex + this.pageSize);
    this.cdr.markForCheck();
  }

  nextPage() {
    if (this.currentPage < this.totalPages) {
      this.currentPage++;
      this.updatePagination();
    }
  }

  prevPage() {
    if (this.currentPage > 1) {
      this.currentPage--;
      this.updatePagination();
    }
  }

  goToPage(page: number) {
    if (page >= 1 && page <= this.totalPages) {
      this.currentPage = page;
      this.updatePagination();
    }
  }

  // ─── Count helpers for badges ────────────────────────────────────────────────

  countForCategory(cat: WatchCategory): number {
    switch (cat) {
      case 'up-next':      return this.allItems.filter(i => i.watched !== 1).length;
      case 'watched':      return this.allItems.filter(i => i.watched === 1 && i.rewatch !== 1).length;
      case 'watch-again':  return this.allItems.filter(i => i.rewatch === 1).length;
      default:             return this.allItems.length;
    }
  }

  // ─── Actions ─────────────────────────────────────────────────────────────────

  handleRefresh(event: any) {
    this.watchlistService.syncFromBackend().subscribe({
      next: () => {
        this.loadData();
        event.target.complete();
      },
      error: () => {
        this.loadData();
        event.target.complete();
      }
    });
  }

  goToSearch() {
    this.router.navigate(['/search']);
  }

  goToItem(backendId: string) {
    this.router.navigate(['/item', backendId]);
  }

  deleteItem(backendId: string) {
    this.watchlistService.removeFromWatchlist(backendId).subscribe({
      next: () => this.loadData(),
      error: () => this.loadData()
    });
  }
}
