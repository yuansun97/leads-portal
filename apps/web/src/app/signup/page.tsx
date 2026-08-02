import { Suspense } from "react";
import SignupForm from "./signup-form";

export default function SignupRoute() {
  return (
    <Suspense fallback={<main className="p-10 text-[var(--ink-soft)]">Loading…</main>}>
      <SignupForm />
    </Suspense>
  );
}
