import { useMemo, useState } from "react";
import {
  ActivityIndicator,
  KeyboardAvoidingView,
  Platform,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  View,
} from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import { API_BASE_URL, parseJsonResponse, useAuth } from "../contexts/AuthContext";

export default function LoginScreen() {
  const { login } = useAuth();
  const [busy, setBusy] = useState(false);
  const [email, setEmail] = useState("");
  const [code, setCode] = useState("");
  const [message, setMessage] = useState("");
  const [devCode, setDevCode] = useState<string | null>(null);

  const normalizedEmail = useMemo(() => email.trim().toLowerCase(), [email]);

  const requestCode = async () => {
    if (!normalizedEmail) {
      setMessage("Enter your email first.");
      return;
    }
    setBusy(true);
    setMessage("");
    setDevCode(null);
    try {
      const response = await fetch(`${API_BASE_URL}/auth/request-code`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email: normalizedEmail }),
      });
      const data = await parseJsonResponse(response);
      setMessage(data.message ?? "Code sent.");
      setDevCode(data.dev_code ?? null);
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Failed to request code");
    } finally {
      setBusy(false);
    }
  };

  const verifyCode = async () => {
    if (!normalizedEmail || code.trim().length !== 6) {
      setMessage("Enter a valid email and 6-digit code.");
      return;
    }
    setBusy(true);
    setMessage("");
    try {
      const response = await fetch(`${API_BASE_URL}/auth/verify-code`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email: normalizedEmail, code: code.trim() }),
      });
      const data = await parseJsonResponse(response);
      const accessToken = data.access_token as string;
      await login(accessToken);
      setCode("");
      setMessage("Login successful.");
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Failed to verify code");
    } finally {
      setBusy(false);
    }
  };

  const isError = message.toLowerCase().includes("failed") || message.toLowerCase().includes("invalid");

  return (
    <SafeAreaView style={styles.safeArea} edges={["top", "bottom"]}>
      <KeyboardAvoidingView
        style={styles.keyboardWrap}
        behavior={Platform.OS === "ios" ? "padding" : undefined}
      >
        <ScrollView contentContainerStyle={styles.container} keyboardShouldPersistTaps="handled">
          <View style={styles.hero}>
            <View style={styles.badge}>
              <Text style={styles.badgeText}>P</Text>
            </View>
            <Text style={styles.title}>Welcome to Polyglot</Text>
            <Text style={styles.subtitle}>Log in with your email and a one-time verification code.</Text>
          </View>

          <View style={styles.card}>
            <Text style={styles.sectionTitle}>Email verification login</Text>

            <Text style={styles.label}>Email</Text>
            <TextInput
              autoCapitalize="none"
              autoCorrect={false}
              keyboardType="email-address"
              placeholder="you@example.com"
              placeholderTextColor="#9ca3af"
              value={email}
              onChangeText={setEmail}
              style={styles.input}
            />

            <Pressable
              onPress={requestCode}
              disabled={busy}
              style={({ pressed }) => [
                styles.primaryButton,
                (pressed || busy) && styles.primaryButtonPressed,
              ]}
            >
              {busy ? (
                <ActivityIndicator color="#ffffff" />
              ) : (
                <Text style={styles.primaryButtonText}>Send verification code</Text>
              )}
            </Pressable>

            <Text style={styles.label}>Verification code</Text>
            <TextInput
              placeholder="6-digit code"
              placeholderTextColor="#9ca3af"
              value={code}
              onChangeText={setCode}
              maxLength={6}
              keyboardType="number-pad"
              style={styles.input}
            />

            <Pressable
              onPress={verifyCode}
              disabled={busy}
              style={({ pressed }) => [
                styles.secondaryButton,
                (pressed || busy) && styles.secondaryButtonPressed,
              ]}
            >
              <Text style={styles.secondaryButtonText}>Verify and sign in</Text>
            </Pressable>

            {devCode ? <Text style={styles.devCode}>Dev code: {devCode}</Text> : null}
          </View>

          {message ? (
            <View style={[styles.messageBox, isError ? styles.messageBoxError : styles.messageBoxInfo]}>
              <Text style={styles.message}>{message}</Text>
            </View>
          ) : null}
        </ScrollView>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safeArea: { flex: 1, backgroundColor: "#eef2ff" },
  keyboardWrap: { flex: 1 },
  container: { padding: 20, paddingTop: 28, paddingBottom: 36 },
  hero: { marginBottom: 18 },
  badge: {
    width: 44,
    height: 44,
    borderRadius: 22,
    backgroundColor: "#1d4ed8",
    alignItems: "center",
    justifyContent: "center",
    marginBottom: 14,
  },
  badgeText: { color: "#ffffff", fontSize: 20, fontWeight: "700" },
  title: { fontSize: 30, fontWeight: "800", color: "#111827" },
  subtitle: { color: "#4b5563", marginTop: 8, fontSize: 15, lineHeight: 22 },
  card: {
    backgroundColor: "#ffffff",
    borderRadius: 16,
    padding: 16,
    gap: 12,
    borderWidth: 1,
    borderColor: "#e5e7eb",
    shadowColor: "#000000",
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.08,
    shadowRadius: 12,
    elevation: 4,
  },
  sectionTitle: { fontWeight: "700", fontSize: 16, color: "#111827", marginBottom: 2 },
  label: { fontSize: 13, color: "#4b5563", fontWeight: "600" },
  input: {
    borderWidth: 1,
    borderColor: "#cbd5e1",
    borderRadius: 10,
    paddingHorizontal: 12,
    paddingVertical: 11,
    fontSize: 15,
    backgroundColor: "#fff",
  },
  primaryButton: {
    marginTop: 4,
    backgroundColor: "#2563eb",
    borderRadius: 10,
    alignItems: "center",
    justifyContent: "center",
    minHeight: 44,
    paddingHorizontal: 12,
  },
  primaryButtonPressed: { opacity: 0.88 },
  primaryButtonText: { color: "#ffffff", fontSize: 15, fontWeight: "700" },
  secondaryButton: {
    marginTop: 4,
    backgroundColor: "#111827",
    borderRadius: 10,
    alignItems: "center",
    justifyContent: "center",
    minHeight: 44,
    paddingHorizontal: 12,
  },
  secondaryButtonPressed: { opacity: 0.88 },
  secondaryButtonText: { color: "#ffffff", fontSize: 15, fontWeight: "700" },
  devCode: { color: "#1d4ed8", fontWeight: "700", marginTop: 4 },
  messageBox: {
    marginTop: 14,
    borderRadius: 10,
    paddingHorizontal: 12,
    paddingVertical: 10,
  },
  messageBoxInfo: { backgroundColor: "#dbeafe" },
  messageBoxError: { backgroundColor: "#fee2e2" },
  message: { color: "#111827", fontWeight: "600" },
});
