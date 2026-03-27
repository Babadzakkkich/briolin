import { Camera } from 'lucide-react';

export function AvatarUpload() {
  return (
    <label className='border-border bg-surface hover:bg-muted/25 flex size-20 cursor-pointer items-center justify-center rounded-full border transition-colors'>
      <Camera size={24} className='text-muted' />
      <input type='file' accept='image/png,image/jpeg' className='hidden' />
    </label>
  );
}
