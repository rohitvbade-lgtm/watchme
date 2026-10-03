import { Component, Input } from '@angular/core';

@Component({
  selector: 'app-media-card',
  templateUrl: './media-card.component.html',
  styleUrls: ['./media-card.component.scss']
})
export class MediaCardComponent {
  @Input() title!: string;
  @Input() posterUrl?: string;
  @Input() mediaType!: string;
  @Input() year?: string;
  @Input() overview?: string;
}
