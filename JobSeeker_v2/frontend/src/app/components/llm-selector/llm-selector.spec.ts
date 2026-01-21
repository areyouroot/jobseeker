import { ComponentFixture, TestBed } from '@angular/core/testing';

import { LlmSelector } from './llm-selector';

describe('LlmSelector', () => {
  let component: LlmSelector;
  let fixture: ComponentFixture<LlmSelector>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [LlmSelector]
    })
    .compileComponents();

    fixture = TestBed.createComponent(LlmSelector);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
