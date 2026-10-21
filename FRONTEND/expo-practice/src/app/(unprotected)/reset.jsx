/**
 * WHAT: Guide users through password recovery.
 * WHY: Verify email ownership before accepting a new password.
 * HOW: Request an OTP, verify it, then send a one-use reset token.
 * IMPORTANT: FastAPI decides whether the OTP and token are valid.
 */

import { useState } from "react";
import { useRouter } from "expo-router";
import {
  ActivityIndicator,
  KeyboardAvoidingView,
  Platform,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  View,
} from "react-native";

import {
  confirmPasswordReset,
  requestPasswordReset,
  verifyPasswordResetCode,
} from "@/backendCall/callBackend";

export default function ResetPasswordPage() {
  const router = useRouter();

  // Track the current recovery step and its values.
  const [currentStep, setCurrentStep] = useState(1);
  const [email, setEmail] = useState("");
  const [otp, setOtp] = useState("");
  const [resetToken, setResetToken] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [message, setMessage] = useState("");
  const [errorMessage, setErrorMessage] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Read a safe message from request failures.
  function readErrorMessage(error) {
    return error instanceof Error
      ? error.message
      : "Something went wrong. Please try again.";
  }

  // Ask FastAPI to create and send an OTP.
  async function handleEmailSubmit() {
    const cleanEmail = email.trim().toLowerCase();

    if (!cleanEmail.includes("@")) {
      setErrorMessage("Enter a valid email address.");
      return;
    }

    setIsSubmitting(true);
    setErrorMessage("");
    setMessage("");

    try {
      const response = await requestPasswordReset({ email: cleanEmail });

      setEmail(cleanEmail);
      setMessage(response.message);
      setCurrentStep(2);
    } catch (error) {
      setErrorMessage(readErrorMessage(error));
    } finally {
      setIsSubmitting(false);
    }
  }

  // Verify the OTP and save the limited reset token.
  async function handleOtpSubmit() {
    if (otp.length !== 6) {
      setErrorMessage("Enter the six-digit code.");
      return;
    }

    setIsSubmitting(true);
    setErrorMessage("");
    setMessage("");

    try {
      const response = await verifyPasswordResetCode({ email, otp });

      setResetToken(response.resetToken);
      setMessage(response.message);
      setCurrentStep(3);
    } catch (error) {
      setErrorMessage(readErrorMessage(error));
    } finally {
      setIsSubmitting(false);
    }
  }

  // Change the password using the verified reset token.
  async function handlePasswordSubmit() {
    if (password.length < 8) {
      setErrorMessage("Password must be at least 8 characters.");
      return;
    }

    if (password !== confirmPassword) {
      setErrorMessage("Passwords do not match.");
      return;
    }

    setIsSubmitting(true);
    setErrorMessage("");
    setMessage("");

    try {
      await confirmPasswordReset({
        email,
        resetToken,
        password,
      });

      router.replace("/(unprotected)/login");
    } catch (error) {
      setErrorMessage(readErrorMessage(error));
    } finally {
      setIsSubmitting(false);
    }
  }

  // Restart verification when the email changes.
  function returnToEmailStep() {
    setCurrentStep(1);
    setOtp("");
    setResetToken("");
    setMessage("");
    setErrorMessage("");
  }

  return (
    <KeyboardAvoidingView
      behavior={Platform.OS === "ios" ? "padding" : "height"}
      style={styles.page}
    >
      <ScrollView
        contentContainerStyle={styles.content}
        keyboardShouldPersistTaps="handled"
      >
        <View style={styles.form}>
          <View style={styles.heading}>
            <Text style={styles.step}>Step {currentStep} of 3</Text>
            <Text style={styles.title}>Reset password</Text>
            <Text style={styles.subtitle}>
              {currentStep === 1 && "Enter the email for your account."}
              {currentStep === 2 && `Enter the code sent to ${email}.`}
              {currentStep === 3 && "Choose a new account password."}
            </Text>
          </View>

          {currentStep === 1 && (
            <View style={styles.field}>
              <Text style={styles.label}>Email</Text>
              <TextInput
                accessibilityLabel="Email"
                autoCapitalize="none"
                autoComplete="email"
                autoCorrect={false}
                editable={!isSubmitting}
                keyboardType="email-address"
                maxLength={50}
                onChangeText={setEmail}
                onSubmitEditing={handleEmailSubmit}
                placeholder="you@example.com"
                placeholderTextColor="#64748b"
                returnKeyType="send"
                style={styles.input}
                value={email}
              />
            </View>
          )}

          {currentStep === 2 && (
            <View style={styles.field}>
              <Text style={styles.label}>Six-digit code</Text>
              <TextInput
                accessibilityLabel="Six-digit reset code"
                autoComplete="one-time-code"
                editable={!isSubmitting}
                keyboardType="number-pad"
                maxLength={6}
                onChangeText={(value) => {
                  setOtp(value.replace(/\D/g, ""));
                }}
                onSubmitEditing={handleOtpSubmit}
                placeholder="000000"
                placeholderTextColor="#64748b"
                returnKeyType="done"
                style={[styles.input, styles.otpInput]}
                value={otp}
              />
            </View>
          )}

          {currentStep === 3 && (
            <>
              <View style={styles.field}>
                <Text style={styles.label}>New password</Text>
                <TextInput
                  accessibilityLabel="New password"
                  autoCapitalize="none"
                  autoComplete="new-password"
                  autoCorrect={false}
                  editable={!isSubmitting}
                  maxLength={128}
                  onChangeText={setPassword}
                  placeholder="At least 8 characters"
                  placeholderTextColor="#64748b"
                  returnKeyType="next"
                  secureTextEntry
                  style={styles.input}
                  value={password}
                />
              </View>

              <View style={styles.field}>
                <Text style={styles.label}>Confirm password</Text>
                <TextInput
                  accessibilityLabel="Confirm new password"
                  autoCapitalize="none"
                  autoComplete="new-password"
                  autoCorrect={false}
                  editable={!isSubmitting}
                  maxLength={128}
                  onChangeText={setConfirmPassword}
                  onSubmitEditing={handlePasswordSubmit}
                  placeholder="Enter the password again"
                  placeholderTextColor="#64748b"
                  returnKeyType="done"
                  secureTextEntry
                  style={styles.input}
                  value={confirmPassword}
                />
              </View>
            </>
          )}

          {message ? <Text style={styles.message}>{message}</Text> : null}
          {errorMessage ? (
            <Text accessibilityLiveRegion="polite" style={styles.error}>
              {errorMessage}
            </Text>
          ) : null}

          <Pressable
            accessibilityRole="button"
            disabled={isSubmitting}
            onPress={
              currentStep === 1
                ? handleEmailSubmit
                : currentStep === 2
                  ? handleOtpSubmit
                  : handlePasswordSubmit
            }
            style={({ pressed }) => [
              styles.primaryButton,
              pressed && styles.buttonPressed,
              isSubmitting && styles.buttonDisabled,
            ]}
          >
            {isSubmitting ? (
              <ActivityIndicator color="#ffffff" />
            ) : (
              <Text style={styles.primaryButtonText}>
                {currentStep === 1 && "Send code"}
                {currentStep === 2 && "Verify code"}
                {currentStep === 3 && "Change password"}
              </Text>
            )}
          </Pressable>

          {currentStep === 2 && (
            <Pressable
              accessibilityRole="button"
              disabled={isSubmitting}
              onPress={returnToEmailStep}
              style={({ pressed }) => pressed && styles.buttonPressed}
            >
              <Text style={styles.secondaryButtonText}>Change email</Text>
            </Pressable>
          )}
        </View>
      </ScrollView>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  page: {
    flex: 1,
    backgroundColor: "#f8fafc",
  },
  content: {
    flexGrow: 1,
    alignItems: "center",
    justifyContent: "center",
    padding: 24,
  },
  form: {
    width: "100%",
    maxWidth: 440,
    gap: 20,
  },
  heading: {
    gap: 8,
  },
  step: {
    fontSize: 14,
    fontWeight: "700",
    color: "#2563eb",
  },
  title: {
    fontSize: 32,
    fontWeight: "700",
    color: "#0f172a",
  },
  subtitle: {
    fontSize: 16,
    color: "#475569",
  },
  field: {
    gap: 8,
  },
  label: {
    fontSize: 16,
    fontWeight: "600",
    color: "#0f172a",
  },
  input: {
    minHeight: 52,
    borderWidth: 1,
    borderColor: "#cbd5e1",
    borderRadius: 10,
    backgroundColor: "#ffffff",
    paddingHorizontal: 16,
    fontSize: 16,
    color: "#0f172a",
  },
  otpInput: {
    textAlign: "center",
    fontSize: 24,
    letterSpacing: 12,
  },
  message: {
    color: "#166534",
  },
  error: {
    color: "#b91c1c",
  },
  primaryButton: {
    minHeight: 52,
    alignItems: "center",
    justifyContent: "center",
    borderRadius: 10,
    backgroundColor: "#2563eb",
    paddingHorizontal: 20,
  },
  primaryButtonText: {
    color: "#ffffff",
    fontSize: 16,
    fontWeight: "700",
  },
  secondaryButtonText: {
    textAlign: "center",
    color: "#2563eb",
    fontSize: 16,
    fontWeight: "600",
  },
  buttonPressed: {
    opacity: 0.8,
  },
  buttonDisabled: {
    opacity: 0.6,
  },
});
