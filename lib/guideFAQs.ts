import type { Faq } from "./types";

// Supplemental FAQ entries keyed by guide slug. These are merged into each
// guide's own `faqs` at render time, so they appear BOTH in the visible FAQ
// section and in the FAQPage JSON-LD (via faqSchema()). We reuse the existing
// Faq shape ({ q, a }) so no schema-builder changes are needed.
//
// Guides from the SEO brief that already ship their own FAQ + FAQPage schema
// (cold-plunge-vs-ice-bath, infrared-vs-traditional-sauna — both top-level
// pages) are intentionally omitted here to avoid duplicate questions.
export const GUIDE_FAQS: Record<string, Faq[]> = {
  "how-often-should-you-do-the-cold-plunge": [
    {
      q: "How many times per week should you cold plunge?",
      a: "For general recovery and mood benefits, 2–4 sessions per week is the range most practitioners and studies point to. Daily plunging is fine for many people but isn't required to see results — beginners do well starting at 2–3 sessions and building from there.",
    },
    {
      q: "Can you cold plunge every day?",
      a: "Yes, daily cold plunging is generally safe for healthy adults as long as sessions stay short (about 2–5 minutes) and the water isn't extreme. Pay attention to how you feel: if you're run-down or not recovering, scale back to a few times per week.",
    },
    {
      q: "Is it better to cold plunge in the morning or at night?",
      a: "Morning plunges give an alertness and energy boost from the norepinephrine spike, which suits most people. Evening plunges work too, but the stimulation can make it harder to fall asleep, so leave a few hours before bed.",
    },
  ],
  "is-a-3-minute-cold-plunge-safe": [
    {
      q: "Is a 3-minute cold plunge long enough?",
      a: "Yes. Three minutes at around 50°F is enough to trigger the main benefits — the norepinephrine release, reduced muscle soreness, and mood lift. Many protocols target just 1–3 minutes, so three minutes is a solid, effective session.",
    },
    {
      q: "What happens if you stay in a cold plunge too long?",
      a: "Staying in too long raises the risk of hypothermia and, in cold enough water, an after-drop where your core temperature keeps falling after you exit. For most people, keeping sessions under about 5 minutes and rewarming gradually afterward avoids these risks.",
    },
    {
      q: "Is 3 minutes safe for beginners?",
      a: "Beginners should build up to three minutes rather than starting there. Begin with 30–60 seconds, focus on controlling your breathing, and add time over several sessions as your cold tolerance improves.",
    },
  ],
  "what-happens-after-30-days-of-ice-baths": [
    {
      q: "What are the benefits of doing ice baths for 30 days?",
      a: "Over 30 consecutive days, most people report better cold tolerance, faster workout recovery, improved mood and focus, and a sense of discipline from the daily challenge. Much of the adaptation is neurological — your body grows far more comfortable with the cold-shock response.",
    },
    {
      q: "How long should each ice bath be during a 30-day challenge?",
      a: "Two to four minutes per session at roughly 45–55°F is a common target. Consistency matters more than duration, so a shorter session every day beats forcing long, uncomfortable ones.",
    },
    {
      q: "Will 30 days of ice baths help with weight loss?",
      a: "Cold exposure can modestly raise calorie burn by activating brown fat, but the effect is small. Ice baths support recovery and mood far more than they drive weight loss, so treat any metabolic benefit as a minor bonus rather than the goal.",
    },
  ],
};
