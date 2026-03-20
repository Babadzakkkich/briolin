import type React from 'react';
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';

import { ProfileStep } from './steps/ProfileStep';
import { ResultStep } from './steps/ResultStep';
import { TestStep } from './steps/TestStep';

export type StepProps = {
  onNext: () => void;
};

const STEPS: React.ComponentType<StepProps>[] = [ProfileStep, TestStep, ResultStep];

export function OnboardingPage() {
  const [step, setStep] = useState(0);
  const navigate = useNavigate();

  const handleNext = () => {
    if (step < STEPS.length - 1) {
      setStep((s) => s + 1);
    } else {
      navigate('/');
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
      <StepComponent onNext={handleNext} />
    </div>
  );
}
