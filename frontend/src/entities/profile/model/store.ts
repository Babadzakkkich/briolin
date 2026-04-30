import { create } from 'zustand';
import { persist } from 'zustand/middleware';

interface ProfileState {
  firstName: string | null;
  lastName: string | null;
  city: string | null;
  gender: string | null;
  dateOfBirth: string | null;
  thumbnailUrl: string | null;
  setProfile: (profile: {
    first_name: string;
    last_name: string;
    city: string;
    gender: string;
    date_of_birth: string;
    thumbnail_url?: string | null;
  }) => void;
  setThumbnailUrl: (url: string | null) => void;
  clear: () => void;
}

export const useProfileStore = create<ProfileState>()(
  persist(
    (set) => ({
      firstName: null,
      lastName: null,
      city: null,
      gender: null,
      dateOfBirth: null,
      thumbnailUrl: null,
      setProfile: (profile) =>
        set({
          firstName: profile.first_name,
          lastName: profile.last_name,
          city: profile.city,
          gender: profile.gender,
          dateOfBirth: profile.date_of_birth,
          thumbnailUrl: profile.thumbnail_url ?? null,
        }),
      setThumbnailUrl: (url) => set({ thumbnailUrl: url }),
      clear: () =>
        set({ firstName: null, lastName: null, city: null, gender: null, dateOfBirth: null, thumbnailUrl: null }),
    }),
    { name: 'profile' },
  ),
);
