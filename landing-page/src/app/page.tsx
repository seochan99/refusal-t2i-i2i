"use client";

import Image from "next/image";
import { useState, useEffect } from "react";

// Dark mode toggle component
function ThemeToggle() {
  const [isDark, setIsDark] = useState(true);

  useEffect(() => {
    const stored = localStorage.getItem("theme");
    if (stored === "light") {
      setIsDark(false);
      document.documentElement.classList.remove("dark");
    } else {
      setIsDark(true);
      document.documentElement.classList.add("dark");
    }
  }, []);

  const toggleTheme = () => {
    if (isDark) {
      document.documentElement.classList.remove("dark");
      localStorage.setItem("theme", "light");
    } else {
      document.documentElement.classList.add("dark");
      localStorage.setItem("theme", "dark");
    }
    setIsDark(!isDark);
  };

  return (
    <button
      onClick={toggleTheme}
      className="p-2.5 rounded-lg bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 transition-colors border border-slate-200 dark:border-slate-700"
      aria-label="Toggle theme"
    >
      {isDark ? (
        <svg className="w-5 h-5 text-amber-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z" />
        </svg>
      ) : (
        <svg className="w-5 h-5 text-slate-700" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z" />
        </svg>
      )}
    </button>
  );
}

// Navigation component
function Navigation() {
  const [isScrolled, setIsScrolled] = useState(false);

  useEffect(() => {
    const handleScroll = () => {
      setIsScrolled(window.scrollY > 20);
    };
    window.addEventListener("scroll", handleScroll);
    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  return (
    <nav className={`fixed top-0 left-0 right-0 z-50 transition-all duration-300 ${
      isScrolled
        ? "bg-white/80 dark:bg-slate-900/80 nav-blur shadow-lg shadow-slate-200/20 dark:shadow-slate-900/50"
        : "bg-transparent"
    }`}>
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 bg-gradient-to-br from-amber-400 to-orange-500 rounded-lg flex items-center justify-center">
              <span className="text-white font-bold text-sm">I2I</span>
            </div>
            <span className="font-semibold text-slate-800 dark:text-white hidden sm:block">Demographic Bias Study</span>
          </div>

          <div className="hidden md:flex items-center gap-8">
            <a href="#findings" className="text-sm text-slate-600 dark:text-slate-300 hover:text-amber-500 dark:hover:text-amber-400 transition-colors">Findings</a>
            <a href="#failures" className="text-sm text-slate-600 dark:text-slate-300 hover:text-amber-500 dark:hover:text-amber-400 transition-colors">Failure Modes</a>
            <a href="#disparity" className="text-sm text-slate-600 dark:text-slate-300 hover:text-amber-500 dark:hover:text-amber-400 transition-colors">Disparity</a>
            <a href="#method" className="text-sm text-slate-600 dark:text-slate-300 hover:text-amber-500 dark:hover:text-amber-400 transition-colors">Method</a>
            <a href="#citation" className="text-sm text-slate-600 dark:text-slate-300 hover:text-amber-500 dark:hover:text-amber-400 transition-colors">Citation</a>
          </div>

          <div className="flex items-center gap-3">
            <ThemeToggle />
            <a
              href="https://github.com"
              target="_blank"
              rel="noopener noreferrer"
              className="p-2.5 rounded-lg bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 transition-colors border border-slate-200 dark:border-slate-700"
            >
              <svg className="w-5 h-5 text-slate-700 dark:text-slate-300" fill="currentColor" viewBox="0 0 24 24">
                <path fillRule="evenodd" d="M12 2C6.477 2 2 6.484 2 12.017c0 4.425 2.865 8.18 6.839 9.504.5.092.682-.217.682-.483 0-.237-.008-.868-.013-1.703-2.782.605-3.369-1.343-3.369-1.343-.454-1.158-1.11-1.466-1.11-1.466-.908-.62.069-.608.069-.608 1.003.07 1.531 1.032 1.531 1.032.892 1.53 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.029-2.688-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.026A9.564 9.564 0 0112 6.844c.85.004 1.705.115 2.504.337 1.909-1.296 2.747-1.027 2.747-1.027.546 1.379.202 2.398.1 2.651.64.7 1.028 1.595 1.028 2.688 0 3.848-2.339 4.695-4.566 4.943.359.309.678.92.678 1.855 0 1.338-.012 2.419-.012 2.747 0 .268.18.58.688.482A10.019 10.019 0 0022 12.017C22 6.484 17.522 2 12 2z" clipRule="evenodd" />
              </svg>
            </a>
          </div>
        </div>
      </div>
    </nav>
  );
}

// Stat card component
function StatCard({ value, label, desc, delay }: { value: string; label: string; desc: string; delay: number }) {
  return (
    <div
      className="bg-white dark:bg-slate-800/50 border border-slate-200 dark:border-slate-700 rounded-2xl p-6 text-center card-hover hover:border-amber-500/50"
      style={{ animationDelay: `${delay}ms` }}
    >
      <div className="text-3xl md:text-4xl font-bold gradient-text mb-2">
        {value}
      </div>
      <div className="text-slate-800 dark:text-white font-semibold mb-1">{label}</div>
      <div className="text-slate-500 dark:text-slate-400 text-sm">{desc}</div>
    </div>
  );
}

export default function Home() {
  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-900 transition-colors">
      <Navigation />

      {/* Hero Section */}
      <header className="relative overflow-hidden pt-16">
        <div className="absolute inset-0 animated-gradient opacity-50"></div>
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-amber-500/10 via-transparent to-transparent"></div>

        <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-20 pb-16">
          <div className="text-center">
            <div className="inline-flex items-center px-4 py-2 rounded-full bg-amber-500/10 dark:bg-amber-500/20 border border-amber-500/30 mb-8">
              <span className="relative flex h-2 w-2 mr-2">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-amber-400 opacity-75"></span>
                <span className="relative inline-flex rounded-full h-2 w-2 bg-amber-500"></span>
              </span>
              <span className="text-amber-600 dark:text-amber-400 text-sm font-medium">IJCAI 2026 Under Review</span>
            </div>

            <h1 className="text-4xl sm:text-5xl md:text-6xl lg:text-7xl font-bold text-slate-900 dark:text-white mb-6 leading-tight tracking-tight">
              Evaluating Demographic<br />
              <span className="gradient-text">Misrepresentation</span><br />
              <span className="text-3xl sm:text-4xl md:text-5xl lg:text-6xl">in I2I Portrait Editing</span>
            </h1>

            <p className="text-lg md:text-xl text-slate-600 dark:text-slate-300 max-w-3xl mx-auto mb-10 leading-relaxed">
              We systematically study demographic-conditioned failures in instruction-guided image-to-image editing,
              revealing <span className="text-amber-600 dark:text-amber-400 font-semibold">pervasive skin lightening</span> and <span className="text-amber-600 dark:text-amber-400 font-semibold">stereotype replacement</span> across open-weight models.
            </p>

            <div className="flex flex-wrap justify-center gap-4">
              <a
                href="#findings"
                className="group px-8 py-3.5 bg-gradient-to-r from-amber-500 to-orange-500 hover:from-amber-400 hover:to-orange-400 text-white font-semibold rounded-xl transition-all shadow-lg shadow-amber-500/25 hover:shadow-xl hover:shadow-amber-500/30 hover:-translate-y-0.5"
              >
                View Findings
                <svg className="inline-block ml-2 w-4 h-4 group-hover:translate-x-1 transition-transform" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7l5 5m0 0l-5 5m5-5H6" />
                </svg>
              </a>
              <a
                href="#citation"
                className="px-8 py-3.5 border-2 border-slate-300 dark:border-slate-600 hover:border-amber-500 dark:hover:border-amber-500 text-slate-700 dark:text-white font-semibold rounded-xl transition-all hover:-translate-y-0.5"
              >
                Read Paper
              </a>
            </div>
          </div>
        </div>
      </header>

      {/* Teaser Figure */}
      <section className="py-12 md:py-16">
        <div className="max-w-6xl mx-auto px-4">
          <div className="relative rounded-2xl overflow-hidden shadow-2xl shadow-slate-200/50 dark:shadow-slate-900/50 border border-slate-200 dark:border-slate-700">
            <Image
              src="/assets/figure0.png"
              alt="Qualitative examples of demographic-conditioned failures"
              width={1200}
              height={400}
              className="w-full"
              priority
            />
          </div>
          <p className="text-center text-slate-500 dark:text-slate-400 mt-6 text-sm max-w-3xl mx-auto">
            <span className="font-semibold text-slate-700 dark:text-slate-300">Figure 1:</span> Our proposed Feature Prompt approach (bottom row) preserves subject identity across racial groups,
            while baseline methods (middle row) exhibit stereotype replacement - changing race, gender, or applying excessive aging.
          </p>
        </div>
      </section>

      {/* Key Statistics */}
      <section id="findings" className="py-20 md:py-24">
        <div className="max-w-7xl mx-auto px-4">
          <div className="text-center mb-16">
            <span className="inline-block px-4 py-1.5 rounded-full bg-amber-500/10 dark:bg-amber-500/20 text-amber-600 dark:text-amber-400 text-sm font-medium mb-4">
              Key Findings
            </span>
            <h2 className="text-3xl md:text-4xl font-bold text-slate-900 dark:text-white mb-4">
              Systematic Demographic Bias
            </h2>
            <p className="text-slate-600 dark:text-slate-400 max-w-2xl mx-auto text-lg">
              Our analysis of 5,040 edited images reveals pervasive demographic bias across all tested models.
            </p>
          </div>

          <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-6">
            <StatCard value="62-71%" label="Skin Lightening Rate" desc="of edited outputs show lighter skin tones" delay={0} />
            <StatCard value="72-75%" label="Indian/Black Impact" desc="vs 44% for White subjects" delay={100} />
            <StatCard value="84-86%" label="Stereotype Adherence" desc="follow gender-occupation stereotypes" delay={200} />
            <StatCard value="-1.48pt" label="Mitigation Effect" desc="race change reduction for Black subjects" delay={300} />
          </div>
        </div>
      </section>

      {/* Failure Modes */}
      <section id="failures" className="py-20 md:py-24 bg-slate-100/50 dark:bg-slate-800/30">
        <div className="max-w-7xl mx-auto px-4">
          <div className="text-center mb-16">
            <span className="inline-block px-4 py-1.5 rounded-full bg-red-500/10 dark:bg-red-500/20 text-red-600 dark:text-red-400 text-sm font-medium mb-4">
              Failure Analysis
            </span>
            <h2 className="text-3xl md:text-4xl font-bold text-slate-900 dark:text-white mb-4">
              Two Distinct Failure Modes
            </h2>
            <p className="text-slate-600 dark:text-slate-400 max-w-2xl mx-auto text-lg">
              We identify and formally define two failure patterns in instruction-guided I2I editing.
            </p>
          </div>

          <div className="grid md:grid-cols-2 gap-8 mb-12">
            <div className="bg-white dark:bg-gradient-to-br dark:from-slate-800 dark:to-slate-900 rounded-2xl p-8 border border-slate-200 dark:border-slate-700 card-hover">
              <div className="w-14 h-14 bg-red-100 dark:bg-red-500/20 rounded-xl flex items-center justify-center mb-6">
                <svg className="w-7 h-7 text-red-500 dark:text-red-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M18.364 18.364A9 9 0 005.636 5.636m12.728 12.728A9 9 0 015.636 5.636m12.728 12.728L5.636 5.636" />
                </svg>
              </div>
              <h3 className="text-2xl font-bold text-slate-900 dark:text-white mb-3">Soft Erasure</h3>
              <p className="text-slate-600 dark:text-slate-400 leading-relaxed">
                The editor produces an output image but <span className="text-red-600 dark:text-red-400 font-medium">silently suppresses the requested edit</span>,
                yielding unchanged or minimally altered results in which key elements of the instruction are omitted.
              </p>
            </div>

            <div className="bg-white dark:bg-gradient-to-br dark:from-slate-800 dark:to-slate-900 rounded-2xl p-8 border border-slate-200 dark:border-slate-700 card-hover">
              <div className="w-14 h-14 bg-amber-100 dark:bg-amber-500/20 rounded-xl flex items-center justify-center mb-6">
                <svg className="w-7 h-7 text-amber-500 dark:text-amber-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                </svg>
              </div>
              <h3 className="text-2xl font-bold text-slate-900 dark:text-white mb-3">Stereotype Replacement</h3>
              <p className="text-slate-600 dark:text-slate-400 leading-relaxed">
                Edits introduce <span className="text-amber-600 dark:text-amber-400 font-medium">stereotype-consistent demographic attributes</span> not specified in the prompt.
                Outputs exhibit visually strong edits while introducing unrequested identity changes.
              </p>
            </div>
          </div>

          <div className="max-w-4xl mx-auto">
            <div className="rounded-2xl overflow-hidden border border-slate-200 dark:border-slate-700 shadow-lg">
              <Image
                src="/assets/failure_example.png"
                alt="Examples of Soft Erasure and Stereotype Replacement"
                width={1000}
                height={400}
                className="w-full"
              />
            </div>
          </div>
        </div>
      </section>

      {/* Racial Disparity */}
      <section id="disparity" className="py-20 md:py-24">
        <div className="max-w-7xl mx-auto px-4">
          <div className="text-center mb-16">
            <span className="inline-block px-4 py-1.5 rounded-full bg-purple-500/10 dark:bg-purple-500/20 text-purple-600 dark:text-purple-400 text-sm font-medium mb-4">
              Racial Analysis
            </span>
            <h2 className="text-3xl md:text-4xl font-bold text-slate-900 dark:text-white mb-4">
              Racial Disparity in Identity Change
            </h2>
            <p className="text-slate-600 dark:text-slate-400 max-w-2xl mx-auto text-lg">
              Indian and Black subjects experience significantly higher rates of skin lightening and race change.
            </p>
          </div>

          <div className="grid lg:grid-cols-2 gap-8 items-center">
            <div className="rounded-2xl overflow-hidden border border-slate-200 dark:border-slate-700 shadow-lg">
              <Image
                src="/assets/exp1_race_disparity.png"
                alt="Racial disparities in skin lightening and race change"
                width={800}
                height={400}
                className="w-full"
              />
            </div>

            <div className="space-y-6">
              <div className="bg-white dark:bg-slate-800/50 rounded-2xl p-6 border border-slate-200 dark:border-slate-700">
                <h4 className="text-lg font-semibold text-slate-900 dark:text-white mb-5">Skin Lightening by Race</h4>
                <div className="space-y-4">
                  {[
                    { race: "Indian", value: 75, color: "bg-red-500" },
                    { race: "Black", value: 72, color: "bg-red-400" },
                    { race: "Middle Eastern", value: 73, color: "bg-orange-500" },
                    { race: "Latino", value: 65, color: "bg-amber-500" },
                    { race: "Southeast Asian", value: 54, color: "bg-amber-400" },
                    { race: "East Asian", value: 54, color: "bg-yellow-500" },
                    { race: "White", value: 44, color: "bg-green-500" },
                  ].map((item, i) => (
                    <div key={i}>
                      <div className="flex justify-between text-sm mb-1.5">
                        <span className="text-slate-700 dark:text-slate-300 font-medium">{item.race}</span>
                        <span className="text-slate-500 dark:text-slate-400 font-mono">{item.value}%</span>
                      </div>
                      <div className="h-2.5 bg-slate-200 dark:bg-slate-700 rounded-full overflow-hidden">
                        <div className={`h-full ${item.color} rounded-full transition-all duration-500`} style={{ width: `${item.value}%` }}></div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              <div className="bg-gradient-to-r from-purple-500/10 to-pink-500/10 dark:from-purple-500/20 dark:to-pink-500/20 rounded-xl p-5 border border-purple-500/20">
                <p className="text-slate-700 dark:text-slate-300 text-sm leading-relaxed">
                  This systematic change toward lighter skin and White-presenting features occurs across <span className="font-semibold">all three models</span> and
                  <span className="font-semibold"> all prompt categories</span>, suggesting deeply embedded priors in diffusion-based architectures.
                </p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Feature Prompt Mitigation */}
      <section className="py-20 md:py-24 bg-slate-100/50 dark:bg-slate-800/30">
        <div className="max-w-7xl mx-auto px-4">
          <div className="text-center mb-16">
            <span className="inline-block px-4 py-1.5 rounded-full bg-green-500/10 dark:bg-green-500/20 text-green-600 dark:text-green-400 text-sm font-medium mb-4">
              Mitigation Strategy
            </span>
            <h2 className="text-3xl md:text-4xl font-bold text-slate-900 dark:text-white mb-4">
              Prompt-Level Mitigation
            </h2>
            <p className="text-slate-600 dark:text-slate-400 max-w-2xl mx-auto text-lg">
              Feature prompts specifying observable appearance attributes can substantially reduce demographic change.
            </p>
          </div>

          <div className="max-w-5xl mx-auto mb-10">
            <div className="rounded-2xl overflow-hidden border border-slate-200 dark:border-slate-700 shadow-lg">
              <Image
                src="/assets/figure4.png"
                alt="Feature prompt mitigation comparison"
                width={1200}
                height={400}
                className="w-full"
              />
            </div>
          </div>

          <div className="max-w-3xl mx-auto">
            <div className="bg-gradient-to-r from-green-500/10 to-emerald-500/10 dark:from-green-500/20 dark:to-emerald-500/20 border border-green-500/30 rounded-2xl p-8">
              <div className="flex items-start gap-4">
                <div className="w-12 h-12 bg-green-500/20 rounded-xl flex items-center justify-center flex-shrink-0">
                  <svg className="w-6 h-6 text-green-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
                  </svg>
                </div>
                <div>
                  <h4 className="text-lg font-semibold text-green-700 dark:text-green-400 mb-3">Asymmetric Mitigation Effect</h4>
                  <p className="text-slate-700 dark:text-slate-300 leading-relaxed">
                    Feature prompts reduce race change by <span className="font-bold text-slate-900 dark:text-white">1.48 points for Black subjects</span> but only
                    <span className="font-bold text-slate-900 dark:text-white"> 0.06 points for White subjects</span>. This asymmetry reveals an implicit
                    &ldquo;default to White&rdquo; prior: without constraints, edits drift toward White-presenting outputs,
                    whereas explicit identity constraints disproportionately benefit non-White subjects.
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* WinoBias Results */}
      <section className="py-20 md:py-24">
        <div className="max-w-7xl mx-auto px-4">
          <div className="text-center mb-16">
            <span className="inline-block px-4 py-1.5 rounded-full bg-blue-500/10 dark:bg-blue-500/20 text-blue-600 dark:text-blue-400 text-sm font-medium mb-4">
              Gender Bias Study
            </span>
            <h2 className="text-3xl md:text-4xl font-bold text-slate-900 dark:text-white mb-4">
              Gender-Occupation Stereotypes
            </h2>
            <p className="text-slate-600 dark:text-slate-400 max-w-2xl mx-auto text-lg">
              Using WinoBias-derived prompts, we find models consistently adopt stereotype-consistent gender presentations.
            </p>
          </div>

          <div className="grid lg:grid-cols-2 gap-8 items-center">
            <div className="order-2 lg:order-1 space-y-6">
              <div className="bg-white dark:bg-slate-800/50 rounded-2xl p-6 border border-slate-200 dark:border-slate-700">
                <h4 className="text-lg font-semibold text-slate-900 dark:text-white mb-6">Stereotype Adherence Rate</h4>

                <div className="grid grid-cols-2 gap-6 mb-6">
                  <div className="text-center p-4 bg-slate-50 dark:bg-slate-800 rounded-xl">
                    <div className="text-4xl font-bold gradient-text mb-1">84%</div>
                    <div className="text-slate-500 dark:text-slate-400 text-sm">FLUX.2-dev</div>
                  </div>
                  <div className="text-center p-4 bg-slate-50 dark:bg-slate-800 rounded-xl">
                    <div className="text-4xl font-bold gradient-text mb-1">86%</div>
                    <div className="text-slate-500 dark:text-slate-400 text-sm">Qwen-Image-Edit</div>
                  </div>
                </div>

                <div className="bg-blue-50 dark:bg-blue-500/10 rounded-xl p-4 border border-blue-200 dark:border-blue-500/20">
                  <p className="text-slate-700 dark:text-slate-300 text-sm leading-relaxed">
                    Both models follow occupational stereotypes in <span className="font-semibold">84-86% of cases</span>, shifting toward stereotype-consistent
                    gender presentations regardless of the source gender.
                  </p>
                </div>
              </div>
            </div>

            <div className="order-1 lg:order-2 rounded-2xl overflow-hidden border border-slate-200 dark:border-slate-700 shadow-lg">
              <Image
                src="/assets/figure5.png"
                alt="Gender-occupation stereotypes in WinoBias-based edits"
                width={800}
                height={500}
                className="w-full"
              />
            </div>
          </div>
        </div>
      </section>

      {/* Method Overview */}
      <section id="method" className="py-20 md:py-24 bg-slate-100/50 dark:bg-slate-800/30">
        <div className="max-w-7xl mx-auto px-4">
          <div className="text-center mb-16">
            <span className="inline-block px-4 py-1.5 rounded-full bg-slate-500/10 dark:bg-slate-500/20 text-slate-600 dark:text-slate-400 text-sm font-medium mb-4">
              Methodology
            </span>
            <h2 className="text-3xl md:text-4xl font-bold text-slate-900 dark:text-white mb-4">
              Benchmark Overview
            </h2>
            <p className="text-slate-600 dark:text-slate-400 max-w-2xl mx-auto text-lg">
              Our controlled benchmark systematically probes demographic-conditioned behavior in I2I portrait editing.
            </p>
          </div>

          <div className="max-w-6xl mx-auto mb-12">
            <div className="rounded-2xl overflow-hidden border border-slate-200 dark:border-slate-700 shadow-lg bg-white dark:bg-slate-800/50">
              <Image
                src="/assets/figure2.png"
                alt="Method pipeline overview"
                width={1400}
                height={400}
                className="w-full"
              />
            </div>
          </div>

          <div className="grid md:grid-cols-3 gap-6">
            {[
              {
                icon: (
                  <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
                  </svg>
                ),
                title: "84 Source Images",
                desc: "Factorially sampled from FairFace across 7 races, 2 genders, and 6 age groups",
                color: "bg-purple-500/10 text-purple-500"
              },
              {
                icon: (
                  <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
                ),
                title: "20 Diagnostic Prompts",
                desc: "Occupational stereotypes and vulnerability attributes designed to expose failures",
                color: "bg-blue-500/10 text-blue-500"
              },
              {
                icon: (
                  <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 3v2m6-2v2M9 19v2m6-2v2M5 9H3m2 6H3m18-6h-2m2 6h-2M7 19h10a2 2 0 002-2V7a2 2 0 00-2-2H7a2 2 0 00-2 2v10a2 2 0 002 2zM9 9h6v6H9V9z" />
                  </svg>
                ),
                title: "3 Open-Weight Editors",
                desc: "FLUX.2-dev, Step1X-Edit-v1p2, and Qwen-Image-Edit-2511 evaluated under identical conditions",
                color: "bg-green-500/10 text-green-500"
              },
            ].map((item, i) => (
              <div key={i} className="bg-white dark:bg-slate-800/50 border border-slate-200 dark:border-slate-700 rounded-2xl p-6 card-hover">
                <div className={`w-12 h-12 ${item.color} rounded-xl flex items-center justify-center mb-4`}>
                  {item.icon}
                </div>
                <h3 className="text-xl font-bold text-slate-900 dark:text-white mb-2">{item.title}</h3>
                <p className="text-slate-600 dark:text-slate-400 text-sm leading-relaxed">{item.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Citation */}
      <section id="citation" className="py-20 md:py-24">
        <div className="max-w-4xl mx-auto px-4">
          <div className="text-center mb-12">
            <span className="inline-block px-4 py-1.5 rounded-full bg-slate-500/10 dark:bg-slate-500/20 text-slate-600 dark:text-slate-400 text-sm font-medium mb-4">
              Reference
            </span>
            <h2 className="text-3xl md:text-4xl font-bold text-slate-900 dark:text-white mb-4">Citation</h2>
          </div>

          <div className="bg-slate-900 dark:bg-slate-800 rounded-2xl p-6 md:p-8 border border-slate-700 shadow-lg">
            <div className="flex items-center justify-between mb-4">
              <span className="text-slate-400 text-sm font-medium">BibTeX</span>
              <button
                onClick={() => {
                  navigator.clipboard.writeText(`@inproceedings{anonymous2026demographic,
  title={Evaluating Demographic Misrepresentation in
         Image-to-Image Portrait Editing},
  author={Anonymous},
  booktitle={Proceedings of the Thirty-Fifth International
             Joint Conference on Artificial Intelligence},
  year={2026},
  note={Under Review}
}`);
                }}
                className="text-sm text-amber-400 hover:text-amber-300 transition-colors flex items-center gap-1.5"
              >
                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                </svg>
                Copy
              </button>
            </div>
            <pre className="font-mono text-sm text-slate-300 overflow-x-auto whitespace-pre-wrap">{`@inproceedings{anonymous2026demographic,
  title={Evaluating Demographic Misrepresentation in
         Image-to-Image Portrait Editing},
  author={Anonymous},
  booktitle={Proceedings of the Thirty-Fifth International
             Joint Conference on Artificial Intelligence},
  year={2026},
  note={Under Review}
}`}</pre>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="py-12 border-t border-slate-200 dark:border-slate-800">
        <div className="max-w-7xl mx-auto px-4">
          <div className="flex flex-col md:flex-row items-center justify-between gap-6">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-gradient-to-br from-amber-400 to-orange-500 rounded-xl flex items-center justify-center">
                <span className="text-white font-bold text-sm">I2I</span>
              </div>
              <div>
                <div className="font-semibold text-slate-800 dark:text-white">I2I Demographic Bias Study</div>
                <div className="text-sm text-slate-500 dark:text-slate-400">IJCAI 2026 Submission</div>
              </div>
            </div>

            <div className="flex items-center gap-6">
              <a href="#findings" className="text-sm text-slate-500 dark:text-slate-400 hover:text-amber-500 dark:hover:text-amber-400 transition-colors">Findings</a>
              <a href="#method" className="text-sm text-slate-500 dark:text-slate-400 hover:text-amber-500 dark:hover:text-amber-400 transition-colors">Method</a>
              <a href="#citation" className="text-sm text-slate-500 dark:text-slate-400 hover:text-amber-500 dark:hover:text-amber-400 transition-colors">Citation</a>
              <a
                href="https://github.com"
                target="_blank"
                rel="noopener noreferrer"
                className="text-slate-400 hover:text-amber-500 dark:hover:text-amber-400 transition-colors"
              >
                <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
                  <path fillRule="evenodd" d="M12 2C6.477 2 2 6.484 2 12.017c0 4.425 2.865 8.18 6.839 9.504.5.092.682-.217.682-.483 0-.237-.008-.868-.013-1.703-2.782.605-3.369-1.343-3.369-1.343-.454-1.158-1.11-1.466-1.11-1.466-.908-.62.069-.608.069-.608 1.003.07 1.531 1.032 1.531 1.032.892 1.53 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.029-2.688-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.026A9.564 9.564 0 0112 6.844c.85.004 1.705.115 2.504.337 1.909-1.296 2.747-1.027 2.747-1.027.546 1.379.202 2.398.1 2.651.64.7 1.028 1.595 1.028 2.688 0 3.848-2.339 4.695-4.566 4.943.359.309.678.92.678 1.855 0 1.338-.012 2.419-.012 2.747 0 .268.18.58.688.482A10.019 10.019 0 0022 12.017C22 6.484 17.522 2 12 2z" clipRule="evenodd" />
                </svg>
              </a>
            </div>
          </div>

          <div className="mt-8 pt-8 border-t border-slate-200 dark:border-slate-800 text-center">
            <p className="text-sm text-slate-500 dark:text-slate-400">
              Anonymous Authors | IJCAI 2026 Submission
            </p>
          </div>
        </div>
      </footer>
    </div>
  );
}
