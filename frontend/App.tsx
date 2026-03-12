import AsyncStorage from "@react-native-async-storage/async-storage";
import { useEffect, useMemo, useState } from "react";
import {
  ActivityIndicator,
  Button,
  SafeAreaView,
  ScrollView,
  StatusBar,
  StyleSheet,
  Text,
  TextInput,
  View,
} from "react-native";

const TOKEN_KEY = "polyglot_access_token";
const API_BASE_URL =
  process.env.EXPO_PUBLIC_API_BASE_URL ?? "http://localhost:8000/api/v1";

type User = {
  id: number;
  email: string;
  is_verified: boolean;
  created_at: string;
};

async function parseJsonResponse(response: Response) {
  const body = await response.json().catch(() => ({}));
  if (!response.ok) {
    const detail = body?.detail || body?.message || "Request failed";
    throw new Error(typeof detail === "string" ? detail : JSON.stringify(detail));
  }
  return body;
}

export default function App() {
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [token, setToken] = useState<string | null>(null);
  const [user, setUser] = useState<User | null>(null);
  const [email, setEmail] = useState("");
  const [code, setCode] = useState("");
  const [message, setMessage] = useState("");
  const [devCode, setDevCode] = useState<string | null>(null);
  const [aiPrompt, setAiPrompt] = useState("Give me one simple French greeting.");
  const [aiAnswer, setAiAnswer] = useState("");

  const normalizedEmail = useMemo(() => email.trim().toLowerCase(), [email]);

  useEffect(() => {
    (async () => {
      const storedToken = await AsyncStorage.getItem(TOKEN_KEY);
      if (!storedToken) {
        setLoading(false);
        return;
      }
      setToken(storedToken);
      await fetchMe(storedToken);
      setLoading(false);
    })();
  }, []);

  const fetchMe = async (accessToken: string) => {
    try {
      const response = await fetch(`${API_BASE_URL}/me`, {
        headers: { Authorization: `Bearer ${accessToken}` },
      });
      const data = await parseJsonResponse(response);
      setUser(data);
    } catch (error) {
      await AsyncStorage.removeItem(TOKEN_KEY);
      setToken(null);
      setUser(null);
      setMessage(error instanceof Error ? error.message : "Could not load current user");
    }
  };

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
      await AsyncStorage.setItem(TOKEN_KEY, accessToken);
      setToken(accessToken);
      await fetchMe(accessToken);
      setCode("");
      setMessage("Login successful.");
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Failed to verify code");
    } finally {
      setBusy(false);
    }
  };

  const callDummyAi = async () => {
    setBusy(true);
    setAiAnswer("");
    try {
      const response = await fetch(`${API_BASE_URL}/ai/dummy`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ prompt: aiPrompt }),
      });
      const data = await parseJsonResponse(response);
      setAiAnswer(data.answer ?? "No answer");
    } catch (error) {
      setAiAnswer(error instanceof Error ? error.message : "AI request failed");
    } finally {
      setBusy(false);
    }
  };

  const logout = async () => {
    await AsyncStorage.removeItem(TOKEN_KEY);
    setToken(null);
    setUser(null);
    setMessage("Logged out.");
  };

  if (loading) {
    return (
      <SafeAreaView style={styles.centered}>
        <ActivityIndicator size="large" />
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.safeArea}>
      <StatusBar barStyle="dark-content" />
      <ScrollView contentContainerStyle={styles.container}>
        <Text style={styles.title}>Polyglot</Text>
        <Text style={styles.subtitle}>Simple local starter app</Text>
        <Text style={styles.url}>API: {API_BASE_URL}</Text>

        {!token || !user ? (
          <View style={styles.card}>
            <Text style={styles.sectionTitle}>Passwordless Login</Text>
            <TextInput
              autoCapitalize="none"
              autoCorrect={false}
              keyboardType="email-address"
              placeholder="you@example.com"
              value={email}
              onChangeText={setEmail}
              style={styles.input}
            />
            <Button title="Send verification code" onPress={requestCode} disabled={busy} />
            <TextInput
              placeholder="6-digit code"
              value={code}
              onChangeText={setCode}
              maxLength={6}
              keyboardType="number-pad"
              style={styles.input}
            />
            <Button title="Verify and login" onPress={verifyCode} disabled={busy} />
            {devCode ? <Text style={styles.devCode}>Dev code: {devCode}</Text> : null}
          </View>
        ) : (
          <View style={styles.card}>
            <Text style={styles.sectionTitle}>Logged In</Text>
            <Text>Email: {user.email}</Text>
            <Text>User ID: {user.id}</Text>
            <Text>Verified: {String(user.is_verified)}</Text>
            <View style={styles.spacer} />
            <Button title="Logout" onPress={logout} />
          </View>
        )}

        <View style={styles.card}>
          <Text style={styles.sectionTitle}>OpenAI Dummy Endpoint</Text>
          <TextInput value={aiPrompt} onChangeText={setAiPrompt} style={styles.input} multiline />
          <Button title="Ask backend AI endpoint" onPress={callDummyAi} disabled={busy} />
          {aiAnswer ? <Text style={styles.aiAnswer}>{aiAnswer}</Text> : null}
        </View>

        {message ? <Text style={styles.message}>{message}</Text> : null}
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safeArea: {
    flex: 1,
    backgroundColor: "#f3f4f6",
  },
  centered: {
    flex: 1,
    justifyContent: "center",
    alignItems: "center",
  },
  container: {
    padding: 20,
    gap: 14,
  },
  title: {
    fontSize: 30,
    fontWeight: "700",
  },
  subtitle: {
    color: "#4b5563",
  },
  url: {
    fontSize: 12,
    color: "#6b7280",
  },
  card: {
    backgroundColor: "#ffffff",
    borderRadius: 12,
    padding: 14,
    gap: 10,
  },
  sectionTitle: {
    fontWeight: "700",
    fontSize: 16,
  },
  input: {
    borderWidth: 1,
    borderColor: "#d1d5db",
    borderRadius: 8,
    paddingHorizontal: 10,
    paddingVertical: 10,
    backgroundColor: "#fff",
  },
  devCode: {
    color: "#1d4ed8",
    fontWeight: "600",
  },
  aiAnswer: {
    color: "#111827",
  },
  message: {
    color: "#111827",
    fontWeight: "500",
  },
  spacer: {
    height: 8,
  },
});
