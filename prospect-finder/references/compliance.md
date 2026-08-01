# Consent, opt-out and data — the short version

**Not legal advice.** A practical summary so a list isn't built in a way that
has to be thrown away. For a regulated space — healthcare, finance, EU
consumers, anything at scale — the user should talk to a lawyer, and you should
say so once rather than guessing on their behalf.

*(Structure and the compliance checklist below are adapted from the cold-outbound
starter kit's legal reference — see `../CREDITS.md`.)*

## The two regimes people actually hit

**US (CAN-SPAM-style).** Cold B2B email is legal without prior consent. What's
required is honesty and an exit:

- Real sender identity — the From name and address belong to a real person
- A subject line that describes the email — never "Re:" on a thread that doesn't exist
- A physical postal address in the footer
- A working opt-out, honoured promptly and across every campaign

**EU / UK (GDPR-style).** Stricter, and the distinction that matters is
**business vs individual**:

- Contacting a role at a company about something relevant to that role generally
  has a path (legitimate interest), *with* a clear opt-out and a real relevance
  argument you could defend
- Individuals and consumers are a different matter, and several countries are
  stricter than the baseline
- People can ask what you hold about them and ask you to delete it — so keep the
  list small, sourced, and deletable

Other countries vary — Canada's regime is consent-first, and several others are
stricter than the US default.

## What that means for a list you're building

- **Keep the source URL per row.** "Where did you get my data?" is a question
  with a legal answer requirement in some regimes, and a reputational one
  everywhere
- **Collect the minimum.** Name, company, one route, one observable, the source.
  Not everything the tool offers
- **Business routes over personal ones.** A work address for a work reason;
  a personal address for a work pitch is where complaints come from
- **Deletion has to be possible.** One CSV or CRM you can actually edit, not
  data smeared across six exports
- **Opt-outs are permanent and global** — `status=closed` survives every future
  import, on every list, forever. This is the rule people break by accident, by
  re-importing an old source six months later

## Platform terms

Separate from the law, and it's the one that bites first: most platforms'
terms restrict automated collection, and enforcement lands on the *account*, not
the lawyer.

- Public profile data a person could read is one thing; a login-walled page, a
  private group, or a rate-limit you're evading is another
- The risk is the user's account — say so plainly once, let them decide, and
  don't quietly do it for them
- If a platform offers an official API or export, prefer it even when it's slower

## The line this skill won't cross

- **Never scrape a private or closed space** to build a list
- **Never mislead about identity or source** to obtain contact details
- **Never re-add someone who opted out**, on any list, for any campaign
- **Never hand over a list without its sources**, so nobody downstream has to
  guess where a person came from

## One line in the email

Whatever the regime, a plain opt-out sentence costs nothing and settles most of
it:

> *If you'd rather not hear from me, just reply "unsubscribe" and I won't write
> again.*

Honour it the same day, in the CRM, permanently.
