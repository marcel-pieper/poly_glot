import { NavigationContainer } from "@react-navigation/native";
import { createNativeStackNavigator } from "@react-navigation/native-stack";
import { StatusBar } from "expo-status-bar";
import { ActivityIndicator, View } from "react-native";
import { SafeAreaProvider } from "react-native-safe-area-context";
import { AuthProvider, useAuth } from "./contexts/AuthContext";
import ChatScreen from "./screens/ChatScreen";
import ExplainScreen from "./screens/ExplainScreen";
import HomeTabsScreen from "./screens/HomeTabsScreen";
import LoginScreen from "./screens/LoginScreen";
import TranslationScreen from "./screens/TranslationScreen";
import type { RootStackParamList } from "./types/navigation";

const Stack = createNativeStackNavigator<RootStackParamList>();

const screenOptions = {
  headerStyle: { backgroundColor: "#f9fafb" as const },
  headerTitleStyle: { fontWeight: "600" as const, fontSize: 18 },
};

function AppContent() {
  const { token, loading } = useAuth();

  if (loading) {
    return (
      <View style={{ flex: 1, justifyContent: "center", alignItems: "center" }}>
        <ActivityIndicator size="large" />
      </View>
    );
  }

  // Avoid transient navigator state on logout by hard-switching to Login.
  if (!token) {
    return <LoginScreen />;
  }

  return (
    <NavigationContainer>
      <Stack.Navigator key={token} initialRouteName="MainTabs" screenOptions={screenOptions}>
        <Stack.Screen
          name="MainTabs"
          component={HomeTabsScreen}
          options={{ headerShown: false }}
        />
        <Stack.Screen
          name="ChatScreen"
          component={ChatScreen}
          options={({ route }) => ({ title: route.params.title ?? "New chat" })}
        />
        <Stack.Screen
          name="ExplainScreen"
          component={ExplainScreen}
          options={{ title: "Explain" }}
        />
        <Stack.Screen
          name="TranslationScreen"
          component={TranslationScreen}
          options={{ title: "Translation" }}
        />
      </Stack.Navigator>
    </NavigationContainer>
  );
}

export default function App() {
  return (
    <SafeAreaProvider>
      <AuthProvider>
        <StatusBar style="dark" />
        <AppContent />
      </AuthProvider>
    </SafeAreaProvider>
  );
}
