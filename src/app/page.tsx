"use client";

import { useState } from "react";
import { LandingPage } from "@/components/layout/LandingPage";
import { MainDashboard } from "@/components/layout/MainDashboard";

export default function Home() {
  const [showDashboard, setShowDashboard] = useState(false);

  if (!showDashboard) {
    return <LandingPage onDataLoaded={() => setShowDashboard(true)} />;
  }

  return (
    <main className="min-h-screen bg-background">
      <MainDashboard onBackToHome={() => setShowDashboard(false)} />
    </main>
  );
}
