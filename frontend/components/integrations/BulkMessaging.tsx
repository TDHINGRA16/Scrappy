// ========================================
// Bulk Messaging Component for WhatsApp
// ========================================

"use client";

import { useState } from "react";
import { useWhatsApp } from "@/hooks";
import { Button } from "@/components/common";
import type { Lead, WhatsAppBulkResponse } from "@/types";

interface BulkMessagingProps {
  leads: Lead[];
  onClose?: () => void;
}

const MESSAGE_PLACEHOLDERS = [
  { placeholder: "{name}", description: "Business name" },
  { placeholder: "{phone}", description: "Phone number" },
  { placeholder: "{address}", description: "Address" },
  { placeholder: "{website}", description: "Website" },
  { placeholder: "{rating}", description: "Rating" },
  { placeholder: "{category}", description: "Category" },
];

const DEFAULT_TEMPLATES = [
  {
    name: "Introduction",
    message: "Hi {name}! 👋 I came across your business and wanted to reach out. I offer services that could help grow your business. Would you be interested in a quick chat?",
  },
  {
    name: "Services Offer",
    message: "Hello {name}! I noticed your business at {address}. I specialize in helping businesses like yours increase their online presence. Can I share some ideas with you?",
  },
  {
    name: "Partnership",
    message: "Hi there! I'm reaching out to {name} because I believe we could create a great partnership. Your {rating}⭐ rating shows you care about quality. Let's connect!",
  },
];

