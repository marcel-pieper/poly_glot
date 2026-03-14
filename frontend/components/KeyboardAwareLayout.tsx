import { ReactNode } from "react";
import { StyleProp, View, ViewStyle } from "react-native";

import { useKeyboardAvoidance } from "../hooks/useKeyboardAvoidance";

type KeyboardAwareLayoutProps = {
  children: ReactNode;
  footer?: ReactNode;
  containerStyle?: StyleProp<ViewStyle>;
  footerStyle?: StyleProp<ViewStyle>;
  onKeyboardShow?: () => void;
  showDelayMs?: number;
  minFooterPadding?: number;
};

export default function KeyboardAwareLayout({
  children,
  footer,
  containerStyle,
  footerStyle,
  onKeyboardShow,
  showDelayMs,
  minFooterPadding,
}: KeyboardAwareLayoutProps) {
  const { keyboardHeight, footerBottomPadding } = useKeyboardAvoidance({
    onKeyboardShow,
    showDelayMs,
    minFooterPadding,
  });

  return (
    <View style={[{ flex: 1, paddingBottom: keyboardHeight }, containerStyle]}>
      {children}
      {footer ? <View style={[footerStyle, { paddingBottom: footerBottomPadding }]}>{footer}</View> : null}
    </View>
  );
}
