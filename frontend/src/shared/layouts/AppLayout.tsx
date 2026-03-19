import { Link, Outlet } from 'react-router-dom';
import { LogoIcon } from '@/shared/icons/Logo';

export function AppLayout() {
    return (
        <>
            <div className='bg-surface min-h-screen'>
                <header className='sticky top-0 backdrop-blur-sm'>
                    <div className='mx-auto flex h-16 max-w-[1280px] items-center'>
                        <Link to='/'>
                            <div className='flex items-center gap-2'>
                                <LogoIcon />
                                <span className='font-onest text-primary text-xl font-medium'>
                                    Бриолин
                                </span>
                            </div>
                        </Link>
                    </div>
                </header>
                <main className='flex-1'>
                    <div className='mx-auto flex min-h-[calc(100vh-10rem)] max-w-[1280px] items-center justify-center px-4'>
                        <Outlet />
                    </div>
                </main>
            </div>
        </>
    );
}
