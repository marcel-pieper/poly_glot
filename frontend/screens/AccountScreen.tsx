import { useEffect, useMemo, useState } from "react";
import { Alert, Button, Pressable, ScrollView, StyleSheet, Text, View } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import { API_BASE_URL, useAuth } from "../contexts/AuthContext";

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

export default function AccountScreen() {
  const { user, token, logout, fetchMe } = useAuth();
  const [languageData, setLanguageData] = useState<LanguagesResponse | null>(null);
  const [saving, setSaving] = useState(false);

  if (!user) return null;

  const nativeLanguageId = languageData?.native_language?.id ?? user.native_language_id ?? null;
  const activeLanguageId = languageData?.active_language?.id ?? null;

  const activeLanguageOptions = useMemo(
    () =>
      (languageData?.all_available_languages ?? []).filter(
        (lang) => lang.learning_enabled && lang.id !== nativeLanguageId
      ),
    [languageData?.all_available_languages, nativeLanguageId]
  );

  const loadLanguages = async () => {
    if (!token) return;
    const response = await fetch(`${API_BASE_URL}/languages`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    const data = (await response.json().catch(() => ({}))) as LanguagesResponse;
    if (!response.ok) {
      const detail = (data as { detail?: unknown })?.detail ?? "Failed to load languages";
      throw new Error(typeof detail === "string" ? detail : JSON.stringify(detail));
    }
    setLanguageData(data);
  };

  useEffect(() => {
    loadLanguages().catch((error) => {
      Alert.alert("Language load failed", error instanceof Error ? error.message : "Unknown error");
    });
    // token refresh should trigger a reload.
  }, [token]);

  const updateMe = async (payload: { native_language?: number | null; active_language?: number | null }) => {
    if (!token) throw new Error("Not authenticated");
    setSaving(true);
    try {
      const response = await fetch(`${API_BASE_URL}/me`, {
        method: "PATCH",
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify(payload),
      });
      const body = await response.json().catch(() => ({}));
      if (!response.ok) {
        const detail = body?.detail || "Failed to update profile";
        throw new Error(typeof detail === "string" ? detail : JSON.stringify(detail));
      }
      await fetchMe(token);
      await loadLanguages();
    } finally {
      setSaving(false);
    }
  };

  const languageLabel = (language: SupportedLanguage | null | undefined) =>
    language ? `${language.name} (${language.code})` : "Not set";

  const deleteAccount = () => {
    Alert.alert(
      "Delete account?",
      "This will permanently delete your account and associated data.",
      [
        { text: "Cancel", style: "cancel" },
        {
          text: "Delete",
          style: "destructive",
          onPress: async () => {
            try {
              if (!token) throw new Error("Not authenticated");
              const response = await fetch(`${API_BASE_URL}/me`, {
                method: "DELETE",
                headers: { Authorization: `Bearer ${token}` },
              });
              if (!response.ok) {
                const body = await response.json().catch(() => ({}));
                const detail = body?.detail || "Failed to delete account";
                throw new Error(typeof detail === "string" ? detail : JSON.stringify(detail));
              }
              await logout();
            } catch (error) {
              Alert.alert("Delete failed", error instanceof Error ? error.message : "Unknown error");
            }
          },
        },
      ]
    );
  };

  return (
    <SafeAreaView style={styles.container}>
      <ScrollView contentContainerStyle={styles.scrollContent}>
        <View style={styles.card}>
          <Text style={styles.label}>Email</Text>
          <Text style={styles.email}>{user.email}</Text>
        </View>

        <View style={styles.card}>
          <Text style={styles.sectionTitle}>Native language</Text>
          <Text style={styles.currentValue}>
            {languageLabel(languageData?.native_language)}
          </Text>
          <View style={styles.optionsWrap}>
            {(languageData?.all_available_languages ?? []).map((lang) => (
              <Pressable
                key={`native-${lang.id}`}
                style={[styles.optionChip, nativeLanguageId === lang.id && styles.optionChipSelected]}
                disabled={saving}
                onPress={() => updateMe({ native_language: lang.id })}
              >
                <Text
                  style={[
                    styles.optionChipText,
                    nativeLanguageId === lang.id && styles.optionChipTextSelected,
                  ]}
                >
                  {lang.code.toUpperCase()}
                </Text>
              </Pressable>
            ))}
          </View>
        </View>

        <View style={styles.card}>
          <Text style={styles.sectionTitle}>Active language</Text>
          <Text style={styles.currentValue}>
            {languageLabel(languageData?.active_language)}
          </Text>
          <Text style={styles.helperText}>
            Native language is excluded from these options on purpose.
          </Text>
          <View style={styles.optionsWrap}>
            {activeLanguageOptions.map((lang) => (
              <Pressable
                key={`active-${lang.id}`}
                style={[styles.optionChip, activeLanguageId === lang.id && styles.optionChipSelected]}
                disabled={saving}
                onPress={() => updateMe({ active_language: lang.id })}
              >
                <Text
                  style={[
                    styles.optionChipText,
                    activeLanguageId === lang.id && styles.optionChipTextSelected,
                  ]}
                >
                  {lang.code.toUpperCase()}
                </Text>
              </Pressable>
            ))}
          </View>
        </View>

        <View style={styles.card}>
          <Button title="Log out" onPress={logout} />
          <View style={styles.spacerSmall} />
          <Button title="Delete account" color="#dc2626" onPress={deleteAccount} />
        </View>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: "#f3f4f6" },
  scrollContent: { padding: 20, gap: 14 },
  card: {
    backgroundColor: "#ffffff",
    borderRadius: 12,
    padding: 20,
  },
  sectionTitle: { fontSize: 16, fontWeight: "700", color: "#111827", marginBottom: 8 },
  currentValue: { fontSize: 15, color: "#111827", marginBottom: 8 },
  helperText: { fontSize: 13, color: "#6b7280", marginBottom: 10 },
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
  optionChipText: { color: "#0f172a", fontWeight: "600", fontSize: 12 },
  optionChipTextSelected: { color: "#1e3a8a" },
  label: { fontSize: 14, color: "#6b7280", marginBottom: 4 },
  email: { fontSize: 18, fontWeight: "600", color: "#111827" },
  spacerSmall: { height: 12 },
});
