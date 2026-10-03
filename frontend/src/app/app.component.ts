import { Component } from '@angular/core';
import { NotificationService } from './core/services/notification.service';
import { Platform } from '@ionic/angular';

@Component({
  selector: 'app-root',
  templateUrl: 'app.component.html',
  styleUrls: ['app.component.scss'],
})
export class AppComponent {
  constructor(
    private notificationService: NotificationService,
    private platform: Platform
  ) {
    this.initializeApp();
  }

  initializeApp() {
    this.platform.ready().then(() => {
      this.notificationService.registerForPushNotifications();
      this.notificationService.setupNotificationListeners();
    });
  }
}
