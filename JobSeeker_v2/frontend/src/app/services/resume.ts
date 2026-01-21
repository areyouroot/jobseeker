import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

@Injectable({
  providedIn: 'root'
})
export class ResumeService {
  private apiUrl = 'http://localhost:3000/api/resume'; // Gateway URL

  constructor(private http: HttpClient) { }

  uploadResume(file: File): Observable<any> {
    const formData = new FormData();
    formData.append('file', file);
    return this.http.post(`${this.apiUrl}/upload`, formData);
  }

  optimizeResume(resumeId: string, instructions: string, model: string): Observable<any> {
    return this.http.post(`${this.apiUrl}/optimize`, { resumeId, instructions, model });
  }

  getResume(id: string): Observable<any> {
    return this.http.get(`${this.apiUrl}/${id}`);
  }
}
