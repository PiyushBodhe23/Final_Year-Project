import { Card } from "@/components/ui/card";
import { Container } from "@/components/ui/container";
import { Section } from "@/components/ui/section";
import { SectionHeading } from "@/components/ui/section-heading";
import { resources } from "@/data/home";

export function Resources() {
  return (
    <Section id="resources">
      <Container>
        <SectionHeading
          id="resources-title"
          eyebrow="Resources"
          title="Short guides, written for families and HR teams."
        />
        <div className="mt-8 grid gap-4 md:grid-cols-3">
          {resources.map((item) => (
            <Card key={item.title} className="p-6">
              <h3 className="text-lg">{item.title}</h3>
              <p className="mt-2 text-sm leading-relaxed text-muted-foreground">{item.body}</p>
            </Card>
          ))}
        </div>
      </Container>
    </Section>
  );
}
