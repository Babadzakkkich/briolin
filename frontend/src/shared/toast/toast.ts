import { create } from 'zustand';

export type ToastType = 'success' | 'error' | 'warn' | 'info';

export interface ToastItem {
  id: string;
  type: ToastType;
  message: string;
}

interface ToastStore {
  toasts: ToastItem[];
  add: (type: ToastType, message: string) => void;
  remove: (id: string) => void;
}

const DURATION = 4000;
let nextToastId = 0;
const removalTimers = new Map<string, ReturnType<typeof setTimeout>>();

const createToastId = () => `toast-${Date.now()}-${nextToastId++}`;

export const useToastStore = create<ToastStore>((set) => ({
  toasts: [],
  add: (type, message) => {
    const id = createToastId();
    let added = false;

    set((s) => {
      const duplicateExists = s.toasts.some(
        (toast) => toast.type === type && toast.message === message,
      );

      if (duplicateExists) return s;

      added = true;
      return { toasts: [...s.toasts, { id, type, message }] };
    });

    if (!added) return;

    const timer = setTimeout(() => {
      removalTimers.delete(id);
      set((s) => ({ toasts: s.toasts.filter((t) => t.id !== id) }));
    }, DURATION);
    removalTimers.set(id, timer);
  },
  remove: (id) => {
    const timer = removalTimers.get(id);
    if (timer) {
      clearTimeout(timer);
      removalTimers.delete(id);
    }
    set((s) => ({ toasts: s.toasts.filter((t) => t.id !== id) }));
  },
}));

export const toast = {
  success: (message: string) => useToastStore.getState().add('success', message),
  error: (message: string) => useToastStore.getState().add('error', message),
  warn: (message: string) => useToastStore.getState().add('warn', message),
  info: (message: string) => useToastStore.getState().add('info', message),
};
