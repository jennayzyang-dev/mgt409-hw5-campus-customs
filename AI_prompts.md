# AI Prompts Log — HW 5: Campus Customs Multi-Agent Operations

This is a log of the prompts I typed to my vibe coder, organized by problem.

---

## Problem 1: Vibe coder prompts

**Prompt:**
> create AI_prompts.md at the start of the assignment and keep it updated as you work
> this file is the log of what you typed to your vibe coder
>
> describe each problem to your vibe coder in your own words
>
> put one section for each problem
> each section must include
>
> * the problem number and title
> * at least one prompt you typed, inyour own words as much as possible
> * one follow up prompt if you needed it (and one sentence on what was lacking after the first )

**Follow-up prompt:** None needed.

---

## Problem 2: Explore the database and start the harness

**Prompt:**
> open data/campus_customs.db and look through every table and its fields
> copy the original file to data/campus_customs_new.db - later problems update that working copy
>
> study the three open tickets so you see how they link to other tables
> start output/harness.md. for each table, list the fields and one short line on why that table matters for the agents
>
> you will keep going this harness file in later problems
>
> ok for this question can you please show me the table so I can check the files and provie sone short line?

**Follow-up prompt:**
> I wrote my own one-line "why it matters" for each of the 9 tables — is my one sentence good? [then] yup pls do (add them to the harness)

