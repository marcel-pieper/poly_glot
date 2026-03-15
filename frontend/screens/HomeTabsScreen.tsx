import { createBottomTabNavigator } from "@react-navigation/bottom-tabs";
import { Ionicons } from "@expo/vector-icons";
import { StyleSheet, Text, View } from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";

import type { HomeTabParamList } from "../types/navigation";
import AccountScreen from "./AccountScreen";
import ChatOverviewScreen from "./ChatOverviewScreen";
import TranslateOverviewScreen from "./TranslateOverviewScreen";

const Tab = createBottomTabNavigator<HomeTabParamList>();

function DummyPage({ title }: { title: string }) {
  return (
    <View style={styles.container}>
      <Text style={styles.title}>{title}</Text>
      <Text style={styles.subtitle}>Placeholder page</Text>
    </View>
  );
}

export default function HomeTabsScreen() {
  const insets = useSafeAreaInsets();

  return (
    <Tab.Navigator
      initialRouteName="ChatTab"
      screenOptions={({ route }) => ({
        headerTitleAlign: "center",
        tabBarLabelStyle: { fontSize: 12 },
        tabBarStyle: {
          height: 56 + insets.bottom,
          paddingBottom: Math.max(insets.bottom, 6),
          paddingTop: 6,
        },
        tabBarIcon: ({ color, size, focused }) => {
          let iconName: keyof typeof Ionicons.glyphMap = "ellipse-outline";

          if (route.name === "PracticeTab") {
            iconName = focused ? "barbell" : "barbell-outline";
          } else if (route.name === "VocabTab") {
            iconName = focused ? "book" : "book-outline";
          } else if (route.name === "ChatTab") {
            iconName = focused ? "chatbubble-ellipses" : "chatbubble-ellipses-outline";
          } else if (route.name === "TranslateTab") {
            iconName = focused ? "language" : "language-outline";
          } else if (route.name === "DataTab") {
            iconName = focused ? "person-circle" : "person-circle-outline";
          }

          return <Ionicons name={iconName} size={size} color={color} />;
        },
      })}
    >
      <Tab.Screen
        name="PracticeTab"
        options={{ title: "Practice", tabBarLabel: "Practice" }}
      >
        {() => <DummyPage title="Practice" />}
      </Tab.Screen>
      <Tab.Screen name="VocabTab" options={{ title: "Vocab", tabBarLabel: "Vocab" }}>
        {() => <DummyPage title="Vocab" />}
      </Tab.Screen>
      <Tab.Screen name="ChatTab" options={{ title: "Chat", tabBarLabel: "Chat" }}>
        {() => <ChatOverviewScreen />}
      </Tab.Screen>
      <Tab.Screen
        name="TranslateTab"
        options={{ title: "Translate", tabBarLabel: "Translate" }}
      >
        {() => <TranslateOverviewScreen />}
      </Tab.Screen>
      <Tab.Screen name="DataTab" options={{ title: "Data", tabBarLabel: "Data" }}>
        {() => <AccountScreen />}
      </Tab.Screen>
    </Tab.Navigator>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    alignItems: "center",
    justifyContent: "center",
    backgroundColor: "#f8fafc",
    padding: 20,
  },
  title: {
    fontSize: 30,
    fontWeight: "700",
    color: "#0f172a",
  },
  subtitle: {
    marginTop: 8,
    fontSize: 15,
    color: "#64748b",
  },
});
