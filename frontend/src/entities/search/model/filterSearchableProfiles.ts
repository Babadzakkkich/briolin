import { profileApi } from '@/entities/profile';
import type { ProfileQuestions } from '@/entities/profile';
import type { ProfilePreview } from './types';

const REQUIRED_QUESTION_KEYS: (keyof ProfileQuestions)[] = [
  'question_1',
  'question_2',
  'question_3',
  'question_4',
  'question_5',
];

function hasCompletedQuestions(questions: ProfileQuestions) {
  return REQUIRED_QUESTION_KEYS.every((key) => {
    const answer = questions[key];
    return typeof answer === 'string' && answer.trim().length > 0;
  });
}

/**
 * Frontend-only eligibility check. A candidate stays in search results only when
 * all five primary answers can be loaded and are non-empty.
 */
export async function filterSearchableProfiles(profiles: ProfilePreview[]) {
  const checks = await Promise.allSettled(
    profiles.map(async (profile) => {
      const { data } = await profileApi.getUserQuestions(profile.keycloak_id);
      return hasCompletedQuestions(data) ? profile : null;
    }),
  );

  return checks.flatMap((result) =>
    result.status === 'fulfilled' && result.value ? [result.value] : [],
  );
}
