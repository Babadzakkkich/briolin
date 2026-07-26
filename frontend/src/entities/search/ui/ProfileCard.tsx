import { MapPin, Heart } from 'lucide-react';
import { Button } from '@/shared/uikit/Button';
import { AuthImage } from '@/shared/uikit/AuthImage';
import type { ProfilePreview } from '../model/types';

interface ProfileCardProps {
  profile: ProfilePreview;
  onLike: () => void;
  onView: () => void;
}

function AvatarPlaceholder({ name }: { name: string }) {
  const initials = name
    .split(' ')
    .slice(0, 2)
    .map((w) => w[0] ?? '')
    .join('')
    .toUpperCase();
  return (
    <div className='bg-accent/15 text-accent flex h-full w-full items-center justify-center text-4xl font-semibold'>
      {initials || '?'}
    </div>
  );
}

export function ProfileCard({ profile, onLike, onView }: ProfileCardProps) {
  return (
    <div className='border-border hover:border-muted flex flex-col overflow-hidden rounded-2xl border bg-white transition-colors'>
      <div className='bg-surface relative aspect-square w-full overflow-hidden'>
        {profile.avatar_url ? (
          <AuthImage
            src={profile.avatar_url}
            alt={profile.display_name}
            className='h-full w-full object-cover'
            fallback={<AvatarPlaceholder name={profile.display_name} />}
          />
        ) : (
          <AvatarPlaceholder name={profile.display_name} />
        )}
        {profile.online && (
          <span className='absolute top-3 right-3 h-2.5 w-2.5 rounded-full bg-green-400 ring-2 ring-white' />
        )}
      </div>
      <div className='flex flex-col gap-3 p-4'>
        <div>
          <p className='text-primary text-[15px] font-semibold'>
            {profile.display_name}, {profile.age}
          </p>
          <p className='text-secondary mt-0.5 flex items-center gap-1 text-[13px]'>
            <MapPin size={12} className='shrink-0' />
            {profile.city}
          </p>
        </div>
        <div className='flex justify-between gap-2'>
          <Button onClick={onLike} className='px-4!'>
            <Heart size={14} strokeWidth={2.5} />
          </Button>
          <Button variant='secondary' onClick={onView} className='w-full'>
            Посмотреть
          </Button>
        </div>
      </div>
    </div>
  );
}
