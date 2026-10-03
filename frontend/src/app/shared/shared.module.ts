import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { IonicModule } from '@ionic/angular';
import { MediaCardComponent } from './components/media-card/media-card.component';

@NgModule({
  declarations: [MediaCardComponent],
  imports: [CommonModule, IonicModule],
  exports: [MediaCardComponent]
})
export class SharedModule {}
