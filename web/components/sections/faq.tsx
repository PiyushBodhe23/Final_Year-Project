import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from "@/components/ui/accordion";
import { Container } from "@/components/ui/container";
import { Section } from "@/components/ui/section";
import { SectionHeading } from "@/components/ui/section-heading";
import { faqs } from "@/data/home";

export function Faq() {
  return (
    <Section id="faq" className="bg-muted/40">
      <Container className="max-w-3xl">
        <SectionHeading id="faq-title" eyebrow="FAQ" title="Straight answers before you book a call." />
        <Accordion type="single" collapsible className="mt-8">
          {faqs.map((item, index) => (
            <AccordionItem key={item.q} value={`faq-${index}`}>
              <AccordionTrigger>{item.q}</AccordionTrigger>
              <AccordionContent>{item.a}</AccordionContent>
            </AccordionItem>
          ))}
        </Accordion>
      </Container>
    </Section>
  );
}
