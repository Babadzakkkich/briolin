import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { ChevronLeft, ChevronRight, Search, ShieldCheck } from 'lucide-react';
import { adminApi } from '@/entities/admin';
import type { AdminUser } from '@/entities/admin';
import type { UserRole } from '@/entities/account';
import { Loader } from '@/shared/uikit/Loader';
import { Button } from '@/shared/uikit/Button';
import { toast } from '@/shared/toast/toast';

const ROLE_LABELS: Record<UserRole, string> = {
  admin: 'Администратор',
  psychologist: 'Психолог',
  user: 'Пользователь',
};

const LIMIT = 20;

export function AdminUsersPage() {
  const navigate = useNavigate();
  const [users, setUsers] = useState<AdminUser[]>([]);
  const [total, setTotal] = useState(0);
  const [skip, setSkip] = useState(0);
  const [roleFilter, setRoleFilter] = useState<UserRole | 'all'>('all');
  const [loading, setLoading] = useState(true);
  const [query, setQuery] = useState('');
  const [searching, setSearching] = useState(false);

  useEffect(() => {
    setLoading(true);
    const request =
      roleFilter === 'all'
        ? adminApi.listUsers({ skip, limit: LIMIT })
        : adminApi.listByRole(roleFilter, { skip, limit: LIMIT });

    request
      .then((data) => {
        setUsers(data.users);
        setTotal(data.total);
      })
      .catch(() => toast.error('Не удалось загрузить пользователей'))
      .finally(() => setLoading(false));
  }, [skip, roleFilter]);

  async function handleSearch(e: React.SyntheticEvent<HTMLFormElement>) {
    e.preventDefault();
    const trimmed = query.trim();
    if (!trimmed) return;
    setSearching(true);
    try {
      const user = trimmed.includes('@')
        ? await adminApi.getUserByEmail(trimmed)
        : await adminApi.getUserByUsername(trimmed);
      navigate(`/dashboard/admin/users/${user.keycloak_id}`);
    } catch {
      toast.error('Пользователь не найден');
    } finally {
      setSearching(false);
    }
  }

  function formatDate(dateStr: string) {
    return new Date(dateStr).toLocaleDateString('ru-RU', { day: '2-digit', month: '2-digit', year: 'numeric' });
  }

  return (
    <div className='flex-1 overflow-y-auto px-8 py-10'>
      <div className='mx-auto max-w-5xl'>
        <h1 className='font-onest text-primary mb-6 flex items-center gap-2 text-3xl font-medium'>
          <ShieldCheck className='text-accent' size={28} />
          Админка
        </h1>

        <div className='mb-5 flex flex-wrap items-center gap-3'>
          <form onSubmit={handleSearch} className='flex flex-1 min-w-[240px] items-center gap-2'>
            <div className='relative flex-1'>
              <Search size={14} className='text-muted pointer-events-none absolute top-1/2 left-3 -translate-y-1/2' />
              <input
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder='Поиск по username или email...'
                className='border-border focus:border-accent font-inter text-primary placeholder:text-muted w-full rounded-xl border bg-white py-2.5 pr-3 pl-8 text-[14px] transition-colors outline-none'
              />
            </div>
            <Button type='submit' size='sm' disabled={searching}>
              {searching ? 'Ищем...' : 'Найти'}
            </Button>
          </form>
          <select
            value={roleFilter}
            onChange={(e) => {
              setRoleFilter(e.target.value as UserRole | 'all');
              setSkip(0);
            }}
            className='border-border font-inter text-primary rounded-xl border bg-white px-3 py-2.5 text-[13px] outline-none'
          >
            <option value='all'>Все роли</option>
            <option value='admin'>Администраторы</option>
            <option value='psychologist'>Психологи</option>
            <option value='user'>Пользователи</option>
          </select>
        </div>

        <div className='overflow-hidden rounded-2xl bg-white'>
          {loading ? (
            <Loader center label='Загружаем пользователей...' />
          ) : users.length === 0 ? (
            <p className='text-secondary p-8 text-center text-[13px]'>Пользователи не найдены</p>
          ) : (
            <table className='w-full text-left text-[13px]'>
              <thead>
                <tr className='border-b border-[#F0E9E0] text-[11px] text-muted'>
                  <th className='px-5 py-3 font-medium'>Username</th>
                  <th className='px-5 py-3 font-medium'>Email</th>
                  <th className='px-5 py-3 font-medium'>Роли</th>
                  <th className='px-5 py-3 font-medium'>Статус</th>
                  <th className='px-5 py-3 font-medium'>Регистрация</th>
                </tr>
              </thead>
              <tbody>
                {users.map((u) => (
                  <tr
                    key={u.keycloak_id}
                    onClick={() => navigate(`/dashboard/admin/users/${u.keycloak_id}`)}
                    className='hover:bg-surface cursor-pointer border-b border-[#F0E9E0] last:border-0'
                  >
                    <td className='text-primary px-5 py-3 font-medium'>{u.username}</td>
                    <td className='text-secondary px-5 py-3'>{u.email}</td>
                    <td className='px-5 py-3'>
                      <div className='flex flex-wrap gap-1'>
                        {u.roles.map((role) => (
                          <span key={role} className='bg-accent/10 text-accent rounded-lg px-2 py-0.5 text-[11px]'>
                            {ROLE_LABELS[role]}
                          </span>
                        ))}
                      </div>
                    </td>
                    <td className='px-5 py-3'>
                      <span
                        className={[
                          'rounded-lg px-2 py-0.5 text-[11px] font-medium',
                          u.is_active ? 'bg-green-50 text-green-600' : 'bg-red-50 text-red-600',
                        ].join(' ')}
                      >
                        {u.is_active ? 'Активен' : 'Заблокирован'}
                      </span>
                    </td>
                    <td className='text-secondary px-5 py-3'>{formatDate(u.created_at)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>

        {!loading && total > LIMIT && (
          <div className='mt-4 flex items-center justify-center gap-3'>
            <Button
              variant='secondary'
              size='sm'
              disabled={skip === 0}
              onClick={() => setSkip((s) => Math.max(0, s - LIMIT))}
            >
              <ChevronLeft size={14} />
              Назад
            </Button>
            <span className='text-secondary text-[13px]'>
              {skip + 1}–{Math.min(skip + LIMIT, total)} из {total}
            </span>
            <Button
              variant='secondary'
              size='sm'
              disabled={skip + LIMIT >= total}
              onClick={() => setSkip((s) => s + LIMIT)}
            >
              Дальше
              <ChevronRight size={14} />
            </Button>
          </div>
        )}
      </div>
    </div>
  );
}
