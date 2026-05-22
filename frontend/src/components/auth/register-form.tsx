"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { zodResolver } from "@hookform/resolvers/zod";
import { UserPlus } from "lucide-react";
import { useForm } from "react-hook-form";
import { z } from "zod";
import { register as registerUser } from "@/lib/auth-api";
import { persistSession } from "@/lib/auth";
import { Button } from "@/components/ui/button";
import { Field } from "@/components/ui/field";
import { Input } from "@/components/ui/input";

const registerSchema = z.object({
  first_name: z.string().max(150).optional(),
  last_name: z.string().max(150).optional(),
  username: z.string().min(3, "Username must be at least 3 characters").max(150),
  email: z.string().email("Enter a valid email address"),
  password: z.string().min(8, "Password must be at least 8 characters")
});

type RegisterValues = z.infer<typeof registerSchema>;

export function RegisterForm() {
  const router = useRouter();
  const [serverError, setServerError] = useState<string | null>(null);
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting }
  } = useForm<RegisterValues>({
    resolver: zodResolver(registerSchema),
    defaultValues: {
      first_name: "",
      last_name: "",
      username: "",
      email: "",
      password: ""
    }
  });

  async function onSubmit(values: RegisterValues) {
    setServerError(null);
    try {
      const response = await registerUser(values);
      persistSession(response);
      router.push("/dashboard");
    } catch (error) {
      setServerError(error instanceof Error ? error.message : "Unable to create your account.");
    }
  }

  return (
    <form className="grid gap-4" onSubmit={handleSubmit(onSubmit)}>
      <div className="grid gap-4 sm:grid-cols-2">
        <Field label="First name" error={errors.first_name?.message}>
          <Input autoComplete="given-name" placeholder="Nayem" {...register("first_name")} />
        </Field>
        <Field label="Last name" error={errors.last_name?.message}>
          <Input autoComplete="family-name" placeholder="Hossain" {...register("last_name")} />
        </Field>
      </div>
      <Field label="Username" error={errors.username?.message}>
        <Input autoComplete="username" placeholder="nayem" {...register("username")} />
      </Field>
      <Field label="Email" error={errors.email?.message}>
        <Input type="email" autoComplete="email" placeholder="you@example.com" {...register("email")} />
      </Field>
      <Field label="Password" error={errors.password?.message}>
        <Input type="password" autoComplete="new-password" placeholder="At least 8 characters" {...register("password")} />
      </Field>
      {serverError ? (
        <div className="rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm font-medium text-red-700">
          {serverError}
        </div>
      ) : null}
      <Button type="submit" disabled={isSubmitting} className="mt-2 w-full">
        <UserPlus size={17} />
        {isSubmitting ? "Creating account..." : "Create account"}
      </Button>
    </form>
  );
}
