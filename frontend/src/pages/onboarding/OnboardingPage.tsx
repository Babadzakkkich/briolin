import type React from 'react';
import { useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { ProfileStep } from '@/features/onboarding/steps/ProfileStep';
import { ResultStep } from '@/features/onboarding/steps/ResultStep';
import { TestStep } from '@/features/onboarding/steps/TestStep';
import type { StepProps } from '@/features/onboarding/model/types';
import { WelcomeStep } from '@/features/onboarding/steps/WelcomeStep';

const STEPS: React.ComponentType<StepProps<unknown>>[] = [
  WelcomeStep,
  ProfileStep,
  TestStep,
  ResultStep,
];

export function OnboardingPage() {
  const location = useLocation();
  const requestedStep = (location.state as { step?: number } | null)?.step ?? 0;
  const initialStep = Math.min(Math.max(requestedStep, 0), STEPS.length - 1);
  const [step, setStep] = useState(initialStep);
  const [stepData, setStepData] = useState<unknown>(undefined);
  const navigate = useNavigate();

  const handleNext = (data?: unknown) => {
    setStepData(data);
    if (step < STEPS.length - 1) {
      setStep((s) => s + 1);
    } else {
      navigate('/dashboard');
    }
  };

  const StepComponent = STEPS[step];

  return (
    <div className='flex flex-col items-center gap-6'>
      <div className='flex gap-2' aria-label={`Шаг ${step + 1} из ${STEPS.length}`}>
        {STEPS.map((_, i) => (
          <div
            key={i}
            className={`h-2 w-8 rounded-full transition-colors ${
              i <= step ? 'bg-accent' : 'bg-border'
            }`}
          />
        ))}
      </div>
      <StepComponent onNext={handleNext} onRetry={() => setStep(1)} data={stepData} />
    </div>
  );
}
