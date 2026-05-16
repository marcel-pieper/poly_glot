import { requireNativeViewManager } from "expo-modules-core";
import * as React from "react";

import type { SelectableTranslateTextProps, TranslateEvent } from "./SelectionActions.types";

type NativeProps = Omit<SelectableTranslateTextProps, "onTranslate"> & {
  onTranslate?: (event: { nativeEvent: TranslateEvent }) => void;
};

const NativeView: React.ComponentType<NativeProps> = requireNativeViewManager("SelectionActions");

export default function SelectableTranslateText({ onTranslate, ...props }: SelectableTranslateTextProps) {
  return (
    <NativeView
      {...props}
      onTranslate={onTranslate ? (e) => onTranslate(e.nativeEvent) : undefined}
    />
  );
}
