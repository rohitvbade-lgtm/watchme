import { Component, OnInit, ChangeDetectorRef } from '@angular/core';
import { Router } from '@angular/router';
import { NavController, ToastController } from '@ionic/angular';
import { SearchResult } from '../../core/models/search-result.model';
import { WatchlistService } from '../../core/services/watchlist.service';
import { LocalDbService } from '../../core/services/local-db.service';

@Component({
  selector: 'app-item-detail',
  templateUrl: './item-detail.page.html',
  styleUrls: ['./item-detail.page.scss'],
})
export class ItemDetailPage implements OnInit {
  result?: SearchResult;
  inWatchlist = false;
  adding = false;

  constructor(
    private router: Router,
    private navCtrl: NavController,
    private watchlistService: WatchlistService,
    private localDb: LocalDbService,
    private toastCtrl: ToastController,
    private cdr: ChangeDetectorRef
  ) {
    const navigation = this.router.getCurrentNavigation();
    if (navigation?.extras.state && navigation.extras.state['result']) {
      this.result = navigation.extras.state['result'];
    }
  }

  async ngOnInit() {
    if (!this.result) {
      this.navCtrl.back();
      return;
    }
    this.inWatchlist = await this.localDb.isInWatchlist(this.result.providerId, this.result.mediaType);
    this.cdr.markForCheck();
  }

  async addToWatchlist() {
    if (!this.result || this.inWatchlist) return;
    
    this.adding = true;
    this.cdr.markForCheck();

    this.watchlistService.addToWatchlist(this.result).subscribe({
      next: async () => {
        this.adding = false;
        this.inWatchlist = true;
        this.cdr.markForCheck();
        const toast = await this.toastCtrl.create({
          message: 'Added to watchlist',
          duration: 2000,
          color: 'success'
        });
        await toast.present();
        this.navCtrl.back();
      },
      error: async () => {
        this.adding = false;
        this.cdr.markForCheck();
        const toast = await this.toastCtrl.create({
          message: 'Failed to add. Try again.',
          duration: 2000,
          color: 'danger'
        });
        await toast.present();
      }
    });
  }
}
