# selection-actions

Local Expo Module that renders selectable text natively and adds a custom
`Translate` action to the OS text-selection menu. `Copy` remains the standard
OS action.

## Usage

```tsx
import { SelectableTranslateText } from "selection-actions";

<SelectableTranslateText
  text={message}
  fontSize={15}
  color="#0f172a"
  translateLabel="Translate"
  onTranslate={({ text }) => navigation.navigate("TranslationScreen", { inputText: text })}
/>
```

## Workflow

This module requires a custom dev client (Expo Go cannot load native modules).

```bash
cd frontend
npm install
npx expo prebuild --clean
npx expo run:ios     # or
npx expo run:android
```

## Platforms

- iOS 15.1+: `UITextView` with a custom `UIMenuItem` injected via
  `UIMenuController.willShowMenuNotification`.
- Android: `TextView` with `setTextIsSelectable(true)` and a
  `customSelectionActionModeCallback` that adds the `Translate` action to the
  contextual `ActionMode` menu.

The native view emits an `onTranslate` event with the selected substring and
its character range in the full text.
