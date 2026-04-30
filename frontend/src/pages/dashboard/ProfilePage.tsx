import { useEffect, useState } from 'react';
import { z } from 'zod';
import { profileApi, useProfileStore, AvatarUpload } from '@/entities/profile';
import type { ProfileResponse, ProfileQuestions } from '@/entities/profile';
import {
  BasicInfoSection,
  genderToDisplay,
  displayToGender,
} from '@/features/profile/ui/BasicInfoSection';
import { DetailedInfoSection } from '@/features/profile/ui/DetailedInfoSection';
import { QuestionsSection, validateQuestions } from '@/features/profile/ui/QuestionsSection';
import { Loader } from '@/shared/uikit/Loader';
import { toast } from '@/shared/toast/toast';

const basicSchema = z.object({
  first_name: z.string().min(1, 'Введите имя').max(100),
  last_name: z.string().min(1, 'Введите фамилию').max(100),
  city: z.string().min(1, 'Введите город').max(200),
  date_of_birth: z.string().min(1, 'Выберите дату рождения'),
});

const detailedSchema = z.object({
  about_me: z.string().min(10, 'Минимум 10 символов').max(2000),
  education: z.string().min(1, 'Введите информацию об образовании').max(500),
  hobbies: z.string().min(1, 'Введите хобби и интересы').max(1000),
  partner_preferences: z.string().min(10, 'Минимум 10 символов').max(2000),
});

type BasicErrors = Partial<Record<keyof z.infer<typeof basicSchema>, string>>;
type DetailedErrors = Partial<Record<keyof z.infer<typeof detailedSchema> | 'red_flags', string>>;
type QuestionsErrors = Partial<Record<'question_1' | 'question_2' | 'question_3' | 'question_4' | 'question_5', string>>;

const maxBirthDate = new Date();
maxBirthDate.setFullYear(maxBirthDate.getFullYear() - 18);
const maxBirthDateStr = maxBirthDate.toISOString().split('T')[0];

const emptyQuestions: Omit<ProfileQuestions, 'created_at' | 'updated_at'> = {
  question_1: '',
  question_2: '',
  question_3: '',
  question_4: '',
  question_5: '',
};

