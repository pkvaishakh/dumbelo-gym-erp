/* The public landing page at "/": what Dumbelo is, for gym owners deciding whether to book a demo. Rendered on the
 * server; only the parts in motion.tsx and LeadForm.tsx run in the browser. Built from the design system's tokens
 * and pieces; the depth is perspective, layers and motion that answers the pointer and the scroll. */
import {
  ArrowRight, Building2, Check, Fingerprint, IndianRupee, Mail, MessageCircle, QrCode, Receipt, Smartphone, Users,
} from "lucide-react";
import Link from "next/link";

import { Barbell, Icon, Mark } from "@/components/brand";
import { CHAT_TEXT, CONTACT_EMAIL, SALES_WHATSAPP, SITE_URL, whatsappLink } from "@/lib/site";

import { DESCRIPTION, FAQ, FEATURES, ROLES, TRUST } from "./content";
import s from "./landing.module.css";
import { LeadForm } from "./LeadForm";
import { Header, HeroStage, MotionRoot, ReachUs, RoleSwitcher, TiltCard } from "./motion";
import { Phone } from "./phones";

const DEMO = "#demo";
const CHAT = whatsappLink(CHAT_TEXT.general);

export function Landing() {
  return (
    <MotionRoot>
      <StructuredData />
      <a className={s.skip} href="#main">Skip to content</a>
      <Header>
        <nav className={s.nav} aria-label="Page">
          <a href="#check-in">Check-in</a>
          <a href="#roles">Your team</a>
          <a href="#features">Features</a>
          <a href="#pricing">Pricing</a>
          <a href="#faq">Questions</a>
        </nav>
      </Header>
      <main id="main">
        <Hero />
        <Door />
        <Roles />
        <Features />
        <CtaBand />
        <Trust />
        <Pricing />
        <Faq />
        <Demo />
      </main>
      <Footer />
      <ReachUs />
    </MotionRoot>
  );
}

function Hero() {
  return (
    <section id="top" className={s.heroFrame} aria-labelledby="hero-title">
      <div className={s.hero}>
        <div className={s.heroCopy}>
          <h1 id="hero-title" className={s.heroTitle}>
            <span className={s.eyebrow}><span className={s.eyebrowDot} aria-hidden="true" />Gym management software made for India</span>{" "}
            <span className={s.heroLine}>Open up.</span> <span className={s.heroLine}>Check in.</span> <span className={s.heroLine}>Close out.</span>
          </h1>
          <p className={s.heroLede}>
            Members, plans, payments, check-ins, staff and money for every branch, in one app on your phone. Your front
            desk, your trainers and your members use it too.
          </p>
          <div className={s.heroActions}>
            <a className="rl-button rl-button--accent" href={DEMO}>Book a Free Demo<Icon as={ArrowRight} size="sm" /></a>
            <a className="rl-button rl-button--on-ink" href="#roles">See How It Works</a>
          </div>
          <p className={s.heroNote}>A free call at a time that suits you. No card, no commitment.</p>
          <ul className={s.heroFacts}>
            <li><Icon as={Smartphone} size="sm" />Opens on any phone, nothing to install</li>
            <li><Icon as={MessageCircle} size="sm" />Renewal and dues reminders on WhatsApp</li>
            <li><Icon as={Building2} size="sm" />Every branch under one sign-in</li>
          </ul>
        </div>
        <HeroStage>
          <Phone role="admin" className={s.phoneLeft} />
          <Phone role="member" className={s.phoneRight} />
          <Phone role="desk" className={s.phoneCenter} />
          <div className={`${s.float} ${s.floatA}`}>
            <span className={s.floatTick}><Icon as={Check} size="sm" /></span>
            <span><span className="rl-row__title">Checked in at 6:42 AM</span><span className="rl-row__meta">Rahul Kumar · Premium Plan</span></span>
          </div>
          <div className={`${s.float} ${s.floatB}`}>
            <span className="rl-chipicon"><Icon as={IndianRupee} size="sm" /></span>
            <span><span className="rl-row__title">₹1,500 collected</span><span className="rl-row__meta">UPI · receipt sent on WhatsApp</span></span>
          </div>
          <div className={`${s.float} ${s.floatC}`}>
            <span className="rl-chipicon"><Icon as={MessageCircle} size="sm" /></span>
            <span><span className="rl-row__title">Renewal reminder sent</span><span className="rl-row__meta">Karthik’s plan ends today</span></span>
          </div>
        </HeroStage>
      </div>
    </section>
  );
}

