import { Injectable } from '@angular/core';
import { Capacitor } from '@capacitor/core';

@Injectable({
  providedIn: 'root'
})
export class DeviceService {
  private deviceIdKey = 'watchme_device_id';

  constructor() {}

  getDeviceId(): string {
    let deviceId = localStorage.getItem(this.deviceIdKey);
    if (!deviceId) {
      deviceId = `watchme_${crypto.randomUUID()}`;
      localStorage.setItem(this.deviceIdKey, deviceId);
      console.log('[DeviceService] New deviceId generated:', deviceId);
    }
    return deviceId;
  }

  setDeviceId(newId: string): void {
    if (newId && newId.trim()) {
      localStorage.setItem(this.deviceIdKey, newId.trim());
      console.log('[DeviceService] DeviceId manually updated to:', newId.trim());
    }
  }

  getPlatform(): string {
    const platform = Capacitor.getPlatform();
    if (platform === 'web') return 'web';
    if (platform === 'ios') return 'ios';
    if (platform === 'android') return 'android';
    return 'web';
  }
}
