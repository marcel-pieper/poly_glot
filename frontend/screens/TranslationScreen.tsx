import { useEffect, useState } from "react";
import { ActivityIndicator, Pressable, StyleSheet, Text, View } from "react-native";

import { API_BASE_URL, parseJsonResponse, useAuth } from "../contexts/AuthContext";
import type { RootStackScreenProps } from "../types/navigation";

type Props = RootStackScreenProps<"TranslationScreen">;

type TranslateApiResponse = {
  source_text: string;
  translated_text: string;
  status: "complete" | "failed";
};

export default function TranslationScreen({ route }: Props) {
  const { token } = useAuth();
  const { inputText } = route.params;
  const [loading, setLoading] = useState(true);
  const [translation, setTranslation] = useState("");
  const [error, setError] = useState<string | null>(null);

  const loadTranslation = async () => {
    if (!token) {
      setError("Not authenticated");
      setLoading(false);
      return;
    }
    setLoading(true);
    setError(null);
    setTranslation("");
    try {
      const response = await fetch(`${API_BASE_URL}/ai/translate`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ text: inputText }),
      });
      const data = (await parseJsonResponse(response)) as TranslateApiResponse;
      setTranslation(data.translated_text ?? "");
      if (data.status !== "complete" && !data.translated_text) {
        setError("Translation failed");
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not translate");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void loadTranslation();
    // inputText and token define request identity for this screen.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [inputText, token]);

  return (
    <View style={styles.container}>
      <Text style={styles.heading}>Input text</Text>
      <View style={styles.card}>
        <Text style={styles.inputText}>{inputText}</Text>
      </View>

      <Text style={styles.heading}>Translation</Text>
      {loading ? (
        <View style={styles.centeredCard}>
          <ActivityIndicator size="small" color="#2563eb" />
          <Text style={styles.loadingText}>Translating...</Text>
        </View>
      ) : translation ? (
        <View style={styles.card}>
          <Text style={styles.inputText}>{translation}</Text>
          {error ? <Text style={styles.errorInline}>{error}</Text> : null}
        </View>
      ) : (
        <View style={styles.centeredCard}>
          <Text style={styles.errorText}>{error ?? "Could not translate"}</Text>
          <Pressable onPress={() => void loadTranslation()} style={styles.retryButton}>
            <Text style={styles.retryButtonText}>Retry</Text>
          </Pressable>
        </View>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: "#f8fafc",
    padding: 16,
  },
  heading: {
    fontSize: 16,
    fontWeight: "700",
    color: "#0f172a",
    marginBottom: 10,
    marginTop: 16,
  },
  card: {
    borderWidth: 1,
    borderColor: "#e2e8f0",
    borderRadius: 10,
    padding: 14,
    backgroundColor: "#ffffff",
  },
  inputText: {
    fontSize: 16,
    color: "#0f172a",
    lineHeight: 22,
  },
  centeredCard: {
    borderWidth: 1,
    borderColor: "#e2e8f0",
    borderRadius: 10,
    padding: 16,
    backgroundColor: "#ffffff",
    alignItems: "center",
    justifyContent: "center",
    gap: 10,
  },
  loadingText: {
    color: "#475569",
    fontSize: 14,
  },
  errorText: {
    color: "#b91c1c",
    fontSize: 14,
  },
  retryButton: {
    marginTop: 6,
    backgroundColor: "#2563eb",
    borderRadius: 8,
    paddingHorizontal: 14,
    paddingVertical: 8,
  },
  retryButtonText: {
    color: "#ffffff",
    fontWeight: "600",
  },
  errorInline: {
    marginTop: 10,
    color: "#b91c1c",
    fontSize: 13,
  },
});