function SectionHead({ kicker, title, lede, id }: { kicker: string; title: string; lede: string; id: string }) {
  return (
    <div className={s.head} data-reveal>
      <p className={s.kicker}>{kicker}</p>
      <h2 id={id} className={s.title}>{title}</h2>
      <p className={s.lede}>{lede}</p>
    </div>
  );
}

function Door() {
  return (
    <section id="check-in" className={s.band} aria-labelledby="door-title">
      <div className={s.wrap}>
        <SectionHead id="door-title" kicker="Check-in" title="Three ways in at the door"
          lede="Gym check-in at the desk, by QR code or through your turnstile, all in one list, one per person a day. An expired or frozen plan is turned away with the reason, so the desk never has to argue." />
        <div className={s.doors}>
          <TiltCard className={s.door} i={0}>
            <div className={s.doorArt} aria-hidden="true">
              <div className={`rl-card ${s.doorResult}`}>
                <span className="rl-photo">RK</span>
                <span className={s.grow}><span className="rl-row__title">Rahul Kumar</span><span className="rl-row__meta">RL-2041 · Premium</span></span>
                <span className="rl-button rl-button--sm">Check In</span>
              </div>
              <div className={`rl-card ${s.doorResult} ${s.doorBack}`}>
                <span className="rl-photo">RM</span>
                <span className={s.grow}><span className="rl-row__title">Raghav Menon</span><span className="rl-row__meta">Renew it to check in</span></span>
                <span className="rl-status rl-status--expired">Expired</span>
              </div>
            </div>
            <h3 className={s.cardTitle}>At the front desk</h3>
            <p className={s.cardText}>Search a name, phone or member ID, or scan their code. One tap checks them in.</p>
          </TiltCard>
          <TiltCard className={s.door} i={1}>
            <div className={s.doorArt} aria-hidden="true">
              <div className={s.poster}>
                <span className={s.posterCode}><Icon as={QrCode} /></span>
                <span className="rl-row__title">Indiranagar</span>
                <span className="rl-row__meta">Scan to check in</span>
              </div>
            </div>
            <h3 className={s.cardTitle}>With the wall QR</h3>
            <p className={s.cardText}>Each branch gets one code for the wall. Members and staff scan it with their own phone.</p>
          </TiltCard>
          <TiltCard className={s.door} i={2}>
            <div className={s.doorArt} aria-hidden="true">
              <div className={s.device}>
                <span className={s.deviceIcon}><Icon as={Fingerprint} /></span>
                <span className={s.deviceLine}><span className="rl-row__title">6:42 AM</span><span className="rl-row__meta">Main door</span></span>
              </div>
            </div>
            <h3 className={s.cardTitle}>Through your turnstile</h3>
            <p className={s.cardText}>Turnstile and biometric punches come straight in, counted the same way as the desk.</p>
          </TiltCard>
        </div>
      </div>
    </section>
  );
}

function Roles() {
  return (
    <section id="roles" className={`${s.band} ${s.bandSurface}`} aria-labelledby="roles-title">
      <div className={s.wrap}>
        <SectionHead id="roles-title" kicker="Your team" title="One app, four views of it"
          lede="Owners, front desk, trainers and members sign in at the same place and land on their own home. What each person can see is checked by the server, not just hidden on the screen." />
        <RoleSwitcher roles={ROLES} phones={{ admin: <Phone role="admin" />, desk: <Phone role="desk" />, trainer: <Phone role="trainer" />, member: <Phone role="member" /> }} />
      </div>
    </section>
  );
}

function Features() {
  return (
    <section id="features" className={s.band} aria-labelledby="features-title">
      <div className={s.wrap}>
        <SectionHead id="features-title" kicker="Features" title="The whole gym, not just the gate"
          lede="Membership management, billing, attendance, staff and money, from the first sale to the last cash count of the day. Built around how gyms here run: rupees, part payments, UPI and WhatsApp." />
        <div className={s.bento}>
          {FEATURES.map((f, i) => (
            <TiltCard key={f.title} className={s.feature} outer={f.wide ? s.featureWide : ""} i={i % 3}>
              <span className={s.featureIcon}><Icon as={f.icon} /></span>
              <h3 className={s.cardTitle}>{f.title}</h3>
              <p className={s.cardText}>{f.text}</p>
            </TiltCard>
          ))}
        </div>
      </div>
    </section>
  );
}

