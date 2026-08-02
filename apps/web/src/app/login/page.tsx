import { Suspense } from "react";
import LoginPage from "./login-form";

export default function LoginRoute() {
  return (
    <Suspense fallback={<main className="p-10 text-[var(--ink-soft)]">Loading…</main>}>
      <LoginPage />
    </Suspense>
  );
}
