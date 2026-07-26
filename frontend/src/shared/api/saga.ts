export interface SagaStatus {
  saga_id: string;
  status: 'in_progress' | 'completed' | 'failed' | 'not_found';
  error?: string | null;
  [key: string]: unknown;
}

interface PollSagaOptions {
  intervalMs?: number;
  timeoutMs?: number;
}

// Большинство мутаций (смена логина/почты, удаление аккаунта/анкеты, роли, бан)
// возвращают 202 + saga_id и выполняются асинхронно через saga-воркер.
// pollSaga ждёт, пока статус перестанет быть "in_progress".
export async function pollSaga(
  fetchStatus: () => Promise<SagaStatus>,
  { intervalMs = 1200, timeoutMs = 20000 }: PollSagaOptions = {},
): Promise<SagaStatus> {
  const deadline = Date.now() + timeoutMs;

  while (true) {
    const status = await fetchStatus();
    if (status.status !== 'in_progress') return status;
    if (Date.now() >= deadline) {
      return { ...status, status: 'failed', error: status.error ?? 'Превышено время ожидания' };
    }
    await new Promise((resolve) => setTimeout(resolve, intervalMs));
  }
}
