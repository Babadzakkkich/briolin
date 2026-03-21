import type React from 'react';
import { useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';

import { ProfileStep } from './steps/ProfileStep';
import { ResultStep } from './steps/ResultStep';
import { TestStep } from './steps/TestStep';

export type StepProps<TData = undefined> = {
  onNext: (data?: TData) => void;
  onRetry?: () => void;
  data?: unknown;
};

const STEPS: React.ComponentType<StepProps<unknown>>[] = [ProfileStep, TestStep, ResultStep];

export function OnboardingPage() {
  const location = useLocation();
  const initialStep = (location.state as { step?: number } | null)?.step ?? 0;
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
      <div className='flex gap-2'>
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
