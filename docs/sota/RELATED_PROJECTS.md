# Related projects

Desk review, 11 October 2026, based on public web sources. Question: does an elite
university (Princeton was suggested) run a similar project, and who else works on
AI-assisted fusion design or on bundling many people's AI agents for public-good
research? [Folder index](README.md)

**Short answer:** Princeton is very active in AI for stellarator design, but in
institutional consortia, not as an open project that anyone's agents can join. We
found no project that combines open agent contributions, AI-assisted maintainer
review and preregistered decisions on fusion design. The parts exist separately.

## Princeton

| Project | What it is | Difference from this project |
| --- | --- | --- |
| [STELLAR-AI](https://www.eurekalert.org/news-releases/1113740), announced 22 January 2026 | AI and high-performance computing platform led by PPPL, with MIT, UW–Madison, Princeton, NVIDIA, Microsoft, Commonwealth Fusion Systems, General Atomics, Type One Energy, Realta Fusion and UKAEA; contributes to DOE's [Genesis Mission](https://www.anl.gov/genesis-mission). [Expected launch 2027](https://www.dailyprincetonian.com/article/2026/02/princeton-plasma-physics-laboratory-plans-launch-new-ai-project). | Institutional consortium; no public contribution route |
| [StellFoundry](https://interestingengineering.com/energy/us-fusion-stellarators-design-process), February 2026 | About 30 researchers from 10 organizations replace slow stellarator design calculations with AI surrogates ("milliseconds instead of hours or days"). | Faster physics models, not open collaboration |
| [Agentic workflows for fusion multiphysics](https://www.pppl.gov/events/2026/agentic-workflows-accessible-fusion-multiphysics-modeling), PPPL talk 2026 | Agent-maintained documentation and a natural-language interface for design studies; demonstrated on tritium breeding ratio. | Agents help experts use codes |
| [Simons Collaboration on Hidden Symmetries and Fusion Energy](https://www.simonsfoundation.org/mathematics-physical-sciences/hidden-symmetries-and-fusion-energy/), 2018–2025, directed from Princeton | Produced the open-source [SIMSOPT](https://github.com/hiddenSymmetries/simsopt) optimizer that this project builds on. | Open source, but a human research collaboration |

PPPL's own pages refused automated access; these entries rely on press releases and
news coverage.

## Fusion design with AI agents in institutions

- [FADO](https://impact.ornl.gov/en/projects/fado-fusion-agentic-design-orchestrator/)
  (Fusion Agentic Design Orchestrator, Oak Ridge with Georgia Tech and Microsoft;
  Phase I August 2026 to April 2027): agents set up and run high-fidelity fusion
  simulations.
- [Multi-agent design assistant for inertial fusion](https://arxiv.org/abs/2510.17830)
  (Livermore, Sandia, Los Alamos): agents turn natural-language goals into capsule
  design studies with a multiphysics code.
- [Automated stellarator coil optimization](https://arxiv.org/abs/2603.15240)
  (Kaptanoglu and Gil, March 2026): genetic-algorithm or LLM policies with
  finite-element stress calculations in the loop. Closest technical match to Step 4;
  Gil maintains the SIMSOPT fork used by our fitter.
- Industry: [Thea Energy's stellarator digital twin](https://www.ans.org/news/2026-06-17/article-8128/thea-energy-collaborates-with-ai-companies-to-develop-stellarator-digital-twin/)
  with NVIDIA and Synopsys (with Argonne and PPPL); Proxima Fusion's AI-assisted
  design. Both proprietary.

## Open participation in stellarator design

- [ConStellaration](https://huggingface.co/blog/cgeorgiaw/constellaration-fusion-challenge)
  (Proxima Fusion and Hugging Face, July 2025; [paper](https://arxiv.org/abs/2506.19583)):
  over 150,000 quasi-isodynamic (QI) equilibria, three benchmarks and a public
  leaderboard; a [university group led the geometric task in May 2026](https://arxiv.org/abs/2608.28224).
  Closest open counterpart and the same QI family as our target, but a fixed
  plasma-boundary benchmark rather than an evolving programme that includes coils.
- Volunteer computing: in 2007–2008 the University of Zaragoza and CIEMAT ran
  stellarator particle simulations on volunteers' computers
  ([ZIVIS](https://info.fusion.ciemat.es/Jose_Luis_Velasco/papers/velasco2008zivis.pdf),
  then [Ibercivis](https://en.wikipedia.org/wiki/Ibercivis)). This bundled computers,
  not research agents.
- We found no stellarator citizen-science game comparable to Foldit.

## Bundling AI agents for public-good research

- [EinsteinArena](https://arxiv.org/abs/2606.10402) (Bianchi, Kwon, Pappu and Zou;
  launched March 2026): an agent-native platform where anyone's agents work on open
  mathematical problems, each with a verifier, a public leaderboard and a discussion
  forum. Agents build on each other's ideas; 12 new state-of-the-art results by May
  2026, for example the kissing number in dimension 11 from 593 to 604. Closest to
  our organizational model.
- [Erdős problems](https://github.com/teorth/erdosproblems/wiki/AI-contributions-to-Erd%C5%91s-problems):
  AI contributions to more than 100 open problems; per
  [Quanta](https://www.quantamagazine.org/why-the-legendary-erdos-problems-are-falling-to-ai-20260803/),
  most came from hobbyists and undergraduates using public models.
- [Tokens for Good](https://github.com/Tokens-for-Good/tokens-for-good): donated spare
  AI tokens, through an MCP server for Claude Code and similar tools, research
  nonprofits; dual independent submissions and a deterministic scorer, never the
  writing model.
- Context: about [a million agent pull requests](https://arxiv.org/pdf/2609.26847) on
  GitHub in 2025, new GitHub controls restricting outside pull requests, and work on
  [governing agent contributions](https://arxiv.org/pdf/2607.15769).

## What this means for this project

1. **The niche appears open.** Unpublished or internal projects may exist; a web
   search cannot exclude them.
2. **ConStellaration is a candidate community benchmark.** The roadmap already
   prefers an existing benchmark for MS0, and
   [issue #65](https://github.com/DrWorkhard/nuclear-fusion-at-home/issues/65) lists it as a data source.
   Its coil benchmark also calibrates our boundary limit; see the
   [deep dive](CONSTELLARATION.md).
3. **EinsteinArena shows that open agent collaboration works when results are
   checked automatically.** Our acceptance checks play that role; making them
   portable (MS0) is what lets agent contributions add up; see the
   [deep dive](EINSTEINARENA.md).
4. **Possible contacts:** Kaptanoglu and Gil (coil realization) and the PPPL/Simons
   community. Contact needs the owner's separate decision.

Limits: web search through October 2026; no project's code or results were rerun.
