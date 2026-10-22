import { Metadata } from "next";
import { AuthCard } from "@/components/auth/auth-card";

export const metadata: Metadata = {
  title: "Create Account — ContextIQ Cognitive Suite",
  description: "Create your personalized ContextIQ workspace calibrated for your profession and language.",
};

export default function SignupPage() {
  return (
    <div className="flex min-h-[85vh] items-center justify-center py-10 px-4">
      <AuthCard initialMode="signup" />
    </div>
  );
}
