import { Lock } from 'lucide-react';
import type { SearchLockInfo } from '../model/types';

function formatUnlockTime(seconds?: number | null) {
  if (!seconds) return '';
  const h = Math.floor(seconds / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  if (h > 0) return `${h} ч ${m} мин`;
  return `${m} мин`;
}

export function LockBanner({ lockInfo }: { lockInfo: SearchLockInfo }) {
  return (
    <div className='mb-4 flex items-start gap-3 rounded-2xl border border-amber-200 bg-amber-50 p-4'>
      <Lock size={16} className='mt-0.5 shrink-0 text-amber-600' strokeWidth={2} />
      <div>
        <p className='text-[13px] font-semibold text-amber-800'>
          Таргетированный поиск заблокирован
        </p>
        <p className='mt-0.5 text-[12px] text-amber-700'>
          Просмотрено {lockInfo.profiles_viewed} анкет.
          {lockInfo.time_until_unlock
            ? ` Разблокируется через ${formatUnlockTime(lockInfo.time_until_unlock)}.`
            : ''}
        </p>
      </div>
    </div>
  );
}