export function ProfilePage() {
  const { setProfile, setThumbnailUrl } = useProfileStore();
  const [profile, setProfileData] = useState<ProfileResponse | null>(null);
  const [loading, setLoading] = useState(true);

  const [editingBasic, setEditingBasic] = useState(false);
  const [firstName, setFirstName] = useState('');
  const [lastName, setLastName] = useState('');
  const [city, setCity] = useState('');
  const [gender, setGender] = useState('Мужской');
  const [birthDate, setBirthDate] = useState('');
  const [savingBasic, setSavingBasic] = useState(false);
  const [basicErrors, setBasicErrors] = useState<BasicErrors>({});

  const [editingDetailed, setEditingDetailed] = useState(false);
  const [aboutMe, setAboutMe] = useState('');
  const [education, setEducation] = useState('');
  const [hobbies, setHobbies] = useState('');
  const [partnerPreferences, setPartnerPreferences] = useState('');
  const [redFlags, setRedFlags] = useState<string[]>([]);
  const [savingDetailed, setSavingDetailed] = useState(false);
  const [detailedErrors, setDetailedErrors] = useState<DetailedErrors>({});

  const [editingQuestions, setEditingQuestions] = useState(false);
  const [questions, setQuestions] = useState<Omit<ProfileQuestions, 'created_at' | 'updated_at'>>(emptyQuestions);
  const [savedQuestions, setSavedQuestions] = useState<Omit<ProfileQuestions, 'created_at' | 'updated_at'>>(emptyQuestions);
  const [savingQuestions, setSavingQuestions] = useState(false);
  const [questionsErrors, setQuestionsErrors] = useState<QuestionsErrors>({});

  function initBasicFields(p: ProfileResponse) {
    setFirstName(p.basic.first_name);
    setLastName(p.basic.last_name);
    setCity(p.basic.city);
    setGender(genderToDisplay(p.basic.gender));
    setBirthDate(p.basic.date_of_birth.split('T')[0]);
  }

  function initDetailedFields(p: ProfileResponse) {
    setAboutMe(p.detailed?.about_me ?? '');
    setEducation(p.detailed?.education ?? '');
    setHobbies(p.detailed?.hobbies ?? '');
    setPartnerPreferences(p.detailed?.partner_preferences ?? '');
    setRedFlags(p.detailed?.red_flags ?? []);
  }

  useEffect(() => {
    profileApi
      .getMe()
      .then((res) => {
        setProfileData(res.data);
        setProfile({ ...res.data.basic, thumbnail_url: res.data.basic.thumbnail_url });
        initBasicFields(res.data);
        initDetailedFields(res.data);
      })
      .catch(() => toast.error('Не удалось загрузить профиль'))
      .finally(() => setLoading(false));

    profileApi
      .getMyQuestions()
      .then((res) => {
        const q = {
          question_1: res.data.question_1,
          question_2: res.data.question_2,
          question_3: res.data.question_3,
          question_4: res.data.question_4,
          question_5: res.data.question_5,
        };
        setQuestions(q);
        setSavedQuestions(q);
      })
      .catch(() => {
        // 404 means no questions yet — start with empty
      });
  }, []);

  function cancelBasic() {
    if (profile) initBasicFields(profile);
    setBasicErrors({});
    setEditingBasic(false);
  }

  function saveBasic() {
    const result = basicSchema.safeParse({
      first_name: firstName,
      last_name: lastName,
      city,
      date_of_birth: birthDate,
    });
    if (!result.success) {
      const errs: BasicErrors = {};
      result.error.issues.forEach((e) => {
        errs[e.path[0] as keyof BasicErrors] = e.message;
      });
      setBasicErrors(errs);
      return;
    }
    setBasicErrors({});
    setSavingBasic(true);
    profileApi
      .updateMe({
        basic: {
          first_name: firstName,
          last_name: lastName,
          city,
          gender: displayToGender(gender),
          date_of_birth: birthDate,
        },
      })
      .then(() => {
        toast.success('Основная информация обновлена');
        setProfileData((prev) =>
          prev
            ? {
                ...prev,
                basic: {
                  ...prev.basic,
                  first_name: firstName,
                  last_name: lastName,
                  city,
                  gender: displayToGender(gender),
                  date_of_birth: birthDate,
                },
              }
            : prev,
        );
        setProfile({
          first_name: firstName,
          last_name: lastName,
          city,
          gender: displayToGender(gender),
          date_of_birth: birthDate,
        });
        setEditingBasic(false);
      })
      .catch(() => toast.error('Ошибка при сохранении'))
      .finally(() => setSavingBasic(false));
  }

  function cancelDetailed() {
    if (profile) initDetailedFields(profile);
    setDetailedErrors({});
    setEditingDetailed(false);
  }

  function saveDetailed() {
    const result = detailedSchema.safeParse({
      about_me: aboutMe,
      education,
      hobbies,
      partner_preferences: partnerPreferences,
    });
    if (!result.success) {
      const errs: DetailedErrors = {};
      result.error.issues.forEach((e) => {
        errs[e.path[0] as keyof DetailedErrors] = e.message;
      });
      setDetailedErrors(errs);
      return;
    }
    setDetailedErrors({});
    setSavingDetailed(true);
    const isCreate = !profile?.detailed;
    const apiCall = isCreate
      ? profileApi.createDetailed({
          about_me: aboutMe,
          education,
          hobbies,
          partner_preferences: partnerPreferences,
          red_flags: redFlags.length > 0 ? redFlags : null,
        })
      : profileApi.updateMe({
          detailed: {
            about_me: aboutMe,
            education,
            hobbies,
            partner_preferences: partnerPreferences,
            red_flags: redFlags.length > 0 ? redFlags : null,
          },
        });

    apiCall
      .then(() => {
        toast.success('Дополнительная информация обновлена');
        setProfileData((prev) =>
          prev
            ? {
                ...prev,
                detailed: {
                  id: prev.detailed?.id ?? 0,
                  about_me: aboutMe,
                  education,
                  hobbies,
                  partner_preferences: partnerPreferences,
                  red_flags: redFlags.length > 0 ? redFlags : null,
                },
              }
            : prev,
        );
        setEditingDetailed(false);
      })
      .catch(() => toast.error('Ошибка при сохранении'))
      .finally(() => setSavingDetailed(false));
  }

  function cancelQuestions() {
    setQuestions(savedQuestions);
    setQuestionsErrors({});
    setEditingQuestions(false);
  }

  function saveQuestions() {
    const errors = validateQuestions(questions);
    if (Object.keys(errors).length > 0) {
      setQuestionsErrors(errors);
      return;
    }
    setQuestionsErrors({});
    setSavingQuestions(true);
    profileApi
      .createOrUpdateQuestions(questions)
      .then(() => {
        toast.success('Вопросы сохранены');
        setSavedQuestions(questions);
        setEditingQuestions(false);
      })
      .catch(() => toast.error('Ошибка при сохранении вопросов'))
      .finally(() => setSavingQuestions(false));
  }

  if (loading) return <Loader center label='Загружаем профиль...' />;

  if (!profile) {
    return (
      <div className='flex flex-1 items-center justify-center'>
        <p className='text-muted text-[14px]'>Профиль не найден</p>
      </div>
    );
  }

  const { basic, detailed } = profile;

  function handleAvatarUploaded(url: string, thumbnailUrl: string) {
    setProfileData((prev) =>
      prev
        ? {
            ...prev,
            basic: {
              ...prev.basic,
              avatar_url: url || null,
              thumbnail_url: thumbnailUrl || null,
            },
          }
        : prev,
    );
    setThumbnailUrl(thumbnailUrl || null);
  }

  return (
    <div className='flex-1 overflow-y-auto px-8 py-10'>
      <div className='mx-auto max-w-3xl'>
        <div className='mb-8 flex items-center gap-5'>
          <AvatarUpload
            src={basic.avatar_url ?? null}
            name={`${basic.first_name} ${basic.last_name}`}
            onUploaded={handleAvatarUploaded}
          />
          <div>
            <h1 className='font-onest text-primary text-3xl font-medium'>
              {basic.first_name} {basic.last_name}
            </h1>
            <p className='text-secondary mt-0.5 text-[14px]'>{basic.city}</p>
          </div>
        </div>

        <div className='flex flex-col gap-4'>
          <BasicInfoSection
            basic={basic}
            editing={editingBasic}
            saving={savingBasic}
            errors={basicErrors}
            firstName={firstName}
            lastName={lastName}
            city={city}
            gender={gender}
            birthDate={birthDate}
            maxBirthDateStr={maxBirthDateStr}
            onEdit={() => setEditingBasic(true)}
            onSave={saveBasic}
            onCancel={cancelBasic}
            onFirstNameChange={(v) => {
              setFirstName(v);
              setBasicErrors((p) => ({ ...p, first_name: undefined }));
            }}
            onLastNameChange={(v) => {
              setLastName(v);
              setBasicErrors((p) => ({ ...p, last_name: undefined }));
            }}
            onCityChange={(v) => {
              setCity(v);
              setBasicErrors((p) => ({ ...p, city: undefined }));
            }}
            onGenderChange={setGender}
            onBirthDateChange={(v) => {
              setBirthDate(v);
              setBasicErrors((p) => ({ ...p, date_of_birth: undefined }));
            }}
          />

          <DetailedInfoSection
            detailed={detailed}
            editing={editingDetailed}
            saving={savingDetailed}
            errors={detailedErrors}
            aboutMe={aboutMe}
            education={education}
            hobbies={hobbies}
            partnerPreferences={partnerPreferences}
            redFlags={redFlags}
            onEdit={() => setEditingDetailed(true)}
            onSave={saveDetailed}
            onCancel={cancelDetailed}
            onAboutMeChange={(v) => {
              setAboutMe(v);
              setDetailedErrors((p) => ({ ...p, about_me: undefined }));
            }}
            onEducationChange={(v) => {
              setEducation(v);
              setDetailedErrors((p) => ({ ...p, education: undefined }));
            }}
            onHobbiesChange={(v) => {
              setHobbies(v);
              setDetailedErrors((p) => ({ ...p, hobbies: undefined }));
            }}
            onPartnerPreferencesChange={(v) => {
              setPartnerPreferences(v);
              setDetailedErrors((p) => ({ ...p, partner_preferences: undefined }));
            }}
            onRedFlagsChange={(v) => {
              setRedFlags(v);
              setDetailedErrors((p) => ({ ...p, red_flags: undefined }));
            }}
          />

          <QuestionsSection
            questions={questions}
            editing={editingQuestions}
            saving={savingQuestions}
            errors={questionsErrors}
            onEdit={() => setEditingQuestions(true)}
            onSave={saveQuestions}
            onCancel={cancelQuestions}
            onChange={(key, value) => {
              setQuestions((prev) => ({ ...prev, [key]: value }));
              setQuestionsErrors((prev) => ({ ...prev, [key]: undefined }));
            }}
          />
        </div>
      </div>
    </div>
  );
}
