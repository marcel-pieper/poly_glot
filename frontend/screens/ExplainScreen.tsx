import type { NativeStackScreenProps } from "@react-navigation/native-stack";
import { useCallback, useEffect, useState } from "react";
import {
  ActivityIndicator,
  Alert,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  View,
} from "react-native";

import KeyboardAwareLayout from "../components/KeyboardAwareLayout";
import { API_BASE_URL, useAuth } from "../contexts/AuthContext";
import type { RootStackParamList } from "../types/navigation";

type Props = NativeStackScreenProps<RootStackParamList, "ExplainScreen">;

type MessageContent =
  | { text: string; correction_status?: "pending" | "complete" | "failed"; correction?: unknown }
  | { assistant_response: string };

type ExplainMessage = {
  id: number;
  role: "user" | "assistant" | string;
  content: MessageContent;
  created_at: string;
};

export default function ExplainScreen({ route, navigation }: Props) {
  const { sourceThreadId, sourceMessageId, messageText, correctionStatus, correction } = route.params;
  const { token } = useAuth();
  const [question, setQuestion] = useState("");
  const [messages, setMessages] = useState<ExplainMessage[]>([]);
  const [sending, setSending] = useState(false);
  const [loadingMessages, setLoadingMessages] = useState(false);
  const [explainThreadId, setExplainThreadId] = useState<number | undefined>(route.params.explainThreadId);

  useEffect(() => {
    setExplainThreadId(route.params.explainThreadId);
  }, [route.params.explainThreadId]);

  const fetchMessages = useCallback(async () => {
    if (!token || !explainThreadId) return;
    try {
      const res = await fetch(`${API_BASE_URL}/explain/threads/${explainThreadId}/messages`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!res.ok) throw new Error("Failed to load explain messages");
      const data = await res.json();
      setMessages(data.messages ?? []);
    } catch (err) {
      Alert.alert("Error", err instanceof Error ? err.message : "Could not load explain messages");
    }
  }, [token, explainThreadId]);

  useEffect(() => {
    if (!explainThreadId) return;
    (async () => {
      setLoadingMessages(true);
      await fetchMessages();
      setLoadingMessages(false);
    })();
  }, [fetchMessages, explainThreadId]);

  const askQuestion = async () => {
    const text = question.trim();
    if (!text || sending || !token) return;

    setQuestion("");
    setSending(true);

    const optimisticUserMsg: ExplainMessage = {
      id: Date.now(),
      role: "user",
      content: { text, correction_status: "pending", correction: null },
      created_at: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, optimisticUserMsg]);

    try {
      const body: Record<string, unknown> = { text, thread_id: explainThreadId };
      if (!explainThreadId) {
        body.seed = {
          source_thread_id: sourceThreadId,
          source_message_id: sourceMessageId,
        };
      }
      const res = await fetch(`${API_BASE_URL}/explain/messages`, {
        method: "POST",
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify(body),
      });
      if (!res.ok) {
        const errorBody = await res.json().catch(() => ({}));
        throw new Error(errorBody?.detail ?? "Failed to send explain message");
      }
      const data = await res.json();
      if (!explainThreadId && typeof data.thread_id === "number") {
        setExplainThreadId(data.thread_id);
        navigation.setParams({ explainThreadId: data.thread_id });
      }
      setMessages((prev) => {
        const withoutOptimistic = prev.filter((m) => m.id !== optimisticUserMsg.id);
        return [...withoutOptimistic, data.user_message, data.assistant_message];
      });
    } catch (err) {
      setMessages((prev) => prev.filter((m) => m.id !== optimisticUserMsg.id));
      Alert.alert("Error", err instanceof Error ? err.message : "Could not send explain message");
    } finally {
      setSending(false);
    }
  };

  const renderThreadMessages = () => {
    if (loadingMessages) {
      return (
        <View style={styles.threadLoading}>
          <ActivityIndicator size="small" color="#2563eb" />
        </View>
      );
    }
    if (messages.length === 0) return null;

    return (
      <View style={styles.threadBlock}>
        {messages.map((msg) => {
          const content = msg.content as Record<string, unknown>;
          const text = msg.role === "assistant"
            ? ((content.assistant_response as string) ?? "")
            : ((content.text as string) ?? "");
          const isAssistant = msg.role === "assistant";
          return (
            <View key={msg.id} style={[styles.msgBubble, isAssistant ? styles.assistantBubble : styles.userBubble]}>
              <Text style={isAssistant ? styles.assistantText : styles.userText}>{text}</Text>
            </View>
          );
        })}
      </View>
    );
  };

  return (
    <KeyboardAwareLayout
      containerStyle={styles.container}
      footerStyle={styles.inputPanel}
      footer={
        <>
          <Text style={styles.inputLabel}>Ask about this correction</Text>
          <View style={styles.inputRow}>
            <TextInput
              style={styles.input}
              value={question}
              onChangeText={setQuestion}
              placeholder="Why is this corrected that way?"
              placeholderTextColor="#94a3b8"
              multiline
            />
            <Pressable
              style={({ pressed }) => [styles.askButton, (pressed || sending) && styles.askButtonPressed]}
              onPress={askQuestion}
              disabled={sending || !question.trim()}
            >
              {sending ? <ActivityIndicator size="small" color="#ffffff" /> : <Text style={styles.askButtonText}>Ask</Text>}
            </Pressable>
          </View>
        </>
      }
    >
      <ScrollView contentContainerStyle={styles.content}>
        <View style={styles.topCard}>
          <Text style={styles.sectionLabel}>Original message</Text>
          <Text style={styles.originalText}>{messageText}</Text>

          <Text style={[styles.sectionLabel, styles.correctionLabelSpacing]}>Correction</Text>
          {correctionStatus === "pending" && <Text style={styles.metaText}>Generating correction...</Text>}
          {correctionStatus === "failed" && <Text style={styles.metaText}>Correction was not available.</Text>}
          {correctionStatus === "complete" && correction && (
            <View style={styles.correctionBlock}>
              <Text style={styles.correctedText}>{correction.corrected}</Text>
              {correction.notes.map((note, idx) => (
                <Text key={idx} style={styles.noteText}>
                  • {note}
                </Text>
              ))}
            </View>
          )}
          {correctionStatus === "complete" && !correction && (
            <Text style={styles.metaText}>No correction needed.</Text>
          )}
        </View>
        {renderThreadMessages()}
      </ScrollView>
    </KeyboardAwareLayout>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: "#f8fafc",
  },
  content: {
    padding: 16,
    justifyContent: "flex-start",
  },
  topCard: {
    backgroundColor: "#ffffff",
    borderRadius: 12,
    borderWidth: 1,
    borderColor: "#e2e8f0",
    padding: 14,
  },
  sectionLabel: {
    fontSize: 11,
    fontWeight: "700",
    color: "#64748b",
    textTransform: "uppercase",
    letterSpacing: 0.5,
    marginBottom: 6,
  },
  correctionLabelSpacing: {
    marginTop: 14,
  },
  originalText: {
    fontSize: 16,
    color: "#0f172a",
    lineHeight: 22,
    fontWeight: "600",
  },
  correctionBlock: {
    gap: 4,
  },
  correctedText: {
    fontSize: 16,
    color: "#1c1917",
    fontWeight: "600",
    lineHeight: 22,
  },
  noteText: {
    color: "#57534e",
    fontSize: 14,
    lineHeight: 20,
  },
  metaText: {
    color: "#64748b",
    fontSize: 14,
  },
  inputPanel: {
    borderTopWidth: 1,
    borderTopColor: "#e2e8f0",
    backgroundColor: "#ffffff",
    paddingHorizontal: 12,
    paddingTop: 10,
    paddingBottom: 12,
  },
  inputLabel: {
    color: "#334155",
    fontSize: 13,
    fontWeight: "600",
    marginBottom: 8,
  },
  inputRow: {
    flexDirection: "row",
    alignItems: "flex-end",
    gap: 8,
  },
  input: {
    flex: 1,
    minHeight: 44,
    maxHeight: 120,
    borderWidth: 1,
    borderColor: "#cbd5e1",
    borderRadius: 10,
    paddingHorizontal: 12,
    paddingVertical: 10,
    backgroundColor: "#f8fafc",
    color: "#0f172a",
    fontSize: 15,
  },
  askButton: {
    height: 44,
    backgroundColor: "#2563eb",
    borderRadius: 10,
    justifyContent: "center",
    alignItems: "center",
    paddingHorizontal: 16,
  },
  askButtonPressed: {
    opacity: 0.75,
  },
  askButtonText: {
    color: "#ffffff",
    fontWeight: "700",
    fontSize: 14,
  },
  threadLoading: {
    paddingTop: 12,
    alignItems: "center",
  },
  threadBlock: {
    marginTop: 12,
    gap: 8,
  },
  msgBubble: {
    borderRadius: 12,
    paddingHorizontal: 12,
    paddingVertical: 10,
    maxWidth: "90%",
  },
  assistantBubble: {
    alignSelf: "flex-start",
    borderWidth: 1,
    borderColor: "#e2e8f0",
    backgroundColor: "#ffffff",
  },
  userBubble: {
    alignSelf: "flex-end",
    backgroundColor: "#2563eb",
  },
  assistantText: {
    color: "#0f172a",
    fontSize: 14,
    lineHeight: 20,
  },
  userText: {
    color: "#ffffff",
    fontSize: 14,
    lineHeight: 20,
  },
});
