import { IconCard } from '@/shared/cards/IconCard';
import { Button } from '@/shared/uikit/Button';
import { Input } from '@/shared/uikit/Input';
import { Text } from '@/shared/uikit/Text';
import { Link } from 'react-router-dom';

export function ForgotPasswordPage() {
    return (
        <>
            <div className='border-border flex w-100 flex-col gap-8 rounded-lg border bg-white px-8 py-8'>
                <div className='flex flex-col items-center gap-6 text-center'>
                    <div className='flex flex-col items-center gap-2'>
                        <IconCard icon='mail' />
                        <Text variant='h2' as='h2'>
                            Забыли пароль?
                        </Text>
                    </div>
                    <Text variant='p-sm' as='p'>
                        Мы отправили ссылку для подтверждения на ваш электронный адрес. Пожалуйста,
                        перейдите по ссылке, чтобы подтвердить учётную запись и продолжить.
                    </Text>
                    <div className='flex flex-col'>
                        <Text variant='p-sm'>Не получили письмо?</Text>
                        <Link to='#'>
                            <Text className='text-accent! underline' variant='p-sm'>
                                Отправить заново
                            </Text>
                        </Link>
                    </div>
                </div>
            </div>
        </>
    );
}
