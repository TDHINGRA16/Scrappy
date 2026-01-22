// ========================================
// Home Page (Landing) - Redesigned with Animations
// ========================================

"use client";

import Link from "next/link";
import { useRef, useEffect } from "react";
import { motion } from "framer-motion";
import gsap from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";
import { 
  Zap, 
  CheckCircle2, 
  FileSpreadsheet, 
  MessageSquare, 
  Gauge, 
  Database,
  ArrowRight,
  Sparkles,
  Star
} from "lucide-react";
import { Header } from "@/components/layout/Header";
import { Footer } from "@/components/layout/Footer";
import { Hero } from "@/components/sections/hero";
import { AnimatedButton } from "@/components/ui/animated-button";
import { AnimatedCard } from "@/components/ui/animated-card";
import { ScrollReveal, CounterAnimation } from "@/components/animations/scroll-reveal";
import { StaggerContainer, StaggerItem } from "@/components/animations/stagger-animation";

// Register GSAP plugins
if (typeof window !== "undefined") {
  gsap.registerPlugin(ScrollTrigger);
}

// ========================================
// Feature Card Component
// ========================================

interface FeatureCardProps {
  icon: React.ReactNode;
  title: string;
  description: string;
  color: string;
  delay?: number;
}

function FeatureCard({ icon, title, description, color, delay = 0 }: FeatureCardProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 30 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, margin: "-50px" }}
      transition={{ duration: 0.5, delay }}
    >
      <AnimatedCard variant="elevated" className="h-full group">
        <div className={`w-12 h-12 ${color} rounded-xl flex items-center justify-center mb-6 transition-transform duration-300 group-hover:scale-110`}>
          {icon}
        </div>
        <h3 className="text-xl font-semibold text-neutral-900 mb-3">
          {title}
        </h3>
        <p className="text-neutral-600 leading-relaxed">
          {description}
        </p>
      </AnimatedCard>
    </motion.div>
  );
}

// ========================================
// Stats Component
// ========================================

