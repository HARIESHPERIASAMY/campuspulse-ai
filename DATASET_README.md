# Original Synthetic Dataset - CampusPulse AI 360

## Dataset Overview
To enable robust testing, communication funnel analytics, and AI risk evaluation without compromising real privacy, CampusPulse AI includes an original synthetic dataset generator (`generate_dataset.py`).

The dataset is:
- **Synthetic & Fictional**: Based on Greenfield Institute of Technology.
- **Reproducible**: Fixed random seed (`seed=42`).
- **Internally Consistent**: Engagement records map 1-to-1 to synthetic user accounts and notice categories.

## Files Generated
1. `data/campuspulse_notices.csv` (200+ Records):
   - `notice_id`, `title`, `content`, `category`, `audience`, `department`, `year`, `priority`, `publication_date`, `deadline`, `expiry_date`, `requires_acknowledgement`, `status`.
2. `data/campuspulse_engagement.csv` (1000+ Records):
   - `notice_id`, `user_id`, `viewed`, `viewed_at`, `acknowledged`, `acknowledged_at`, `bookmarked`, `qr_scanned`.

## Generation Command
```bash
python generate_dataset.py
```
