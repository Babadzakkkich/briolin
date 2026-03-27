import { create } from 'zustand';

interface ProfileState {
  firstName: string | null;
  lastName: string | null;
  city: string | null;
  gender: string | null;
  dateOfBirth: string | null;
  setProfile: (profile: {
    first_name: string;
    last_name: string;
    city: string;
    gender: string;
    date_of_birth: string;
  }) => void;
  clear: () => void;
}

export const useProfileStore = create<ProfileState>((set) => ({
  firstName: null,
  lastName: null,
  city: null,
  gender: null,
  dateOfBirth: null,
  setProfile: (profile) =>
    set({
      firstName: profile.first_name,
      lastName: profile.last_name,
      city: profile.city,
      gender: profile.gender,
      dateOfBirth: profile.date_of_birth,
    }),
  clear: () =>
    set({ firstName: null, lastName: null, city: null, gender: null, dateOfBirth: null }),
}));
