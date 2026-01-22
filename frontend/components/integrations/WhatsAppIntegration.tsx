// ========================================
// WhatsApp Integration Component - Modernized
// ========================================

"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { MessageSquare, Phone, User, Key, Building, Check, AlertTriangle, ExternalLink, Zap } from "lucide-react";
import { useWhatsApp } from "@/hooks";
import { Input } from "@/components/common";
import { AnimatedCard } from "@/components/ui";
import { AnimatedButton } from "@/components/ui/animated-button";

export function WhatsAppIntegration() {
  const {
    status,
    isLoading,
    isConnecting,
    error,
    connect,
    disconnect,
    testConnection,
  } = useWhatsApp();

  const [showForm, setShowForm] = useState(false);
  const [showDisconnectConfirm, setShowDisconnectConfirm] = useState(false);
  const [formData, setFormData] = useState({
    phone_number_id: "",
    access_token: "",
    business_account_id: "",
    display_name: "",
  });
  const [formError, setFormError] = useState<string | null>(null);
  const [testResult, setTestResult] = useState<{ success: boolean; message: string } | null>(null);

  const handleConnect = async () => {
    setFormError(null);

    if (!formData.phone_number_id.trim() || !formData.access_token.trim()) {
      setFormError("Phone Number ID and Access Token are required");
      return;
    }

    const success = await connect({
      phone_number_id: formData.phone_number_id.trim(),
      access_token: formData.access_token.trim(),
      business_account_id: formData.business_account_id.trim() || undefined,
      display_name: formData.display_name.trim() || undefined,
    });

    if (success) {
      setShowForm(false);
      setFormData({
        phone_number_id: "",
        access_token: "",
        business_account_id: "",
        display_name: "",
      });
    } else {
      setFormError(error || "Failed to connect WhatsApp account");
    }
  };

  const handleDisconnect = async () => {
    const success = await disconnect();
    if (success) {
      setShowDisconnectConfirm(false);
    }
  };

  const handleTestConnection = async () => {
    setTestResult(null);
    const result = await testConnection();
    
    if (result.success) {
      setTestResult({
        success: true,
        message: `Connected via ${result.using === 'user_account' ? 'your account' : 'shared account'}: ${result.phone}`,
      });
    } else {
      setTestResult({
        success: false,
        message: "Connection test failed",
      });
    }
  };

  if (isLoading) {
    return (
      <AnimatedCard className="p-6">
        <div className="flex items-center space-x-3">
          <div className="w-12 h-12 bg-gradient-to-br from-green-500/10 to-emerald-500/10 rounded-xl flex items-center justify-center">
            <MessageSquare className="w-6 h-6 text-green-600" />
          </div>
          <div>
            <h3 className="text-lg font-semibold text-neutral-900">
              WhatsApp Business
            </h3>
            <p className="text-sm text-neutral-500">Loading...</p>
          </div>
        </div>
      </AnimatedCard>
    );
  }

  return (
    <AnimatedCard className="p-6">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center space-x-4">
          <div className="w-12 h-12 bg-gradient-to-br from-green-500/10 to-emerald-500/10 rounded-xl flex items-center justify-center flex-shrink-0">
            <MessageSquare className="w-6 h-6 text-green-600" />
          </div>
          <div>
            <h3 className="text-lg font-semibold text-neutral-900">
              WhatsApp Business
            </h3>
            <p className="text-sm text-neutral-500">
              {status?.connected
                ? "Send bulk WhatsApp messages to scraped leads"
                : status?.has_shared_access
                  ? "Use shared account or connect your own"
                  : "Connect your WhatsApp Business account"}
            </p>
          </div>
        </div>
        {status?.connected && (
          <span className="px-2.5 py-1 text-xs font-semibold bg-gradient-to-r from-green-500 to-emerald-500 text-white rounded-full">
            Connected
          </span>
        )}
        {!status?.connected && status?.has_shared_access && (
          <span className="px-2.5 py-1 text-xs font-semibold bg-gradient-to-r from-blue-500 to-primary-500 text-white rounded-full">
            Shared Available
          </span>
        )}
      </div>

      {/* Connected State */}
      {status?.connected && (
        <div className="space-y-4">
          <div className="bg-gradient-to-br from-neutral-50 to-green-50/30 rounded-xl p-4 border border-neutral-100">
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div>
                <span className="text-neutral-500 flex items-center gap-1.5">
                  <Phone className="w-3.5 h-3.5" />
                  Phone Number
                </span>
                <p className="font-medium text-neutral-900 mt-0.5">
                  {status.phone_number || "N/A"}
                </p>
              </div>
              <div>
                <span className="text-neutral-500 flex items-center gap-1.5">
                  <User className="w-3.5 h-3.5" />
                  Verified Name
                </span>
                <p className="font-medium text-neutral-900 mt-0.5">
                  {status.verified_name || status.display_name || "N/A"}
                </p>
              </div>
              <div>
                <span className="text-neutral-500 flex items-center gap-1.5">
                  <Zap className="w-3.5 h-3.5" />
                  Quality Rating
                </span>
                <p className="font-medium text-neutral-900 mt-0.5">
                  {status.quality_rating || "N/A"}
                </p>
              </div>
              <div>
                <span className="text-neutral-500">Connected</span>
                <p className="font-medium text-neutral-900 mt-0.5">
                  {status.connected_at
                    ? new Date(status.connected_at).toLocaleDateString()
                    : "N/A"}
                </p>
              </div>
            </div>
          </div>

          <div className="flex flex-wrap gap-2">
            <AnimatedButton
              variant="outline"
              size="sm"
              onClick={handleTestConnection}
            >
              Test Connection
            </AnimatedButton>
            <AnimatedButton
              variant="danger"
              size="sm"
              onClick={() => setShowDisconnectConfirm(true)}
            >
              Disconnect
            </AnimatedButton>
          </div>

          <AnimatePresence>
            {testResult && (
              <motion.div
                initial={{ opacity: 0, y: -10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -10 }}
                className={`p-3 rounded-xl text-sm flex items-center gap-2 ${
                  testResult.success 
                    ? "bg-green-50 text-green-800 border border-green-200"
                    : "bg-red-50 text-red-800 border border-red-200"
                }`}
              >
                {testResult.success ? (
                  <Check className="w-4 h-4 text-green-600" />
                ) : (
                  <AlertTriangle className="w-4 h-4 text-red-600" />
                )}
                {testResult.message}
              </motion.div>
            )}
          </AnimatePresence>

          {/* Disconnect Confirmation */}
          <AnimatePresence>
            {showDisconnectConfirm && (
              <motion.div
                initial={{ opacity: 0, y: -10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -10 }}
                className="bg-red-50 border border-red-200 rounded-xl p-4"
              >
                <p className="text-sm text-red-800 mb-3">
                  Are you sure you want to disconnect your WhatsApp account?
                </p>
                <div className="flex gap-2">
                  <AnimatedButton
                    variant="danger"
                    size="sm"
                    onClick={handleDisconnect}
                    loading={isLoading}
                  >
                    Yes, Disconnect
                  </AnimatedButton>
                  <AnimatedButton
                    variant="ghost"
                    size="sm"
                    onClick={() => setShowDisconnectConfirm(false)}
                  >
                    Cancel
                  </AnimatedButton>
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      )}

      {/* Not Connected State */}
      {!status?.connected && !showForm && (
        <div className="space-y-4">
          {status?.has_shared_access && (
            <div className="bg-gradient-to-br from-blue-50 to-primary-50/30 border border-blue-200 rounded-xl p-4">
              <p className="text-sm text-blue-800 flex items-start gap-2">
                <Zap className="w-4 h-4 text-blue-600 flex-shrink-0 mt-0.5" />
                <span>
                  <strong>Shared Access Available:</strong> You can send messages using our shared WhatsApp Business account, or connect your own for better deliverability and branding.
                </span>
              </p>
            </div>
          )}
          
          <AnimatedButton
            onClick={() => setShowForm(true)}
            glow
          >
            <MessageSquare className="w-4 h-4 mr-2" />
            Connect Your WhatsApp Business
          </AnimatedButton>

          <p className="text-xs text-neutral-500">
            Requires WhatsApp Business API access. Get credentials from{" "}
            <a
              href="https://business.facebook.com/settings/whatsapp-business-accounts"
              target="_blank"
              rel="noopener noreferrer"
              className="text-primary-600 hover:underline inline-flex items-center gap-1"
            >
              Meta Business Suite
              <ExternalLink className="w-3 h-3" />
            </a>
          </p>
        </div>
      )}

      {/* Connection Form */}
      <AnimatePresence>
        {showForm && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            exit={{ opacity: 0, height: 0 }}
            className="space-y-4 overflow-hidden"
          >
            <div className="bg-gradient-to-br from-amber-50 to-orange-50/30 border border-amber-200 rounded-xl p-4">
              <p className="text-sm text-amber-800 flex items-start gap-2">
                <AlertTriangle className="w-4 h-4 text-amber-600 flex-shrink-0 mt-0.5" />
                <span>
                  <strong>Important:</strong> You need WhatsApp Business API access (not regular WhatsApp). Get your Phone Number ID and Access Token from{" "}
                  <a
                    href="https://developers.facebook.com/apps"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="underline inline-flex items-center gap-1"
                  >
                    Meta Developer Portal
                    <ExternalLink className="w-3 h-3" />
                  </a>
                </span>
              </p>
            </div>

            <Input
              label="Phone Number ID *"
              placeholder="e.g., 123456789012345"
              value={formData.phone_number_id}
              onChange={(e) => setFormData({ ...formData, phone_number_id: e.target.value })}
              helperText="Found in WhatsApp Manager > Phone Numbers"
            />

            <Input
              label="Access Token *"
              type="password"
              placeholder="Your WhatsApp API access token"
              value={formData.access_token}
              onChange={(e) => setFormData({ ...formData, access_token: e.target.value })}
              helperText="Create a permanent token in Meta Developer Portal"
            />

            <Input
              label="Business Account ID (Optional)"
              placeholder="e.g., 123456789012345"
              value={formData.business_account_id}
              onChange={(e) => setFormData({ ...formData, business_account_id: e.target.value })}
              helperText="Required to fetch message templates"
            />

            <Input
              label="Display Name (Optional)"
              placeholder="My Business WhatsApp"
              value={formData.display_name}
              onChange={(e) => setFormData({ ...formData, display_name: e.target.value })}
              helperText="A friendly name for this account"
            />

            {formError && (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="bg-red-50 text-red-800 p-3 rounded-xl text-sm border border-red-200 flex items-center gap-2"
              >
                <AlertTriangle className="w-4 h-4 text-red-600" />
                {formError}
              </motion.div>
            )}

            <div className="flex gap-2">
              <AnimatedButton
                onClick={handleConnect}
                loading={isConnecting}
                glow
              >
                Connect Account
              </AnimatedButton>
              <AnimatedButton
                variant="ghost"
                onClick={() => {
                  setShowForm(false);
                  setFormError(null);
                }}
              >
                Cancel
              </AnimatedButton>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </AnimatedCard>
  );
}

export default WhatsAppIntegration;
