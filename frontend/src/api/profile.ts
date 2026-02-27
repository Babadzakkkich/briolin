import type { FullProfile } from "@/types/profile";
import { client } from "./client";

export async function createProfile(payload: FullProfile): Promise<void> {
  try {
    await client.post("/profiles", payload);
  } catch (err: any) {
    if (err.response && err.response.data) {
      throw err.response.data;
    }
    throw err;
  }
}
