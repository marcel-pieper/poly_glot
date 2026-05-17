# Polyglot Android

Pure native Android client for the Polyglot backend. Kotlin + Jetpack Compose, Material 3.

## First-time setup

This repo does not commit the Gradle wrapper jar. From this directory:

```bash
gradle wrapper --gradle-version 8.11.1
```

(Requires a local Gradle 8.x install: `sdk install gradle 8.11.1` via SDKMAN, or `brew install gradle`.)

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
