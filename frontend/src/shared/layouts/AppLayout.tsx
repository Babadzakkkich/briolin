import { Link, Outlet } from 'react-router-dom';
import { LogoIcon } from '@/shared/icons/Logo';
import { Button } from '@/shared/uikit/Button';
import { ToastContainer } from '@/shared/toast/ToastContainer';

export function AppLayout() {
  return (
    <>
      <div className='bg-surface min-h-screen'>
        <header className='sticky top-0 backdrop-blur-sm'>
          <div className='mx-auto flex h-16 max-w-[1280px] items-center justify-between'>
            <Link to='/'>
              <div className='flex items-center gap-2'>
                <LogoIcon />
                <span className='font-onest text-primary text-xl font-medium'>Бриолин</span>
              </div>
            </Link>
            <div className='flex gap-2'>
              <Link to='/login'>
                <Button variant='primary' size='sm'>
                  Войти
                </Button>
              </Link>
              <Link to='/register'>
                <Button variant='secondary' size='sm'>
                  Регистрация
                </Button>
              </Link>
            </div>
          </div>
        </header>
        <main className='flex-1'>
          <div className='mx-auto flex min-h-[calc(100vh-10rem)] max-w-[1280px] items-center justify-center px-4'>
            <Outlet />
          </div>
        </main>
      </div>
      <ToastContainer />
    </>
  );
}
