# QA Checklist: selection-actions

Run after `expo prebuild --clean` and `expo run:ios` / `expo run:android`.

## iOS

- [ ] Assistant chat bubbles render with the same visual style as before.
- [ ] Long-press inside an assistant bubble shows the OS callout with `Copy`, `Translate`, and other default items.
- [ ] Tapping `Copy` copies exactly the selected substring (no regression).
- [ ] Tapping `Translate` navigates to `TranslationScreen` with `inputText` equal to the selected substring.
- [ ] Selection across line breaks works and emits the correct multiline substring.
- [ ] Selecting punctuation, emoji, and RTL characters preserves the substring exactly.
- [ ] Selection deselects after `Translate` is tapped (menu dismisses cleanly).
- [ ] Empty selection does not show `Translate`.

## Android

- [ ] Assistant chat bubbles render with the same visual style as before.
- [ ] Long-press inside an assistant bubble enters selection `ActionMode` with `Copy`, `Translate`, `Select all`.
- [ ] `Copy` copies exactly the selected substring.
- [ ] `Translate` finishes the action mode and navigates to `TranslationScreen` with `inputText` equal to the selected substring.
- [ ] Selection across line breaks works.
- [ ] Selecting punctuation, emoji, and RTL characters preserves the substring exactly.
- [ ] Rotating the device or scrolling the chat does not break selection.

## Regression

- [ ] Sending a chat message still works.
- [ ] Receiving an assistant response still renders correctly.
- [ ] User messages (blue bubbles) are unchanged in behavior.
- [ ] Correction badge, Explain navigation, and starters are unaffected.
- [ ] `TranslationScreen` receives the `inputText` correctly and translates it.
