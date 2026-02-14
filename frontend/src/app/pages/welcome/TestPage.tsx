import { useState } from 'react';
import { useNavigate } from 'react-router-dom';

import { Button } from '@/components/ui/Button';
import { Text } from '@/components/ui/Text';
import questionsData from '@/data/questions.json';
import { ResultCircle } from '@/components/widgets/ResultCircle';

interface Option {
  id: string;
  text: string;
}

interface Question {
  id: number;
  question: string;
  options: Option[];
}

export function TestPage() {
  const navigate = useNavigate();
  const [started, setStarted] = useState(false);
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
  const [answers, setAnswers] = useState<Record<number, string | null>>({});
  const [finished, setFinished] = useState(false);
  const [showFinalFeedback, setShowFinalFeedback] = useState(false);
  const [percentage] = useState(() => Math.floor(Math.random() * 100));

  const isSuccess = percentage >= 30;
  const resultColor = isSuccess ? '#4B6B56' : '#DC4C4C';
  const headerCirclesColorClass = isSuccess ? 'bg-[#4B6B56]' : 'bg-[#DC4C4C]';

  const questions: Question[] = questionsData;
  const currentQuestion = questions[currentQuestionIndex];

  const handleStart = () => {
    setStarted(true);
  };

  const handleSelectOption = (questionId: number, optionId: string) => {
    setAnswers((prev) => ({ ...prev, [questionId]: optionId }));
  };

  const handleNext = () => {
    if (currentQuestionIndex < questions.length - 1) {
      setCurrentQuestionIndex((prev) => prev + 1);
    } else {
      setFinished(true);
    }
  };

  const isCurrentAnswered = !!answers[currentQuestion.id];

  if (!started) {
    return (
      <div className="mx-auto min-h-screen max-w-7xl px-6 py-9 md:px-10">
        <header className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Text variant="base" size="md" className="text-gray-500">
              /тестирование
            </Text>
          </div>
        </header>

        <div className="flex max-w-6xl flex-col items-start gap-8 pt-10 md:gap-12 md:pt-20">
          <div className="space-y-6">
            <h1 className="text-3xl leading-tight font-light text-stone-800 md:text-5xl">
              Позволь нам лучше узнать тебя!
            </h1>
            <Text
              variant="base"
              className="max-w-xl text-lg leading-relaxed text-stone-600"
            >
              Мы подготовили несколько лёгких вопросов, чтобы помочь тебе найти
              партнёра, который разделяет твой ритм. Отвечай честно и в своём
              стиле — ведь только так можно встретить любовь, которая звучит в
              унисон!
            </Text>
          </div>
          <div className="h-20 md:h-40"></div>
          <div className="flex w-full justify-end">
            <Button
              variant="solid"
              onClick={handleStart}
              className="w-full md:w-fit px-8 py-4 text-lg"
            >
              Начать тест
            </Button>
          </div>
        </div>
      </div>
    );
  }

  if (finished && !showFinalFeedback) {
    return (
      <div className="mx-auto min-h-screen max-w-6xl px-6 py-9 md:px-10">
        <header className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Text variant="base" size="md" className="text-gray-500">
              /результат
            </Text>
            <div className="flex items-center">
              <div
                className={`size-7 rounded-full ${headerCirclesColorClass}`}
              ></div>
              <div
                className={`size-7 -translate-x-[14px] rounded-full ${headerCirclesColorClass}`}
              ></div>
            </div>
          </div>
        </header>
        <div className="flex w-full flex-col items-center space-y-8 py-10 md:space-y-10 md:py-20">
          <Text variant="base" size="lg">
            Результат тестирования
          </Text>
          <Text
            variant="base"
            className="text-center text-lg leading-relaxed text-stone-600 max-w-2xl"
          >
            {isSuccess
              ? 'Ваш показатель отражает высокий уровень совпадения по основным критериям. Полученные данные помогут точнее определить круг наиболее подходящих партнёров.'
              : 'К сожалению, результат ниже ожидаемого уровня совпадения. Но не расстраивайтесь, возможно, вам стоит попробовать еще раз!'}
          </Text>
          <div className="scale-75 md:scale-100">
            <ResultCircle percentage={percentage} color={resultColor} />
          </div>
          <div className="h-20 md:h-32"></div>
          <div className="flex w-full justify-end">
            <Button
              variant="solid"
              onClick={() => isSuccess ? setShowFinalFeedback(true) : navigate('/')}
              className="w-full md:w-fit px-8 py-4 text-lg"
            >
              {isSuccess ? 'Далее' : 'На главную страницу'}
            </Button>
          </div>
        </div>
      </div>
    );
  }

  if (showFinalFeedback) {
    return (
      <div className="mx-auto flex min-h-screen max-w-6xl flex-col items-center justify-center px-6 py-9 md:px-10">
        <header className="flex w-full items-center justify-between">
          <div className="flex items-center gap-2">
            <Text variant="base" size="md" className="text-gray-500">
              /результат
            </Text>
            <div className="flex items-center">
              <div
                className={`size-7 rounded-full ${headerCirclesColorClass}`}
              ></div>
              <div
                className={`size-7 -translate-x-[14px] rounded-full ${headerCirclesColorClass}`}
              ></div>
            </div>
          </div>
        </header>

        <div className="flex w-full flex-grow flex-col justify-center space-y-8 py-12">
          <h1 className="text-left text-3xl leading-tight font-light text-stone-800 md:text-5xl">
            {isSuccess
              ? 'Поздравляем! Ты прошел тест!'
              : 'Увы, не в этот раз...'}
          </h1>
          <Text variant="base">
            {isSuccess
              ? 'Отличная работа! Ты прошёл тест и показал свой уникальный ритм. Подробный отчёт отправлен на твою почту. Услуги наших партнёров уже доступны для тебя. Вперёд к новым знакомствам и к большой любви!'
              : 'Тестирование завершено, но результат оказался ниже необходимого. Отчёт отправлен на твой  e-mail. Чтобы не торопиться и ответить лучше, повторная попытка будет доступна через 6 часов. Мы верим —  в следующий раз ты справишься!'}
          </Text>
          <div className="mt-20 flex w-full justify-end md:mt-40">
            <Button
              variant="solid"
              onClick={() => isSuccess ? navigate('/interview') : window.location.reload()}
              className="w-full md:w-fit px-8 py-4 text-lg"
            >
              {isSuccess ? 'Далее' : 'Пройти снова'}
            </Button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="mx-auto flex min-h-screen max-w-7xl flex-col px-6 py-9 md:px-10">
      <header className="mb-8 md:mb-12">
        <Text variant="base" size="md" className="text-stone-400">
          /вопрос {currentQuestionIndex + 1}
        </Text>
      </header>

      <div className="flex flex-grow flex-col justify-center gap-8 pb-10 md:gap-12 md:pb-20">
        <h2 className="text-2xl leading-tight font-light text-stone-800 md:text-4xl">
          {currentQuestion.question}
        </h2>

        <div className="grid grid-cols-1 gap-x-12 gap-y-4 md:grid-cols-2 md:gap-y-6">
          {currentQuestion.options.map((option) => {
            const isSelected = answers[currentQuestion.id] === option.id;
            return (
              <div
                key={option.id}
                onClick={() =>
                  handleSelectOption(currentQuestion.id, option.id)
                }
                className="group flex cursor-pointer items-center gap-4 py-2"
              >
                <div
                  className={`relative flex h-6 w-6 shrink-0 items-center justify-center rounded-full border transition-all duration-300 md:h-8 md:w-8 ${isSelected
                    ? 'border-[#5C7164] bg-[#5C7164]'
                    : 'border-stone-400 group-hover:border-[#5C7164]'
                    }`}
                ></div>
                <span
                  className={`text-base transition-colors duration-300 md:text-lg ${isSelected
                    ? 'font-medium text-stone-800'
                    : 'text-stone-600 group-hover:text-stone-800'
                    }`}
                >
                  {option.text}
                </span>
              </div>
            );
          })}
        </div>

        <div className="flex justify-end pt-8">
          <Button
            variant={isCurrentAnswered ? 'solid' : 'outline'}
            onClick={handleNext}
            disabled={!isCurrentAnswered}
            className={`w-full transition-opacity duration-300 md:w-fit rounded-full border-none bg-ash-blue px-8 py-3 text-white`}
          >
            {currentQuestionIndex === questions.length - 1
              ? 'Завершить'
              : 'Следующий вопрос'}
          </Button>
        </div>
      </div>
    </div>
  );
}
