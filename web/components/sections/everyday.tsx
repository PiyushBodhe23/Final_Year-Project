import { Reveal } from "@/components/motion/reveal";
import { Container } from "@/components/ui/container";
import { Section } from "@/components/ui/section";
import { SectionHeading } from "@/components/ui/section-heading";
import { everyday } from "@/data/home";

export function Everyday() {
  return (
    <Section id="everyday">
      <Container className="grid items-start gap-10 lg:grid-cols-2">
        <SectionHeading
          id="everyday-title"
          eyebrow="Made for real life"
          title="Support that feels human, not clinical."
          description="Whether you are watching your own week, caring for a parent, or preparing for a doctor visit, the aim is fewer surprises."
        />
        <ul className="space-y-4">
          {everyday.map((item, index) => (
            <Reveal key={item.title} delay={index * 0.05}>
              <li className="rounded-3xl border border-border bg-card p-5">
                <h3 className="text-lg">{item.title}</h3>
                <p className="mt-1 text-sm leading-relaxed text-muted-foreground">{item.body}</p>
              </li>
            </Reveal>
          ))}
        </ul>
      </Container>
    </Section>
  );
}
