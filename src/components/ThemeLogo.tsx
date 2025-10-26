"use client";

import { useTheme } from "next-themes";
import { useEffect, useState } from "react";
import Image from "next/image";

interface ThemeLogoProps {
  width?: number;
  height?: number;
  className?: string;
}

export function ThemeLogo({ width = 150, height = 60, className = "" }: ThemeLogoProps) {
  const { theme, resolvedTheme } = useTheme();
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  // Determine which logo to use
  const currentTheme = mounted ? (resolvedTheme || theme) : 'light';
  const logoSrc = currentTheme === 'dark' ? '/IMS_logo_Final.png' : '/IMS_Logo_Horizontal.png';

  if (!mounted) {
    // Return a placeholder with the same dimensions to avoid layout shift
    return <div style={{ width, height }} className={className} />;
  }

  return (
    <div className={`relative ${className}`} style={{ width, height }}>
      <Image
        src={logoSrc}
        alt="IMS Logo"
        width={width}
        height={height}
        className="object-contain transition-opacity duration-300"
        priority
      />
    </div>
  );
}
