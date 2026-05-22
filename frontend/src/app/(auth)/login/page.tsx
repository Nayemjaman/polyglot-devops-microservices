import Link from "next/link";
import { AuthCard } from "@/components/auth/auth-card";
import { LoginForm } from "@/components/auth/login-form";

export default function LoginPage() {
  return (
    <AuthCard
      title="Welcome back"
      description="Sign in to continue to your finance workspace."
      footer={
        <>
          New here?{" "}
          <Link href="/register" className="font-semibold text-teal-700 hover:text-teal-800">
            Create an account
          </Link>
        </>
      }
    >
      <LoginForm />
    </AuthCard>
  );
}
