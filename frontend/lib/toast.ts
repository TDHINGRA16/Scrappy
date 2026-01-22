// ========================================
// Toast Helper Functions
// ========================================

import toast from "react-hot-toast";

export const showToast = {
  success: (message: string) => {
    toast.success(message, {
      style: {
        background: "#dcfce7",
        color: "#166534",
        border: "1px solid #22c55e",
      },
    });
  },

  error: (message: string) => {
    toast.error(message, {
      style: {
        background: "#fee2e2",
        color: "#991b1b",
        border: "1px solid #ef4444",
      },
    });
  },

  info: (message: string) => {
    toast(message, {
      icon: "ℹ️",
      style: {
        background: "#dbeafe",
        color: "#1e40af",
        border: "1px solid #3b82f6",
      },
    });
  },

  warning: (message: string) => {
    toast(message, {
      icon: "⚠️",
      style: {
        background: "#fef3c7",
        color: "#92400e",
        border: "1px solid #f59e0b",
      },
    });
  },

  loading: (message: string) => {
    return toast.loading(message, {
      style: {
        background: "#f4f4f5",
        color: "#3f3f46",
        border: "1px solid #e4e4e7",
      },
    });
  },

  dismiss: (toastId?: string) => {
    if (toastId) {
      toast.dismiss(toastId);
    } else {
      toast.dismiss();
    }
  },

  promise: <T,>(
    promise: Promise<T>,
    messages: {
      loading: string;
      success: string;
      error: string;
    }
  ) => {
    return toast.promise(promise, messages);
  },
};

export default showToast;
