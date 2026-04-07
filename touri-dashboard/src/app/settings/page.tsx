import { AppearanceSection } from '@/components/settings/appearance-section';

export default function SettingsPage() {
  return (
    <div className="p-6 max-w-2xl">
      <h1 className="text-2xl font-bold mb-6">Settings</h1>
      <AppearanceSection />
    </div>
  );
}
