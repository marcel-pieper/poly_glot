import { useNavigation } from "@react-navigation/native";
import type { NativeStackNavigationProp } from "@react-navigation/native-stack";
import { Pressable, StyleSheet, Text, View } from "react-native";
import type { RootStackParamList } from "../types/navigation";

type HomeScreenNav = NativeStackNavigationProp<RootStackParamList, "Home">;

export function AccountIconButton() {
  const navigation = useNavigation<HomeScreenNav>();
  return (
    <Pressable
      onPress={() => navigation.navigate("Account")}
      style={({ pressed }) => [styles.iconButton, pressed && styles.iconButtonPressed]}
      hitSlop={12}
    >
      <Text style={styles.iconText}>👤</Text>
    </Pressable>
  );
}

export default function HomeScreen() {
  const navigation = useNavigation<HomeScreenNav>();

  return (
    <View style={styles.container}>
      <Pressable
        style={({ pressed }) => [styles.chatButton, pressed && styles.chatButtonPressed]}
        onPress={() => navigation.navigate("Chat")}
      >
        <Text style={styles.chatButtonText}>Start Chat</Text>
      </Pressable>
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
  iconButton: {
    marginRight: 16,
    padding: 4,
  },
  iconButtonPressed: { opacity: 0.7 },
  iconText: { fontSize: 26 },
  chatButton: {
    backgroundColor: "#2563eb",
    paddingHorizontal: 32,
    paddingVertical: 16,
    borderRadius: 12,
  },
  chatButtonPressed: { opacity: 0.9 },
  chatButtonText: { color: "#fff", fontSize: 18, fontWeight: "600" },
});
