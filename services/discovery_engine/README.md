1. Scheduler triggers job
2. Scraper fetches search results (with pagination)
3. Extract metadata (title, URL, PDF link)
4. Dedup Layer checks:
   - metadata_id (title/DOI)
5. If new:
   → download PDF
6. Compute file hash
7. Check hash cache:
   - if duplicate → discard
8. Store PDF in filesystem
9. Push job payload to Redis queue
10. Repeat until stop condition
<br>
---
<br>

Crawler (rate-limited)
   ↓
Bounded Queue (500–1000)
   ↓
ThreadPool (5 workers)
   ↓
Download PDF
   ↓
Store (filesystem)
   ↓
Create Job Object
   ↓
Push → Redis Queue