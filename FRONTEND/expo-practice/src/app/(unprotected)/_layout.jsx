/**
 * WHAT: Define navigation for signed-out screens.
 * WHY: Keep login pages separate from protected app pages.
 * HOW: Render the unprotected routes in an Expo Router stack.
 * IMPORTANT: Authentication checks can be added here later.
 */

import { Stack } from "expo-router";

export default function UnprotectedLayout() {
  return <Stack screenOptions={{ headerShown: false }} />;
}
