import { useEffect, useMemo, useState } from "react";
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

type SupportedLanguage = {
  id: number;
  code: string;
  name: string;
  native_name: string | null;
  learning_enabled: boolean;
};

type LanguagesResponse = {
  native_language: SupportedLanguage | null;
  active_language: SupportedLanguage | null;
  all_available_languages: SupportedLanguage[];
};

type LoginStep = "email" | "code" | "native_language" | "active_language";

export default function LoginScreen() {
  const { login, fetchMe, user } = useAuth();
  const [busy, setBusy] = useState(false);
  const [email, setEmail] = useState("");
  const [code, setCode] = useState("");
  const [message, setMessage] = useState("");
  const [devCode, setDevCode] = useState<string | null>(null);
  const [step, setStep] = useState<LoginStep>("email");
  const [token, setToken] = useState<string | null>(null);
  const [languages, setLanguages] = useState<LanguagesResponse | null>(null);

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
      setStep("code");
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Failed to request code");
    } finally {
      setBusy(false);
    }
  };

  const parseSystemLanguageCode = () => {
    const locale = Intl.DateTimeFormat().resolvedOptions().locale || "en";
    return locale.split("-")[0].toLowerCase();
  };

  const fetchLanguages = async (accessToken: string) => {
    const response = await fetch(`${API_BASE_URL}/languages`, {
      headers: { Authorization: `Bearer ${accessToken}` },
    });
    const data = (await response.json().catch(() => ({}))) as LanguagesResponse;
    if (!response.ok) {
      const detail = (data as { detail?: unknown })?.detail ?? "Failed to load languages";
      throw new Error(typeof detail === "string" ? detail : JSON.stringify(detail));
    }
    setLanguages(data);
    return data;
  };

  const updateMe = async (
    accessToken: string,
    payload: { native_language?: number | null; active_language?: number | null }
  ) => {
    const response = await fetch(`${API_BASE_URL}/me`, {
      method: "PATCH",
      headers: {
        Authorization: `Bearer ${accessToken}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify(payload),
    });
    const body = await response.json().catch(() => ({}));
    if (!response.ok) {
      const detail = body?.detail || "Failed to update profile";
      throw new Error(typeof detail === "string" ? detail : JSON.stringify(detail));
    }
  };

  useEffect(() => {
    if (!token || !languages) return;
    if (step !== "native_language") return;
    if (languages.native_language) return;

    const systemCode = parseSystemLanguageCode();
    const all = languages.all_available_languages;
    const systemLang = all.find((lang) => lang.code.toLowerCase() === systemCode);
    const english = all.find((lang) => lang.code.toLowerCase() === "en");
    const fallback = systemLang ?? english;
    if (!fallback) return;

    updateMe(token, { native_language: fallback.id })
      .then(async () => {
        await fetchMe(token);
        await fetchLanguages(token);
      })
      .catch(() => {
        // Ignore prefill failures and let user choose manually.
      });
  }, [token, languages, step, fetchMe]);

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
      setToken(accessToken);
      const languageData = await fetchLanguages(accessToken);
      if (!languageData.native_language) {
        setStep("native_language");
      } else if (!languageData.active_language) {
        setStep("active_language");
      }
      setCode("");
      setMessage("");
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Failed to verify code");
    } finally {
      setBusy(false);
    }
  };

  const onNativeSelect = async (languageId: number) => {
    if (!token) return;
    setBusy(true);
    try {
      await updateMe(token, { native_language: languageId });
      await fetchMe(token);
      await fetchLanguages(token);
      setStep("active_language");
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Failed to set native language");
    } finally {
      setBusy(false);
    }
  };

  const onActiveSelect = async (languageId: number) => {
    if (!token) return;
    setBusy(true);
    try {
      await updateMe(token, { active_language: languageId });
      await fetchMe(token);
      await fetchLanguages(token);
      setMessage("");
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Failed to set active language");
    } finally {
      setBusy(false);
    }
  };

  const nativeLanguageId = languages?.native_language?.id ?? user?.native_language_id ?? null;
  const activeLanguageId = languages?.active_language?.id ?? user?.active_language_space_id ?? null;

  const nativeOptions = (languages?.all_available_languages ?? []).filter(
    (lang) => lang.id !== (languages?.active_language?.id ?? null)
  );
  const activeOptions = (languages?.all_available_languages ?? []).filter(
    (lang) => lang.learning_enabled && lang.id !== nativeLanguageId
  );

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
            <Text style={styles.subtitle}>Log in and quickly set your language preferences.</Text>
          </View>

          {(step === "email" || step === "code") && (
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
                <Text style={styles.secondaryButtonText}>Verify and continue</Text>
              </Pressable>

              {devCode ? <Text style={styles.devCode}>Dev code: {devCode}</Text> : null}
            </View>
          )}

          {step === "native_language" && (
            <View style={styles.card}>
              <Text style={styles.sectionTitle}>Choose your native language</Text>
              <Text style={styles.subtitleSmall}>
                Used for corrections and explanations. The active language is excluded.
              </Text>
              <View style={styles.optionsWrap}>
                {nativeOptions.map((lang) => (
                  <Pressable
                    key={`native-${lang.id}`}
                    style={[styles.optionChip, nativeLanguageId === lang.id && styles.optionChipSelected]}
                    disabled={busy}
                    onPress={() => onNativeSelect(lang.id)}
                  >
                    <Text
                      style={[
                        styles.optionChipText,
                        nativeLanguageId === lang.id && styles.optionChipTextSelected,
                      ]}
                    >
                      {lang.name}
                    </Text>
                  </Pressable>
                ))}
              </View>
            </View>
          )}

          {step === "active_language" && (
            <View style={styles.card}>
              <Text style={styles.sectionTitle}>Choose active learning language</Text>
              <Text style={styles.subtitleSmall}>
                Pick the language you are currently learning. Native language is excluded.
              </Text>
              <View style={styles.optionsWrap}>
                {activeOptions.map((lang) => (
                  <Pressable
                    key={`active-${lang.id}`}
                    style={[styles.optionChip, activeLanguageId === lang.id && styles.optionChipSelected]}
                    disabled={busy}
                    onPress={() => onActiveSelect(lang.id)}
                  >
                    <Text
                      style={[
                        styles.optionChipText,
                        activeLanguageId === lang.id && styles.optionChipTextSelected,
                      ]}
                    >
                      {lang.name}
                    </Text>
                  </Pressable>
                ))}
              </View>
              <Pressable
                onPress={() => setStep("native_language")}
                style={({ pressed }) => [styles.backButton, pressed && styles.backButtonPressed]}
              >
                <Text style={styles.backButtonText}>Back</Text>
              </Pressable>
            </View>
          )}

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
  subtitleSmall: { color: "#4b5563", marginBottom: 12, fontSize: 14, lineHeight: 20 },
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
  optionsWrap: { flexDirection: "row", flexWrap: "wrap", gap: 8 },
  optionChip: {
    paddingHorizontal: 10,
    paddingVertical: 8,
    borderWidth: 1,
    borderColor: "#cbd5e1",
    borderRadius: 10,
    backgroundColor: "#ffffff",
  },
  optionChipSelected: { borderColor: "#2563eb", backgroundColor: "#dbeafe" },
  optionChipText: { color: "#0f172a", fontWeight: "600", fontSize: 13 },
  optionChipTextSelected: { color: "#1e3a8a" },
  backButton: {
    marginTop: 12,
    alignSelf: "flex-start",
    paddingHorizontal: 12,
    paddingVertical: 8,
  },
  backButtonPressed: { opacity: 0.75 },
  backButtonText: { color: "#1d4ed8", fontWeight: "700" },
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
