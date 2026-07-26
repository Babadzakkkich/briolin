import { useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { ArrowLeft, Ban, CheckCircle2, RotateCcw, Trash2 } from 'lucide-react';
import { adminApi } from '@/entities/admin';
import type { AdminUser, AdminProfileResponse } from '@/entities/admin';
import type { UserRole } from '@/entities/account';
import { pollSaga } from '@/shared/api/saga';
import { Button } from '@/shared/uikit/Button';
import { Loader } from '@/shared/uikit/Loader';
import { ConfirmDialog } from '@/shared/uikit/ConfirmDialog';
import { toast } from '@/shared/toast/toast';

const ROLE_OPTIONS: { value: UserRole; label: string }[] = [
  { value: 'user', label: 'Пользователь' },
  { value: 'psychologist', label: 'Психолог' },
  { value: 'admin', label: 'Администратор' },
];

type ConfirmAction = 'delete-user' | 'delete-profile' | 'reset-matching' | null;

export function AdminUserDetailPage() {
  const { keycloakId } = useParams<{ keycloakId: string }>();
  const navigate = useNavigate();

  const [user, setUser] = useState<AdminUser | null>(null);
  const [profile, setProfile] = useState<AdminProfileResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [selectedRoles, setSelectedRoles] = useState<UserRole[]>([]);
  const [savingRoles, setSavingRoles] = useState(false);
  const [togglingStatus, setTogglingStatus] = useState(false);
  const [confirmAction, setConfirmAction] = useState<ConfirmAction>(null);
  const [busy, setBusy] = useState(false);

  function loadUser() {
    if (!keycloakId) return;
    return adminApi.getUserById(keycloakId).then((data) => {
      setUser(data);
      setSelectedRoles(data.roles);
    });
  }

  function loadProfile() {
    if (!keycloakId) return;
    adminApi
      .getUserProfile(keycloakId)
      .then(setProfile)
      .catch(() => setProfile(null));
  }

  useEffect(() => {
    Promise.resolve(loadUser())
      .catch(() => toast.error('Не удалось загрузить пользователя'))
      .finally(() => setLoading(false));
    loadProfile();
  }, [keycloakId]);

  function toggleRole(role: UserRole) {
    setSelectedRoles((prev) => (prev.includes(role) ? prev.filter((r) => r !== role) : [...prev, role]));
  }

  async function saveRoles() {
    if (!keycloakId) return;
    setSavingRoles(true);
    try {
      const { saga_id } = await adminApi.updateRoles(keycloakId, selectedRoles);
      const status = await pollSaga(() => adminApi.getUserSagaStatus(saga_id));
      if (status.status === 'completed') {
        await loadUser();
        toast.success('Роли обновлены');
      } else {
        toast.error(status.error ?? 'Не удалось обновить роли');
      }
    } catch {
      toast.error('Не удалось обновить роли');
    } finally {
      setSavingRoles(false);
    }
  }

  async function toggleStatus() {
    if (!keycloakId) return;
    setTogglingStatus(true);
    try {
      const { saga_id } = await adminApi.toggleStatus(keycloakId);
      const status = await pollSaga(() => adminApi.getUserSagaStatus(saga_id));
      if (status.status === 'completed') {
        await loadUser();
        toast.success('Статус пользователя изменён');
      } else {
        toast.error(status.error ?? 'Не удалось изменить статус');
      }
    } catch {
      toast.error('Не удалось изменить статус');
    } finally {
      setTogglingStatus(false);
    }
  }

  async function handleDeleteUser() {
    if (!keycloakId) return;
    setBusy(true);
    try {
      const { saga_id } = await adminApi.deleteUser(keycloakId);
      const status = await pollSaga(() => adminApi.getUserSagaStatus(saga_id));
      if (status.status === 'completed') {
        toast.success('Пользователь удалён');
        navigate('/dashboard/admin');
      } else {
        toast.error(status.error ?? 'Не удалось удалить пользователя');
      }
    } catch {
      toast.error('Не удалось удалить пользователя');
    } finally {
      setBusy(false);
      setConfirmAction(null);
    }
  }

  async function handleDeleteProfile() {
    if (!keycloakId) return;
    setBusy(true);
    try {
      const { saga_id } = await adminApi.deleteUserProfile(keycloakId);
      const status = await pollSaga(() => adminApi.getProfileSagaStatus(saga_id));
      if (status.status === 'completed') {
        setProfile(null);
        toast.success('Анкета удалена');
      } else {
        toast.error(status.error ?? 'Не удалось удалить анкету');
      }
    } catch {
      toast.error('Не удалось удалить анкету');
    } finally {
      setBusy(false);
      setConfirmAction(null);
    }
  }

  async function handleResetMatching() {
    if (!keycloakId) return;
    setBusy(true);
    try {
      const { swipes_deleted } = await adminApi.resetUserMatching(keycloakId);
      toast.success(`Сброшено лайков: ${swipes_deleted}`);
    } catch {
      toast.error('Не удалось сбросить мэтчинг');
    } finally {
      setBusy(false);
      setConfirmAction(null);
    }
  }

  if (loading) return <Loader center label='Загружаем пользователя...' />;
  if (!user) {
    return (
      <div className='flex flex-1 items-center justify-center'>
        <p className='text-muted text-[14px]'>Пользователь не найден</p>
      </div>
    );
  }

  const rolesChanged =
    selectedRoles.length !== user.roles.length || selectedRoles.some((r) => !user.roles.includes(r));

  return (
    <div className='flex-1 overflow-y-auto px-8 py-10'>
      <div className='mx-auto max-w-2xl'>
        <button
          onClick={() => navigate('/dashboard/admin')}
          className='text-secondary hover:text-primary mb-6 flex cursor-pointer items-center gap-1.5 text-[13px] transition-colors'
        >
          <ArrowLeft size={15} />
          К списку пользователей
        </button>

        <div className='flex flex-col gap-4'>
          <div className='rounded-2xl bg-white p-6'>
            <h2 className='font-onest text-primary mb-4 text-[18px] font-medium'>{user.username}</h2>
            <p className='text-secondary mb-5 text-[13px]'>{user.email}</p>

            <div className='mb-5 flex flex-col gap-2'>
              <p className='text-muted text-[11px] font-medium'>Роли</p>
              <div className='flex flex-wrap gap-2'>
                {ROLE_OPTIONS.map(({ value, label }) => (
                  <button
                    key={value}
                    onClick={() => toggleRole(value)}
                    className={[
                      'cursor-pointer rounded-xl border px-3 py-1.5 text-[13px] transition-colors',
                      selectedRoles.includes(value)
                        ? 'border-accent bg-accent/15 text-accent'
                        : 'border-border text-secondary hover:bg-surface',
                    ].join(' ')}
                  >
                    {label}
                  </button>
                ))}
              </div>
              {rolesChanged && (
                <Button size='sm' onClick={saveRoles} disabled={savingRoles} className='mt-2 self-start'>
                  {savingRoles ? 'Сохранение...' : 'Сохранить роли'}
                </Button>
              )}
            </div>

            <div className='flex flex-wrap gap-2 border-t border-[#F0E9E0] pt-5'>
              <Button
                variant='secondary'
                size='sm'
                onClick={toggleStatus}
                disabled={togglingStatus}
              >
                {user.is_active ? <Ban size={14} /> : <CheckCircle2 size={14} />}
                {user.is_active ? 'Заблокировать' : 'Разблокировать'}
              </Button>
              <Button variant='destructive' size='sm' onClick={() => setConfirmAction('delete-user')}>
                <Trash2 size={14} />
                Удалить пользователя
              </Button>
            </div>
          </div>

          <div className='rounded-2xl bg-white p-6'>
            <h2 className='font-onest text-primary mb-4 text-[18px] font-medium'>Анкета</h2>
            {profile ? (
              <div className='flex flex-col gap-3'>
                <p className='text-primary text-[14px]'>
                  {profile.basic.first_name} {profile.basic.last_name}, {profile.basic.city}
                </p>
                <Button
                  variant='destructive'
                  size='sm'
                  onClick={() => setConfirmAction('delete-profile')}
                  className='self-start'
                >
                  <Trash2 size={14} />
                  Удалить анкету
                </Button>
              </div>
            ) : (
              <p className='text-secondary text-[13px]'>Анкета не заполнена</p>
            )}
          </div>

          <div className='rounded-2xl bg-white p-6'>
            <h2 className='font-onest text-primary mb-4 text-[18px] font-medium'>Мэтчинг</h2>
            <Button variant='destructive' size='sm' onClick={() => setConfirmAction('reset-matching')}>
              <RotateCcw size={14} />
              Сбросить лайки и мэтчинг
            </Button>
          </div>
        </div>
      </div>

      {confirmAction === 'delete-user' && (
        <ConfirmDialog
          title='Удалить пользователя?'
          description='Аккаунт, анкета и доступ к приложению будут удалены безвозвратно.'
          confirmLabel='Удалить'
          destructive
          loading={busy}
          onConfirm={handleDeleteUser}
          onClose={() => setConfirmAction(null)}
        />
      )}
      {confirmAction === 'delete-profile' && (
        <ConfirmDialog
          title='Удалить анкету пользователя?'
          confirmLabel='Удалить'
          destructive
          loading={busy}
          onConfirm={handleDeleteProfile}
          onClose={() => setConfirmAction(null)}
        />
      )}
      {confirmAction === 'reset-matching' && (
        <ConfirmDialog
          title='Сбросить лайки и мэтчинг?'
          description='Все лайки, дизлайки и блокировки поиска этого пользователя будут удалены.'
          confirmLabel='Сбросить'
          destructive
          loading={busy}
          onConfirm={handleResetMatching}
          onClose={() => setConfirmAction(null)}
        />
      )}
    </div>
  );
}
