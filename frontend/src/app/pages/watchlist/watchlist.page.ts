import { Component, OnInit, OnDestroy, ChangeDetectorRef } from '@angular/core';
import { Router } from '@angular/router';
import { WatchlistService } from '../../core/services/watchlist.service';
import { LocalDbService } from '../../core/services/local-db.service';
import { LocalWatchlistItem } from '../../core/models/watchlist-item.model';
import { ApiService } from '../../core/services/api.service';
import { DeviceService } from '../../core/services/device.service';
import { NotificationService } from '../../core/services/notification.service';
import { Subscription } from 'rxjs';

@Component({
  selector: 'app-watchlist',
  templateUrl: './watchlist.page.html',
  styleUrls: ['./watchlist.page.scss'],
})
export class WatchlistPage implements OnInit, OnDestroy {
  allItems: LocalWatchlistItem[] = [];
  items: LocalWatchlistItem[] = [];
  loading = true;
  triggeringNudge = false;

  // Pagination state (max 10 items viewed at once)
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
    private cdr: ChangeDetectorRef
  ) {}

  triggerTestNudge() {
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

  async loadData() {
    try {
      this.allItems = await this.localDb.getAll();
      this.updatePagination();
    } catch (err) {
      console.error('[WatchlistPage] Error loading local watchlist:', err);
    } finally {
      this.loading = false;
      this.cdr.markForCheck();
    }
  }

  updatePagination() {
    this.totalItems = this.allItems.length;
    this.totalPages = this.totalItems > 0 ? Math.ceil(this.totalItems / this.pageSize) : 1;
    if (this.currentPage > this.totalPages) {
      this.currentPage = this.totalPages;
    }
    if (this.currentPage < 1) {
      this.currentPage = 1;
    }
    const startIndex = (this.currentPage - 1) * this.pageSize;
    this.items = this.allItems.slice(startIndex, startIndex + this.pageSize);
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
