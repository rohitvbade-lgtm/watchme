export interface NotificationEvent {
  id: string;
  deviceId: string;
  watchlistItemId?: string;
  itemTitle?: string;
  itemImageUrl?: string;
  text: string;
  generationMethod: 'ai' | 'template';
  status: 'GENERATED' | 'SENT' | 'FAILED';
  createdAt: string;
  sentAt?: string;
}
