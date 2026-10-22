import { Metadata } from "next";
import { AuthCard } from "@/components/auth/auth-card";

export const metadata: Metadata = {
  title: "Sign In — ContextIQ Cognitive Suite",
  description: "Sign in to access your personalized behavioral telemetry and resumption chronometer.",
};

export default function LoginPage() {
  return (
    <div className="flex min-h-[85vh] items-center justify-center py-10 px-4">
      <AuthCard initialMode="login" />
    </div>
  );
}
