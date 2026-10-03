import { Injectable } from '@angular/core';
import { Router } from '@angular/router';
import { PushNotifications } from '@capacitor/push-notifications';
import { Capacitor } from '@capacitor/core';
import { ApiService } from './api.service';
import { DeviceService } from './device.service';
import { ToastController } from '@ionic/angular';

@Injectable({
  providedIn: 'root'
})
export class NotificationService {
  private lastSeenNotificationId: string | null = null;
  private pollingInterval: any = null;

  constructor(
    private router: Router,
    private apiService: ApiService,
    private deviceService: DeviceService,
    private toastCtrl: ToastController
  ) {}

  async registerForPushNotifications(): Promise<void> {
    const deviceId = this.deviceService.getDeviceId();
    const platform = this.deviceService.getPlatform();

    if (platform === 'web') {
      // In web development mode, register device with a simulated token so the backend scheduler targets it
      this.apiService.registerDevice(deviceId, platform, 'simulated_web_token').subscribe({
        next: () => console.log('[NotificationService] Web device registered for notifications:', deviceId),
        error: (err) => console.error('[NotificationService] Failed to register web device:', err)
      });
      return;
    }

    let permStatus = await PushNotifications.checkPermissions();
    if (permStatus.receive === 'prompt') {
      permStatus = await PushNotifications.requestPermissions();
    }

    if (permStatus.receive !== 'granted') {
      console.warn('Push notification permission denied');
      return;
    }

    await PushNotifications.register();

    PushNotifications.addListener('registration', (token) => {
      this.apiService.registerDevice(deviceId, platform, token.value).subscribe();
    });

    PushNotifications.addListener('registrationError', (error: any) => {
      console.error('Error on registration: ' + JSON.stringify(error));
    });
  }

  setupNotificationListeners(): void {
    if (Capacitor.getPlatform() === 'web') {
      this.startWebNotificationPolling();
      return;
    }

    PushNotifications.addListener('pushNotificationReceived', async (notification) => {
      const itemTitle = notification.data?.itemTitle || notification.title || 'WatchMe';
      const imageUrl = notification.data?.imageUrl || (notification as any).image;
      const text = notification.body || '';
      const url = notification.data?.url;
      let watchlistItemId: string | undefined = undefined;
      if (url && url.startsWith('/item/')) {
        watchlistItemId = url.replace('/item/', '');
      }

      await this.showNotification(itemTitle, text, imageUrl, watchlistItemId);
    });

    PushNotifications.addListener('pushNotificationActionPerformed', (notification) => {
      console.log('Push action performed: ' + JSON.stringify(notification));
      const url = notification.notification?.data?.url;
      if (url) {
        this.router.navigateByUrl(url);
      }
    });
  }

  private startWebNotificationPolling(): void {
    if (this.pollingInterval) return;

    const deviceId = this.deviceService.getDeviceId();
    let initialSyncDone = false;

    // Fetch initial list so we record what's already in the DB and don't replay old items
    this.apiService.getNotifications(deviceId).subscribe({
      next: (notifs) => {
        if (notifs && notifs.length > 0) {
          this.lastSeenNotificationId = notifs[0].id;
        }
        initialSyncDone = true;
      },
      error: () => {
        initialSyncDone = true;
      }
    });

    // Poll every 4 seconds for new notifications created by backend scheduler or test endpoint
    this.pollingInterval = setInterval(() => {
      this.apiService.getNotifications(deviceId).subscribe({
        next: async (notifs) => {
          if (!notifs || notifs.length === 0) return;
          const latest = notifs[0];

          if (!initialSyncDone) {
            this.lastSeenNotificationId = latest.id;
            initialSyncDone = true;
            return;
          }

          if (this.lastSeenNotificationId === null || latest.id !== this.lastSeenNotificationId) {
            this.lastSeenNotificationId = latest.id;
            const itemTitle = latest.itemTitle || 'WatchMe';
            const text = latest.text;
            const imageUrl = latest.itemImageUrl;
            const watchlistItemId = latest.watchlistItemId;

            await this.showNotification(itemTitle, text, imageUrl, watchlistItemId);
          }
        },
        error: (err) => console.error('[NotificationService] Polling error:', err)
      });
    }, 4000);
  }

  async showNotification(title: string, text: string, imageUrl?: string, watchlistItemId?: string): Promise<void> {
    const escapedTitle = this.escapeHtml(title || 'WatchMe');
    const escapedText = this.escapeHtml(text || '');

    let messageHtml: string;
    if (imageUrl) {
      messageHtml = `
        <div style="display: flex; align-items: center; gap: 12px; margin-top: 4px;">
          <img src="${imageUrl}" alt="${escapedTitle}" style="width: 44px; height: 66px; object-fit: cover; border-radius: 6px; flex-shrink: 0; box-shadow: 0 2px 6px rgba(0,0,0,0.5);" onerror="this.style.display='none'"/>
          <div style="flex: 1; min-width: 0; font-size: 0.9rem; line-height: 1.35; color: #ffffff;">
            ${escapedText}
          </div>
        </div>
      `;
    } else {
      messageHtml = escapedText;
    }

    const buttons: any[] = [];
    if (watchlistItemId) {
      buttons.push({
        text: 'View',
        handler: () => {
          this.router.navigate(['/item', watchlistItemId]);
        }
      });
    }
    buttons.push({ text: 'Close', role: 'cancel' });

    try {
      const toast = await this.toastCtrl.create({
        header: `🎬 ${title || 'WatchMe'}`,
        message: messageHtml,
        duration: 8000,
        position: 'top',
        color: 'primary',
        buttons
      });
      await toast.present();
    } catch (e) {
      console.warn('[NotificationService] Rich toast failed, displaying standard fallback toast:', e);
      const fallback = await this.toastCtrl.create({
        header: `🎬 ${title || 'WatchMe'}`,
        message: text,
        duration: 6000,
        position: 'top',
        color: 'primary',
        buttons
      });
      await fallback.present();
    }
  }

  private escapeHtml(str: string): string {
    if (!str) return '';
    return str
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#039;');
  }
}
