import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { z } from 'zod';
import { ShieldCheck } from 'lucide-react';
import { accountApi, useAccountStore } from '@/entities/account';
import type { UserRole } from '@/entities/account';
import { profileApi, useProfileStore } from '@/entities/profile';
import { useAuthStore } from '@/entities/session';
import { pollSaga } from '@/shared/api/saga';
import { SectionHeader } from '@/features/profile/ui/SectionHeader';
import { Input } from '@/shared/uikit/Input';
import { Button } from '@/shared/uikit/Button';
import { Loader } from '@/shared/uikit/Loader';
import { ConfirmDialog } from '@/shared/uikit/ConfirmDialog';
import { toast } from '@/shared/toast/toast';

const ROLE_LABELS: Record<UserRole, string> = {
  admin: 'Администратор',
  psychologist: 'Психолог',
  user: 'Пользователь',
};

const accountSchema = z.object({
  username: z.string().min(3, 'Минимум 3 символа').max(50),
  email: z.email('Введите корректный email'),
});

type AccountErrors = Partial<Record<'username' | 'email', string>>;

function formatDate(dateStr: string) {
  return new Date(dateStr).toLocaleDateString('ru-RU', {
    day: 'numeric',
    month: 'long',
    year: 'numeric',
  });
}

export function SettingsPage() {
  const keycloakId = useAuthStore((s) => s.keycloakId);
  const { username, email, roles, createdAt, loaded, setAccount, clear: clearAccount } = useAccountStore();
  const { clear: clearProfile } = useProfileStore();
  const { clear: clearAuth } = useAuthStore();
  const navigate = useNavigate();

  const [loading, setLoading] = useState(!loaded);
  const [editing, setEditing] = useState(false);
  const [saving, setSaving] = useState(false);
  const [usernameField, setUsernameField] = useState('');
  const [emailField, setEmailField] = useState('');
  const [errors, setErrors] = useState<AccountErrors>({});

  const [confirmAction, setConfirmAction] = useState<'profile' | 'account' | null>(null);
  const [deleting, setDeleting] = useState(false);

  useEffect(() => {
    accountApi
      .getMe()
      .then(({ data }) => setAccount(data))
      .catch(() => toast.error('Не удалось загрузить аккаунт'))
      .finally(() => setLoading(false));
  }, []);

  function startEdit() {
    setUsernameField(username ?? '');
    setEmailField(email ?? '');
    setErrors({});
    setEditing(true);
  }

  function cancelEdit() {
    setErrors({});
    setEditing(false);
  }

  async function saveAccount() {
    const result = accountSchema.safeParse({ username: usernameField, email: emailField });
    if (!result.success) {
      const errs: AccountErrors = {};
      result.error.issues.forEach((e) => {
        errs[e.path[0] as keyof AccountErrors] = e.message;
      });
      setErrors(errs);
      return;
    }
    if (!keycloakId) return;
    setErrors({});
    setSaving(true);
    try {
      const { data } = await accountApi.updateMe(keycloakId, {
        username: usernameField,
        email: emailField,
      });
      const status = await pollSaga(() => accountApi.getSagaStatus(data.saga_id).then((r) => r.data));
      if (status.status === 'completed') {
        const refreshed = await accountApi.getMe();
        setAccount(refreshed.data);
        toast.success('Аккаунт обновлён');
        setEditing(false);
      } else {
        toast.error(status.error ?? 'Не удалось обновить аккаунт');
      }
    } catch {
      toast.error('Не удалось обновить аккаунт');
    } finally {
      setSaving(false);
    }
  }

  async function handleDeleteProfile() {
    setDeleting(true);
    try {
      const { data } = await profileApi.deleteProfile();
      const status = await pollSaga(() => profileApi.getSagaStatus(data.saga_id).then((r) => r.data));
      if (status.status === 'completed') {
        clearProfile();
        toast.success('Анкета удалена');
        navigate('/onboarding', { state: { step: 0 } });
      } else {
        toast.error(status.error ?? 'Не удалось удалить анкету');
      }
    } catch {
      toast.error('Не удалось удалить анкету');
    } finally {
      setDeleting(false);
      setConfirmAction(null);
    }
  }

  async function handleDeleteAccount() {
    if (!keycloakId) return;
    setDeleting(true);
    try {
      const { data } = await accountApi.deleteMe(keycloakId);
      const status = await pollSaga(() => accountApi.getSagaStatus(data.saga_id).then((r) => r.data));
      if (status.status === 'completed') {
        clearAuth();
        clearProfile();
        clearAccount();
        navigate('/login');
        toast.success('Аккаунт удалён');
      } else {
        toast.error(status.error ?? 'Не удалось удалить аккаунт');
      }
    } catch {
      toast.error('Не удалось удалить аккаунт');
    } finally {
      setDeleting(false);
      setConfirmAction(null);
    }
  }

  if (loading) return <Loader center label='Загружаем настройки...' />;

  return (
    <div className='flex-1 overflow-y-auto px-8 py-10'>
      <div className='mx-auto max-w-3xl'>
        <h1 className='font-onest text-primary mb-8 text-3xl font-medium'>Настройки</h1>

        <div className='flex flex-col gap-4'>
          <div className='rounded-2xl bg-white p-6'>
            <SectionHeader
              title='Аккаунт'
              editing={editing}
              saving={saving}
              onEdit={startEdit}
              onSave={saveAccount}
              onCancel={cancelEdit}
            />

            {!editing ? (
              <div className='flex flex-col gap-4'>
                <div className='grid grid-cols-2 gap-4'>
                  <div>
                    <p className='text-muted text-[11px] font-medium'>Логин</p>
                    <p className='text-primary mt-0.5 text-[14px] font-medium'>{username}</p>
                  </div>
                  <div>
                    <p className='text-muted text-[11px] font-medium'>Email</p>
                    <p className='text-primary mt-0.5 text-[14px] font-medium'>{email}</p>
                  </div>
                  {createdAt && (
                    <div>
                      <p className='text-muted text-[11px] font-medium'>Дата регистрации</p>
                      <p className='text-primary mt-0.5 text-[14px] font-medium'>{formatDate(createdAt)}</p>
                    </div>
                  )}
                </div>
                <div className='flex items-center gap-1.5'>
                  {roles.map((role) => (
                    <span
                      key={role}
                      className='bg-accent/10 text-accent inline-flex items-center gap-1 rounded-xl px-3 py-1.5 text-[12px] font-medium'
                    >
                      <ShieldCheck size={12} />
                      {ROLE_LABELS[role]}
                    </span>
                  ))}
                </div>
              </div>
            ) : (
              <div className='grid grid-cols-2 gap-4'>
                <Input
                  label='Логин'
                  value={usernameField}
                  error={errors.username}
                  onChange={(e) => {
                    setUsernameField(e.target.value);
                    setErrors((p) => ({ ...p, username: undefined }));
                  }}
                />
                <Input
                  label='Email'
                  value={emailField}
                  error={errors.email}
                  onChange={(e) => {
                    setEmailField(e.target.value);
                    setErrors((p) => ({ ...p, email: undefined }));
                  }}
                />
              </div>
            )}
          </div>

          <div className='rounded-2xl border border-red-200 bg-red-50/40 p-6'>
            <h2 className='font-onest text-[18px] font-medium text-red-600'>Опасная зона</h2>
            <p className='text-secondary mt-1 text-[13px]'>
              Эти действия нельзя отменить.
            </p>
            <div className='mt-5 flex flex-wrap gap-3'>
              <Button variant='destructive' size='sm' onClick={() => setConfirmAction('profile')}>
                Удалить анкету
              </Button>
              <Button variant='destructive' size='sm' onClick={() => setConfirmAction('account')}>
                Удалить аккаунт
              </Button>
            </div>
          </div>
        </div>
      </div>

      {confirmAction === 'profile' && (
        <ConfirmDialog
          title='Удалить анкету?'
          description='Анкета знакомств (основная информация, описание, вопросы и аватарки) будет удалена. Аккаунт и доступ к приложению останутся — анкету можно будет заполнить заново.'
          confirmLabel='Удалить анкету'
          destructive
          loading={deleting}
          onConfirm={handleDeleteProfile}
          onClose={() => setConfirmAction(null)}
        />
      )}

      {confirmAction === 'account' && (
        <ConfirmDialog
          title='Удалить аккаунт?'
          description='Аккаунт, анкета и доступ к приложению будут удалены безвозвратно. Вы будете разлогинены.'
          confirmLabel='Удалить аккаунт'
          destructive
          loading={deleting}
          onConfirm={handleDeleteAccount}
          onClose={() => setConfirmAction(null)}
        />
      )}
    </div>
  );
}
