import type { NativeStackScreenProps } from "@react-navigation/native-stack";
import { useCallback, useEffect, useRef, useState } from "react";
import {
  ActivityIndicator,
  Alert,
  FlatList,
  Pressable,
  StyleSheet,
  Text,
  TextInput,
  View,
} from "react-native";

import KeyboardAwareLayout from "../components/KeyboardAwareLayout";
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

export default function ChatScreen({ route, navigation }: Props) {
  const [currentThreadId, setCurrentThreadId] = useState<number | undefined>(route.params.threadId);
  const { token } = useAuth();

  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [loadingMessages, setLoadingMessages] = useState(true);
  const [inputText, setInputText] = useState("");
  const [sending, setSending] = useState(false);
  const [expandedCorrections, setExpandedCorrections] = useState<Record<number, boolean>>({});

  const flatListRef = useRef<FlatList>(null);

  const openExplain = (params: RootStackParamList["ExplainScreen"]) => {
    navigation.navigate("ExplainScreen", params);
  };
  const toggleCorrectionExpanded = (messageId: number) => {
    setExpandedCorrections((prev) => ({
      ...prev,
      [messageId]: !prev[messageId],
    }));
  };

  useEffect(() => {
    setCurrentThreadId(route.params.threadId);
  }, [route.params.threadId]);

  const fetchMessages = useCallback(async () => {
    if (!token) return;
    if (!currentThreadId) {
      setMessages([]);
      return;
    }
    try {
      const res = await fetch(`${API_BASE_URL}/chat/threads/${currentThreadId}/messages`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!res.ok) throw new Error("Failed to load messages");
      const data = await res.json();
      setMessages(data.messages ?? []);
    } catch (err) {
      Alert.alert("Error", err instanceof Error ? err.message : "Could not load messages");
    }
  }, [token, currentThreadId]);

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
      const res = await fetch(`${API_BASE_URL}/chat/messages`, {
        method: "POST",
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ text, thread_id: currentThreadId }),
      });
      if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        throw new Error(body?.detail ?? "Failed to send message");
      }
      const data = await res.json();
      if (!currentThreadId && typeof data.thread_id === "number") {
        setCurrentThreadId(data.thread_id);
        navigation.setParams({
          threadId: data.thread_id,
          title: `Chat ${data.thread_id}`,
        });
      }
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
      const isExpanded = !!expandedCorrections[item.id];
      const text = (content.text as string) ?? "";
      const correction = content.correction as Correction | null | undefined;
      const rawStatus = content.correction_status as "pending" | "complete" | "failed" | undefined;
      const correctionStatus = rawStatus ?? (correction ? "complete" : undefined);
      const canOpenExplain = typeof currentThreadId === "number" && correctionStatus === "complete";
      return (
        <View style={styles.userContainer}>
          <View style={[styles.bubble, styles.userBubble]}>
            <Text style={styles.userText}>{text}</Text>
          </View>
          {correctionStatus === "pending" && (
            <View style={styles.noCorrectionRow}>
              <ActivityIndicator size="small" color="#64748b" />
            </View>
          )}
          {correctionStatus === "failed" && (
            <View style={styles.correctionBox}>
              <Text style={styles.correctionNote}>Could not generate correction.</Text>
            </View>
          )}
          {correctionStatus === "complete" && correction && (
            <View style={styles.correctionBox}>
              <Text style={styles.correctedText}>{correction.corrected}</Text>
              {isExpanded &&
                correction.notes.map((note, i) => (
                  <Text key={i} style={styles.correctionNote}>
                    • {note}
                  </Text>
                ))}
              <View style={styles.correctionFooterRow}>
                <Pressable onPress={() => toggleCorrectionExpanded(item.id)} hitSlop={8}>
                  <Text style={styles.chevronToggle}>{isExpanded ? "^" : ">"}</Text>
                </Pressable>
                {isExpanded && canOpenExplain && (
                  <Pressable
                    onPress={() =>
                      openExplain({
                        sourceThreadId: currentThreadId,
                        sourceMessageId: item.id,
                        messageText: text,
                        correctionStatus: "complete",
                        correction,
                      })
                    }
                  >
                    <Text style={styles.explainLink}>{">> Ask"}</Text>
                  </Pressable>
                )}
              </View>
            </View>
          )}
          {correctionStatus === "complete" && !correction && (
            <View style={styles.noCorrectionRow}>
              <Text style={styles.noCorrectionCheck}>✓</Text>
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
    <KeyboardAwareLayout
      containerStyle={styles.container}
      footerStyle={styles.inputRow}
      onKeyboardShow={() => flatListRef.current?.scrollToEnd({ animated: true })}
      footer={
        <>
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
        </>
      }
    >
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
    </KeyboardAwareLayout>
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
  correctionHeaderRow: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    marginBottom: 2,
  },
  explainLink: {
    color: "#2563eb",
    fontSize: 12,
    fontWeight: "600",
    textDecorationLine: "underline",
  },
  correctionFooterRow: {
    marginTop: 4,
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
  },
  chevronToggle: {
    color: "#78716c",
    fontSize: 16,
    fontWeight: "700",
    lineHeight: 16,
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
  noCorrectionRow: {
    alignSelf: "flex-start",
    marginTop: 2,
    marginLeft: 2,
  },
  noCorrectionCheck: {
    color: "#16a34a",
    fontSize: 16,
    fontWeight: "700",
    lineHeight: 16,
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
