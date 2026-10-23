import { Comparison } from "@/components/sections/comparison";
import { Corporates } from "@/components/sections/corporates";
import { Everyday } from "@/components/sections/everyday";
import { Faq } from "@/components/sections/faq";
import { Features } from "@/components/sections/features";
import { FinalCta } from "@/components/sections/final-cta";
import { Footer } from "@/components/sections/footer";
import { Hero } from "@/components/sections/hero";
import { HowItWorks } from "@/components/sections/how-it-works";
import { MobileCta } from "@/components/sections/mobile-cta";
import { Navbar } from "@/components/sections/navbar";
import { Problem } from "@/components/sections/problem";
import { Programs } from "@/components/sections/programs";
import { Resources } from "@/components/sections/resources";
import { RiskDemo } from "@/components/sections/risk-demo";
import { Security } from "@/components/sections/security";
import { Testimonials } from "@/components/sections/testimonials";
import { TrustBar } from "@/components/sections/trust-bar";

export default function HomePage() {
  return (
    <>
      <Navbar />
      <main>
        <Hero />
        <TrustBar />
        <Problem />
        <HowItWorks />
        <Comparison />
        <Features />
        <RiskDemo />
        <Corporates />
        <Programs />
        <Everyday />
        <Testimonials />
        <Security />
        <Resources />
        <Faq />
        <FinalCta />
      </main>
      <Footer />
      <MobileCta />
    </>
  );
}