**What was lacking after the first prompt:** The AI only listed the fields, so I wrote the rationale lines myself and asked for feedback; it caught that I had invoices backwards (they're bills vendors send us, not ones we send clients).

---

## Problem 3: MCP server with three tools

**Prompt:**
> write an MCP server in mcp_server/ using fastmcp. it will talk to data/campus_customes_new.db
> you do not need to connect or run it in this problem
>
> every agent in this hw uses the tools in this mcp server
> you will add more tools to it later; for now write three tools you know you will need for the tickets in the database
> keep the names clear. never invent any data, only use info in the database
>
> in output/harness.md, list each of your three MCP tools. for every tool include: which table it reads, which ticket it helps unlock (101,102,103), and one sentence on why that tool is the right one for that tikcet
>
> vague lines like 'read inventroy'' score low, tie  the tool to the ticket
>
> also add a short mcp_server/README.md file that explanins what the MCP server is for, which databse file it uses, and the tree tools it has

**Follow-up prompt:** None needed.

---

## Problem 4: Connect the MCP server and smoke-test each tool

**Prompt:**
> add the mcp server to vibe coder and test each tool
>
> in your vibe coder, add your mcp server to this project so the vibe coder can call the tools. save the connection JSON text in .mcp.json at the project root (or however your vibe coder saves local mcp server lists)
>
> with your vibe coder connected, test each of your three mcp tools
> save the evidence in output/mcp_smoke.json.
>
> for every tool include:
>
> * the prompt you asked the vibe coder
> * the tool name
> * the tool output (must match values in data/campus_customs_new.db)

**Follow-up prompt:**
> ok keep going finshih the prob 4

**What was lacking after the first prompt:** My first prompt didn't include the specific test prompts to run for each tool, so I had to tell it to go ahead and run the three smoke tests.

---

## Problem 5: Build the agent team and grow the MCP tools

**Prompt:**
> build the agentic team for campus customs using pydanticai: boss, inventory, accounting, facilities, and customer service
> include prompts, models, and agent loops so they can delegate work to each other with full connectivity.
>
> put the agent prompts in backend/prompts/ - one file per agent. put data types in backend/models.py, and the agent files under backend/ (your layout can vary as long as the five roles are clear). use your portkey_api_key and only gpt-6-luna for every agent
>
> write each prompt in your own words with the shop rules that agent needs. more detailed prompts that cover all aspects of an agent's work and scope score higher than a short generic prompt
>
> add any tools the agents need to your mcp server so they can work on the open tickets. shop facts come from the mcp server over data/campus_customs_new.db - do not invent a second shop-tools layer that bypasses MCP
>
> wire the agents so they append to output/audit_trail.json as they run: for each agent-loop step, record enough to audit later. append to this file - do not wipe it each run
>
> in output/harness.md, list each agent and each MCP tool (including ones you add in this problem) along with which table the tool uses. also add a short safety section: the guardrails a real business would want when agents touch real customers and real money, plus limits that keep token use in check
>
> update mcp_server/readme.md so the tool list matches what you have now

**Follow-up prompts:**
> show me your prompts now so i can revise
>
> 1 make it to 10% / 2 ok, 10 is good / 3 300 in checking / 4 ok / 5 ok / 6 2 days / 7 why cant agree? / 8 ok
>
> Humans approve money ... > here can you add maker and checker? so two humans can handle this not only one ppl

**What was lacking after the first prompt:** The AI drafted the shop rules itself (15% max discount, $500 cash warning, 3-day rent urgency, one approver), so I reviewed the prompts and set my own policy: 10% max discount, warn under $300, urgent at 2 days, and maker-checker so two different people must approve every payment.

---

## Problem 6: Plan the three tickets

**Prompt:**
> before you wire the backed, write down what you expect the team to do on each open ticket. build output/desk_tickets.html - a page you can double click with one tab per ticket (101,102 and 103) Also add empty cash and reflection tabs for later problems (leave them blank or with a short 'coming later' note for now)
>
> on each ticket tab, fill an expected section only (leave room for an actual section you will fill after you run the agents)
>
> for each ticket's expected section, write in your own words:
>
> * who the boss should call first, and why
> * all the agent delegations you expect - not "boss calls everyone"
> * which mcp tools you expect that run to use
>
> plans that send every specialist on every ticket score low. you will compare this plan to what actually happens when your agents resolve the three tickets

**Follow-up prompts:**
> show me three ticket detail first
>
> for 101 ticket > why call accounting if we have no invewntory
>
> pls update these (my input) for problem 6 — [then I wrote my own plan for each ticket: who the boss calls first and why, the delegations, and the MCP tools]

**What was lacking after the first prompt:** The AI wrote the plan in its own words, so I checked the ticket details, asked why accounting was on ticket 101 (to unblock the unpaid reprint invoice 501), and then replaced the plan with my own input.

---

## Problem 7: Backend routes

**Prompt:**
> your react frontend dashboard (the next problem) needs a backend it can call. in backend/main.py, use fastapi and add routes that do the following:
>
> * return the three tickets and whether each is open or resolved
> * take a ticket id and run your agent team on that ticket
> * return recent agent events - waht each agent said and which tools they used - so the board can refresh
> * approve a payment or purchase after a human clicks approve (agents only prepare the pay; this route is what actually changes cash)
> * return the current checking balance from cash_accounts
> * reset the database to the original values when you want to try a fresh run
>
> from the backend/ folder, start the server with:
> uvicorn main:app --reload --port 8000
>
> this turns on your backend at http://localhost:8000 so the frontend dashboard can call those routes.
> in output/harness.md, list each route in one line (what url/what it does)

**Follow-up prompts:**
> pls dont do anything related my hw4, for lecture it's fine its not that important as my homework
> so jjust follow what problem 7 says cuz im doing my hw5 and its more important

**What was lacking after the first prompt:** Port 8000 was already taken by an old Lecture 13 server, so the backend couldn't start with the exact command from the problem. I told the AI to stop only the lecture server (not my HW 4 one) and start the HW 5 backend on port 8000 as the problem says.

---

## Problem 8: Agent dashboard

**Prompt:**
> build the frontend dashboard in frontend/ with react + vite+typescript. the page should call the routes you built in problem 7. at minimum the board should:
>
> * list all 3 tickets
> * let you pick one ticket and start the agent team on it
> * show each agent and what they are saying/ doing while the ticket runs
> * mark a ticket resolved when the run finishes
> * show a short summary of what each agent did on that ticket
> * let a human approve a pay or purchase when asked
> * show the checking balance (it should drop after an approved pay)
>
> make the dashboard look good. be creative with the layout and feel - this is a real desk people would want to sit at, so put thought into how it looks
>
> tell the front end to talk to your backend at http://localhost:8000. on the backend, allow the vite page origin (usually http://localhost:5173) so the browser is allowed to call those routes.
>
> start the board with
> npm run dev
>
> this opens the react desk in your browser so you can pick tickets and watch agents
>
> write output/design.md with what you chose for the dashboard look (layout, how agents read differently, how resolved tickets and cash show up) and why - including the creative choices that make it feel special and something humans would actually enjoy using.

**Follow-up prompt:**
> give me the link and I'll check the layout

**What was lacking after the first prompt:** The board was built and tested, but I wanted to see the layout myself, so I asked for the link. It ran on http://localhost:5174 because another dev server was already using 5173, and the backend allows any local Vite port.

---

## Problem 9: Resolve the tickets

**Prompt:**
> before testing the agents on a full run over the three tickets, reset the working database data/campus_customs_new.db again so you start clean. note the starting checking balance. then run all three tickets on the board (101,102,103) until each is resolved.
>
> open output/desk_tickets.html from problem 6, on each ticket tab, fill the actual section from this run: which agents worked, what they delegated, and which tools they used. keep your expected section so you can compare the two.
>
> on the cash tab of the same output/desk_tickets.html, itemize the money: starting checking balance (after the reset); for each ticket: how cash changed when that ticket resolved, and why (which pay / purchase, dollar amount); ending checking balance — it must match cash_accounts in the working database. Wrong cash math loses points even if the board shows every ticket resolved. Also save: output/resolved_tickets.json — for each ticket: id, final status, short outcome, what each agent contributed, and any human approvals; output/resolved_board.html — a page you can double-click with a screenshot of your React board for each resolved ticket (101, 102, and 103). Append real runs to output/audit_trail.json. Finish output/harness.md so it covers tables, MCP tools, the five agents, API routes, the dashboard, and safety rules.

**Follow-up prompt (my approval decision):**
> Approve only invoice 501 ($840); signers: Jenna Yang (maker) / Test Checker (checker)

**What was lacking after the first prompt:** The prompt didn't say which prepared payments a human should approve, so I chose: pay the overdue $840 reprint invoice and leave the $2,400 rent and the $264 hoodie restock pending. Cash ended at $2,560.

---

## Problem 10: Reflection

**Prompt:**
> open output/desk_tickets.html and fill the reflection tab. answer in your own vibe, and be detailed and thorough: how would you evaluate the performance of the agents on each ticket and why; for each ticket, how did actual compare to the expected plan you wrote earlier; what would have been simpler as one agent with tools - and why; describe three new problems campus customs might face that this agent team could solve with the tools you built; describe three new problems campus customs might face that this agent team could not solve with the tools you built, and explain the tools and agents you would need to solve them. tie every answer to this app and the three tickets you ran - use the ticket tabs and cash tab on the same page as your evidence. generic AI essays without campus customs details will score low >> pls make sure you dont let me score low. and then pls answer those for me first

**Follow-up prompts:**
> can you pls make it my own words
>
> yes put in reflection tab and let me know if problem 10 is finished

**What was lacking after the first prompt:** The first draft didn't sound like me, so I asked for it in simpler, more casual wording, then checked it against my ticket tabs and Cash tab before putting it in the Reflection tab.
