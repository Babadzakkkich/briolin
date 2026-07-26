export type StepProps<TData = undefined> = {
  onNext: (data?: TData) => void;
  onRetry?: () => void;
  data?: unknown;
};
