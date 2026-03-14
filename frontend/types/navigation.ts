import type { NativeStackScreenProps } from "@react-navigation/native-stack";

export type RootStackParamList = {
  Login: undefined;
  MainTabs: undefined;
  ChatScreen: {
    chatId: string;
    title: string;
  };
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
