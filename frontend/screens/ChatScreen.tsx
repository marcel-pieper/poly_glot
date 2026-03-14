import type { NativeStackScreenProps } from "@react-navigation/native-stack";
import { useCallback, useEffect, useRef, useState } from "react";
import {
  ActivityIndicator,
  Alert,
  FlatList,
  Keyboard,
  Platform,
  Pressable,
  StyleSheet,
  Text,
  TextInput,
  View,
} from "react-native";

import { useSafeAreaInsets } from "react-native-safe-area-context";

import { API_BASE_URL, useAuth } from "../contexts/AuthContext";
import type { RootStackParamList } from "../types/navigation";

type Props = NativeStackScreenProps<RootStackParamList, "ChatScreen">;

type Correction = {
  corrected: string;
  notes: string[];
};

type MessageContent =
  | { text: string; correction_status?: "pending" | "complete" | "failed"; correction?: Correction | null }
  | { assistant_response: string };

type ChatMessage = {
  id: number;
  role: "user" | "assistant" | string;
  content: MessageContent;
  created_at: string;
};

export default function ChatScreen({ route }: Props) {
  const insets = useSafeAreaInsets();
  const { threadId } = route.params;
  const { token } = useAuth();

  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [loadingMessages, setLoadingMessages] = useState(true);
  const [inputText, setInputText] = useState("");
  const [sending, setSending] = useState(false);
  const [keyboardHeight, setKeyboardHeight] = useState(0);

  const flatListRef = useRef<FlatList>(null);

  const fetchMessages = useCallback(async () => {
    if (!token) return;
    try {
      const res = await fetch(`${API_BASE_URL}/chat/threads/${threadId}/messages`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!res.ok) throw new Error("Failed to load messages");
      const data = await res.json();
      setMessages(data.messages ?? []);
    } catch (err) {
      Alert.alert("Error", err instanceof Error ? err.message : "Could not load messages");
    }
  }, [token, threadId]);

  useEffect(() => {
    (async () => {
      setLoadingMessages(true);
      await fetchMessages();
      setTimeout(() => {
        flatListRef.current?.scrollToEnd({ animated: true });
      }, 100);
      setLoadingMessages(false);
    })();
  }, [fetchMessages, flatListRef]);

  useEffect(() => {
    const show = Keyboard.addListener(
      Platform.OS === "ios" ? "keyboardWillShow" : "keyboardDidShow",
      (e) => {
        setKeyboardHeight(e.endCoordinates.height);
        setTimeout(() => {
          flatListRef.current?.scrollToEnd({ animated: true });
        }, 100);
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
  }, []);

  const sendMessage = async () => {
    const text = inputText.trim();
    if (!text || sending || !token) return;

    setInputText("");
    setSending(true);

    const optimisticUserMsg: ChatMessage = {
      id: Date.now(),
      role: "user",
      content: { text, correction_status: "pending", correction: null },
      created_at: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, optimisticUserMsg]);

    try {
      const res = await fetch(`${API_BASE_URL}/chat/threads/${threadId}/messages`, {
        method: "POST",
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ text }),
      });
      if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        throw new Error(body?.detail ?? "Failed to send message");
      }
      const data = await res.json();
      setMessages((prev) => {
        const withoutOptimistic = prev.filter((m) => m.id !== optimisticUserMsg.id);
        return [...withoutOptimistic, data.user_message, data.assistant_message];
      });
    } catch (err) {
      setMessages((prev) => prev.filter((m) => m.id !== optimisticUserMsg.id));
      Alert.alert("Error", err instanceof Error ? err.message : "Could not send message");
    } finally {
      setSending(false);
    }
  };

  const renderMessage = ({ item }: { item: ChatMessage }) => {
    const isUser = item.role === "user";
    const content = item.content as Record<string, unknown>;

    if (isUser) {
      const text = (content.text as string) ?? "";
      const correction = content.correction as Correction | null | undefined;
      const rawStatus = content.correction_status as "pending" | "complete" | "failed" | undefined;
      const correctionStatus =
        rawStatus ?? (correction ? "complete" : undefined);
      return (
        <View style={styles.userContainer}>
          <View style={[styles.bubble, styles.userBubble]}>
            <Text style={styles.userText}>{text}</Text>
          </View>
          {correctionStatus === "pending" && (
            <View style={styles.correctionBox}>
              <Text style={styles.correctionLabel}>Correction</Text>
              <Text style={styles.correctionNote}>Generating correction...</Text>
            </View>
          )}
          {correctionStatus === "failed" && (
            <View style={styles.correctionBox}>
              <Text style={styles.correctionLabel}>Correction</Text>
              <Text style={styles.correctionNote}>Could not generate correction.</Text>
            </View>
          )}
          {correctionStatus === "complete" && correction && (
            <View style={styles.correctionBox}>
              <Text style={styles.correctionLabel}>Correction</Text>
              <Text style={styles.correctedText}>{correction.corrected}</Text>
              {correction.notes.map((note, i) => (
                <Text key={i} style={styles.correctionNote}>
                  • {note}
                </Text>
              ))}
            </View>
          )}
          {correctionStatus === "complete" && !correction && (
            <View style={styles.correctionBox}>
              <Text style={styles.correctionLabel}>Correction</Text>
              <Text style={styles.correctionNone}>No correction needed.</Text>
            </View>
          )}
        </View>
      );
    }

    const assistantResponse = (content.assistant_response as string) ?? "";

    return (
      <View style={styles.assistantContainer}>
        <View style={[styles.bubble, styles.assistantBubble]}>
          <Text style={styles.assistantText}>{assistantResponse}</Text>
        </View>
      </View>
    );
  };

  if (loadingMessages) {
    return (
      <View style={styles.centered}>
        <ActivityIndicator size="large" color="#2563eb" />
      </View>
    );
  }

  return (
    <View style={[styles.container, { paddingBottom: keyboardHeight }]}>
      <FlatList
        ref={flatListRef}
        data={messages}
        keyExtractor={(item) => String(item.id)}
        renderItem={renderMessage}
        contentContainerStyle={styles.messageList}
        onContentSizeChange={() => flatListRef.current?.scrollToEnd({ animated: true })}
        ListEmptyComponent={
          <View style={styles.emptyChat}>
            <Text style={styles.emptyChatText}>Send a message to start the conversation.</Text>
          </View>
        }
      />

      <View style={[styles.inputRow, { paddingBottom: Math.max(insets.bottom, 10) }]}>
        <TextInput
          style={styles.textInput}
          value={inputText}
          onChangeText={setInputText}
          placeholder="Type a message…"
          placeholderTextColor="#94a3b8"
          multiline
          returnKeyType="default"
          editable={!sending}
        />
        <Pressable
          style={({ pressed }) => [styles.sendButton, (pressed || sending) && styles.sendButtonPressed]}
          onPress={sendMessage}
          disabled={sending || !inputText.trim()}
        >
          {sending ? (
            <ActivityIndicator color="#ffffff" size="small" />
          ) : (
            <Text style={styles.sendButtonText}>Send</Text>
          )}
        </Pressable>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: "#f8fafc",
  },
  centered: {
    flex: 1,
    justifyContent: "center",
    alignItems: "center",
    backgroundColor: "#f8fafc",
  },
  messageList: {
    padding: 12,
    gap: 10,
    paddingBottom: 4,
  },
  bubble: {
    maxWidth: "80%",
    borderRadius: 14,
    padding: 12,
  },
  userBubble: {
    backgroundColor: "#2563eb",
    alignSelf: "flex-end",
  },
  userContainer: {
    alignSelf: "flex-end",
    maxWidth: "85%",
    gap: 6,
  },
  userText: {
    color: "#ffffff",
    fontSize: 15,
    lineHeight: 21,
  },
  assistantContainer: {
    alignSelf: "flex-start",
    maxWidth: "85%",
    gap: 6,
  },
  assistantBubble: {
    backgroundColor: "#ffffff",
    borderWidth: 1,
    borderColor: "#e2e8f0",
  },
  assistantText: {
    color: "#0f172a",
    fontSize: 15,
    lineHeight: 21,
  },
  correctionBox: {
    backgroundColor: "#fefce8",
    borderWidth: 1,
    borderColor: "#fde68a",
    borderRadius: 10,
    padding: 10,
    gap: 4,
  },
  correctionLabel: {
    fontSize: 11,
    fontWeight: "700",
    color: "#92400e",
    textTransform: "uppercase",
    letterSpacing: 0.5,
    marginBottom: 2,
  },
  correctedText: {
    color: "#1c1917",
    fontSize: 14,
    fontWeight: "600",
  },
  correctionNone: {
    color: "#57534e",
    fontSize: 13,
    fontStyle: "italic",
  },
  correctionNote: {
    color: "#57534e",
    fontSize: 13,
    lineHeight: 18,
  },
  emptyChat: {
    paddingTop: 60,
    alignItems: "center",
  },
  emptyChatText: {
    color: "#94a3b8",
    fontSize: 14,
  },
  inputRow: {

    flexDirection: "row",
    alignItems: "flex-end",
    gap: 8,
    padding: 10,
    borderTopWidth: 1,
    borderTopColor: "#e2e8f0",
    backgroundColor: "#ffffff",
  },
  textInput: {
    flex: 1,
    minHeight: 44,
    maxHeight: 120,
    borderWidth: 1,
    borderColor: "#cbd5e1",
    borderRadius: 10,
    paddingHorizontal: 14,
    paddingVertical: 10,
    fontSize: 15,
    color: "#0f172a",
    backgroundColor: "#f8fafc",
  },
  sendButton: {
    backgroundColor: "#2563eb",
    borderRadius: 10,
    paddingHorizontal: 18,
    height: 44,
    justifyContent: "center",
    alignItems: "center",
  },
  sendButtonPressed: {
    opacity: 0.75,
  },
  sendButtonText: {
    color: "#ffffff",
    fontWeight: "700",
    fontSize: 15,
  },
});
