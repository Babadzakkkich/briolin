import { useEffect, useState } from 'react';
import { useLocation, useNavigate, useParams } from 'react-router-dom';
import {
  MapPin,
  Calendar,
  GraduationCap,
  Heart,
  MessageCircle,
  ArrowLeft,
  Wifi,
} from 'lucide-react';
import { chatApi } from '@/entities/chat';
import { profileApi } from '@/entities/profile';
import { Button } from '@/shared/uikit/Button';
import { toast } from '@/shared/toast/toast';
import type { ProfilePreview } from '@/entities/search';

function getInitials(first: string, last: string) {
  return `${first[0] ?? ''}${last[0] ?? ''}`.toUpperCase();
}

function InfoBlock({
  icon,
  label,
  value,
}: {
  icon: React.ReactNode;
  label: string;
  value: string;
}) {
  return (
    <div className='flex items-start gap-3'>
      <div className='bg-surface mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-xl'>
        {icon}
      </div>
      <div>
        <p className='text-muted text-[11px] font-medium tracking-wide uppercase'>{label}</p>
        <p className='text-primary mt-0.5 text-[14px] leading-relaxed'>{value}</p>
      </div>
    </div>
  );
}

function Skeleton() {
  return (
    <div className='mx-auto max-w-2xl animate-pulse'>
      <div className='mb-4 rounded-2xl bg-white p-6'>
        <div className='flex items-center gap-5'>
          <div className='bg-surface h-20 w-20 rounded-2xl' />
          <div className='flex-1 space-y-2'>
            <div className='bg-surface h-5 w-48 rounded' />
            <div className='bg-surface h-4 w-28 rounded' />
          </div>
        </div>
        <div className='mt-5 flex gap-2 border-t border-[#F0E9E0] pt-5'>
          <div className='bg-surface h-9 flex-1 rounded-xl' />
          <div className='bg-surface h-9 flex-1 rounded-xl' />
        </div>
      </div>
      <div className='rounded-2xl bg-white p-6'>
        <div className='bg-surface mb-5 h-4 w-32 rounded' />
        <div className='flex flex-col gap-5'>
          {[80, 60, 100].map((w, i) => (
            <div key={i} className='flex gap-3'>
              <div className='bg-surface h-8 w-8 rounded-xl' />
              <div className='flex-1 space-y-1.5'>
                <div className='bg-surface h-2.5 w-16 rounded' />
                <div className={`bg-surface h-3.5 rounded`} style={{ width: `${w}%` }} />
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

export function UserProfilePage() {
  const { keycloakId } = useParams<{ keycloakId: string }>();
  const location = useLocation();
  const navigate = useNavigate();

  const stateProfile = location.state?.profile as ProfilePreview | undefined;
  const [profile, setProfile] = useState<ProfilePreview | null>(stateProfile ?? null);
  const [loading, setLoading] = useState(!stateProfile);
  const [starting, setStarting] = useState(false);

  useEffect(() => {
    if (stateProfile) return;
    if (!keycloakId || keycloakId === 'undefined') {
      setLoading(false);
      return;
    }
    profileApi
      .getByKeycloakId(keycloakId)
      .then((res) => {
        const { basic, detailed } = res.data;
        setProfile({
          keycloak_id: keycloakId,
          first_name: basic.first_name,
          last_name: basic.last_name,
          gender: basic.gender,
          age: calculateAge(basic.date_of_birth),
          city: basic.city,
          online: basic.online ?? false,
          education: detailed?.education ?? null,
          hobbies: detailed?.hobbies ?? null,
          about_me: detailed?.about_me ?? null,
          partner_preferences: detailed?.partner_preferences ?? null,
        });
      })
      .catch(() => toast.error('Не удалось загрузить профиль'))
      .finally(() => setLoading(false));
  }, [keycloakId, stateProfile]);

  const handleMessage = async () => {
    if (!profile?.keycloak_id || profile.keycloak_id === 'undefined') {
      toast.error('Не удалось определить пользователя');
      return;
    }
    setStarting(true);
    try {
      const chat = await chatApi.createDirectChat(profile.keycloak_id);
      navigate('/dashboard/messages', { state: { chatId: chat.id } });
    } catch {
      toast.error('Не удалось создать чат');
    } finally {
      setStarting(false);
    }
  };

  if (loading) {
    return (
      <div className='flex-1 overflow-y-auto px-8 py-8'>
        <div className='bg-surface mx-auto mb-6 h-5 w-16 max-w-2xl animate-pulse rounded' />
        <Skeleton />
      </div>
    );
  }

  if (!profile || keycloakId === 'undefined') {
    return (
      <div className='flex flex-1 items-center justify-center'>
        <div className='text-center'>
          <p className='text-primary text-[15px] font-medium'>Профиль не найден</p>
          <button
            onClick={() => navigate(-1)}
            className='text-accent mt-2 cursor-pointer text-[13px] hover:underline'
          >
            Вернуться назад
          </button>
        </div>
      </div>
    );
  }

  const hobbies = profile.hobbies
    ? profile.hobbies
        .split(',')
        .map((h) => h.trim())
        .filter(Boolean)
    : [];

  const effectiveKeycloakId = profile.keycloak_id || keycloakId;

  return (
    <div className='flex-1 overflow-y-auto px-8 py-8'>
      <div className='mx-auto max-w-2xl'>
        <button
          onClick={() => navigate(-1)}
          className='text-secondary hover:text-primary mb-6 flex cursor-pointer items-center gap-1.5 text-[13px] transition-colors'
        >
          <ArrowLeft size={15} />
          Назад
        </button>
        <div className='mb-4 rounded-2xl bg-white p-6'>
          <div className='flex items-center gap-5'>
            <div className='bg-accent/15 text-accent flex h-20 w-20 shrink-0 items-center justify-center rounded-2xl text-2xl font-semibold'>
              {getInitials(profile.first_name, profile.last_name)}
            </div>
            <div className='min-w-0 flex-1'>
              <div className='flex items-center gap-2'>
                <h1 className='font-onest text-primary text-2xl font-medium'>
                  {profile.first_name} {profile.last_name}, {profile.age}
                </h1>
                {profile.online && (
                  <span className='flex items-center gap-1 rounded-full bg-green-50 px-2 py-0.5 text-[12px] font-medium text-green-600'>
                    <Wifi size={11} />
                    онлайн
                  </span>
                )}
              </div>
              <p className='text-secondary mt-1 flex items-center gap-1 text-[14px]'>
                <MapPin size={13} className='shrink-0' />
                {profile.city}
              </p>
            </div>
          </div>

          <div className='mt-5 flex gap-2 border-t border-[#F0E9E0] pt-5'>
            <Button
              onClick={handleMessage}
              disabled={starting || !effectiveKeycloakId}
              className='flex-1'
            >
              <MessageCircle size={15} />
              {starting ? 'Открываем...' : 'Написать'}
            </Button>
            <Button
              variant='secondary'
              onClick={() => toast.info('Функция в разработке')}
              className='flex-1'
            >
              <Heart size={15} />
              Лайк
            </Button>
          </div>
        </div>
        <div className='rounded-2xl bg-white p-6'>
          <h2 className='font-onest text-primary mb-5 text-[16px] font-medium'>О человеке</h2>
          <div className='flex flex-col gap-5'>
            {profile.about_me && (
              <InfoBlock
                icon={<MessageCircle size={15} className='text-accent' />}
                label='О себе'
                value={profile.about_me}
              />
            )}
            {profile.education && (
              <InfoBlock
                icon={<GraduationCap size={15} className='text-accent' />}
                label='Образование'
                value={profile.education}
              />
            )}
            {profile.partner_preferences && (
              <InfoBlock
                icon={<Heart size={15} className='text-accent' />}
                label='Ищет партнёра'
                value={profile.partner_preferences}
              />
            )}
            {hobbies.length > 0 && (
              <div className='flex items-start gap-3'>
                <div className='bg-surface mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-xl'>
                  <Calendar size={15} className='text-accent' />
                </div>
                <div>
                  <p className='text-muted text-[11px] font-medium tracking-wide uppercase'>
                    Интересы
                  </p>
                  <div className='mt-2 flex flex-wrap gap-1.5'>
                    {hobbies.map((h, i) => (
                      <span
                        key={i}
                        className='bg-surface text-secondary rounded-xl px-3 py-1.5 text-[13px]'
                      >
                        {h}
                      </span>
                    ))}
                  </div>
                </div>
              </div>
            )}
            {!profile.about_me &&
              !profile.education &&
              !profile.partner_preferences &&
              hobbies.length === 0 && (
                <p className='text-muted text-[14px]'>Информация не заполнена</p>
              )}
          </div>
        </div>
      </div>
    </div>
  );
}

function calculateAge(dateOfBirth?: string | null): number {
  if (!dateOfBirth) return 0;
  const birth = new Date(dateOfBirth);
  const today = new Date();
  let age = today.getFullYear() - birth.getFullYear();
  const m = today.getMonth() - birth.getMonth();
  if (m < 0 || (m === 0 && today.getDate() < birth.getDate())) age--;
  return age;
}
