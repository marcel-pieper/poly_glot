import { useFocusEffect, useNavigation } from "@react-navigation/native";
import type { NativeStackNavigationProp } from "@react-navigation/native-stack";
import { useCallback, useEffect, useState } from "react";
import {
  ActivityIndicator,
  Alert,
  Pressable,
  RefreshControl,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from "react-native";

import { API_BASE_URL, useAuth } from "../contexts/AuthContext";
import type { RootStackParamList } from "../types/navigation";

type RootNav = NativeStackNavigationProp<RootStackParamList>;

type Thread = {
  id: number;
  title: string | null;
  created_at: string;
  updated_at: string;
};

export default function ChatOverviewScreen() {
  const navigation = useNavigation<RootNav>();
  const { token } = useAuth();
  const [threads, setThreads] = useState<Thread[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const fetchThreads = useCallback(async () => {
    if (!token) return;
    try {
      const res = await fetch(`${API_BASE_URL}/chat/threads`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!res.ok) throw new Error("Failed to load chats");
      const data = await res.json();
      setThreads(data.threads ?? []);
    } catch (err) {
      Alert.alert("Error", err instanceof Error ? err.message : "Could not load chats");
    }
  }, [token]);

  useEffect(() => {
    (async () => {
      setLoading(true);
      await fetchThreads();
      setLoading(false);
    })();
  }, [fetchThreads]);

  useFocusEffect(
    useCallback(() => {
      if (!loading) {
        void fetchThreads();
      }
    }, [fetchThreads, loading]),
  );

  const onRefresh = useCallback(async () => {
    setRefreshing(true);
    await fetchThreads();
    setRefreshing(false);
  }, [fetchThreads]);

  const startChat = () => {
    navigation.navigate("ChatScreen", { title: "New chat" });
  };

  const openChat = (thread: Thread) => {
    navigation.navigate("ChatScreen", {
      threadId: thread.id,
      title: thread.title ?? `Chat ${thread.id}`,
    });
  };

  if (loading) {
    return (
      <View style={styles.centered}>
        <ActivityIndicator size="large" color="#2563eb" />
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <Pressable
        style={({ pressed }) => [styles.startButton, pressed && styles.startButtonPressed]}
        onPress={startChat}
      >
        <Text style={styles.startButtonText}>Start Chat</Text>
      </Pressable>

      <Text style={styles.sectionTitle}>Previous chats</Text>
      <ScrollView
        contentContainerStyle={styles.listContent}
        refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} />}
      >
        {threads.length === 0 ? (
          <View style={styles.emptyState}>
            <Text style={styles.emptyStateTitle}>No chats yet</Text>
            <Text style={styles.emptyStateSub}>Start your first chat to see it here.</Text>
          </View>
        ) : (
          threads.map((thread) => (
            <Pressable
              key={thread.id}
              onPress={() => openChat(thread)}
              style={({ pressed }) => [styles.chatRow, pressed && styles.chatRowPressed]}
            >
              <Text style={styles.chatTitle}>{thread.title ?? `Chat ${thread.id}`}</Text>
              <Text style={styles.chatMeta}>{new Date(thread.updated_at).toLocaleString()}</Text>
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
  centered: {
    flex: 1,
    justifyContent: "center",
    alignItems: "center",
    backgroundColor: "#f8fafc",
  },
  startButton: {
    backgroundColor: "#2563eb",
    borderRadius: 10,
    paddingVertical: 14,
    alignItems: "center",
    marginBottom: 16,
  },
  startButtonPressed: {
    opacity: 0.75,
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
