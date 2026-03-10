Introduction
Hackathon Galáctica: WDK Edition 1 is the first hackathon in Tether's Hackathon Galáctica series—an online program designed to explore agents as economic infrastructure and accelerate the next generation of agentic builders.

From 25.02.2026 to 22.03.2026, developers will build AI agents and applications that hold wallets, move money, and settle value onchain—powered by self-custodial infrastructure across 6+ chains.

AI agents are no longer just tools — but they are also not social experiments.
In this hackathon, we explore agents as economic infrastructure: autonomous systems that execute tasks, manage capital, and interact with onchain logic under clearly defined constraints.

→ Builders define the rules → Agents do the work → Value settles onchain

Rather than optimizing for discourse, engagement, or popularity, projects are evaluated on correctness, autonomy, and real-world viability.

While others chase hype, we build what lasts.

Please read the Rules and Terms of Participation carefully before deciding if you want to participate. You are required to agree to both the Rules and Terms of Participation in order to participate in this Hackathon. The Rules and  Terms of Participation  should be read in conjunction with the Privacy Statement for the Hackathon.

Prizes
🏆 Best Projects Overall
Awarded to the team that delivers the most complete, impactful, and forward-looking project of the hackathon. This prize recognizes excellence across all dimensions—technical execution, product vision, real-world applicability, and alignment with the future of agentic finance and programmable money. The winning project should not just work, but set a standard others will want to build on.

Tracks
Additionally, there are prizes for the winners of each track:

🤖 Agent Wallets (WDK / Openclaw and Agents Integration)

Hackathon Timeline
February 25 – March 15

Feb 25 – Registrations open
Mar 9 – Submissions open
Mar 22 – Submissions close
Tips for Hackers
Start with the docs — Get familiar with WDK modules, MCP tools, and agent skills before you build. → WDK Docs
Use the AI toolkit — Connect your coding assistant to WDK docs, or give your agent wallet capabilities out of the box. → WDK AI Docs
Community Support
Join the Discord — Ask questions, find teammates, and get help from mentors
Eligibility
Open to everyone, worldwide
Individuals and teams are welcome
New or existing projects are allowed, as long as they are actively extended or adapted during the hackathon
Submissions must clearly fit at least one official track and meet that track’s requirements
Each project can be submitted to one primary track
Participants must follow applicable laws, platform rules, and hackathon terms
All participants may be subject to a standard background check
Judging criteria
Projects are evaluated based on:

Technical correctness Sound architecture, clean integrations, and reliable execution. Proper use of relevant tools (e.g. WDK, OpenClaw, protocols) and working end-to-end flows are expected.
Degree of agent autonomy How independently the agent operates. Strong submissions demonstrate planning, decision-making, and execution without constant human input, rather than simple scripts or manual triggers.
Economic soundness Sensible use of USD₮, XAU₮, or other assets, with attention to incentives, risk, and sustainability. The agent’s behavior should make economic sense in real conditions.
Real-world applicability Clear user value, realistic use cases, and a plausible path to adoption. Projects should feel deployable beyond the hackathon, not just proof-of-concept demos.
Contact us
You can reach the team throughout the hackathon via our Discord server or by posting questions in the DoraHacks Questions section. We’ll be actively monitoring both channels to support all hackers.

Once you join the Discord, head to the Hackathon Galáctica: WDK Edition 1 category, where you'll find dedicated channels for announcements, rules, team finding, project ideas, and technical support.

About us
After democratizing finance with USD₮, we are now advancing toward technology sovereignty — empowering users with autonomous, open, and censorship-resistant systems.

WDK Docs: https://docs.wdk.tether.io/
WDK AI Docs: https://docs.wdk.tether.io/start-building/build-with-ai


## SOLUTION SUGGESTION


### The Winning Concept: "Axiom" (Autonomous Financial Controller)
**Target Track:** 🌊 Autonomous DeFi Agent (or 🤖 Agent Wallets)
**Elevator Pitch:** Axiom is an AI-driven treasury and escrow agent for DAOs, small businesses, and freelancers. You give it a natural language economic mandate, and it autonomously manages cash flow, lends idle funds for yield, and executes payments based on real-world triggers verified via off-chain APIs.

#### The Core "Rule -> Work -> Settle" Flow
1. **The Builder defines the rule:** *"Keep 500 USD₮ liquid in the checking wallet. Lend all excess USD₮ on the highest-yielding pool across Arbitrum or Base. If a contributor merges a Pull Request in our GitHub repo, pay them 50 USD₮."*
2. **The Agent does the work:** Axiom runs in a continuous loop. It monitors your GitHub repo via an MCP (Model Context Protocol) tool. Simultaneously, it monitors DeFi lending rates. *Crucially, it calculates gas and bridge fees before moving funds to ensure the move is mathematically profitable.*
3. **Value settles onchain:** When a PR is merged, the agent uses Tether WDK to send 50 USD₮ to the developer. It uses Openclaw to autonomously bridge and deposit excess funds into Aave.

### Why this specific idea wins the Hackathon

To win the Overall Best Project (6,000 USD₮), you must score perfectly across the four judging criteria. Here is how Axiom dominates them:

#### 1. Technical Correctness (Flawless Execution)
*   **How to win it:** Do not use a generic smart contract wallet. You **must** deeply integrate Tether’s **WDK** (Wallet Development Kit) to generate and manage the self-custodial wallet. Use the **AI Toolkit / Openclaw** to give your LLM the exact functions it needs to execute transactions. Use standard **MCP tools** to pull in off-chain data (like GitHub PRs, or a web scraper for APY rates).

