import { useAuthStore } from "@/stores/authStore";
import { useQuery } from "@tanstack/react-query";
import { client } from "../client";

export const useMe = () => {
  const token = useAuthStore((s) => s.accessToken);

  return useQuery({
    queryKey: ["me"],
    queryFn: () => client.get("/auth/me").then((r) => r.data),
    enabled: !!token,
    staleTime: 5 * 60 * 1000,
  });
};
