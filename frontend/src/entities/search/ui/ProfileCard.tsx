import { MapPin, Heart } from 'lucide-react';
import { Button } from '@/shared/uikit/Button';
import type { ProfilePreview } from '../model/types';

function getInitials(first: string, last: string) {
  return `${first[0] ?? ''}${last[0] ?? ''}`.toUpperCase();
}

interface ProfileCardProps {
  profile: ProfilePreview;
  onLike: () => void;
  onView: () => void;
}

export function ProfileCard({ profile, onLike, onView }: ProfileCardProps) {
  return (
    <div className='border-border hover:border-muted flex flex-col overflow-hidden rounded-2xl border bg-white transition-colors'>
      {/* Photo area */}
      <div className='bg-surface relative aspect-square w-full overflow-hidden'>
        <div className='bg-accent/15 text-accent flex h-full w-full items-center justify-center text-4xl font-semibold'>
          {getInitials(profile.first_name, profile.last_name)}
        </div>
        {profile.online && (
          <span className='absolute top-3 right-3 h-2.5 w-2.5 rounded-full bg-green-400 ring-2 ring-white' />
        )}
      </div>

      {/* Info */}
      <div className='flex flex-col gap-3 p-4'>
        <div>
          <p className='text-primary text-[15px] font-semibold'>
            {profile.first_name}, {profile.age}
          </p>
          <p className='text-secondary mt-0.5 flex items-center gap-1 text-[13px]'>
            <MapPin size={12} className='shrink-0' />
            {profile.city}
          </p>
        </div>

        {/* Actions */}
        <div className='flex gap-2'>
          <Button onClick={onLike} className='flex-1 gap-1.5'>
            <Heart size={14} strokeWidth={2.5} />
            Лайк
          </Button>
          <Button variant='secondary' onClick={onView} className='flex-1'>
            Посмотреть
          </Button>
        </div>
      </div>
    </div>
  );
}
