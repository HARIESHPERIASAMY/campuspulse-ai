# CampusPulse AI 360 - 3-5 Minute Hackathon Demonstration Script

This walkthrough provides a step-by-step demonstration flow for judges and evaluation panels.

---

## ⏱️ Step-by-Step Demo Script (3-5 Minutes)

### Step 1: Admin Authentication & Security Verification (0:00 - 0:45)
1. Open `http://127.0.0.1:5000`
2. Sign in as Admin:
   - Email: `admin@campuspulse.demo`
   - Password: `Admin@123`
3. Notice secondary security prompt: **Admin Security Authorization**.
4. Enter Admin Verification Key: `CP_ADMIN_2026_SECURE`
5. Click **Verify Key & Unlock Admin Workspace**.

---

### Step 2: AI Notice Creation & Intelligence Studio (0:45 - 2:00)
1. Click **AI Notice Studio** in the sidebar (or **Create AI Notice**).
2. Enter the following notice details:
   - **Title**: `Final Year Placement Registration with TechCorp`
   - **Content**: `Final year CSE students must register for the upcoming campus placement drive with TechCorp before tomorrow 5 PM. Mandatory registration fee receipt must be attached.`
   - **Category**: `Placement`
   - **Department**: `CSE`
   - **Year**: `FINAL YEAR`
   - **Check**: `Mandatory Student Acknowledgement Required`
3. Click **AI ANALYZE NOTICE**.
4. Show the **AI Notice Intelligence Panel**:
   - Automated Executive Summary
   - Extracted Key Points
   - Content Quality Score (e.g. 95/100)
   - Suggested Priority (`HIGH`/`URGENT`)
   - Detected Deadline
5. Click **APPLY AI SUGGESTIONS**, then click **PUBLISH NOTICE**.

---

### Step 3: Student Experience & Personalized Feed (2:00 - 3:00)
1. Logout from Admin account and log in as Student:
   - Email: `student@campuspulse.demo`
   - Password: `Student@123`
2. Show **Personalized Feed**:
   - Notice appears under **URGENT** & **IMPORTANT FOR YOU**.
   - Notice shows `UNREAD` / `NEW` badges.
3. Click on the notice to open **Notice Details**.
4. Point out:
   - Verified read timestamp and view count.
   - Click **Bookmark**.
   - Click **ACKNOWLEDGE NOTICE** -> State changes to **✓ ACKNOWLEDGED**.
5. Show **Mobile QR Verification** box on the sidebar.

---

### Step 4: Public Mobile QR Verification (3:00 - 3:30)
1. Open public mobile URL: `http://127.0.0.1:5000/notice/public/1`
2. Show mobile-first public layout displaying notice authentication, AI summary, category, and deadline.

---

### Step 5: Admin Communication Funnel & AI Assistant (3:30 - 4:30)
1. Logout and sign back in as Admin (`admin@campuspulse.demo`).
2. Go to **Dashboard**:
   - Show updated **Communication Funnel** (Targeted → Viewed → Read → Acknowledged).
3. Open **Notice Analytics** & **Viewer Roster**:
   - Show individual student status (ACKNOWLEDGED vs PENDING).
4. Go to **AI Assistant**:
   - Click query: *"Which notices need attention?"* or *"Who has not acknowledged the placement notice?"*
   - Demonstrate that response is calculated directly from actual SQLite database data.
