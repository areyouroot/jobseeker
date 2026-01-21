import { ComponentFixture, TestBed } from '@angular/core/testing';

import { ResumeOptimizer } from './resume-optimizer';

describe('ResumeOptimizer', () => {
  let component: ResumeOptimizer;
  let fixture: ComponentFixture<ResumeOptimizer>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [ResumeOptimizer]
    })
    .compileComponents();

    fixture = TestBed.createComponent(ResumeOptimizer);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
