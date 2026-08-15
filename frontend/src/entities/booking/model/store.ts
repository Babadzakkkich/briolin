import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type { Booking, PsychologistService } from './types';

const INITIAL_SERVICES: PsychologistService[] = [
  {
    id: 'intro-interview',
    title: 'Первичное собеседование',
    type: 'Отборочное интервью',
    description: 'Знакомство с психологом, обсуждение результатов анкеты и следующих шагов.',
    duration: 50,
    price: 2500,
    format: 'online',
    active: true,
  },
  {
    id: 'compatibility-session',
    title: 'Разбор совместимости',
    type: 'Индивидуальная консультация',
    description: 'Персональный разбор паттернов отношений и рекомендаций по поиску партнёра.',
    duration: 75,
    price: 3900,
    format: 'online',
    active: true,
  },
];

const DEMO_BOOKINGS: Booking[] = [
  {
    id: 'demo-booking-1',
    serviceId: 'intro-interview',
    serviceTitle: 'Первичное собеседование',
    psychologistName: 'Анна Смирнова',
    clientName: 'Мария Волкова',
    clientEmail: 'maria@example.ru',
    date: '2026-08-15',
    time: '11:00',
    duration: 50,
    price: 2500,
    status: 'upcoming',
    paymentStatus: 'paid',
    meetingUrl: 'https://meet.example.ru/demo-booking-1',
  },
  {
    id: 'demo-booking-2',
    serviceId: 'compatibility-session',
    serviceTitle: 'Разбор совместимости',
    psychologistName: 'Анна Смирнова',
    clientName: 'Иван Петров',
    clientEmail: 'ivan@example.ru',
    date: '2026-08-12',
    time: '16:30',
    duration: 75,
    price: 3900,
    status: 'completed',
    paymentStatus: 'paid',
  },
];

interface BookingState {
  services: PsychologistService[];
  bookings: Booking[];
  draftBooking: Booking | null;
  saveService: (service: PsychologistService) => void;
  toggleService: (id: string) => void;
  removeService: (id: string) => void;
  setDraftBooking: (booking: Booking | null) => void;
  confirmDraftPayment: () => Booking | null;
  saveInterviewResult: (
    id: string,
    data: Pick<Booking, 'result' | 'recommendations' | 'privateNote'>,
  ) => void;
}

export const useBookingStore = create<BookingState>()(
  persist(
    (set, get) => ({
      services: INITIAL_SERVICES,
      bookings: DEMO_BOOKINGS,
      draftBooking: null,
      saveService: (service) =>
        set((state) => ({
          services: state.services.some((item) => item.id === service.id)
            ? state.services.map((item) => (item.id === service.id ? service : item))
            : [...state.services, service],
        })),
      toggleService: (id) =>
        set((state) => ({
          services: state.services.map((item) =>
            item.id === id ? { ...item, active: !item.active } : item,
          ),
        })),
      removeService: (id) =>
        set((state) => ({ services: state.services.filter((item) => item.id !== id) })),
      setDraftBooking: (draftBooking) => set({ draftBooking }),
      confirmDraftPayment: () => {
        const draft = get().draftBooking;
        if (!draft) return null;
        const confirmed: Booking = {
          ...draft,
          paymentStatus: 'paid',
          status: 'upcoming',
          meetingUrl: `https://meet.example.ru/${draft.id}`,
        };
        set((state) => ({ bookings: [confirmed, ...state.bookings], draftBooking: null }));
        return confirmed;
      },
      saveInterviewResult: (id, data) =>
        set((state) => ({
          bookings: state.bookings.map((booking) =>
            booking.id === id ? { ...booking, ...data, status: 'completed' } : booking,
          ),
        })),
    }),
    { name: 'briolin-booking-demo' },
  ),
);
