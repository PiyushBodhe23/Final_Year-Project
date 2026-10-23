import { Lock, Shield, SlidersHorizontal, MapPin } from "lucide-react";

import { Card } from "@/components/ui/card";
import { Container } from "@/components/ui/container";
import { Section } from "@/components/ui/section";
import { SectionHeading } from "@/components/ui/section-heading";
import { securityPoints } from "@/data/home";

const icons = [Shield, Lock, SlidersHorizontal, MapPin];

export function Security() {
  return (
    <Section id="security">
      <Container>
        <SectionHeading
          id="security-title"
          eyebrow="Privacy"
          title="Your data stays in your control."
          description="We describe how the product is built. We do not invent certifications."
        />
        <div className="mt-8 grid gap-4 sm:grid-cols-2">
          {securityPoints.map((point, index) => {
            const Icon = icons[index] ?? Shield;
            return (
              <Card key={point.title} className="p-6">
                <Icon className="h-5 w-5 text-brand-600" aria-hidden />
                <h3 className="mt-3 text-lg">{point.title}</h3>
                <p className="mt-2 text-sm leading-relaxed text-muted-foreground">{point.body}</p>
              </Card>
            );
          })}
        </div>
      </Container>
    </Section>
  );
}
