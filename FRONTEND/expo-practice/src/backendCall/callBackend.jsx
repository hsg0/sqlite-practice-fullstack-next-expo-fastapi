/**
 * WHAT: Send reusable requests to the FastAPI backend.
 * WHY: Keep login and registration network logic in one place.
 * HOW: Configure one Axios client and expose shared request functions.
 * IMPORTANT: Set EXPO_PUBLIC_API_URL for production or a remote backend.
 */

import axios from "axios";
import Constants from "expo-constants";
import { Platform } from "react-native";

// Use the configured backend URL when one is provided.
const configuredBackendUrl = process.env.EXPO_PUBLIC_API_URL;

// Read the Expo development server host for physical devices.
const developmentHost = Constants.expoConfig?.hostUri?.split(":")[0];

// Reach FastAPI from web, simulators, emulators, and Expo Go.
const localBackendUrl = developmentHost
  ? `http://${developmentHost}:4020`
  : Platform.OS === "android"
    ? "http://10.0.2.2:4020"
    : "http://127.0.0.1:4020";

// Remove a final slash so endpoint paths stay consistent.
const backendUrl = (configuredBackendUrl || localBackendUrl).replace(/\/+$/, "");

// Share backend settings across every request.
const backendClient = axios.create({
  baseURL: backendUrl,
  timeout: 10000,
  withCredentials: true,
  headers: {
    Accept: "application/json",
    "Content-Type": "application/json",
  },
});

// Convert Axios failures into messages screens can display.
function createBackendError(error) {
  if (!axios.isAxiosError(error)) {
    return error;
  }

  const errorDetails = error.response?.data?.detail;

  if (typeof errorDetails === "string") {
    const backendError = new Error(errorDetails);
    backendError.statusCode = error.response?.status ?? null;
    return backendError;
  }

  if (Array.isArray(errorDetails)) {
    const validationMessage = errorDetails
      .map((errorDetail) => errorDetail.msg)
      .filter(Boolean)
      .join(" ");

    const backendError = new Error(
      validationMessage || "The submitted information is invalid.",
    );
    backendError.statusCode = error.response?.status ?? null;
    return backendError;
  }

  if (!error.response) {
    return new Error("Cannot reach the backend. Check that FastAPI is running.");
  }

  const backendError = new Error("The backend request failed.");
  backendError.statusCode = error.response.status;
  return backendError;
}

// Send any request through the shared Axios client.
export async function callBackend({
  endpoint,
  method = "GET",
  data,
  accessToken,
  params,
}) {
  try {
    const response = await backendClient.request({
      url: endpoint,
      method,
      data,
      params,
      headers: accessToken
        ? { Authorization: `Bearer ${accessToken}` }
        : undefined,
    });

    return response.data;
  } catch (error) {
    throw createBackendError(error);
  }
}

// Register a new account through the shared client.
export function registerUser({ username, email, password }) {
  return callBackend({
    endpoint: "/api/users/register",
    method: "POST",
    data: {
      username,
      email,
      password,
    },
  });
}

// Log in using the correct token transport for this platform.
export function loginUser({ email, password }) {
  return callBackend({
    endpoint: "/api/users/login",
    method: "POST",
    data: {
      email,
      password,
      clientType: Platform.OS === "web" ? "web" : "mobile",
    },
  });
}

// Ask the backend to issue a password reset code.
export function requestPasswordReset({ email }) {
  return callBackend({
    endpoint: "/api/users/password-reset/request",
    method: "POST",
    data: { email },
  });
}

// Verify the code and receive a limited reset token.
export function verifyPasswordResetCode({ email, otp }) {
  return callBackend({
    endpoint: "/api/users/password-reset/verify",
    method: "POST",
    data: {
      email,
      otp,
    },
  });
}

// Change the password using the verified reset token.
export function confirmPasswordReset({ email, resetToken, password }) {
  return callBackend({
    endpoint: "/api/users/password-reset/confirm",
    method: "POST",
    data: {
      email,
      resetToken,
      password,
    },
  });
}
