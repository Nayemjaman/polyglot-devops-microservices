"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { zodResolver } from "@hookform/resolvers/zod";
import { LogIn } from "lucide-react";
import { useForm } from "react-hook-form";
import { z } from "zod";
import { login } from "@/lib/auth-api";
import { persistSession } from "@/lib/auth";
import { Button } from "@/components/ui/button";
import { Field } from "@/components/ui/field";
import { Input } from "@/components/ui/input";

const loginSchema = z.object({
  email: z.string().email("Enter a valid email address"),
  password: z.string().min(1, "Password is required")
});

type LoginValues = z.infer<typeof loginSchema>;

export function LoginForm() {
  const router = useRouter();
  const [serverError, setServerError] = useState<string | null>(null);
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting }
  } = useForm<LoginValues>({
    resolver: zodResolver(loginSchema),
    defaultValues: {
      email: "",
      password: ""
    }
  });

  async function onSubmit(values: LoginValues) {
    setServerError(null);
    try {
      const response = await login(values);
      persistSession(response);
      router.push("/dashboard");
    } catch (error) {
      setServerError(error instanceof Error ? error.message : "Unable to sign in.");
    }
  }

  return (
    <form className="grid gap-4" onSubmit={handleSubmit(onSubmit)}>
      <Field label="Email" error={errors.email?.message}>
        <Input type="email" autoComplete="email" placeholder="you@example.com" {...register("email")} />
      </Field>
      <Field label="Password" error={errors.password?.message}>
        <Input type="password" autoComplete="current-password" placeholder="Your password" {...register("password")} />
      </Field>
      {serverError ? (
        <div className="rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm font-medium text-red-700">
          {serverError}
        </div>
      ) : null}
      <Button type="submit" disabled={isSubmitting} className="mt-2 w-full">
        <LogIn size={17} />
        {isSubmitting ? "Signing in..." : "Sign in"}
      </Button>
    </form>
  );
}