function CtaBand() {
  return (
    <section className={s.ctaBand} aria-labelledby="cta-title">
      <div className={`${s.wrap} ${s.ctaBandIn}`} data-reveal>
        <div>
          <h2 id="cta-title" className={s.ctaTitle}>See it with your own plans and branches</h2>
          <p className={s.cardText}>A short call, at a time that suits you. Every feature above comes with every plan.</p>
        </div>
        <div className={s.ctaActions}>
          <a className="rl-button" href={DEMO}>Book a Free Demo</a>
          <a className="rl-button rl-button--secondary" href="#pricing">See Pricing</a>
        </div>
      </div>
    </section>
  );
}

function Trust() {
  return (
    <section className={s.inkFrame} aria-labelledby="trust-title">
      <div className={s.ink}>
        <div className={s.wrap}>
          <div className={s.head} data-reveal>
            <p className={`${s.kicker} ${s.kickerOnInk}`}>Your records</p>
            <h2 id="trust-title" className={s.title}>Money exact to the paisa. History you can trust.</h2>
          </div>
          <div className={s.trust}>
            {TRUST.map((t, i) => (
              <div key={t.title} className={s.trustItem} data-reveal style={{ "--i": i } as React.CSSProperties}>
                <span className={s.trustIcon}><Icon as={t.icon} /></span>
                <h3 className={s.cardTitle}>{t.title}</h3>
                <p className={s.trustText}>{t.text}</p>
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}

function Pricing() {
  return (
    <section id="pricing" className={`${s.band} ${s.bandSurface}`} aria-labelledby="pricing-title">
      <div className={`${s.wrap} ${s.pricing}`}>
        <SectionHead id="pricing-title" kicker="Pricing" title="One plan. Pay for the branches you run."
          lede="A monthly fee for your gym and one for each branch, billed once a month. Every feature and every role is included." />
        <TiltCard className={`rl-card ${s.priceCard}`} max={4}>
          <ul className={s.priceRows}>
            <li><span className="rl-chipicon"><Icon as={Building2} size="sm" /></span><span><span className="rl-row__title">Your gym</span><span className="rl-row__meta">A monthly base fee: members, staff, reports, all of it</span></span></li>
            <li><span className="rl-chipicon"><Icon as={Users} size="sm" /></span><span><span className="rl-row__title">Each branch</span><span className="rl-row__meta">A monthly fee per branch. Add one when you open it</span></span></li>
            <li><span className="rl-chipicon"><Icon as={MessageCircle} size="sm" /></span><span><span className="rl-row__title">WhatsApp</span><span className="rl-row__meta">Send from our number and pay for what goes out, or connect your own business number</span></span></li>
            <li><span className="rl-chipicon"><Icon as={Receipt} size="sm" /></span><span><span className="rl-row__title">No card on file</span><span className="rl-row__meta">You get an invoice each month and pay it like any other bill</span></span></li>
          </ul>
          <div className={s.priceActions}>
            <a className="rl-button rl-button--block" href={DEMO}>Get Prices for My Gym</a>
            {SALES_WHATSAPP && (
              <a className="rl-button rl-button--secondary rl-button--block" href={whatsappLink(CHAT_TEXT.prices)} target="_blank" rel="noopener noreferrer" data-chat-here>
                <Icon as={MessageCircle} size="sm" />Ask on WhatsApp
              </a>
            )}
            <p className="rl-row__meta">Tell us your branches and we&apos;ll send what you&apos;d pay, with nothing hidden.</p>
          </div>
        </TiltCard>
      </div>
    </section>
  );
}

function Faq() {
  return (
    <section id="faq" className={s.band} aria-labelledby="faq-title">
      <div className={`${s.wrap} ${s.faqWrap}`}>
        <SectionHead id="faq-title" kicker="Questions" title="Before you ask" lede="The things gym owners ask us first." />
        <div className={`rl-card ${s.faq}`} data-reveal>
          {FAQ.map(([q, a]) => (
            <details key={q} className={s.faqItem}>
              <summary><h3 className={s.faqQ}>{q}</h3><span className={s.faqMark} aria-hidden="true" /></summary>
              <p>{a}</p>
            </details>
          ))}
        </div>
      </div>
    </section>
  );
}

function Demo() {
  return (
    <section id="demo" className={s.inkFrame} aria-labelledby="demo-title">
      <div className={`${s.ink} ${s.demo}`}>
        <div className={s.demoArt} data-reveal><Barbell onInk load /></div>
        <div className={`${s.wrap} ${s.demoGrid}`}>
          <div className={s.demoCopy}>
            <h2 id="demo-title" className={s.closingTitle}>Ready before you open up tomorrow</h2>
            <p className={s.heroLede}>Tell us about your gym. We&apos;ll show you Dumbelo with plans and branches like yours, and set it up with you.</p>
            <p className={`${s.kicker} ${s.kickerOnInk} ${s.demoKicker}`}>On the call</p>
            <ul className={s.demoSteps}>
              <li><span className={s.checkYes}><Icon as={Check} size="xs" /></span>Your front desk, trainers and members, each on their own phone</li>
              <li><span className={s.checkYes}><Icon as={Check} size="xs" /></span>Check-in, payments and WhatsApp reminders with your own plans</li>
              <li><span className={s.checkYes}><Icon as={Check} size="xs" /></span>What you&apos;d pay for your branches, and how we move you over</li>
            </ul>
            <div className={s.demoAlt}>
              {SALES_WHATSAPP && (
                <a className="rl-button rl-button--on-ink" href={CHAT} target="_blank" rel="noopener noreferrer"><Icon as={MessageCircle} size="sm" />Chat on WhatsApp</a>
              )}
              <a className={s.demoMail} href={`mailto:${CONTACT_EMAIL}`}><Icon as={Mail} size="sm" />{CONTACT_EMAIL}</a>
            </div>
          </div>
          <div className={`rl-card ${s.formCard}`}><LeadForm /></div>
        </div>
      </div>
    </section>
  );
}

function Footer() {
  return (
    <footer className={s.footer}>
      <div className={`${s.wrap} ${s.footerIn}`}>
        <div className={s.footerBrand}>
          <Link className="rl-logo" href="/" aria-label="Dumbelo home"><Mark /><span className="rl-logo__name">Dumbelo</span></Link>
          <p className="rl-row__meta">Gym management software for members, check-ins and payments. Made in India.</p>
        </div>
        <nav className={s.footerNav} aria-label="Footer">
          <a className="rl-link rl-link--plain" href="#features">Features</a>
          <a className="rl-link rl-link--plain" href="#pricing">Pricing</a>
          <a className="rl-link rl-link--plain" href={DEMO}>Book a demo</a>
          <Link className="rl-link rl-link--plain" href="/login">Sign in</Link>
          {SALES_WHATSAPP && <a className="rl-link rl-link--plain" href={CHAT} target="_blank" rel="noopener noreferrer" data-chat-here>WhatsApp</a>}
          <a className="rl-link rl-link--plain" href={`mailto:${CONTACT_EMAIL}`}>{CONTACT_EMAIL}</a>
        </nav>
        <p className={`rl-row__meta ${s.footerCopy}`}>© {new Date().getFullYear()} Dumbelo</p>
      </div>
    </footer>
  );
}

/** What search engines read about Dumbelo: the organisation, the site, the software and the questions above. */
function StructuredData() {
  const graph = {
    "@context": "https://schema.org",
    "@graph": [
      { "@type": "Organization", "@id": `${SITE_URL}/#org`, name: "Dumbelo", url: SITE_URL, logo: `${SITE_URL}/icons/icon-512.png`, email: CONTACT_EMAIL, areaServed: "IN" },
      { "@type": "WebSite", "@id": `${SITE_URL}/#site`, url: SITE_URL, name: "Dumbelo", inLanguage: "en-IN", publisher: { "@id": `${SITE_URL}/#org` } },
      {
        "@type": "SoftwareApplication", name: "Dumbelo", url: SITE_URL, description: DESCRIPTION,
        applicationCategory: "BusinessApplication", applicationSubCategory: "Gym management software",
        operatingSystem: "Any phone, tablet or computer with a web browser", inLanguage: "en-IN",
        publisher: { "@id": `${SITE_URL}/#org` }, featureList: FEATURES.map((f) => f.title),
      },
      {
        "@type": "FAQPage",
        mainEntity: FAQ.map(([q, a]) => ({ "@type": "Question", name: q, acceptedAnswer: { "@type": "Answer", text: a } })),
      },
    ],
  };
  // The one place this page sets HTML from a string: JSON we build ourselves from the constants above, with "<"
  // escaped so nothing in it can close the script tag.
  return <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: JSON.stringify(graph).replace(/</g, "\\u003c") }} />;
}
