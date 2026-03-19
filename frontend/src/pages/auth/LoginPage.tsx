import { Button } from '@/shared/uikit/Button';
import { Input } from '@/shared/uikit/Input';
import { Text } from '@/shared/uikit/Text';
import { Link } from 'react-router-dom';

export function LoginPage() {
    return (
        <>
            <div className='border-border flex w-100 flex-col gap-8 rounded-lg border bg-white px-8 py-8'>
                <div className='flex flex-col text-center'>
                    <Text variant='h2' as='h2'>
                        Вход
                    </Text>
                    <Text variant='p' as='p'>
                        Бла бла бла
                    </Text>
                </div>
                <div className='flex w-full flex-col gap-4'>
                    <Input label='Логин/Почта' placeholder='Введите логин или почту' />
                    <div className='flex flex-col gap-1.5'>
                        <div className='flex items-center justify-between'>
                            <span className='font-inter text-muted text-[12px] font-medium'>
                                Пароль
                            </span>
                            <Link
                                to='/forgot-password'
                                className='font-inter text-secondary hover:text-accent text-[12px] transition-colors'
                            >
                                Забыли пароль?
                            </Link>
                        </div>
                        <Input placeholder='Введите пароль' type='password' />
                    </div>
                </div>
                <div className='flex flex-col gap-4 text-center'>
                    <Button>Войти</Button>
                    <div className='flex flex-col'>
                        <Text variant='p-sm'>Еще нет аккаунта?</Text>
                        <Link to='/registration'>
                            <Text className='text-accent! underline' variant='p-sm'>
                                Зарегистрироваться
                            </Text>
                        </Link>
                    </div>
                </div>
            </div>
        </>
    );
}