function StatsSection() {
  const stats = [
    { value: 10000, label: "Leads Generated", suffix: "+" },
    { value: 500, label: "Happy Users", suffix: "+" },
    { value: 99.9, label: "Uptime", suffix: "%" },
    { value: 24, label: "Support", suffix: "/7" },
  ];

  return (
    <section className="py-20 bg-gradient-to-r from-primary-600 via-primary-700 to-secondary-600 relative overflow-hidden">
      {/* Background decoration */}
      <div className="absolute inset-0 opacity-10">
        <div className="absolute top-0 left-1/4 w-96 h-96 bg-white rounded-full blur-3xl" />
        <div className="absolute bottom-0 right-1/4 w-96 h-96 bg-white rounded-full blur-3xl" />
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-8">
          {stats.map((stat, index) => (
            <motion.div
              key={stat.label}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.5, delay: index * 0.1 }}
              className="text-center"
            >
              <div className="text-4xl md:text-5xl font-bold text-white mb-2">
                <CounterAnimation end={stat.value} duration={2} />
                {stat.suffix}
              </div>
              <div className="text-primary-100 font-medium">{stat.label}</div>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}

// ========================================
// Testimonials Component
// ========================================

function TestimonialsSection() {
  const testimonials = [
    {
      quote: "Scrappy has completely transformed our lead generation process. We're now getting 3x more qualified leads.",
      author: "Sarah Chen",
      role: "Marketing Director",
      company: "TechStart Inc.",
      avatar: "SC",
    },
    {
      quote: "The Google Sheets integration is seamless. Our sales team can access leads instantly.",
      author: "Michael Ross",
      role: "Sales Manager",
      company: "GrowthCo",
      avatar: "MR",
    },
    {
      quote: "Best ROI we've ever had from a lead generation tool. Highly recommended!",
      author: "Emily Watson",
      role: "Founder",
      company: "LocalBiz Pro",
      avatar: "EW",
    },
  ];

  return (
    <section className="py-24 bg-neutral-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <ScrollReveal direction="up">
          <div className="text-center mb-16">
            <span className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-secondary-100 text-secondary-700 text-sm font-medium mb-4">
              <Star className="w-4 h-4" />
              Testimonials
            </span>
            <h2 className="text-3xl md:text-4xl font-bold text-neutral-900 mb-4">
              Loved by businesses worldwide
            </h2>
            <p className="text-lg text-neutral-600 max-w-2xl mx-auto">
              See what our customers have to say about their experience with Scrappy.
            </p>
          </div>
        </ScrollReveal>

        <div className="grid md:grid-cols-3 gap-8">
          {testimonials.map((testimonial, index) => (
            <motion.div
              key={testimonial.author}
              initial={{ opacity: 0, y: 30 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.5, delay: index * 0.1 }}
            >
              <AnimatedCard variant="glass" className="h-full">
                <div className="flex gap-1 mb-4">
                  {[...Array(5)].map((_, i) => (
                    <Star key={i} className="w-5 h-5 fill-warning-400 text-warning-400" />
                  ))}
                </div>
                <p className="text-neutral-700 mb-6 italic">"{testimonial.quote}"</p>
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-full bg-gradient-to-br from-primary-500 to-secondary-500 flex items-center justify-center text-white font-semibold text-sm">
                    {testimonial.avatar}
                  </div>
                  <div>
                    <div className="font-semibold text-neutral-900">{testimonial.author}</div>
                    <div className="text-sm text-neutral-500">
                      {testimonial.role} at {testimonial.company}
                    </div>
                  </div>
                </div>
              </AnimatedCard>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}

// ========================================
// CTA Section
// ========================================

function CTASection() {
  return (
    <section className="py-24 relative overflow-hidden">
      {/* Gradient background */}
      <div className="absolute inset-0 bg-gradient-to-br from-neutral-900 via-neutral-800 to-neutral-900" />
      
      {/* Animated gradient orbs */}
      <div className="absolute inset-0 overflow-hidden">
        <motion.div
          animate={{ 
            x: [0, 100, 0],
            y: [0, -50, 0],
          }}
          transition={{ duration: 20, repeat: Infinity, ease: "linear" }}
          className="absolute top-0 left-1/4 w-[600px] h-[600px] bg-primary-500/20 rounded-full blur-3xl"
        />
        <motion.div
          animate={{ 
            x: [0, -100, 0],
            y: [0, 50, 0],
          }}
          transition={{ duration: 15, repeat: Infinity, ease: "linear" }}
          className="absolute bottom-0 right-1/4 w-[600px] h-[600px] bg-secondary-500/20 rounded-full blur-3xl"
        />
      </div>

      <div className="max-w-4xl mx-auto text-center px-4 sm:px-6 lg:px-8 relative">
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6 }}
        >
          <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-white/10 backdrop-blur-sm text-white/80 text-sm font-medium mb-6">
            <Sparkles className="w-4 h-4" />
            Start for free, no credit card required
          </div>
          <h2 className="text-3xl md:text-5xl font-bold text-white mb-6">
            Ready to supercharge your{" "}
            <span className="bg-gradient-to-r from-primary-400 to-secondary-400 bg-clip-text text-transparent">
              lead generation
            </span>
            ?
          </h2>
          <p className="text-xl text-neutral-300 mb-10 max-w-2xl mx-auto">
            Join thousands of businesses using Scrappy to find and reach new customers.
          </p>
          <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
            <Link href="/auth/signup">
              <AnimatedButton size="lg" glow className="min-w-[200px]">
                Get Started Free
                <ArrowRight className="w-5 h-5 ml-2" />
              </AnimatedButton>
            </Link>
            <Link href="/dashboard">
              <AnimatedButton variant="outline" size="lg" className="min-w-[200px] border-white/20 text-white hover:bg-white/10">
                View Demo
              </AnimatedButton>
            </Link>
          </div>
        </motion.div>
      </div>
    </section>
  );
}

// ========================================
// Main Page Component
// ========================================

export default function HomePage() {
  const features = [
    {
      icon: <Zap className="w-6 h-6 text-primary-600" />,
      title: "Parallel Extraction",
      description: "Extract data from multiple business cards simultaneously using advanced async processing for maximum speed.",
      color: "bg-primary-100",
    },
    {
      icon: <CheckCircle2 className="w-6 h-6 text-success-600" />,
      title: "Smart Deduplication",
      description: "Automatically remove duplicate leads using Place ID, CID, and URL-based matching for clean data.",
      color: "bg-success-100",
    },
    {
      icon: <FileSpreadsheet className="w-6 h-6 text-secondary-600" />,
      title: "Google Sheets Export",
      description: "One-click export to Google Sheets. Create new spreadsheets or append to existing ones automatically.",
      color: "bg-secondary-100",
    },
    {
      icon: <MessageSquare className="w-6 h-6 text-warning-600" />,
      title: "SMS & WhatsApp Outreach",
      description: "Built-in messaging with Twilio, Fast2SMS, and WhatsApp integration. Reach leads instantly.",
      color: "bg-warning-100",
    },
    {
      icon: <Gauge className="w-6 h-6 text-error-600" />,
      title: "Smart Rate Limiting",
      description: "Intelligent rate limiting to avoid detection. Mimics human behavior for reliable, consistent scraping.",
      color: "bg-error-100",
    },
    {
      icon: <Database className="w-6 h-6 text-indigo-600" />,
      title: "Complete Data Fields",
      description: "Extract 15+ data fields including name, phone, email, website, address, rating, reviews, and more.",
      color: "bg-indigo-100",
    },
  ];

  return (
    <div className="min-h-screen flex flex-col bg-white">
      <Header />

      <main className="flex-1">
        {/* Hero Section */}
        <Hero />

        {/* Features Section */}
        <section className="py-24 bg-white relative">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <ScrollReveal direction="up">
              <div className="text-center mb-16">
                <span className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-primary-100 text-primary-700 text-sm font-medium mb-4">
                  <Sparkles className="w-4 h-4" />
                  Features
                </span>
                <h2 className="text-3xl md:text-4xl font-bold text-neutral-900 mb-4">
                  Everything you need for lead generation
                </h2>
                <p className="text-lg text-neutral-600 max-w-2xl mx-auto">
                  Built with best practices from industry leaders like Linear, Vercel, and Stripe.
                </p>
              </div>
            </ScrollReveal>

            <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
              {features.map((feature, index) => (
                <FeatureCard
                  key={feature.title}
                  {...feature}
                  delay={index * 0.1}
                />
              ))}
            </div>
          </div>
        </section>

        {/* Stats Section */}
        <StatsSection />

        {/* Testimonials Section */}
        <TestimonialsSection />

        {/* CTA Section */}
        <CTASection />
      </main>

      <Footer />
    </div>
  );
}
