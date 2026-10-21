/**
 * WHAT: Manage authenticated user and device context state.
 * WHY: Keep the signed-in user and login device available across screens.
 * HOW: Collect safe Expo device fields and store them in a Redux slice.
 * IMPORTANT: Device context is not a unique identifier or proof of identity.
 */

import { createSlice, PayloadAction } from "@reduxjs/toolkit";
import * as Device from "expo-device";
import { Platform } from "react-native";

export type AuthenticatedUser = {
  _id: string;
  username: string;
  email: string;
};

export type DeviceFingerprint = {
  platform: typeof Platform.OS;
  deviceType: Device.DeviceType | null;
  isPhysicalDevice: boolean;
  manufacturer: string | null;
  modelName: string | null;
  operatingSystem: string | null;
  operatingSystemVersion: string | null;
};

export type AuthenticatedSession = {
  user: AuthenticatedUser;
  deviceFingerprint: DeviceFingerprint;
};

type AuthenticationState = {
  user: AuthenticatedUser | null;
  deviceFingerprint: DeviceFingerprint | null;
  isAuthenticated: boolean;
};

const initialAuthenticationState: AuthenticationState = {
  user: null,
  deviceFingerprint: null,
  isAuthenticated: false,
};

// Collect non-unique device context during login.
export function collectDeviceFingerprint(): DeviceFingerprint {
  return {
    platform: Platform.OS,
    deviceType: Device.deviceType,
    isPhysicalDevice: Device.isDevice,
    manufacturer: Device.manufacturer,
    modelName: Device.modelName,
    operatingSystem: Device.osName,
    operatingSystemVersion: Device.osVersion,
  };
}

// Store authentication and device context together.
const authenticationSlice = createSlice({
  name: "authentication",
  initialState: initialAuthenticationState,
  reducers: {
    setAuthenticatedSession(
      state,
      action: PayloadAction<AuthenticatedSession>,
    ) {
      state.user = action.payload.user;
      state.deviceFingerprint = action.payload.deviceFingerprint;
      state.isAuthenticated = true;
    },
    clearAuthenticatedSession(state) {
      state.user = null;
      state.deviceFingerprint = null;
      state.isAuthenticated = false;
    },
  },
});

export const { setAuthenticatedSession, clearAuthenticatedSession } =
  authenticationSlice.actions;

export default authenticationSlice.reducer;