#### 2. Degree of Agent Autonomy (No manual triggers)
*   **How to win it:** Most hackers will build a chatbot where the user has to type "send 50 USDT". *That is a script, not an agent.* Axiom will use a cron-job or a continuous evaluation loop (e.g., LangGraph or AutoGen). It wakes up every 10 minutes, evaluates its constraints, plans its actions ("PR merged + excess funds detected"), and executes without a single human click. 

#### 3. Economic Soundness (The Secret Weapon)
*   **How to win it:** Judges hate when a DeFi agent spends $5 in gas to farm $0.10 in yield. Axiom will have a built-in "Profitability Checker" skill. Before any DeFi transaction, the agent queries current gas fees and calculates the "Time to Break Even." If it takes 6 months to earn back the bridge fee, the agent decides *not* to move the money. **Printing this logical decision in your demo video will instantly prove "economic soundness" to the judges.** Furthermore, you can program it to hedge 10% of funds into **XAU₮ (Tether Gold)** if market volatility (read via MCP) spikes.

#### 4. Real-World Applicability (Viability)
*   **How to win it:** Every Web3 project, DAO, and freelancer needs an automated way to manage idle cash and pay contributors trustlessly. This is a deployable B2B SaaS product, not a toy. 

---

### Technical Architecture Blueprint

If you want to build this today, here is the exact tech stack you should use:

*   **Brain:** Claude 3.5 Sonnet or GPT-4o (excellent at strict tool-calling and json outputs).
*   **Agent Framework:** LangGraph or simple Python/Node.js while-loops. You want strict control over the agent's thought process.
*   **Wallet Infrastructure:** **Tether WDK** (Mandatory). Use the WDK AI tools to inject wallet capabilities directly into the LLM context.
*   **Onchain Interactions:** **Openclaw** to read balances, transfer USD₮, and interact with basic DeFi protocols.
*   **Off-chain Integrations:** **Model Context Protocol (MCP)**. Set up an MCP server to connect to the GitHub API (for the task-to-pay feature) and a standard Crypto API (like CoinGecko/DefiLlama) to fetch live APY and Gas rates.

### Recommended Development Timeline (Now to March 22)

*   **Days 1-2 (Mar 10-11):** **Start with the docs.** Clone the WDK and set up a basic Node.js/Python script that can generate a WDK wallet and send USD₮ on a testnet. 
*   **Days 3-5 (Mar 12-14):** Build the Agentic Loop. Give your LLM access to WDK tools via Openclaw and set up the MCP server to read mock APY rates or a mock Web2 API (like GitHub or a Weather API).
*   **Days 6-8 (Mar 15-17):** Implement the "Economic Soundness" logic. Force the agent to calculate gas costs vs. yield before executing a WDK transaction.
*   **Days 9-10 (Mar 18-19):** End-to-end testing across at least 2 chains (e.g., Arbitrum and Base) to prove the cross-chain viability mentioned in the prompt.
*   **Days 11-12 (Mar 20-21):** Polish the UI/Terminal output. Record a flawless 3-minute demo video showing the agent's terminal logs where it *reasons* about its constraints, checks gas, and moves USD₮ autonomously.

**Pro Hackathon Tip:** Don't build a complex frontend. Since this is an *autonomous agent* hackathon, a beautifully formatted Terminal interface (using something like `rich` in Python or `chalk` in Node) showing the agent's "Thoughts," "Calculations," and "Onchain tx hashes" is actually much more impressive and authentic to judges than a clunky React dashboard. Focus 95% of your time on the agent's logic, autonomy, and WDK integration.


## Hackathon Rules:

Rules
These Rules and your participation in the Hackathon are subject to the Terms of Participation. Anyone can sign up as a participant in the Tether Hackathon Galactica: WDK Edition 1 (“Hackathon”), as long as you meet the Eligibility Requirements described in the Terms of Participation.
You are allowed to submit a single entry. You may not participate both individually and within a team and you may not participate as a member of multiple teams. If you are participating as a part of a team, please ensure that the project page on DoraHacks clearly lists you as a member of that team. See the “Signing-up” section below.
This Hackathon is about encouraging the adoption and use of Tether’s Wallet Development Kit (WDK by Tether), and a fundamental requirement is to use WDK by Tether in what you’re building.
You must ensure that your project is hosted on a GitHub repository that is accessible to us. In addition, given the purpose of this Hackathon is to showcase and encourage adoption of WDK by Tether you must also make it available publicly under the Apache 2.0 license during the Hackathon and for a reasonable period of time afterwards.
You are required to include a video of your project as part of your submission. Please upload the video to YouTube as “unlisted” and share a link to it in the submission form.
Your project must be easy for the judges to evaluate. Make sure it can be accessed directly—such as through a web browser or by running it out of the box.
You may use any programming language and framework, as long as:
Your project must integrate the WDK by Tether (Javascritp/Typescript) in a meaningful way. The technology stack is flexible, but proper agent architecture and WDK by Tether wallet integration are mandatory.
The submission must include clear instructions to run or test the project.
All third-party services, APIs, or pre-built components must be disclosed.
The deadline to submit your project is 22 March, 2026 at 23:59 UTC. The submission
process is detailed below under “Submitting a project”.

