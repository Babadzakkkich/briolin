export interface AnswerOption {
  id: string;
  text: string;
  score: number;
}

export interface Question {
  id: string;
  text: string;
  question_type: 'multiple_choice' | 'likert_scale' | 'true_false';
  options: AnswerOption[];
  min_value?: number;
  max_value?: number;
  labels?: Record<string, string>;
}

export interface TestStartResponse {
  session_id: string;
  test_name: string;
  description: string;
  time_limit_minutes: number;
  questions: Question[];
}

export interface AnswerSubmitResponse {
  session_id: string;
  question_id: string;
  answer_saved: boolean;
  total_answered: number;
  total_questions: number;
}

export interface TestResults {
  total_score: number;
  max_possible_score: number;
  percentage: number;
  passed: boolean;
}

export interface TestCompleteResponse {
  session_id: string;
  results: TestResults;
}

export interface TestHistoryItem {
  session_id: string;
  test_name: string;
  completed_at: string;
  total_score: number;
  percentage: number;
  passed: boolean;
}

export interface TestHistory {
  history: TestHistoryItem[];
  total: number;
}
