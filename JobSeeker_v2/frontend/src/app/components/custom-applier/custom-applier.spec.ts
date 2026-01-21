import { ComponentFixture, TestBed } from '@angular/core/testing';

import { CustomApplier } from './custom-applier';

describe('CustomApplier', () => {
  let component: CustomApplier;
  let fixture: ComponentFixture<CustomApplier>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [CustomApplier]
    })
    .compileComponents();

    fixture = TestBed.createComponent(CustomApplier);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
