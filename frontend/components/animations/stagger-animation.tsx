// ========================================
// Staggered Children Animation
// ========================================

"use client";

import { motion } from "framer-motion";
import { cn } from "@/lib/utils";

interface StaggerContainerProps {
  children: React.ReactNode;
  className?: string;
  staggerDelay?: number;
  initialDelay?: number;
}

const containerVariants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: {
      staggerChildren: 0.1,
      delayChildren: 0.1,
    },
  },
};

export function StaggerContainer({
  children,
  className,
  staggerDelay = 0.1,
  initialDelay = 0.1,
}: StaggerContainerProps) {
  return (
    <motion.div
      variants={{
        hidden: { opacity: 0 },
        visible: {
          opacity: 1,
          transition: {
            staggerChildren: staggerDelay,
            delayChildren: initialDelay,
          },
        },
      }}
      initial="hidden"
      animate="visible"
      className={className}
    >
      {children}
    </motion.div>
  );
}

interface StaggerItemProps {
  children: React.ReactNode;
  className?: string;
  direction?: "up" | "down" | "left" | "right" | "scale";
}

const itemVariants = {
  up: {
    hidden: { opacity: 0, y: 20 },
    visible: { opacity: 1, y: 0 },
  },
  down: {
    hidden: { opacity: 0, y: -20 },
    visible: { opacity: 1, y: 0 },
  },
  left: {
    hidden: { opacity: 0, x: -20 },
    visible: { opacity: 1, x: 0 },
  },
  right: {
    hidden: { opacity: 0, x: 20 },
    visible: { opacity: 1, x: 0 },
  },
  scale: {
    hidden: { opacity: 0, scale: 0.8 },
    visible: { opacity: 1, scale: 1 },
  },
};

export function StaggerItem({
  children,
  className,
  direction = "up",
}: StaggerItemProps) {
  return (
    <motion.div
      variants={itemVariants[direction]}
      transition={{
        duration: 0.5,
        ease: [0.25, 0.1, 0.25, 1],
      }}
      className={className}
    >
      {children}
    </motion.div>
  );
}

export default StaggerContainer;
