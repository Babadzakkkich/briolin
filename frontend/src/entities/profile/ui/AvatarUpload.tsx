import { useState } from 'react';
import { Camera, Images, Loader2, Trash2 } from 'lucide-react';
import { mediaApi } from '@/entities/media';
import { AuthImage } from '@/shared/uikit/AuthImage';
import { toast } from '@/shared/toast/toast';
import { AvatarHistoryModal } from './AvatarHistoryModal';
function getInitials(name?: string) {
  if (!name) return '?';
  return name
    .split(' ')
    .slice(0, 2)
    .map((w) => w[0] ?? '')
    .join('')
    .toUpperCase();
}

interface AvatarUploadProps {
  src?: string | null;
  name?: string;
  onUploaded?: (url: string, thumbnailUrl: string, avatarId?: string) => void;
}

export function AvatarUpload({ src, name, onUploaded }: AvatarUploadProps) {
  const [uploading, setUploading] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [showHistory, setShowHistory] = useState(false);

  async function handleFile(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    e.target.value = '';
    if (!file) return;

    setUploading(true);
    try {
      const res = await mediaApi.uploadAvatar(file);
      onUploaded?.(res.data.url, res.data.thumbnail_url, res.data.avatar_id);
      toast.success('Аватарка загружена');
    } catch (err: unknown) {
      const status = (err as { response?: { status?: number } })?.response?.status;
      if (status === 413) toast.error('Файл слишком большой (макс. 5 МБ)');
      else if (status === 415) toast.error('Неподдерживаемый формат (JPEG, PNG, WebP, GIF)');
      else if (status === 400) toast.error('Превышен лимит аватарок (10 штук)');
      else toast.error('Ошибка загрузки аватарки');
    } finally {
      setUploading(false);
    }
  }

  async function handleDelete() {
    setDeleting(true);
    try {
      await mediaApi.deleteCurrentAvatar();
      onUploaded?.('', '');
      toast.success('Аватарка удалена');
    } catch {
      toast.error('Не удалось удалить аватарку');
    } finally {
      setDeleting(false);
    }
  }

  const busy = uploading || deleting;

  return (
    <div className='relative h-20 w-20'>
      <div className='h-20 w-20 overflow-hidden rounded-2xl'>
        {src ? (
          <AuthImage
            src={src}
            alt={name ?? 'avatar'}
            className='h-full w-full object-cover'
            fallback={
              <div className='bg-accent/15 text-accent flex h-full w-full items-center justify-center text-2xl font-semibold'>
                {getInitials(name)}
              </div>
            }
          />
        ) : (
          <div className='bg-accent/15 text-accent flex h-full w-full items-center justify-center text-2xl font-semibold'>
            {getInitials(name)}
          </div>
        )}
      </div>

      {busy ? (
        <div className='absolute inset-0 flex items-center justify-center rounded-2xl bg-black/40'>
          <Loader2 size={20} className='animate-spin text-white' />
        </div>
      ) : (
        <>
          <label className='absolute inset-0 flex cursor-pointer items-center justify-center rounded-2xl bg-black/0 transition-all hover:bg-black/30 group'>
            <Camera size={20} className='text-white opacity-0 group-hover:opacity-100 transition-opacity' />
            <input
              type='file'
              accept='image/jpeg,image/png,image/webp,image/gif'
              className='hidden'
              onChange={handleFile}
              disabled={busy}
            />
          </label>
          {src && (
            <>
              <button
                onClick={handleDelete}
                disabled={busy}
                className='absolute -right-2 -bottom-2 flex h-6 w-6 items-center justify-center rounded-full bg-white shadow-sm border border-[#F0E9E0] hover:bg-red-50 transition-colors'
                title='Удалить аватарку'
              >
                <Trash2 size={11} className='text-red-500' />
              </button>
              <button
                onClick={() => setShowHistory(true)}
                disabled={busy}
                className='absolute -top-2 -left-2 flex h-6 w-6 items-center justify-center rounded-full bg-white shadow-sm border border-[#F0E9E0] hover:bg-surface transition-colors'
                title='Все аватарки'
              >
                <Images size={11} className='text-secondary' />
              </button>
            </>
          )}
        </>
      )}

      {showHistory && (
        <AvatarHistoryModal
          onClose={() => setShowHistory(false)}
          onCurrentChanged={(url, thumbnailUrl) => onUploaded?.(url, thumbnailUrl)}
        />
      )}
    </div>
  );
}
