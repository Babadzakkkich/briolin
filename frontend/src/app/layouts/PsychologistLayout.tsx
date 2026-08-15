import { BriefcaseBusiness, CalendarDays, LayoutDashboard, LogOut, UserRound } from 'lucide-react';
import { NavLink, Outlet, useNavigate } from 'react-router-dom';
import { useAuth } from '@/features/auth/useAuth';

const NAV = [
  { to: '/psychologist', label: 'Обзор', icon: LayoutDashboard, end: true },
  { to: '/psychologist/bookings', label: 'Записи', icon: CalendarDays },
  { to: '/psychologist/services', label: 'Услуги', icon: BriefcaseBusiness },
];

export function PsychologistLayout() {
  const navigate = useNavigate();
  const { logout } = useAuth();

  return (
    <div className='bg-surface min-h-screen md:flex'>
      <aside className='border-border hidden w-64 shrink-0 flex-col border-r bg-white p-5 md:flex'>
        <button
          onClick={() => navigate('/psychologist')}
          className='text-primary flex cursor-pointer items-center gap-3 px-2 py-3 text-left'
        >
          <span className='bg-accent flex h-10 w-10 items-center justify-center rounded-2xl text-white'>
            <UserRound size={20} />
          </span>
          <span>
            <strong className='font-onest block text-[16px]'>Бриолин</strong>
            <small className='text-secondary'>Кабинет психолога</small>
          </span>
        </button>
        <nav className='mt-8 flex flex-col gap-1'>
          {NAV.map(({ to, label, icon: Icon, end }) => (
            <NavLink
              key={to}
              to={to}
              end={end}
              className={({ isActive }) =>
                `flex items-center gap-3 rounded-xl px-4 py-3 text-[13px] transition-colors ${isActive ? 'bg-accent/10 text-accent' : 'text-secondary hover:bg-surface'}`
              }
            >
              <Icon size={18} /> {label}
            </NavLink>
          ))}
        </nav>
        <button
          onClick={logout}
          className='text-secondary hover:text-primary mt-auto flex cursor-pointer items-center gap-3 rounded-xl px-4 py-3 text-[13px]'
        >
          <LogOut size={17} /> Выйти
        </button>
      </aside>
      <div className='min-w-0 flex-1'>
        <header className='border-border sticky top-0 z-20 flex h-16 items-center gap-2 overflow-x-auto border-b bg-white px-4 md:hidden'>
          {NAV.map(({ to, label, end }) => (
            <NavLink
              key={to}
              to={to}
              end={end}
              className={({ isActive }) =>
                `rounded-xl px-3 py-2 text-[12px] whitespace-nowrap ${isActive ? 'bg-accent/10 text-accent' : 'text-secondary'}`
              }
            >
              {label}
            </NavLink>
          ))}
        </header>
        <Outlet />
      </div>
    </div>
  );
}
