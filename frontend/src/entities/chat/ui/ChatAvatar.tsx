import { Avatar } from '@/shared/uikit/Avatar';

interface ChatAvatarProps {
  name?: string;
  size?: 'sm' | 'md' | 'lg';
}

export function ChatAvatar({ name, size = 'md' }: ChatAvatarProps) {
  return <Avatar name={name} size={size} />;
}
