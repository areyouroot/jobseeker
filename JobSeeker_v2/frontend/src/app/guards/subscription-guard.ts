import { CanActivateFn } from '@angular/router';

export const subscriptionGuard: CanActivateFn = (route, state) => {
  return true;
};
