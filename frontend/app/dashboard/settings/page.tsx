// ========================================
// Settings Page - Redesigned with Animations
// ========================================

"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import { 
  Settings, 
  FileSpreadsheet, 
  MessageSquare, 
  Phone, 
  Zap, 
  Save,
  CheckCircle2,
  Link2
} from "lucide-react";
import { Input } from "@/components/common";
import { GoogleSheetsIntegration, WhatsAppIntegration } from "@/components/integrations";
import { AnimatedCard } from "@/components/ui";
import { AnimatedButton } from "@/components/ui/animated-button";
import { usePageTransition } from "@/hooks/useAnimation";
import { showToast } from "@/lib/toast";

interface SettingsSection {
  icon: React.ReactNode;
  title: string;
  description?: string;
  children: React.ReactNode;
  delay: number;
}

function SettingsCard({ icon, title, description, children, delay }: SettingsSection) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay }}
    >
      <AnimatedCard className="p-6">
        <div className="flex items-start gap-4 mb-4">
          <div className="p-2.5 bg-gradient-to-br from-primary-500/10 to-secondary-500/10 rounded-xl">
            {icon}
          </div>
          <div>
            <h2 className="text-lg font-semibold text-neutral-900">{title}</h2>
            {description && (
              <p className="text-sm text-neutral-500 mt-0.5">{description}</p>
            )}
          </div>
        </div>
        {children}
      </AnimatedCard>
    </motion.div>
  );
}

export default function SettingsPage() {
  const pageRef = usePageTransition();
  const [isSaving, setIsSaving] = useState(false);
  const [settings, setSettings] = useState({
    googleSheetsId: "",
    twilioAccountSid: "",
    twilioAuthToken: "",
    twilioPhoneNumber: "",
    fast2smsApiKey: "",
    defaultTargetCount: 50,
    headlessMode: true,
  });

  const handleSave = async () => {
    setIsSaving(true);
    try {
      // Save settings to localStorage or backend
      localStorage.setItem("scrappy_settings", JSON.stringify(settings));
      await new Promise(resolve => setTimeout(resolve, 500)); // Simulate save
      showToast.success("Settings saved successfully!");
    } catch (error) {
      showToast.error("Failed to save settings");
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div ref={pageRef}>
      {/* Page Header */}
      <motion.div 
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="mb-8"
      >
        <div className="flex items-center gap-3 mb-2">
          <div className="p-2 bg-gradient-to-br from-primary-500 to-secondary-500 rounded-xl">
            <Settings className="w-6 h-6 text-white" />
          </div>
          <h1 className="text-2xl font-bold bg-gradient-to-r from-neutral-900 to-neutral-600 bg-clip-text text-transparent">
            Settings
          </h1>
        </div>
        <p className="text-neutral-500">
          Configure your Scrappy preferences and integrations
        </p>
      </motion.div>

      <div className="max-w-2xl space-y-6">
        {/* Google Sheets OAuth Integration */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
        >
          <GoogleSheetsIntegration />
        </motion.div>

        {/* WhatsApp Business Integration */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.15 }}
        >
          <WhatsAppIntegration />
        </motion.div>

        {/* Legacy Google Sheets (Service Account) */}
        <SettingsCard
          icon={<Link2 className="w-5 h-5 text-primary-600" />}
          title="Google Sheets (Legacy)"
          description="Use a specific spreadsheet ID for all exports"
          delay={0.2}
        >
          <Input
            label="Default Spreadsheet ID"
            value={settings.googleSheetsId}
            onChange={(e) =>
              setSettings({ ...settings, googleSheetsId: e.target.value })
            }
            placeholder="Enter your Google Sheets ID"
            helperText="Leave empty to create a new spreadsheet each time"
          />
        </SettingsCard>

        {/* Twilio SMS */}
        <SettingsCard
          icon={<Phone className="w-5 h-5 text-primary-600" />}
          title="Twilio SMS"
          description="Configure Twilio for SMS outreach"
          delay={0.25}
        >
          <div className="space-y-4">
            <Input
              label="Account SID"
              value={settings.twilioAccountSid}
              onChange={(e) =>
                setSettings({ ...settings, twilioAccountSid: e.target.value })
              }
              placeholder="ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
            />
            <Input
              label="Auth Token"
              type="password"
              value={settings.twilioAuthToken}
              onChange={(e) =>
                setSettings({ ...settings, twilioAuthToken: e.target.value })
              }
              placeholder="Your Twilio auth token"
            />
            <Input
              label="Phone Number"
              value={settings.twilioPhoneNumber}
              onChange={(e) =>
                setSettings({ ...settings, twilioPhoneNumber: e.target.value })
              }
              placeholder="+1234567890"
            />
          </div>
        </SettingsCard>

        {/* Fast2SMS */}
        <SettingsCard
          icon={<MessageSquare className="w-5 h-5 text-primary-600" />}
          title="Fast2SMS (India)"
          description="Configure Fast2SMS for Indian phone numbers"
          delay={0.3}
        >
          <Input
            label="API Key"
            type="password"
            value={settings.fast2smsApiKey}
            onChange={(e) =>
              setSettings({ ...settings, fast2smsApiKey: e.target.value })
            }
            placeholder="Your Fast2SMS API key"
          />
        </SettingsCard>

        {/* Scraping Settings */}
        <SettingsCard
          icon={<Zap className="w-5 h-5 text-primary-600" />}
          title="Scraping Defaults"
          description="Configure default scraping behavior"
          delay={0.35}
        >
          <div className="space-y-4">
            <Input
              label="Default Target Count"
              type="number"
              value={settings.defaultTargetCount}
              onChange={(e) =>
                setSettings({
                  ...settings,
                  defaultTargetCount: parseInt(e.target.value) || 50,
                })
              }
              min={1}
              max={500}
            />
            <div className="flex items-center gap-3">
              <div className="relative">
                <input
                  type="checkbox"
                  id="headless"
                  checked={settings.headlessMode}
                  onChange={(e) =>
                    setSettings({ ...settings, headlessMode: e.target.checked })
                  }
                  className="w-5 h-5 text-primary-600 rounded-lg border-neutral-300 focus:ring-primary-500 cursor-pointer transition-all"
                />
              </div>
              <label htmlFor="headless" className="text-sm text-neutral-700 cursor-pointer select-none">
                Run browser in headless mode 
                <span className="text-neutral-400 ml-1">(recommended for speed)</span>
              </label>
            </div>
          </div>
        </SettingsCard>

        {/* Save Button */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4 }}
          className="pt-4"
        >
          <AnimatedButton 
            onClick={handleSave} 
            size="lg"
            loading={isSaving}
            glow
            className="w-full sm:w-auto"
          >
            {isSaving ? (
              "Saving..."
            ) : (
              <>
                <Save className="w-5 h-5 mr-2" />
                Save Settings
              </>
            )}
          </AnimatedButton>
        </motion.div>
      </div>
    </div>
  );
}
