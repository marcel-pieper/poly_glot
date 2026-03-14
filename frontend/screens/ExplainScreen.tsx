import type { NativeStackScreenProps } from "@react-navigation/native-stack";
import { useState } from "react";
import {
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  View,
} from "react-native";

import KeyboardAwareLayout from "../components/KeyboardAwareLayout";
import type { RootStackParamList } from "../types/navigation";

type Props = NativeStackScreenProps<RootStackParamList, "ExplainScreen">;

export default function ExplainScreen({ route }: Props) {
  const { messageText, correctionStatus, correction } = route.params;
  const [question, setQuestion] = useState("");

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
            <Pressable style={styles.askButton}>
              <Text style={styles.askButtonText}>Ask</Text>
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
  askButtonText: {
    color: "#ffffff",
    fontWeight: "700",
    fontSize: 14,
  },
});
