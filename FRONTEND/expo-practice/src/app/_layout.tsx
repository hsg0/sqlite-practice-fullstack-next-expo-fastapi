/**
 * WHAT: Configure navigation and global application providers.
 * WHY: Make Redux state available to every Expo Router screen.
 * HOW: Wrap the root navigation stack with React Redux Provider.
 * IMPORTANT: Keep global providers at the root of the application.
 */

import { Stack } from "expo-router";
import { Provider } from "react-redux";

import { reduxStore } from "@/useRedux/store";

export default function RootLayout() {
  return (
    <Provider store={reduxStore}>
      <Stack />
    </Provider>
  );
}
