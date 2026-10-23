import { Container } from "@/components/ui/container";
import { footerColumns, legalLinks, site } from "@/data/site";

export function Footer() {
  return (
    <footer className="border-t border-border bg-card py-14">
      <Container>
        <div className="grid gap-8 md:grid-cols-4">
          <div>
            <p className="font-display text-lg font-bold">{site.name}</p>
            <p className="mt-2 text-sm text-muted-foreground">Made in India. Preventive insight for people, families, and workplaces.</p>
            <p className="mt-4 text-sm">
              <a className="font-medium text-brand-700" href="mailto:hello@preventvital.in">
                {site.email}
              </a>
            </p>
          </div>
          {footerColumns.map((column) => (
            <div key={column.title}>
              <p className="text-sm font-semibold">{column.title}</p>
              <ul className="mt-3 space-y-2">
                {column.links.map((link) => (
                  <li key={link.label}>
                    <a href={link.href} className="text-sm text-muted-foreground hover:text-foreground">
                      {link.label}
                    </a>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>
        <div className="mt-10 flex flex-col gap-3 border-t border-border pt-6 text-xs leading-relaxed text-muted-foreground sm:flex-row sm:items-start sm:justify-between">
          <p className="max-w-2xl">{site.disclaimer}</p>
          <ul className="flex gap-4">
            {legalLinks.map((link) => (
              <li key={link.label}>
                <a href={link.href} className="hover:text-foreground">
                  {link.label}
                </a>
              </li>
            ))}
          </ul>
        </div>
      </Container>
    </footer>
  );
}
