import { useEffect, useState } from 'react';
import { Trash2, X } from 'lucide-react';
import { mediaApi } from '@/entities/media';
import type { AvatarHistoryItem } from '@/entities/media';
import { AuthImage } from '@/shared/uikit/AuthImage';
import { Loader } from '@/shared/uikit/Loader';
import { ConfirmDialog } from '@/shared/uikit/ConfirmDialog';
import { toast } from '@/shared/toast/toast';

interface AvatarHistoryModalProps {
  onClose: () => void;
  onCurrentChanged: (url: string, thumbnailUrl: string) => void;
}

export function AvatarHistoryModal({ onClose, onCurrentChanged }: AvatarHistoryModalProps) {
  const [items, setItems] = useState<AvatarHistoryItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [busyId, setBusyId] = useState<string | null>(null);
  const [pendingDeleteId, setPendingDeleteId] = useState<string | null>(null);

  function load() {
    setLoading(true);
    mediaApi
      .getAvatarHistory()
      .then((res) => setItems(res.data))
      .catch(() => toast.error('Не удалось загрузить аватарки'))
      .finally(() => setLoading(false));
  }

  useEffect(load, []);

  async function handleSetCurrent(item: AvatarHistoryItem) {
    if (item.is_current) return;
    setBusyId(item.avatar_id);
    try {
      await mediaApi.setCurrentAvatar(item.avatar_id);
      onCurrentChanged(item.url, item.thumbnail_url);
      toast.success('Аватарка обновлена');
      load();
    } catch {
      toast.error('Не удалось переключить аватарку');
    } finally {
      setBusyId(null);
    }
  }

  async function handleDelete() {
    if (!pendingDeleteId) return;
    setBusyId(pendingDeleteId);
    try {
      await mediaApi.deleteAvatar(pendingDeleteId);
      const wasCurrent = items.find((i) => i.avatar_id === pendingDeleteId)?.is_current;
      toast.success('Аватарка удалена');
      if (wasCurrent) onCurrentChanged('', '');
      load();
    } catch {
      toast.error('Не удалось удалить аватарку');
    } finally {
      setBusyId(null);
      setPendingDeleteId(null);
    }
  }

  return (
    <div className='fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4'>
      <div className='relative w-full max-w-md rounded-2xl bg-white shadow-xl'>
        <div className='flex items-center justify-between border-b border-[#F0E9E0] p-5'>
          <h2 className='font-onest text-primary text-[17px] font-medium'>Ваши аватарки</h2>
          <button
            onClick={onClose}
            className='text-muted hover:text-primary rounded-lg p-1.5 transition-colors'
          >
            <X size={18} />
          </button>
        </div>

        <div className='max-h-[60vh] overflow-y-auto p-5'>
          {loading ? (
            <Loader center />
          ) : items.length === 0 ? (
            <p className='text-secondary text-center text-[13px]'>Пока нет загруженных аватарок</p>
          ) : (
            <div className='grid grid-cols-3 gap-3'>
              {items.map((item) => (
                <div key={item.avatar_id} className='relative'>
                  <button
                    onClick={() => handleSetCurrent(item)}
                    disabled={busyId === item.avatar_id}
                    className={[
                      'aspect-square w-full overflow-hidden rounded-xl ring-2 transition-opacity',
                      item.is_current ? 'ring-accent' : 'ring-transparent hover:opacity-80',
                      busyId === item.avatar_id ? 'opacity-50' : '',
                    ].join(' ')}
                  >
                    <AuthImage src={item.thumbnail_url} className='h-full w-full object-cover' />
                  </button>
                  {item.is_current && (
                    <span className='bg-accent absolute top-1 left-1 rounded-full px-1.5 py-0.5 text-[9px] font-semibold text-white'>
                      Текущая
                    </span>
                  )}
                  <button
                    onClick={() => setPendingDeleteId(item.avatar_id)}
                    disabled={busyId === item.avatar_id}
                    className='absolute -top-1.5 -right-1.5 flex h-6 w-6 items-center justify-center rounded-full bg-white shadow-sm ring-1 ring-[#F0E9E0] hover:bg-red-50'
                  >
                    <Trash2 size={11} className='text-red-500' />
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {pendingDeleteId && (
        <ConfirmDialog
          title='Удалить аватарку?'
          confirmLabel='Удалить'
          destructive
          loading={busyId === pendingDeleteId}
          onConfirm={handleDelete}
          onClose={() => setPendingDeleteId(null)}
        />
      )}
    </div>
  );
}
