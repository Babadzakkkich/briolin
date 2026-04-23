import { Avatar } from '@/shared/uikit/Avatar';

interface AvatarUploadProps {
  src?: string | null;
  name?: string;
  onUpload?: (file: File) => void;
}

export function AvatarUpload({ src, name, onUpload }: AvatarUploadProps) {
  return <Avatar src={src} name={name} size='2xl' uploadable onUpload={onUpload} />;
}
