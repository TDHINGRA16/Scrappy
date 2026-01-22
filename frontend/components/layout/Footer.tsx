// ========================================
// Footer Component - Redesigned with Modern Styling
// ========================================

"use client";

import Link from "next/link";
import { motion } from "framer-motion";
import { Zap, Github, Twitter, Linkedin, Mail, Heart } from "lucide-react";

export function Footer() {
  const currentYear = new Date().getFullYear();

  const footerLinks = {
    product: [
      { label: "Features", href: "/features" },
      { label: "Pricing", href: "/pricing" },
      { label: "Documentation", href: "/docs" },
      { label: "API", href: "/api" },
    ],
    company: [
      { label: "About", href: "/about" },
      { label: "Blog", href: "/blog" },
      { label: "Careers", href: "/careers" },
      { label: "Contact", href: "/contact" },
    ],
    legal: [
      { label: "Privacy Policy", href: "/privacy" },
      { label: "Terms of Service", href: "/terms" },
      { label: "Cookie Policy", href: "/cookies" },
    ],
  };

  const socialLinks = [
    { icon: <Github className="w-5 h-5" />, href: "https://github.com", label: "GitHub" },
    { icon: <Twitter className="w-5 h-5" />, href: "https://twitter.com", label: "Twitter" },
    { icon: <Linkedin className="w-5 h-5" />, href: "https://linkedin.com", label: "LinkedIn" },
    { icon: <Mail className="w-5 h-5" />, href: "mailto:hello@scrappy.io", label: "Email" },
  ];

  return (
    <footer className="bg-neutral-900 text-neutral-300 relative overflow-hidden">
      {/* Gradient overlay */}
      <div className="absolute inset-0 bg-gradient-to-b from-neutral-900 via-neutral-900 to-neutral-950" />
      
      {/* Decorative gradient orbs */}
      <div className="absolute top-0 left-1/4 w-96 h-96 bg-primary-500/5 rounded-full blur-3xl" />
      <div className="absolute bottom-0 right-1/4 w-96 h-96 bg-secondary-500/5 rounded-full blur-3xl" />

      <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-12 mb-12">
          {/* Brand */}
          <div className="lg:col-span-2">
            <Link href="/" className="flex items-center gap-2.5 mb-6 group">
              <div className="w-10 h-10 bg-gradient-to-br from-primary-500 to-secondary-500 rounded-xl flex items-center justify-center shadow-lg shadow-primary-500/25">
                <Zap className="w-5 h-5 text-white" />
              </div>
              <span className="text-2xl font-bold text-white group-hover:text-primary-400 transition-colors">
                Scrappy
              </span>
            </Link>
            <p className="text-neutral-400 mb-6 max-w-md leading-relaxed">
              Professional-grade Google Maps lead scraper. Extract business data
              at scale with intelligent deduplication, Google Sheets integration, 
              and multi-channel outreach capabilities.
            </p>
            {/* Social Links */}
            <div className="flex items-center gap-3">
              {socialLinks.map((social) => (
                <motion.a
                  key={social.label}
                  href={social.href}
                  target="_blank"
                  rel="noopener noreferrer"
                  whileHover={{ scale: 1.1, y: -2 }}
                  whileTap={{ scale: 0.95 }}
                  className="w-10 h-10 bg-neutral-800 hover:bg-neutral-700 rounded-xl flex items-center justify-center text-neutral-400 hover:text-white transition-colors"
                  aria-label={social.label}
                >
                  {social.icon}
                </motion.a>
              ))}
            </div>
          </div>

          {/* Product Links */}
          <div>
            <h3 className="font-semibold text-white mb-4">Product</h3>
            <ul className="space-y-3">
              {footerLinks.product.map((link) => (
                <li key={link.href}>
                  <Link
                    href={link.href}
                    className="text-neutral-400 hover:text-white transition-colors inline-flex items-center gap-1 group"
                  >
                    <span>{link.label}</span>
                    <span className="opacity-0 group-hover:opacity-100 transition-opacity">→</span>
                  </Link>
                </li>
              ))}
            </ul>
          </div>

          {/* Company Links */}
          <div>
            <h3 className="font-semibold text-white mb-4">Company</h3>
            <ul className="space-y-3">
              {footerLinks.company.map((link) => (
                <li key={link.href}>
                  <Link
                    href={link.href}
                    className="text-neutral-400 hover:text-white transition-colors inline-flex items-center gap-1 group"
                  >
                    <span>{link.label}</span>
                    <span className="opacity-0 group-hover:opacity-100 transition-opacity">→</span>
                  </Link>
                </li>
              ))}
            </ul>
          </div>

          {/* Legal Links */}
          <div>
            <h3 className="font-semibold text-white mb-4">Legal</h3>
            <ul className="space-y-3">
              {footerLinks.legal.map((link) => (
                <li key={link.href}>
                  <Link
                    href={link.href}
                    className="text-neutral-400 hover:text-white transition-colors inline-flex items-center gap-1 group"
                  >
                    <span>{link.label}</span>
                    <span className="opacity-0 group-hover:opacity-100 transition-opacity">→</span>
                  </Link>
                </li>
              ))}
            </ul>
          </div>
        </div>

        {/* Bottom bar */}
        <div className="pt-8 border-t border-neutral-800 flex flex-col md:flex-row items-center justify-between gap-4">
          <p className="text-neutral-500 text-sm flex items-center gap-1">
            © {currentYear} Scrappy. Made with 
            <Heart className="w-4 h-4 text-error-500 fill-error-500 inline" /> 
            for lead generators.
          </p>
          <div className="flex items-center gap-6 text-sm">
            <span className="text-neutral-500">
              Powered by{" "}
              <span className="text-primary-400 font-medium">Next.js</span>
              {" "}+{" "}
              <span className="text-secondary-400 font-medium">Python</span>
            </span>
          </div>
        </div>
      </div>
    </footer>
  );
}

export default Footer;