export function BulkMessaging({ leads, onClose }: BulkMessagingProps) {
  const { status, isSending, sendBulkMessages } = useWhatsApp();
  
  const [messageTemplate, setMessageTemplate] = useState("");
  const [delayMs, setDelayMs] = useState(100);
  const [result, setResult] = useState<WhatsAppBulkResponse | null>(null);
  const [showResult, setShowResult] = useState(false);

  // Filter leads with phone numbers
  const leadsWithPhone = leads.filter((lead) => lead.phone);
  const leadsWithoutPhone = leads.length - leadsWithPhone.length;

  const handleSend = async () => {
    if (!messageTemplate.trim()) {
      return;
    }

    const response = await sendBulkMessages(leadsWithPhone, messageTemplate, delayMs);
    
    if (response) {
      setResult(response);
      setShowResult(true);
    }
  };

  const insertPlaceholder = (placeholder: string) => {
    setMessageTemplate((prev) => prev + placeholder);
  };

  const selectTemplate = (template: string) => {
    setMessageTemplate(template);
  };

  const previewMessage = () => {
    if (!leadsWithPhone.length || !messageTemplate) return messageTemplate;
    
    const sampleLead = leadsWithPhone[0];
    let preview = messageTemplate;
    
    preview = preview.replace(/{name}/g, sampleLead.name || "Business");
    preview = preview.replace(/{phone}/g, sampleLead.phone || "");
    preview = preview.replace(/{address}/g, sampleLead.address || "");
    preview = preview.replace(/{website}/g, sampleLead.website || "");
    preview = preview.replace(/{rating}/g, String(sampleLead.rating || ""));
    preview = preview.replace(/{category}/g, sampleLead.category || "");
    
    return preview;
  };

  // Check if user can send messages
  const canSend = status?.connected || status?.has_shared_access;

  if (!canSend) {
    return (
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6">
        <div className="text-center py-8">
          <div className="w-16 h-16 bg-gray-100 dark:bg-gray-700 rounded-full flex items-center justify-center mx-auto mb-4">
            <svg className="w-8 h-8 text-gray-400" fill="currentColor" viewBox="0 0 24 24">
              <path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413z"/>
            </svg>
          </div>
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
            WhatsApp Not Connected
          </h3>
          <p className="text-gray-600 dark:text-gray-400 mb-4">
            Connect your WhatsApp Business account in Settings to send bulk messages.
          </p>
          <Button variant="outline" onClick={onClose}>
            Close
          </Button>
        </div>
      </div>
    );
  }

  // Show results
  if (showResult && result) {
    return (
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6">
        <div className="text-center py-4">
          <div className={`w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-4 ${
            result.failed === 0 
              ? "bg-green-100 dark:bg-green-900"
              : "bg-yellow-100 dark:bg-yellow-900"
          }`}>
            {result.failed === 0 ? (
              <svg className="w-8 h-8 text-green-600 dark:text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
            ) : (
              <svg className="w-8 h-8 text-yellow-600 dark:text-yellow-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
              </svg>
            )}
          </div>
          
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
            Bulk Send Complete
          </h3>
          
          <div className="grid grid-cols-3 gap-4 my-6">
            <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-4">
              <p className="text-2xl font-bold text-gray-900 dark:text-white">{result.total}</p>
              <p className="text-sm text-gray-500 dark:text-gray-400">Total</p>
            </div>
            <div className="bg-green-50 dark:bg-green-900/20 rounded-lg p-4">
              <p className="text-2xl font-bold text-green-600 dark:text-green-400">{result.sent}</p>
              <p className="text-sm text-green-600 dark:text-green-400">Sent</p>
            </div>
            <div className="bg-red-50 dark:bg-red-900/20 rounded-lg p-4">
              <p className="text-2xl font-bold text-red-600 dark:text-red-400">{result.failed}</p>
              <p className="text-sm text-red-600 dark:text-red-400">Failed</p>
            </div>
          </div>

          {result.errors.length > 0 && (
            <div className="bg-red-50 dark:bg-red-900/20 rounded-lg p-4 mb-4 text-left">
              <p className="text-sm font-medium text-red-800 dark:text-red-200 mb-2">
                Errors ({result.errors.length}):
              </p>
              <ul className="text-xs text-red-700 dark:text-red-300 space-y-1 max-h-32 overflow-y-auto">
                {result.errors.map((err, i) => (
                  <li key={i}>
                    ...{err.phone}: {err.error}
                  </li>
                ))}
              </ul>
            </div>
          )}

          <Button variant="primary" onClick={() => {
            setShowResult(false);
            setResult(null);
            onClose?.();
          }}>
            Done
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6">
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
          📤 Send Bulk WhatsApp Messages
        </h3>
        {onClose && (
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        )}
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 gap-4 mb-6">
        <div className="bg-green-50 dark:bg-green-900/20 rounded-lg p-4">
          <p className="text-2xl font-bold text-green-600 dark:text-green-400">
            {leadsWithPhone.length}
          </p>
          <p className="text-sm text-green-700 dark:text-green-300">Leads with phone</p>
        </div>
        <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-4">
          <p className="text-2xl font-bold text-gray-600 dark:text-gray-400">
            {leadsWithoutPhone}
          </p>
          <p className="text-sm text-gray-500 dark:text-gray-400">Without phone</p>
        </div>
      </div>

      {/* Quick Templates */}
      <div className="mb-4">
        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
          Quick Templates
        </label>
        <div className="flex flex-wrap gap-2">
          {DEFAULT_TEMPLATES.map((template) => (
            <button
              key={template.name}
              onClick={() => selectTemplate(template.message)}
              className="px-3 py-1 text-xs bg-gray-100 hover:bg-gray-200 dark:bg-gray-700 dark:hover:bg-gray-600 rounded-full text-gray-700 dark:text-gray-300 transition-colors"
            >
              {template.name}
            </button>
          ))}
        </div>
      </div>

      {/* Message Template */}
      <div className="mb-4">
        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
          Message Template
        </label>
        <textarea
          value={messageTemplate}
          onChange={(e) => setMessageTemplate(e.target.value)}
          placeholder="Hi {name}! I noticed your business and wanted to reach out..."
          rows={4}
          className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-400 focus:ring-2 focus:ring-green-500 focus:border-green-500"
          maxLength={4096}
        />
        <p className="text-xs text-gray-500 mt-1">
          {messageTemplate.length}/4096 characters
        </p>
      </div>

      {/* Placeholders */}
      <div className="mb-4">
        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
          Insert Placeholders
        </label>
        <div className="flex flex-wrap gap-2">
          {MESSAGE_PLACEHOLDERS.map((item) => (
            <button
              key={item.placeholder}
              onClick={() => insertPlaceholder(item.placeholder)}
              className="px-2 py-1 text-xs bg-blue-100 hover:bg-blue-200 dark:bg-blue-900/30 dark:hover:bg-blue-900/50 rounded text-blue-700 dark:text-blue-300 transition-colors"
              title={item.description}
            >
              {item.placeholder}
            </button>
          ))}
        </div>
      </div>

      {/* Preview */}
      {messageTemplate && leadsWithPhone.length > 0 && (
        <div className="mb-4">
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            Preview (first lead: {leadsWithPhone[0].name})
          </label>
          <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-3 text-sm text-gray-700 dark:text-gray-300 whitespace-pre-wrap">
            {previewMessage()}
          </div>
        </div>
      )}

      {/* Delay Setting */}
      <div className="mb-6">
        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
          Delay between messages: {delayMs}ms
        </label>
        <input
          type="range"
          min="50"
          max="1000"
          step="50"
          value={delayMs}
          onChange={(e) => setDelayMs(Number(e.target.value))}
          className="w-full"
        />
        <p className="text-xs text-gray-500 mt-1">
          Higher delay = lower rate limiting risk
        </p>
      </div>

      {/* Account Info */}
      <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-3 mb-4 text-xs text-gray-600 dark:text-gray-400">
        Sending via: {status?.connected ? (
          <span className="font-medium text-green-600 dark:text-green-400">
            Your Account ({status.phone_number})
          </span>
        ) : (
          <span className="font-medium text-blue-600 dark:text-blue-400">
            Shared Account
          </span>
        )}
      </div>

      {/* Actions */}
      <div className="flex space-x-3">
        <Button
          variant="primary"
          onClick={handleSend}
          isLoading={isSending}
          disabled={!messageTemplate.trim() || leadsWithPhone.length === 0}
          className="bg-green-600 hover:bg-green-700"
        >
          <svg className="w-4 h-4 mr-2" fill="currentColor" viewBox="0 0 24 24">
            <path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413z"/>
          </svg>
          Send to {leadsWithPhone.length} Leads
        </Button>
        {onClose && (
          <Button variant="ghost" onClick={onClose}>
            Cancel
          </Button>
        )}
      </div>
    </div>
  );
}

export default BulkMessaging;
