import { useEffect, useState } from "react";
import { Keyboard, Platform } from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";

type UseKeyboardAvoidanceOptions = {
  onKeyboardShow?: () => void;
  showDelayMs?: number;
  minFooterPadding?: number;
};

export function useKeyboardAvoidance(options: UseKeyboardAvoidanceOptions = {}) {
  const { onKeyboardShow, showDelayMs = 100, minFooterPadding = 10 } = options;
  const insets = useSafeAreaInsets();
  const [keyboardHeight, setKeyboardHeight] = useState(0);

  useEffect(() => {
    const show = Keyboard.addListener(
      Platform.OS === "ios" ? "keyboardWillShow" : "keyboardDidShow",
      (e) => {
        setKeyboardHeight(e.endCoordinates.height);
        if (onKeyboardShow) {
          setTimeout(onKeyboardShow, showDelayMs);
        }
      },
    );

    const hide = Keyboard.addListener(
      Platform.OS === "ios" ? "keyboardWillHide" : "keyboardDidHide",
      () => {
        setKeyboardHeight(0);
      },
    );

    return () => {
      show.remove();
      hide.remove();
    };
  }, [onKeyboardShow, showDelayMs]);

  return {
    keyboardHeight,
    footerBottomPadding: Math.max(insets.bottom, minFooterPadding),
  };
}
