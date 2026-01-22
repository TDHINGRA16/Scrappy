// ========================================
// Toast Notification Provider
// ========================================

"use client";

import { Toaster } from "react-hot-toast";

export function ToastProvider() {
  return (
    <Toaster
      position="top-right"
      gutter={12}
      containerStyle={{
        top: 20,
        right: 20,
      }}
      toastOptions={{
        duration: 4000,
        style: {
          background: "#18181b",
          color: "#fff",
          borderRadius: "12px",
          padding: "16px 20px",
          boxShadow: "0 10px 40px rgba(0, 0, 0, 0.2)",
          border: "1px solid rgba(255, 255, 255, 0.1)",
          fontSize: "14px",
          fontWeight: 500,
        },
        success: {
          style: {
            background: "#dcfce7",
            color: "#166534",
            border: "1px solid #22c55e",
          },
          iconTheme: {
            primary: "#22c55e",
            secondary: "#fff",
          },
        },
        error: {
          style: {
            background: "#fee2e2",
            color: "#991b1b",
            border: "1px solid #ef4444",
          },
          iconTheme: {
            primary: "#ef4444",
            secondary: "#fff",
          },
        },
        loading: {
          style: {
            background: "#f4f4f5",
            color: "#3f3f46",
            border: "1px solid #e4e4e7",
          },
        },
      }}
    />
  );
}

export default ToastProvider;
