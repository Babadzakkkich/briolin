import { MapPin, Heart } from 'lucide-react';
import { Button } from '@/shared/uikit/Button';
import { Avatar } from '@/shared/uikit/Avatar';
import type { ProfilePreview } from '../model/types';

interface ProfileCardProps {
  profile: ProfilePreview;
  onLike: () => void;
  onView: () => void;
}

export function ProfileCard({ profile, onLike, onView }: ProfileCardProps) {
  return (
    <div className='border-border hover:border-muted flex flex-col overflow-hidden rounded-2xl border bg-white transition-colors'>
      <div className='bg-surface relative aspect-square w-full overflow-hidden'>
        <Avatar
          name={`${profile.first_name} ${profile.last_name}`}
          shape='square'
          className='h-full w-full text-4xl'
        />
        {profile.online && (
          <span className='absolute top-3 right-3 h-2.5 w-2.5 rounded-full bg-green-400 ring-2 ring-white' />
        )}
      </div>
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
