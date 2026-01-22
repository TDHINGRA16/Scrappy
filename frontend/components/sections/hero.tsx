// ========================================
// Hero Section with GSAP Animations
// ========================================

"use client";

import { useEffect, useRef } from "react";
import { gsap } from "gsap";
import { ArrowRight, Sparkles, Play, Zap, Shield, Globe } from "lucide-react";
import { AnimatedButton } from "../ui/animated-button";
import Link from "next/link";

export function Hero() {
  const heroRef = useRef<HTMLDivElement>(null);
  const titleRef = useRef<HTMLHeadingElement>(null);
  const subtitleRef = useRef<HTMLParagraphElement>(null);
  const ctaRef = useRef<HTMLDivElement>(null);
  const statsRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const ctx = gsap.context(() => {
      const tl = gsap.timeline({ defaults: { ease: "power3.out" } });

      // Badge animation
      tl.from(".hero-badge", {
        opacity: 0,
        y: -20,
        duration: 0.6,
      });

      // Title animation - word by word with 3D rotation
      if (titleRef.current) {
        const words = titleRef.current.querySelectorAll(".word");
        tl.from(
          words,
          {
            opacity: 0,
            y: 50,
            rotationX: -90,
            stagger: 0.12,
            duration: 0.8,
            ease: "back.out(1.7)",
          },
          "-=0.3"
        );
      }

      // Subtitle fade in
      tl.from(
        subtitleRef.current,
        {
          opacity: 0,
          y: 30,
          duration: 0.8,
        },
        "-=0.4"
      );

      // CTA buttons stagger
      tl.from(
        ctaRef.current?.children || [],
        {
          opacity: 0,
          y: 20,
          stagger: 0.1,
          duration: 0.6,
        },
        "-=0.4"
      );

      // Stats counter
      tl.from(
        statsRef.current?.children || [],
        {
          opacity: 0,
          y: 20,
          stagger: 0.1,
          duration: 0.6,
        },
        "-=0.3"
      );

      // Floating background blobs
      gsap.to(".floating-blob", {
        y: -30,
        duration: 3,
        repeat: -1,
        yoyo: true,
        ease: "power1.inOut",
        stagger: {
          each: 0.5,
          from: "random",
        },
      });
    }, heroRef);

    return () => ctx.revert();
  }, []);

  return (
    <div
      ref={heroRef}
      className="relative min-h-screen flex items-center justify-center overflow-hidden bg-gradient-to-br from-primary-50 via-white to-secondary-50"
    >
      {/* Animated background blobs */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="floating-blob absolute top-20 left-[10%] w-72 h-72 bg-primary-200 rounded-full mix-blend-multiply filter blur-xl opacity-60" />
        <div className="floating-blob absolute top-40 right-[10%] w-96 h-96 bg-secondary-200 rounded-full mix-blend-multiply filter blur-xl opacity-60" />
        <div className="floating-blob absolute -bottom-20 left-1/3 w-80 h-80 bg-pink-200 rounded-full mix-blend-multiply filter blur-xl opacity-50" />
        <div className="floating-blob absolute bottom-40 right-1/4 w-64 h-64 bg-cyan-200 rounded-full mix-blend-multiply filter blur-xl opacity-50" />
      </div>

      {/* Grid pattern overlay */}
      <div
        className="absolute inset-0 opacity-[0.02]"
        style={{
          backgroundImage: `url("data:image/svg+xml,%3Csvg width='60' height='60' viewBox='0 0 60 60' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='none' fill-rule='evenodd'%3E%3Cg fill='%23000000' fill-opacity='1'%3E%3Cpath d='M36 34v-4h-2v4h-4v2h4v4h2v-4h4v-2h-4zm0-30V0h-2v4h-4v2h4v4h2V6h4V4h-4zM6 34v-4H4v4H0v2h4v4h2v-4h4v-2H6zM6 4V0H4v4H0v2h4v4h2V6h4V4H6z'/%3E%3C/g%3E%3C/g%3E%3C/svg%3E")`,
        }}
      />

      <div className="relative z-10 text-center px-4 max-w-6xl mx-auto">
        {/* Badge */}
        <div className="hero-badge inline-flex items-center gap-2 px-4 py-2 bg-white rounded-full shadow-lg mb-8 border border-neutral-200/50">
          <Sparkles className="w-4 h-4 text-primary-600" />
          <span className="text-sm font-medium text-neutral-700">
            Now with AI-powered lead enrichment
          </span>
          <span className="px-2 py-0.5 text-xs font-semibold bg-primary-100 text-primary-700 rounded-full">
            New
          </span>
        </div>

        {/* Title with perspective */}
        <div className="perspective-1000">
          <h1
            ref={titleRef}
            className="text-5xl sm:text-6xl md:text-7xl lg:text-8xl font-bold mb-6 text-neutral-900 leading-tight"
          >
            <span className="word inline-block mr-2 sm:mr-4">Scrape.</span>
            <span className="word inline-block mr-2 sm:mr-4">Enrich.</span>
            <span className="word inline-block">
              <span className="bg-gradient-to-r from-primary-600 via-secondary-600 to-primary-600 bg-clip-text text-transparent bg-[length:200%_auto] animate-gradient">
                Convert.
              </span>
            </span>
          </h1>
        </div>

        {/* Subtitle */}
        <p
          ref={subtitleRef}
          className="text-lg sm:text-xl md:text-2xl text-neutral-600 mb-12 max-w-3xl mx-auto leading-relaxed"
        >
          Extract verified leads from Google Maps, enrich with contact data,
          and automate outreach—all in one powerful platform.
        </p>

        {/* CTA Buttons */}
        <div
          ref={ctaRef}
          className="flex flex-col sm:flex-row gap-4 justify-center items-center"
        >
          <Link href="/auth/signup">
            <AnimatedButton
              size="lg"
              icon={<ArrowRight className="w-5 h-5" />}
              iconPosition="right"
              glow
            >
              Start Free Trial
            </AnimatedButton>
          </Link>
          <AnimatedButton size="lg" variant="outline" icon={<Play className="w-5 h-5" />}>
            Watch Demo
          </AnimatedButton>
        </div>

        {/* Trust indicators */}
        <div className="flex flex-wrap justify-center gap-6 mt-10 text-sm text-neutral-500">
          <div className="flex items-center gap-2">
            <Shield className="w-4 h-4 text-success-500" />
            <span>No credit card required</span>
          </div>
          <div className="flex items-center gap-2">
            <Zap className="w-4 h-4 text-warning-500" />
            <span>Setup in 2 minutes</span>
          </div>
          <div className="flex items-center gap-2">
            <Globe className="w-4 h-4 text-primary-500" />
            <span>Used in 50+ countries</span>
          </div>
        </div>

        {/* Stats */}
        <div
          ref={statsRef}
          className="grid grid-cols-2 sm:grid-cols-4 gap-6 sm:gap-8 mt-16 max-w-3xl mx-auto"
        >
          {[
            { value: "10K+", label: "Active Users" },
            { value: "5M+", label: "Leads Scraped" },
            { value: "99.9%", label: "Uptime" },
            { value: "4.9", label: "User Rating" },
          ].map((stat, index) => (
            <div key={index} className="text-center">
              <div className="text-3xl sm:text-4xl font-bold text-neutral-900 mb-1">
                {stat.value}
              </div>
              <div className="text-sm text-neutral-600">{stat.label}</div>
            </div>
          ))}
        </div>
      </div>

      {/* Bottom gradient fade */}
      <div className="absolute bottom-0 left-0 right-0 h-32 bg-gradient-to-t from-white to-transparent pointer-events-none" />
    </div>
  );
}

export default Hero;
