import { useNavigation } from "@react-navigation/native";
import type { NativeStackNavigationProp } from "@react-navigation/native-stack";
import { useMemo, useState } from "react";
import { Pressable, ScrollView, StyleSheet, Text, TextInput, View } from "react-native";

import type { RootStackParamList } from "../types/navigation";

type RootNav = NativeStackNavigationProp<RootStackParamList>;

type HistoryItem = {
  id: string;
  text: string;
};

export default function TranslateOverviewScreen() {
  const navigation = useNavigation<RootNav>();
  const [inputText, setInputText] = useState("");
  const [history, setHistory] = useState<HistoryItem[]>([]);

  const trimmedInput = useMemo(() => inputText.trim(), [inputText]);
  const canTranslate = trimmedInput.length > 0;

  const submitTranslation = () => {
    if (!canTranslate) return;

    const nextInput = trimmedInput;
    setHistory((prev) => [{ id: `${Date.now()}-${prev.length}`, text: nextInput }, ...prev]);
    setInputText("");
    navigation.navigate("TranslationScreen", { inputText: nextInput });
  };

  return (
    <View style={styles.container}>
      <Text style={styles.sectionTitle}>Translate</Text>
      <TextInput
        value={inputText}
        onChangeText={setInputText}
        style={styles.input}
        placeholder="Type text to translate..."
        placeholderTextColor="#94a3b8"
        multiline
      />
      <Pressable
        onPress={submitTranslation}
        disabled={!canTranslate}
        style={({ pressed }) => [
          styles.translateButton,
          !canTranslate && styles.translateButtonDisabled,
          pressed && canTranslate && styles.translateButtonPressed,
        ]}
      >
        <Text style={styles.translateButtonText}>Translate</Text>
      </Pressable>

      <Text style={styles.sectionTitle}>Previous translations</Text>
      <ScrollView contentContainerStyle={styles.listContent}>
        {history.length === 0 ? (
          <View style={styles.emptyState}>
            <Text style={styles.emptyStateTitle}>No translations yet</Text>
            <Text style={styles.emptyStateSub}>
              Your previous translation requests will appear here.
            </Text>
          </View>
        ) : (
          history.map((item) => (
            <View key={item.id} style={styles.historyRow}>
              <Text style={styles.historyText}>{item.text}</Text>
            </View>
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
  sectionTitle: {
    fontSize: 16,
    fontWeight: "700",
    color: "#0f172a",
    marginBottom: 10,
  },
  input: {
    minHeight: 96,
    borderWidth: 1,
    borderColor: "#cbd5e1",
    borderRadius: 10,
    paddingHorizontal: 12,
    paddingVertical: 10,
    backgroundColor: "#ffffff",
    color: "#0f172a",
    fontSize: 15,
    textAlignVertical: "top",
    marginBottom: 12,
  },
  translateButton: {
    backgroundColor: "#2563eb",
    borderRadius: 10,
    paddingVertical: 14,
    alignItems: "center",
    marginBottom: 18,
  },
  translateButtonDisabled: {
    backgroundColor: "#93c5fd",
  },
  translateButtonPressed: {
    opacity: 0.8,
  },
  translateButtonText: {
    color: "#ffffff",
    fontWeight: "700",
    fontSize: 16,
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
  historyRow: {
    borderWidth: 1,
    borderColor: "#e2e8f0",
    borderRadius: 10,
    padding: 14,
    backgroundColor: "#ffffff",
  },
  historyText: {
    fontSize: 15,
    color: "#0f172a",
  },
});
