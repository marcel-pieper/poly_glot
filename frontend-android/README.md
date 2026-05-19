# Polyglot Android

Pure native Android client for the Polyglot backend. Kotlin + Jetpack Compose, Material 3.

## First-time setup

AGP (`libs.versions.toml`) must match Gradle: use the **Gradle version** pinned in [`gradle-wrapper.properties`](gradle/wrapper/gradle-wrapper.properties).

The repo includes **`gradlew` / `gradlew.bat`** and **`gradle-wrapper.jar`** so Cursor/CI can run builds without generating the wrapper locally.

If you need to regenerate the wrapper (requires a Gradle install on PATH):

```bash
gradle wrapper --gradle-version 8.13
```

Then:

```bash
./gradlew :app:assembleDebug
```

To install on a connected device/emulator:

```bash
./gradlew :app:installDebug
```

## Configuring the API base URL

The base URL is baked into `BuildConfig.API_BASE_URL` at build time. Configure it in `local.properties`:

```
API_BASE_URL_DEBUG=https://your-ngrok-host.ngrok-free.app/api
API_BASE_URL_RELEASE=https://api.polyglot.example.com/api
```

If unset, debug defaults to the ngrok URL from `../frontend/.env`.

## Android Studio

Open `frontend-android/` as a project. Studio will sync Gradle on first open.
