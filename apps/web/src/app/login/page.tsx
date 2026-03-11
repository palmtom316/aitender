import { LoginForm } from "../../components/auth/login-form";

export default function LoginPage() {
  return (
    <main>
      <h1>Sign in to aitender</h1>
      <p>Use your organization account to access tender projects.</p>
      <LoginForm />
    </main>
  );
}
