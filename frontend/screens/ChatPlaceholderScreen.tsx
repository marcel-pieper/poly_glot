import { StyleSheet, Text, View } from "react-native";

export default function ChatPlaceholderScreen() {
  return (
    <View style={styles.container}>
      <Text style={styles.text}>Chat</Text>
      <Text style={styles.subtext}>Placeholder — coming soon</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    justifyContent: "center",
    alignItems: "center",
    backgroundColor: "#f3f4f6",
  },
  text: { fontSize: 24, fontWeight: "600", color: "#111827" },
  subtext: { fontSize: 16, color: "#6b7280", marginTop: 8 },
});
