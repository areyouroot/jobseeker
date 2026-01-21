import { Routes } from '@angular/router';
import { Login } from './components/login/login';
import { Dashboard } from './components/dashboard/dashboard';
import { ResumeOptimizer } from './components/resume-optimizer/resume-optimizer';
import { CustomApplier } from './components/custom-applier/custom-applier';
import { JobHunter } from './components/job-hunter/job-hunter';
import { Pricing } from './components/pricing/pricing';

export const routes: Routes = [
  { path: '', redirectTo: '/dashboard', pathMatch: 'full' },
  { path: 'login', component: Login },
  { path: 'dashboard', component: Dashboard },
  { path: 'optimizer', component: ResumeOptimizer },
  { path: 'custom-applier', component: CustomApplier },
  { path: 'job-hunter', component: JobHunter },
  { path: 'pricing', component: Pricing },
];
