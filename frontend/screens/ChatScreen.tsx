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

export type ConversationStarterItem = {
  id: string;
  display_text: string;
};

type ChatMessage = {
  id: number;
  thread_id?: number;
  role: "user" | "assistant" | string;
  content: MessageContent;
  created_at: string;
  metadata?: Record<string, unknown> | null;
};

export default function ChatScreen({ route, navigation }: Props) {
  const [currentThreadId, setCurrentThreadId] = useState<number | undefined>(route.params.threadId);
  const { token } = useAuth();

  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [loadingMessages, setLoadingMessages] = useState(true);
  const [starters, setStarters] = useState<ConversationStarterItem[]>([]);
  const [inputText, setInputText] = useState("");
  const [sending, setSending] = useState(false);
  const [expandedCorrections, setExpandedCorrections] = useState<Record<number, boolean>>({});

  const flatListRef = useRef<FlatList>(null);
  const optimisticIdRef = useRef<number | null>(null);

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

  useEffect(() => {
    if (!token || currentThreadId) {
      setStarters([]);
      return;
    }
    (async () => {
      try {
        const res = await fetch(`${API_BASE_URL}/chat/conversation-starters`, {
          headers: { Authorization: `Bearer ${token}` },
        });
        if (!res.ok) return;
        const data = await res.json();
        setStarters(Array.isArray(data.starters) ? data.starters : []);
      } catch {
        /* non-fatal: typed send still works */
      }
    })();
  }, [token, currentThreadId]);

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

  const applySendResponse = useCallback(
    (data: { thread_id?: number | null; user_message: ChatMessage; assistant_message: ChatMessage }) => {
      setCurrentThreadId((tid) => {
        if (!tid && typeof data.thread_id === "number") {
          navigation.setParams({
            threadId: data.thread_id,
            title: `Chat ${data.thread_id}`,
          });
          return data.thread_id;
        }
        return tid;
      });

      const optId = optimisticIdRef.current;
      optimisticIdRef.current = null;
      setMessages((prev) => {
        const withoutOptimistic =
          typeof optId === "number" ? prev.filter((m) => m.id !== optId) : prev;
        return [...withoutOptimistic, data.user_message, data.assistant_message];
      });
    },
    [navigation],
  );

  const postChatTurn = useCallback(
    async (body: Record<string, unknown>): Promise<boolean> => {
      if (!token || sending) return false;
      setSending(true);
      try {
        const res = await fetch(`${API_BASE_URL}/chat/messages`, {
          method: "POST",
          headers: {
            Authorization: `Bearer ${token}`,
            "Content-Type": "application/json",
          },
          body: JSON.stringify(body),
        });
        const parsed = await res.json().catch(() => ({}));
        if (!res.ok) {
          const detail = parsed?.detail;
          let msgText = "Failed to send message";
          if (typeof detail === "string") msgText = detail;
          else if (Array.isArray(detail) && detail.length > 0) {
            const first = detail[0] as { msg?: unknown };
            if (typeof first?.msg === "string") msgText = first.msg;
          }
          throw new Error(msgText);
        }
        applySendResponse(parsed);
        return true;
      } catch (err) {
        const rm = optimisticIdRef.current;
        if (typeof rm === "number") {
          optimisticIdRef.current = null;
          setMessages((prev) => prev.filter((m) => m.id !== rm));
        }
        Alert.alert("Error", err instanceof Error ? err.message : "Could not send message");
        return false;
      } finally {
        setSending(false);
      }
    },
    [token, sending, applySendResponse],
  );

  const sendMessage = async () => {
    const text = inputText.trim();
    if (!text || sending || !token) return;

    setInputText("");

    const tempId = Date.now();
    optimisticIdRef.current = tempId;
    const optimisticUserMsg: ChatMessage = {
      id: tempId,
      role: "user",
      content: { text, correction_status: "pending", correction: null },
      created_at: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, optimisticUserMsg]);

    await postChatTurn({ text, thread_id: currentThreadId });
  };

  const sendStarter = async (starterId: string) => {
    if (sending || !token || typeof currentThreadId === "number") return;
    optimisticIdRef.current = null;
    await postChatTurn({ starter_id: starterId });
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

  const showStarterChips =
    starters.length > 0 && !currentThreadId && messages.length === 0 && !loadingMessages && token;

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
      <View style={styles.messagesColumn}>
        {showStarterChips ? (
          <View style={styles.starterSection}>
            <Text style={styles.starterIntro}>Start with a preset or type below.</Text>
            <View style={styles.starterChipsWrap}>
              {starters.map((s) => (
                <Pressable
                  key={s.id}
                  style={({ pressed }) => [
                    styles.starterChip,
                    (pressed || sending) && styles.starterChipPressed,
                    sending && styles.starterChipDisabled,
                  ]}
                  onPress={() => void sendStarter(s.id)}
                  disabled={sending}
                >
                  <Text style={styles.starterChipText}>{s.display_text}</Text>
                </Pressable>
              ))}
            </View>
          </View>
        ) : null}
        <FlatList
          ref={flatListRef}
          style={styles.flexList}
          data={messages}
          keyExtractor={(item) => String(item.id)}
          renderItem={renderMessage}
          contentContainerStyle={styles.messageList}
          onContentSizeChange={() => flatListRef.current?.scrollToEnd({ animated: true })}
          ListEmptyComponent={
            showStarterChips ? null : (
              <View style={styles.emptyChat}>
                <Text style={styles.emptyChatText}>Send a message to start the conversation.</Text>
              </View>
            )
          }
        />
      </View>
    </KeyboardAwareLayout>
  );
}

const styles = StyleSheet.create({
  messagesColumn: {
    flex: 1,
    minHeight: 0,
    backgroundColor: "#f8fafc",
  },
  flexList: {
    flex: 1,
  },
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
  starterSection: {
    paddingHorizontal: 12,
    paddingTop: 12,
    paddingBottom: 4,
    borderBottomWidth: 1,
    borderBottomColor: "#e2e8f0",
    backgroundColor: "#ffffff",
  },
  starterIntro: {
    color: "#64748b",
    fontSize: 13,
    marginBottom: 8,
  },
  starterChipsWrap: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: 8,
  },
  starterChip: {
    backgroundColor: "#eff6ff",
    paddingHorizontal: 14,
    paddingVertical: 10,
    borderRadius: 999,
    borderWidth: 1,
    borderColor: "#bfdbfe",
    maxWidth: "100%",
  },
  starterChipPressed: {
    opacity: 0.85,
  },
  starterChipDisabled: {
    opacity: 0.5,
  },
  starterChipText: {
    color: "#1d4ed8",
    fontSize: 14,
    fontWeight: "600",
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
    height: 44,
    paddingHorizontal: 18,
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
