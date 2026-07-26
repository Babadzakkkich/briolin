import { forwardRef, useImperativeHandle, useRef, useState } from 'react';
import { MapPin, Info } from 'lucide-react';
import { AuthImage } from '@/shared/uikit/AuthImage';
import type { ProfilePreview } from '@/entities/search';

const SWIPE_THRESHOLD = 110;
const FLY_DISTANCE = 700;

export type SwipeDirection = 'left' | 'right';

export interface SwipeCardHandle {
  swipe: (direction: SwipeDirection) => void;
}

interface SwipeCardProps {
  profile: ProfilePreview;
  active: boolean;
  stackIndex: number;
  onSwiped: (direction: SwipeDirection, profile: ProfilePreview) => void;
  onInfo: () => void;
}

function AvatarPlaceholder({ name }: { name: string }) {
  const initials = name
    .split(' ')
    .slice(0, 2)
    .map((w) => w[0] ?? '')
    .join('')
    .toUpperCase();
  return (
    <div className='bg-accent/15 text-accent flex h-full w-full items-center justify-center text-5xl font-semibold'>
      {initials || '?'}
    </div>
  );
}

export const SwipeCard = forwardRef<SwipeCardHandle, SwipeCardProps>(function SwipeCard(
  { profile, active, stackIndex, onSwiped, onInfo },
  ref,
) {
  const [drag, setDrag] = useState({ x: 0, y: 0 });
  const [dragging, setDragging] = useState(false);
  const [flying, setFlying] = useState<SwipeDirection | null>(null);
  const pointerId = useRef<number | null>(null);
  const start = useRef({ x: 0, y: 0 });

  function flyAway(direction: SwipeDirection) {
    const sign = direction === 'right' ? 1 : -1;
    setFlying(direction);
    setDrag((d) => ({ x: sign * FLY_DISTANCE, y: d.y }));
    setTimeout(() => onSwiped(direction, profile), 220);
  }

  useImperativeHandle(ref, () => ({
    swipe: (direction) => {
      if (flying) return;
      flyAway(direction);
    },
  }));

  function handlePointerDown(e: React.PointerEvent) {
    if (!active || flying) return;
    pointerId.current = e.pointerId;
    start.current = { x: e.clientX, y: e.clientY };
    setDragging(true);
    e.currentTarget.setPointerCapture(e.pointerId);
  }

  function handlePointerMove(e: React.PointerEvent) {
    if (!dragging || pointerId.current !== e.pointerId) return;
    setDrag({
      x: e.clientX - start.current.x,
      y: (e.clientY - start.current.y) * 0.4,
    });
  }

  function handlePointerUp(e: React.PointerEvent) {
    if (!dragging || pointerId.current !== e.pointerId) return;
    setDragging(false);
    pointerId.current = null;
    if (Math.abs(drag.x) > SWIPE_THRESHOLD) {
      flyAway(drag.x > 0 ? 'right' : 'left');
    } else {
      setDrag({ x: 0, y: 0 });
    }
  }

  const rotation = drag.x / 18;
  const likeOpacity = Math.min(Math.max(drag.x / SWIPE_THRESHOLD, 0), 1);
  const skipOpacity = Math.min(Math.max(-drag.x / SWIPE_THRESHOLD, 0), 1);

  const transform = active
    ? `translate(${drag.x}px, ${drag.y}px) rotate(${rotation}deg)`
    : `translateY(${stackIndex * 10}px) scale(${1 - stackIndex * 0.05})`;

  return (
    <div
      onPointerDown={handlePointerDown}
      onPointerMove={handlePointerMove}
      onPointerUp={handlePointerUp}
      onPointerCancel={handlePointerUp}
      className={[
        'border-border absolute inset-0 touch-none overflow-hidden rounded-3xl border bg-white select-none',
        active ? 'cursor-grab active:cursor-grabbing' : 'pointer-events-none',
      ].join(' ')}
      style={{
        transform,
        transition: dragging ? 'none' : 'transform 320ms ease',
        opacity: flying ? 0 : 1,
        zIndex: 10 - stackIndex,
      }}
    >
      <div className='relative h-[62%] w-full shrink-0 overflow-hidden'>
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

        <div className='absolute inset-x-0 bottom-0 h-28 bg-gradient-to-t from-black/60 to-transparent' />

        <div className='absolute inset-x-4 bottom-3 flex items-end justify-between gap-2'>
          <div className='text-white'>
            <p className='font-onest text-[22px] font-medium'>
              {profile.display_name}, {profile.age}
            </p>
            <p className='mt-0.5 flex items-center gap-1 text-[13px] text-white/90'>
              <MapPin size={12} className='shrink-0' />
              {profile.city}
              {profile.online && (
                <span className='ml-1.5 inline-flex items-center gap-1 text-[12px] text-green-300'>
                  <span className='h-1.5 w-1.5 rounded-full bg-green-400' />
                  онлайн
                </span>
              )}
            </p>
          </div>
          <button
            onClick={(e) => {
              e.stopPropagation();
              onInfo();
            }}
            className='flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-white/20 text-white backdrop-blur-sm transition-colors hover:bg-white/30'
          >
            <Info size={16} />
          </button>
        </div>

        {active && (
          <>
            <div
              style={{ opacity: likeOpacity }}
              className='absolute top-7 left-5 -rotate-12 rounded-xl bg-white/10 px-3 py-1 text-xl font-bold text-green-400 backdrop-blur-sm'
            >
              ЛАЙК
            </div>
            <div
              style={{ opacity: skipOpacity }}
              className='absolute top-7 right-5 rotate-12 rounded-xl bg-white/10 px-3 py-1 text-xl font-bold text-red-400 backdrop-blur-sm'
            >
              НЕТ
            </div>
          </>
        )}
      </div>

      <div className='flex h-[38%] flex-col gap-3 overflow-y-auto p-4'>
        {profile.about_me && (
          <p className='text-secondary text-[13px] leading-relaxed'>{profile.about_me}</p>
        )}
        {(profile.hobbies || profile.education) && (
          <div className='flex flex-wrap gap-1.5'>
            {profile.hobbies && (
              <span className='bg-surface text-secondary rounded-lg px-2.5 py-1 text-[12px]'>
                {profile.hobbies}
              </span>
            )}
            {profile.education && (
              <span className='bg-surface text-secondary rounded-lg px-2.5 py-1 text-[12px]'>
                {profile.education}
              </span>
            )}
          </div>
        )}
      </div>
    </div>
  );
});
