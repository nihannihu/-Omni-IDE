import Dashboard from '@/components/Dashboard';
import OnboardingWizard from '@/components/OnboardingWizard';

export default function Home() {
  return (
    <main className="min-h-screen bg-black">
      <OnboardingWizard />
      <Dashboard />
    </main>
  );
}
