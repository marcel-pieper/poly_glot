import { NavigationContainer } from "@react-navigation/native";
import { createNativeStackNavigator } from "@react-navigation/native-stack";
import { StatusBar } from "expo-status-bar";
import { ActivityIndicator, View } from "react-native";
import { SafeAreaProvider } from "react-native-safe-area-context";
import { AuthProvider, useAuth } from "./contexts/AuthContext";
import { AccountIconButton } from "./screens/HomeScreen";
import AccountScreen from "./screens/AccountScreen";
import ChatPlaceholderScreen from "./screens/ChatPlaceholderScreen";
import HomeScreen from "./screens/HomeScreen";
import LoginScreen from "./screens/LoginScreen";
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

  const initialRoute: keyof RootStackParamList = token ? "Home" : "Login";
  return (
    <NavigationContainer>
      <Stack.Navigator
        key={token ?? "guest"}
        initialRouteName={initialRoute}
        screenOptions={screenOptions}
      >
        <Stack.Screen
          name="Login"
          component={LoginScreen}
          options={{ headerShown: false }}
        />
        <Stack.Screen
          name="Home"
          component={HomeScreen}
          options={{
            title: "Polyglot",
            headerRight: () => <AccountIconButton />,
          }}
        />
        <Stack.Screen name="Account" component={AccountScreen} options={{ title: "Account" }} />
        <Stack.Screen name="Chat" component={ChatPlaceholderScreen} options={{ title: "Chat" }} />
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
