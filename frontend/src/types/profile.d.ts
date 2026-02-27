export type GenderType = "male" | "female";

export type BasicProfile = {
  first_name: string;
  last_name: string;
  gender: GenderType;
  date_of_birth: string;
  city: string;
};

export type DetailedProfile = {
  about_me: string;
  education: string;
  hobbies: string;
  partner_preferences: string;
};

export type FullProfile = {
  basic: BasicProfile;
  detailed: DetailedProfile;
};
