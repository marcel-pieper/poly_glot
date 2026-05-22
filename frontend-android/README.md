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
# Dev build (local/ngrok API) — package com.polyglot.android.debug
./gradlew :app:installDebug

# Personal/production build — package com.polyglot.android
./gradlew :app:installRelease
```

Debug and release can be installed side by side: debug uses `applicationIdSuffix = ".debug"`.

Debug builds use a different launcher icon (orange background, white **PD** foreground) via `app/src/debug/res/` overrides.

## Configuring the API base URL

The base URL is baked into `BuildConfig.API_BASE_URL` at build time. Configure it in `local.properties`:

```
API_BASE_URL_DEBUG=http://10.0.2.2:8001/api
# API_BASE_URL_DEBUG=https://your-ngrok-host.ngrok-free.app/api
API_BASE_URL_RELEASE=https://poly.thedevmind.com/api
```

| Variant | Package | Property |
|---------|---------|----------|
| debug | `com.polyglot.android.debug` | `API_BASE_URL_DEBUG` |
| release | `com.polyglot.android` | `API_BASE_URL_RELEASE` |

If unset, debug defaults to `http://10.0.2.2:8001/api` and release to `https://poly.thedevmind.com/api`.

## Android Studio

Open `frontend-android/` as a project. Studio will sync Gradle on first open.
