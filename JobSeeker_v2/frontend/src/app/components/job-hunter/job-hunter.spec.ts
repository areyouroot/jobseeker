import { ComponentFixture, TestBed } from '@angular/core/testing';

import { JobHunter } from './job-hunter';

describe('JobHunter', () => {
  let component: JobHunter;
  let fixture: ComponentFixture<JobHunter>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [JobHunter]
    })
    .compileComponents();

    fixture = TestBed.createComponent(JobHunter);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
