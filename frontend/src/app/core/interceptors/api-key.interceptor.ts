import { Injectable } from '@angular/core';
import { HttpInterceptor, HttpRequest, HttpHandler, HttpEvent } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../../environments/environment';

@Injectable()
export class ApiKeyInterceptor implements HttpInterceptor {
  intercept(request: HttpRequest<any>, next: HttpHandler): Observable<HttpEvent<any>> {
    const apiKey = (environment as any).apiKey;
    if (apiKey && typeof apiKey === 'string' && apiKey.trim().length > 0) {
      const cloned = request.clone({
        setHeaders: {
          'x-api-key': apiKey.trim()
        }
      });
      return next.handle(cloned);
    }
    return next.handle(request);
  }
}
