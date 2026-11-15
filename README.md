# bhakti-kutir-releases

Public downloads for the **Bhakti Kutir** app (HKM Vadodara).

- **App releases**: every release has the Android APKs and `version.json`,
  which the app's in-app updater reads. Published from the app's private
  repository with its "Publish release to students" workflow.
- **Daily darshan**: `darshan/today.json` lists the photos of the latest
  daily darshan albums of Hare Krishna Mandir, Ahmedabad
  (harekrishnamandir.org gallery), newest first. Kept up to date by the
  "Daily darshan feed" workflow (`.github/workflows/daily-darshan.yml`), which
  runs every half hour in the morning and hourly after that. The photos stay
  on the temple's website; only their links are here.
