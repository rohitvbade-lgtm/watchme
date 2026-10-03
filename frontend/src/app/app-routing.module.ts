import { NgModule } from '@angular/core';
import { PreloadAllModules, RouterModule, Routes } from '@angular/router';

const routes: Routes = [
  {
    path: '',
    redirectTo: '/watchlist',
    pathMatch: 'full'
  },
  {
    path: 'watchlist',
    loadChildren: () => import('./pages/watchlist/watchlist.module').then(m => m.WatchlistPageModule)
  },
  {
    path: 'search',
    loadChildren: () => import('./pages/search/search.module').then(m => m.SearchPageModule)
  },
  {
    path: 'item-detail',
    loadChildren: () => import('./pages/item-detail/item-detail.module').then(m => m.ItemDetailPageModule)
  },
  {
    path: 'item/:id',
    loadChildren: () => import('./pages/item/item.module').then(m => m.ItemPageModule)
  }
];

@NgModule({
  imports: [
    RouterModule.forRoot(routes, { preloadingStrategy: PreloadAllModules })
  ],
  exports: [RouterModule]
})
export class AppRoutingModule {}
