"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";

import { Button } from "@/components/ui/button";
import { Container } from "@/components/ui/container";
import { Input } from "@/components/ui/input";

const schema = z.object({
  email: z.string().trim().email("Enter a valid work or personal email."),
});

type FormValues = z.infer<typeof schema>;

export function FinalCta() {
  const [done, setDone] = useState(false);
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<FormValues>({ resolver: zodResolver(schema) });

  return (
    <section id="book" aria-labelledby="book-title" className="py-20">
      <Container>
        <div className="grain relative overflow-hidden rounded-[1.75rem] bg-gradient-to-br from-brand-700 via-brand-600 to-emerald-600 px-6 py-12 text-white sm:px-12">
          <h2 id="book-title" className="max-w-xl text-3xl sm:text-4xl">
            Ready for a clearer view of your health?
          </h2>
          <p className="mt-3 max-w-xl text-white/85">Leave an email and we will set a short demo. No spam, and no medical report required.</p>
          {done ? (
            <p className="mt-6 text-sm font-semibold" role="status">
              Thanks. We will write to you about a demo time.
            </p>
          ) : (
            <form className="mt-6 flex max-w-lg flex-col gap-3 sm:flex-row" onSubmit={handleSubmit(() => setDone(true))} noValidate>
              <div className="flex-1">
                <label htmlFor="demo-email" className="sr-only">
                  Email
                </label>
                <Input id="demo-email" type="email" autoComplete="email" placeholder="you@company.com" className="bg-white text-slate-900" {...register("email")} />
                {errors.email ? <p className="mt-1 text-sm text-amber-100">{errors.email.message}</p> : null}
              </div>
              <Button type="submit" variant="secondary" className="shrink-0">
                Book a Demo
              </Button>
            </form>
          )}
        </div>
      </Container>
    </section>
  );
}
