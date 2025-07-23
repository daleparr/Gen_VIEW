"use client";

import { motion, AnimatePresence } from "framer-motion";
import { X, CheckCircle, AlertCircle, Info } from "lucide-react";
import { useEffect, useState } from "react";

interface Toast {
  id: string;
  title: string;
  description?: string;
  type: "success" | "error" | "info";
  duration?: number;
}

let toasts: Toast[] = [];
let listeners: ((toasts: Toast[]) => void)[] = [];

const addToast = (toast: Omit<Toast, "id">) => {
  const id = Math.random().toString(36).substring(2, 9);
  const newToast = { ...toast, id };
  toasts = [...toasts, newToast];
  listeners.forEach((listener) => listener(toasts));

  // Auto remove after duration
  setTimeout(() => {
    removeToast(id);
  }, toast.duration || 5000);
};

const removeToast = (id: string) => {
  toasts = toasts.filter((toast) => toast.id !== id);
  listeners.forEach((listener) => listener(toasts));
};

export const toast = {
  success: (title: string, description?: string) =>
    addToast({ title, description, type: "success" }),
  error: (title: string, description?: string) =>
    addToast({ title, description, type: "error" }),
  info: (title: string, description?: string) =>
    addToast({ title, description, type: "info" }),
};

export function Toaster() {
  const [toastList, setToastList] = useState<Toast[]>([]);

  useEffect(() => {
    listeners.push(setToastList);
    return () => {
      listeners = listeners.filter((listener) => listener !== setToastList);
    };
  }, []);

  return (
    <div className="fixed top-4 right-4 z-50 space-y-2">
      <AnimatePresence>
        {toastList.map((toast) => {
          const Icon = {
            success: CheckCircle,
            error: AlertCircle,
            info: Info,
          }[toast.type];

          const colors = {
            success: "from-green-500/20 to-emerald-500/20 border-green-500/30",
            error: "from-red-500/20 to-pink-500/20 border-red-500/30",
            info: "from-blue-500/20 to-cyan-500/20 border-blue-500/30",
          }[toast.type];

          return (
            <motion.div
              key={toast.id}
              initial={{ opacity: 0, x: 300, scale: 0.3 }}
              animate={{ opacity: 1, x: 0, scale: 1 }}
              exit={{ opacity: 0, x: 300, scale: 0.3 }}
              className={`max-w-sm w-full bg-gradient-to-r ${colors} backdrop-blur-xl border rounded-lg p-4 shadow-2xl`}
            >
              <div className="flex items-start">
                <Icon className="w-5 h-5 text-white mt-0.5 mr-3 flex-shrink-0" />
                <div className="flex-1">
                  <p className="text-sm font-medium text-white">{toast.title}</p>
                  {toast.description && (
                    <p className="text-sm text-gray-300 mt-1">
                      {toast.description}
                    </p>
                  )}
                </div>
                <button
                  onClick={() => removeToast(toast.id)}
                  className="ml-4 text-gray-400 hover:text-white transition-colors"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>
            </motion.div>
          );
        })}
      </AnimatePresence>
    </div>
  );
}