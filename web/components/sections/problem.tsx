import { CountUp } from "@/components/motion/count-up";
import { Reveal } from "@/components/motion/reveal";
import { Card } from "@/components/ui/card";
import { Container } from "@/components/ui/container";
import { Section } from "@/components/ui/section";
import { SectionHeading } from "@/components/ui/section-heading";
import { stats } from "@/data/home";

export function Problem() {
  return (
    <Section id="problem">
      <Container>
        <SectionHeading
          id="problem-title"
          eyebrow="The gap"
          title="Most diseases are detected late. We change that."
          description="Watches already record the day. PreventVital turns those signals into an early, calm conversation — before symptoms become the first alert."
        />
        <div className="mt-10 grid gap-4 md:grid-cols-3">
          {stats.map((stat, index) => (
            <Reveal key={stat.label} delay={index * 0.08}>
              <Card className="h-full p-6">
                <p className="font-display text-5xl text-brand-700">
                  <CountUp value={stat.value} suffix={stat.suffix} />
                </p>
                <h3 className="mt-3 text-lg">{stat.label}</h3>
                <p className="mt-2 text-sm leading-relaxed text-muted-foreground">{stat.detail}</p>
              </Card>
            </Reveal>
          ))}
        </div>
      </Container>
    </Section>
  );
}
