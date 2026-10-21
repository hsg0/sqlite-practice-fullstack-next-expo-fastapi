/**
 * WHAT: Render the responsive home screen.
 * WHY: Adapt the layout to the available window size.
 * HOW: Use React Native window dimensions and width breakpoints.
 * IMPORTANT: Window dimensions update when the app resizes or rotates.
 */

import {
  Pressable,
  StyleSheet,
  Text,
  useWindowDimensions,
  View,
} from "react-native";
import { useRouter } from "expo-router";

const tabletWidth = 768;
const desktopWidth = 1024;

export default function Index() {
  const router = useRouter();

  // Open the login screen inside the unprotected group.
  function openLoginPage() {
    router.push("/(unprotected)/login");
  }

  // Read the current app window before returning the layout.
  const { width, height } = useWindowDimensions();

  // Choose one responsive layout size.
  const screenSize =
    width >= desktopWidth
      ? "desktop"
      : width >= tabletWidth
        ? "tablet"
        : "mobile";

  return (
    <View
      style={[
        styles.container,
        screenSize === "desktop" && styles.desktopContainer,
      ]}
    >
      <View style={styles.content}>
        <Text style={styles.title}>{screenSize} layout</Text>
        <Text style={styles.dimensions}>
          {Math.round(width)} × {Math.round(height)}
        </Text>
      </View>

      <Pressable
        accessibilityRole="button"
        accessibilityLabel="Open login page"
        onPress={openLoginPage}
        style={({ pressed }) => [
          styles.loginButton,
          pressed && styles.loginButtonPressed,
        ]}
      >
        <Text style={styles.loginButtonText}>Login</Text>
      </Pressable>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  content: {
    flex: 1,
    alignItems: "center",
    justifyContent: "center",
    padding: 16,
  },
  desktopContainer: {
    paddingHorizontal: 80,
  },
  title: {
    fontSize: 24,
    fontWeight: "600",
    textTransform: "capitalize",
  },
  dimensions: {
    marginTop: 8,
    fontSize: 16,
  },
  loginButton: {
    minHeight: "15%",
    width: "100%",
    alignItems: "center",
    justifyContent: "center",
    backgroundColor: "#2563eb",
    padding: 20,
  },
  loginButtonPressed: {
    opacity: 0.8,
  },
  loginButtonText: {
    color: "#ffffff",
    fontSize: 20,
    fontWeight: "700",
  },
});
