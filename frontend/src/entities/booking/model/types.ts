export type ServiceFormat = 'online' | 'offline';
export type BookingStatus = 'upcoming' | 'completed' | 'cancelled';
export type PaymentStatus = 'pending' | 'paid' | 'failed';

export interface PsychologistService {
  id: string;
  title: string;
  type: string;
  description: string;
  duration: number;
  price: number;
  format: ServiceFormat;
  active: boolean;
}

export interface Booking {
  id: string;
  serviceId: string;
  serviceTitle: string;
  psychologistName: string;
  clientName: string;
  clientEmail: string;
  date: string;
  time: string;
  duration: number;
  price: number;
  status: BookingStatus;
  paymentStatus: PaymentStatus;
  meetingUrl?: string;
  result?: 'passed' | 'failed';
  recommendations?: string;
  privateNote?: string;
}
