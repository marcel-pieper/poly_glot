import { Button, StyleSheet, Text, View } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import { useAuth } from "../contexts/AuthContext";

export default function AccountScreen() {
  const { user, logout } = useAuth();

  if (!user) return null;

  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.card}>
        <Text style={styles.label}>Email</Text>
        <Text style={styles.email}>{user.email}</Text>
        <View style={styles.spacer} />
        <Button title="Log out" onPress={logout} />
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: "#f3f4f6", padding: 20 },
  card: {
    backgroundColor: "#ffffff",
    borderRadius: 12,
    padding: 20,
  },
  label: { fontSize: 14, color: "#6b7280", marginBottom: 4 },
  email: { fontSize: 18, fontWeight: "600", color: "#111827" },
  spacer: { height: 24 },
});
