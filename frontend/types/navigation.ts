import type { NativeStackScreenProps } from "@react-navigation/native-stack";

export type RootStackParamList = {
  Login: undefined;
  MainTabs: undefined;
};

export type RootStackScreenProps<T extends keyof RootStackParamList> =
  NativeStackScreenProps<RootStackParamList, T>;

export type HomeTabParamList = {
  PracticeTab: undefined;
  VocabTab: undefined;
  ChatTab: undefined;
  TranslateTab: undefined;
  DataTab: undefined;
};
