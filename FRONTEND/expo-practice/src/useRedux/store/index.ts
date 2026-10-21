/**
 * WHAT: Configure the application's Redux store and typed hooks.
 * WHY: Combine Redux slices and provide reusable TypeScript types.
 * HOW: Register reducers with Redux Toolkit configureStore.
 * IMPORTANT: Add future slices to the reducer object here.
 */

import { configureStore } from "@reduxjs/toolkit";
import { useDispatch, useSelector } from "react-redux";

import authenticationReducer from "@/useRedux/redux/authenticationSlice";

export const reduxStore = configureStore({
  reducer: {
    authentication: authenticationReducer,
  },
});

export type RootState = ReturnType<typeof reduxStore.getState>;
export type AppDispatch = typeof reduxStore.dispatch;

// Reuse correctly typed Redux hooks in screens.
export const useAppDispatch = useDispatch.withTypes<AppDispatch>();
export const useAppSelector = useSelector.withTypes<RootState>();
