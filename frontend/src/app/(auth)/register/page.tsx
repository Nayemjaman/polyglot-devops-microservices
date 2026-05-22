import Link from "next/link";
import { AuthCard } from "@/components/auth/auth-card";
import { RegisterForm } from "@/components/auth/register-form";

export default function RegisterPage() {
  return (
    <AuthCard
      title="Create your workspace"
      description="Create an account to start tracking budgets, spending, and reports."
      footer={
        <>
          Already have an account?{" "}
          <Link href="/login" className="font-semibold text-teal-700 hover:text-teal-800">
            Sign in
          </Link>
        </>
      }
    >
      <RegisterForm />
    </AuthCard>
  );
}
