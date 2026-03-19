import { Button } from '@/shared/uikit/Button';
import { Input } from '@/shared/uikit/Input';
import { Text } from '@/shared/uikit/Text';
import { Link } from 'react-router-dom';

export function RegistrationPage() {
    return (
        <>
            <div className='border-border flex w-100 flex-col gap-8 rounded-lg border bg-white px-8 py-8'>
                <div className='flex flex-col text-center'>
                    <Text variant='h2' as='h2'>
                        Регистрация
                    </Text>
                    <Text variant='p' as='p'>
                        Бла бла бла
                    </Text>
                </div>
                <div className='flex w-full flex-col gap-4'>
                    <Input label='Логин' placeholder='Придумайте логин' />
                    <Input label='Почта' placeholder='mail@example.ru' />
                    <Input label='Пароль' placeholder='Придумайте пароль' type='password' />
                </div>
                <div className='flex flex-col gap-4 text-center'>
                    <Button>Создать аккаунт</Button>
                    <div className='flex flex-col'>
                        <Text variant='p-sm'>Уже есть аккаунт?</Text>
                        <Link to='/login'>
                            <Text className='text-accent! underline' variant='p-sm'>
                                Войти
                            </Text>
                        </Link>
                    </div>
                </div>
            </div>
        </>
    );
}
