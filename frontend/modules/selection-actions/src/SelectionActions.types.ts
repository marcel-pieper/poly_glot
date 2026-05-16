import type { StyleProp, TextStyle, ViewStyle } from "react-native";

export type TranslateEvent = {
  text: string;
  fullText: string;
  start: number;
  end: number;
};

export type SelectableTranslateTextProps = {
  text: string;
  fontSize?: number;
  lineHeight?: number;
  color?: string;
  translateLabel?: string;
  style?: StyleProp<ViewStyle | TextStyle>;
  onTranslate?: (event: TranslateEvent) => void;
};
