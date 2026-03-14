import AsyncStorage from "@react-native-async-storage/async-storage";
import { useNavigation } from "@react-navigation/native";
import type { NativeStackNavigationProp } from "@react-navigation/native-stack";
import { useEffect, useState } from "react";
import { Pressable, ScrollView, StyleSheet, Text, View } from "react-native";

import type { RootStackParamList } from "../types/navigation";

const CHAT_LIST_KEY = "polyglot_chat_overview_items";

type ChatOverviewItem = {
  id: string;
  title: string;
  created_at: string;
};

type RootNav = NativeStackNavigationProp<RootStackParamList>;

export default function ChatOverviewScreen() {
  const navigation = useNavigation<RootNav>();
  const [items, setItems] = useState<ChatOverviewItem[]>([]);

  useEffect(() => {
    (async () => {
      const raw = await AsyncStorage.getItem(CHAT_LIST_KEY);
      if (!raw) return;
      try {
        const parsed = JSON.parse(raw) as ChatOverviewItem[];
        setItems(Array.isArray(parsed) ? parsed : []);
      } catch {
        // Keep screen functional if local data is corrupted.
        setItems([]);
      }
    })();
  }, []);

  const persistItems = async (nextItems: ChatOverviewItem[]) => {
    setItems(nextItems);
    await AsyncStorage.setItem(CHAT_LIST_KEY, JSON.stringify(nextItems));
  };

  const startChat = async () => {
    const nextChatNumber = items.length + 1;
    const now = new Date().toISOString();
    const newChat: ChatOverviewItem = {
      id: `${Date.now()}`,
      title: `Chat ${nextChatNumber}`,
      created_at: now,
    };
    const nextItems = [newChat, ...items];
    await persistItems(nextItems);
    navigation.navigate("ChatScreen", { chatId: newChat.id, title: newChat.title });
  };

  const openChat = (item: ChatOverviewItem) => {
    navigation.navigate("ChatScreen", { chatId: item.id, title: item.title });
  };

  return (
    <View style={styles.container}>
      <Pressable style={({ pressed }) => [styles.startButton, pressed && styles.startButtonPressed]} onPress={startChat}>
        <Text style={styles.startButtonText}>Start Chat</Text>
      </Pressable>

      <Text style={styles.sectionTitle}>Previous chats</Text>
      <ScrollView contentContainerStyle={styles.listContent}>
        {items.length === 0 ? (
          <View style={styles.emptyState}>
            <Text style={styles.emptyStateTitle}>No chats yet</Text>
            <Text style={styles.emptyStateSub}>Start your first chat to see it here.</Text>
          </View>
        ) : (
          items.map((item) => (
            <Pressable
              key={item.id}
              onPress={() => openChat(item)}
              style={({ pressed }) => [styles.chatRow, pressed && styles.chatRowPressed]}
            >
              <Text style={styles.chatTitle}>{item.title}</Text>
              <Text style={styles.chatMeta}>{new Date(item.created_at).toLocaleString()}</Text>
            </Pressable>
          ))
        )}
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: "#f8fafc",
    padding: 16,
  },
  startButton: {
    backgroundColor: "#2563eb",
    borderRadius: 10,
    paddingVertical: 14,
    alignItems: "center",
    marginBottom: 16,
  },
  startButtonPressed: {
    opacity: 0.9,
  },
  startButtonText: {
    color: "#ffffff",
    fontWeight: "700",
    fontSize: 16,
  },
  sectionTitle: {
    fontSize: 16,
    fontWeight: "700",
    color: "#0f172a",
    marginBottom: 10,
  },
  listContent: {
    gap: 10,
    paddingBottom: 20,
  },
  emptyState: {
    borderWidth: 1,
    borderColor: "#e2e8f0",
    borderRadius: 10,
    padding: 16,
    backgroundColor: "#ffffff",
  },
  emptyStateTitle: {
    fontSize: 15,
    fontWeight: "700",
    color: "#0f172a",
  },
  emptyStateSub: {
    marginTop: 6,
    color: "#64748b",
    fontSize: 13,
  },
  chatRow: {
    borderWidth: 1,
    borderColor: "#e2e8f0",
    borderRadius: 10,
    padding: 14,
    backgroundColor: "#ffffff",
  },
  chatRowPressed: {
    opacity: 0.9,
  },
  chatTitle: {
    fontSize: 15,
    fontWeight: "700",
    color: "#0f172a",
  },
  chatMeta: {
    marginTop: 4,
    fontSize: 12,
    color: "#64748b",
  },
});
