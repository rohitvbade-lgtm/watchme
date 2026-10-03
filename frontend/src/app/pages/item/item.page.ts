import { Component, OnInit, ChangeDetectorRef } from '@angular/core';
import { ActivatedRoute } from '@angular/router';
import { NavController, AlertController, ToastController } from '@ionic/angular';
import { WatchlistService } from '../../core/services/watchlist.service';
import { LocalDbService } from '../../core/services/local-db.service';
import { ApiService } from '../../core/services/api.service';
import { DeviceService } from '../../core/services/device.service';
import { NotificationService } from '../../core/services/notification.service';
import { LocalWatchlistItem } from '../../core/models/watchlist-item.model';

@Component({
  selector: 'app-item',
  templateUrl: './item.page.html',
  styleUrls: ['./item.page.scss'],
})
export class ItemPage implements OnInit {
  backendId!: string;
  item?: LocalWatchlistItem;
  genres: string[] = [];
  sendingNotification = false;

  constructor(
    private route: ActivatedRoute,
    private navCtrl: NavController,
    private watchlistService: WatchlistService,
    private localDb: LocalDbService,
    private apiService: ApiService,
    private deviceService: DeviceService,
    private notificationService: NotificationService,
    private alertCtrl: AlertController,
    private toastCtrl: ToastController,
    private cdr: ChangeDetectorRef
  ) {}

  async ngOnInit() {
    this.backendId = this.route.snapshot.paramMap.get('id')!;
    await this.loadItem();
  }

  async loadItem() {
    this.item = await this.localDb.getByBackendId(this.backendId) || undefined;
    if (this.item && this.item.genres) {
      try {
        this.genres = JSON.parse(this.item.genres);
      } catch(e) {
        this.genres = [];
      }
    }
    this.cdr.markForCheck();
  }

  getPosterUrl(path?: string): string {
    if (!path) return 'assets/placeholder.svg';
    if (path.startsWith('http')) return path;
    return `https://image.tmdb.org/t/p/w300${path}`;
  }

  getBackdropUrl(path?: string): string {
    if (!path) return '';
    if (path.startsWith('http')) return path;
    return `https://image.tmdb.org/t/p/w780${path}`;
  }

  async toggleWatched() {
    if (!this.item) return;
    const currentlyWatched = this.item.watched === 1;
    
    if (currentlyWatched) {
      this.watchlistService.markUnwatched(this.backendId).subscribe(() => this.loadItem());
    } else {
      this.watchlistService.markWatched(this.backendId).subscribe(() => this.loadItem());
    }
  }

  saveNote(event: any) {
    if (!this.item) return;
    const note = event.target.value;
    this.watchlistService.saveNote(this.backendId, note);
  }

  async confirmRemove() {
    const alert = await this.alertCtrl.create({
      header: 'Remove from Watchlist?',
      message: 'Are you sure you want to remove this item?',
      buttons: [
        { text: 'Cancel', role: 'cancel' },
        { 
          text: 'Remove', 
          role: 'destructive',
          handler: () => {
            this.watchlistService.removeFromWatchlist(this.backendId).subscribe(async () => {
              const toast = await this.toastCtrl.create({
                message: 'Item removed',
                duration: 2000
              });
              await toast.present();
              this.navCtrl.navigateRoot('/watchlist');
            });
          }
        }
      ]
    });
    await alert.present();
  }

  async sendTestNotification() {
    if (!this.item || !this.backendId) return;
    this.sendingNotification = true;
    const deviceId = this.deviceService.getDeviceId();
    this.apiService.testNotification(deviceId, this.backendId).subscribe({
      next: async (res) => {
        this.sendingNotification = false;
        this.cdr.markForCheck();
        if (res && res.text) {
          const title = res.itemTitle || this.item?.title || 'WatchMe';
          const imageUrl = res.itemImageUrl || this.getPosterUrl(this.item?.posterPath);
          await this.notificationService.showNotification(title, res.text, imageUrl, this.backendId);
        }
      },
      error: async (err) => {
        this.sendingNotification = false;
        this.cdr.markForCheck();
        const toast = await this.toastCtrl.create({
          message: 'Could not send test notification',
          duration: 2500,
          color: 'danger'
        });
        await toast.present();
      }
    });
  }
}
