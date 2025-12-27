


From: Carlos Eduardo Pomarino Dextre <carlose.pomarino@gmail.com> 
Sent: Tuesday, 23 December 2025 19:26
To: tijn.vanderzant@gmail.com
Subject: Fwd: first data clean up output LP's



---------- Forwarded message ---------
From: Dirk Meuleman <dirkmeuleman@phenixcapitalgroup.com>
Date: Thu, 18 Dec 2025 at 11:59 AM
Subject: first data clean up output LP's
To: Antoine COLSON <antoine.colson@ipem-market.com>
CC: Claire VILLAUDY <claire.villaudy@ipem-market.com>, Marialena Tsoli <marialena.tsoli@ipem-market.com>, Heloise BORDES <heloise.bordes@ipem-market.com>, Stefan Ciuta <stefanciuta@phenixcapitalgroup.com>, Carlos Eduardo Pomarino Dextre <carlose.pomarino@gmail.com>

Dear Antoine & team,

Here is the first batch of data that was cleaned up and put in an actionable format for the team. This includes both over 1000 companies and 5800 LP contacts: https://docs.google.com/spreadsheets/d/1cunnBZ-V_jGdUL5uW4TKxahwKYMhxMAgsMe4l7a_iAQ/edit?usp=sharing

Most relevant is the “contacts” tab, which contains all the “Certified” contacts cleaned and a few bonus ones from the initial data merger exercise. As much as possible we tried to align this with the draft essential import data standard. The “Work Status” agent columns have an A/B test of two AI models (change happens starting with row 3619), curious what feedback there is between the two models.

Please have a check trough. I notice a number of IR persons that are currently certified LP’s and Automatically decertified contacts where I don’t understand why they are currently registered as such in the IPEM data we received.  Would love to have a call with the team and Stefan to go trough a number of cases where we all spot inconsistencies so we can sharpen the models on that feedback. 

Kind regards,

Dirk



________________________________________




FYI, maybe this also gives you some context into what their tech team has been building.

 
From: Stefan Ciuta <stefanciuta@phenixcapitalgroup.com>
Date: Monday, 8 December 2025 at 13:38
To: Geoffrey RAMDE <geoffrey.ramde@ipem-market.com>
Subject: Re: [EXT] Re: peux tu envoyer la structure de données ERP/HUbspot à Stefan en cc? stp
This is very useful, I think it’s a great idea to go through this! I’m sure that in the process we will also uncover any discrepancies between Hubspot and the ERP to see where the gaps are in the data we received.

Talk soon,
Stefan

Kind regards,
 
Stefan Ciuta
Data Analyst
 
Phenix Capital Group BV
Phenix Capital Group B.V. I De Mondraatoren, Amstelplein 6 I 1096 BC I Amsterdam I The Netherlands
(Company) T : +31 20 240 2731
(Personal) T: +31627859380
W : http://www.phenixcapitalgroup.com
Let us know your biggest challenge with impact investing.
 
 
 
From: Geoffrey RAMDE <geoffrey.ramde@ipem-market.com>
Date: Monday, 8 December 2025 at 11:43
To: Stefan Ciuta <stefanciuta@phenixcapitalgroup.com>
Subject: RE: [EXT] Re: peux tu envoyer la structure de données ERP/HUbspot à Stefan en cc? stp
16.30 it is then.

I am sending a summary of the Laravel 12 sync project "integration-hubspot". 
I was thinking, for our meeting, of presenting the hubspot web interface to visualize the new system and answering any questions you have.

1. The IPEM ERP ↔ HubSpot Connector
What are we building?
We are building a bidirectional synchronization bridge (middleware) between two distinct systems:
1.	The ERP (IPEM-Market): A custom-built Laravel application. This is the operational heart of the company. It manages detailed user profiles, event logistics (badges, booths), invoicing, and the product catalog.
2.	The CRM (HubSpot): A SaaS platform used by the Sales and Marketing teams. It manages lead acquisition, sales pipelines (deals), and email marketing.
Why?
•	Sales Efficiency: Salespeople work in HubSpot. When they close a deal, the ERP needs to know immediately to generate invoices and issue event tickets.
•	Marketing Precision: The ERP holds deep data about customers (e.g., "How much money does this Fund manage?", "What sectors do they invest in?"). Marketing needs this data in HubSpot to send targeted campaigns.
•	Single Source of Truth: We need to prevent data silos. If a user updates their phone number in the ERP, the Sales team must see it in HubSpot.
________________________________________
2. The Architecture
The system is designed as a "Double-Loop" middleware. It lives inside the Laravel ERP codebase but acts as a separate module.
How it works (The Mechanics)
A. Inbound Traffic (HubSpot → ERP)
•	Trigger: When a user modifies data in HubSpot (e.g., changes a phone number), HubSpot sends a Webhook.
•	Process: The ERP receives this webhook, validates it, puts it into a Queue, and processes it asynchronously.
•	Safety: We use a "Silent Save" technique. When the ERP saves this data, it suppresses internal events to prevent sending the data back to HubSpot immediately (preventing an infinite loop).
B. Outbound Traffic (ERP → HubSpot)
•	Trigger: When the ERP code saves a model (e.g., User::save()), an Observer detects the change.
•	Process: A job is dispatched to the Queue. This job transforms the ERP data into HubSpot's JSON format and pushes it via the API.
•	Safety: We use job batching to handle dependencies (e.g., "Create the Company first, then create the Contact, then link them").
________________________________________
3. The Data Model (The Core Challenge)
We are syncing 4 Standard Objects and 2 Custom Objects. Below is the translation guide between the two worlds.
1. Companies (Organizations)
•	ERP Entity: Organization (organismes table)
•	HubSpot Object: Company
•	Key Concept: Hierarchy & Categorization.
o	Matching: We link them via a custom field id_ipem (ERP Primary Key) and Domain Name.
o	Categorization: Companies are strictly categorized via a "Main Activity" dropdown (e.g., Bank, Family Office, Fund Manager).
o	Logic: Depending on the category, specific profile fields unlock (e.g., "Assets Under Management" is only synced if the company is an Investor).
2. Contacts (Users)
•	ERP Entity: User (users table)
•	HubSpot Object: Contact
•	Key Concept: The "LP" (Limited Partner) Profile.
o	The Persona: In our industry, an "LP" is an investor. This is a VIP persona.
o	The EAV Model: The ERP uses an Entity-Attribute-Value system (dynamic forms) to store detailed preferences (e.g., "I invest in Tech in Asia").
o	The Translation: The Connector flattens these complex database rows into simple semi-colon separated strings for HubSpot (e.g., Investment_Area: "Asia;Europe").
3. Deals (Forecasts)
•	ERP Entity: Forecast (previsions table)
•	HubSpot Object: Deal
•	Key Concept: Sales Pipeline vs. Operational Commit.
o	Direction: Primarily HubSpot → ERP. Sales create Deals in HubSpot.
o	The Trigger: When a Deal reaches "Closed Won" (100%) in HubSpot, the ERP "Commits" the forecast. This triggers the generation of Invoices and Badges in the ERP.
o	Billing: The ERP sends back billing details (VAT Number, Billing Address) to HubSpot so the deal record is complete.
4. Products
•	ERP Entity: Product (prestations table)
•	HubSpot Object: Product
•	Direction: ERP → HubSpot.
•	Concept: The ERP is the catalog master. It pushes items like "Visitor Pass", "Gold Sponsorship", or "3x3m Booth" to HubSpot so salespeople can add them to Deals.
5. Events (Editions) — Custom Object
•	ERP Entity: Edition
•	HubSpot Object: Event (Custom ID: 2-145470707)
•	Concept: Represents a physical event (e.g., "IPEM Cannes 2024").
•	Usage: All Contacts, Companies, and Deals are linked to an Event to track participation history.
6. Booth Locations — Custom Object
•	ERP Entity: Booth (tables)
•	HubSpot Object: Booth Location (Custom ID: 2-145470575)
•	Direction: ERP → HubSpot.
•	Concept: Inventory Management.
•	Details: Represents a physical stand on the floor plan. Includes properties like Booth Number, Price, and Availability. Salespeople check this in HubSpot to see what they can sell.


________________________________________
De : Stefan Ciuta <stefanciuta@phenixcapitalgroup.com>
Envoyé : lundi 8 décembre 2025 10:57
À : Geoffrey RAMDE <geoffrey.ramde@ipem-market.com>
Objet : Re: [EXT] Re: peux tu envoyer la structure de données ERP/HUbspot à Stefan en cc? stp 
 
16.30 is fine by me, we can meet then if it’s not too late for you.

Do you need anything from me to prepare for this call besides familiarizing myself with the data model you attached?

See you soon!

Kind regards,
 
Stefan Ciuta
Data Analyst
 
Phenix Capital Group BV
Phenix Capital Group B.V. I De Mondraatoren, Amstelplein 6 I 1096 BC I Amsterdam I The Netherlands
(Company) T : +31 20 240 2731
(Personal) T: +31627859380
W : http://www.phenixcapitalgroup.com
Let us know your biggest challenge with impact investing.
 
 
 
From: Geoffrey RAMDE <geoffrey.ramde@ipem-market.com>
Date: Monday, 8 December 2025 at 10:46
To: Stefan Ciuta <stefanciuta@phenixcapitalgroup.com>
Subject: RE: [EXT] Re: peux tu envoyer la structure de données ERP/HUbspot à Stefan en cc? stp
Hello Stefan,

Sorry for the late reply. Yes, I would like to still meet this afternoon. Is 16h30 Paris time acceptable?
I am sending you the invite.


See you soon,
Geoffrey
________________________________________
De : Stefan Ciuta <stefanciuta@phenixcapitalgroup.com>
Envoyé : lundi 8 décembre 2025 10:38
À : Geoffrey RAMDE <geoffrey.ramde@ipem-market.com>
Objet : Re: [EXT] Re: peux tu envoyer la structure de données ERP/HUbspot à Stefan en cc? stp 
 
Just following up on this in case I missed an invite/email. I looked at the data model and indeed a follow-up call is needed.

Do you still want to meet this afternoon, or shall we schedule for another day? Pls let me know your availability, happy to work around that.

Thank you for your time!

Kind regards,
 
Stefan Ciuta
Data Analyst
 
Phenix Capital Group BV
Phenix Capital Group B.V. I De Mondraatoren, Amstelplein 6 I 1096 BC I Amsterdam I The Netherlands
(Company) T : +31 20 240 2731
(Personal) T: +31627859380
W : http://www.phenixcapitalgroup.com
Let us know your biggest challenge with impact investing.
 
 
 
From: Stefan Ciuta <stefanciuta@phenixcapitalgroup.com>
Date: Friday, 5 December 2025 at 16:58
To: Geoffrey RAMDE <geoffrey.ramde@ipem-market.com>, Antoine COLSON <antoine.colson@ipem-market.com>
Subject: Re: [EXT] Re: peux tu envoyer la structure de données ERP/HUbspot à Stefan en cc? stp
I have another meeting between 3-4PM, otherwise I am available Monday. Please feel free to schedule something at your convenience @Geoffrey RAMDE

Kind regards,
 
Stefan Ciuta
Data Analyst
 
Phenix Capital Group BV
Phenix Capital Group B.V. I De Mondraatoren, Amstelplein 6 I 1096 BC I Amsterdam I The Netherlands
(Company) T : +31 20 240 2731
(Personal) T: +31627859380
W : http://www.phenixcapitalgroup.com
Let us know your biggest challenge with impact investing.
 
 
 
From: Geoffrey RAMDE <geoffrey.ramde@ipem-market.com>
Date: Friday, 5 December 2025 at 16:46
To: Antoine COLSON <antoine.colson@ipem-market.com>, Stefan Ciuta <stefanciuta@phenixcapitalgroup.com>
Subject: [EXT] Re: peux tu envoyer la structure de données ERP/HUbspot à Stefan en cc? stp
Yes. How about Monday afternoon @Stefan?
I am also available most of the rest of the week. 

Envoyé à partir de Outlook pour Android
________________________________________
From: Antoine COLSON <antoine.colson@ipem-market.com>
Sent: Friday, December 5, 2025 4:40:20 PM
To: Geoffrey RAMDE <geoffrey.ramde@ipem-market.com>; Stefan Ciuta <stefanciuta@phenixcapitalgroup.com>
Subject: RE: peux tu envoyer la structure de données ERP/HUbspot à Stefan en cc? stp 
 
Yes it helps a lot ; Stefan will need a direct conversation with you I believe!
 
De : Geoffrey RAMDE <geoffrey.ramde@ipem-market.com>
Envoyé : vendredi 5 décembre 2025 16:29
À : Antoine COLSON <antoine.colson@ipem-market.com>; Stefan Ciuta <stefanciuta@phenixcapitalgroup.com>
Objet : Re: peux tu envoyer la structure de données ERP/HUbspot à Stefan en cc? stp
 
Bonjour Antoine, 
 
 
Est-ce bien cela ? 
________________________________________
From: Antoine COLSON <antoine.colson@ipem-market.com>
Sent: Friday, December 5, 2025 4:17:28 PM
To: Geoffrey RAMDE <geoffrey.ramde@ipem-market.com>; Stefan Ciuta <stefanciuta@phenixcapitalgroup.com>
Subject: peux tu envoyer la structure de données ERP/HUbspot à Stefan en cc? stp
 
 
 
 
 
Antoine COLSON
CEO & Managing Partner
 
antoine.colson@ipem-market.com
+33 (0)6 62 25 36 17
44 avenue George V, 75008 Paris, France
www.ipem-market.com
 
     

 
 
 
 
 



FYI

 
From: Stefan Ciuta <stefanciuta@phenixcapitalgroup.com>
Date: Thursday, 11 December 2025 at 13:26
To: Geoffrey RAMDE <geoffrey.ramde@ipem-market.com>
Cc: Gauthier HUTTEAU <gauthier.hutteau@ipem-market.com>, Benjamin DELESPIERRE <benjamin.delespierre@ipem-market.com>
Subject: Re: [EXT] Global Export from the ERP
Hi Geoffrey,

If the users were archived, I’d suppose they were archived for a reason, so I don’t see the point of including them. Nonetheless, it’s good we understand why the data was mismatched.

Regarding the seemingly few “Certified” contacts, Dirk and I will double check with Antoine if we should only include those. Feel free to share if you have any other relevant information about the contacts’ certification status label.

Many thanks,
Stefan

 
From: Geoffrey RAMDE <geoffrey.ramde@ipem-market.com>
Date: Wednesday, 10 December 2025 at 17:23
To: Stefan Ciuta <stefanciuta@phenixcapitalgroup.com>
Cc: Gauthier HUTTEAU <gauthier.hutteau@ipem-market.com>, Benjamin DELESPIERRE <benjamin.delespierre@ipem-market.com>
Subject: RE: [EXT] Global Export from the ERP
Good evening Stefan,


It seems there are still some discrepencies caused by the fact that I tried to remove the archived users from the tables but not for everything at the same time.
For example, both ADS STRATEGIE PRO and ALCHEMY VENTURES only have archived LP users belonging to them.

As for the small number of Certified LPs compared to the whole of our users. It is because they are truly a minority. For example, I believe that we almost had ALL the french LPs for our event P2025.
I will have to check with our other services to get more info on that.

I think it would be best if I removed the filering on the 'deleted_at' and, instead, showed the value in a column. What do you think?

Great evening to you too!
Geoffrey

________________________________________
De : Stefan Ciuta <stefanciuta@phenixcapitalgroup.com>
Envoyé : mercredi 10 décembre 2025 17:01
À : Geoffrey RAMDE <geoffrey.ramde@ipem-market.com>
Cc : Gauthier HUTTEAU <gauthier.hutteau@ipem-market.com>; Benjamin DELESPIERRE <benjamin.delespierre@ipem-market.com>
Objet : Re: [EXT] Global Export from the ERP 
 
Good afternoon gentlemen,

I have run a small data quality audit to cross-reference the Organizations sheet with the Contacts sheet. Specifically, I analyzed all 8,549 organizations where the “has_lp_user" column is marked “Yes”. I wanted to verify that these organizations actually have valid, associated LP contacts in the database.

Here is the breakdown of what I found:

1.	Data Mismatch (1.5%)
a.	128 organizations are marked as has_lp_user = "Yes", but we could not find any associated contacts for them marked as LPs in the contacts sheet.
a.	Examples: ADS STRATEGIE PRO, ALCHEMY VENTURES.
2.	The "Uncertified" Majority (72.5%)
a.	6,194 organizations have associated LP contacts, but none of those contacts are marked as “Certified".
b.	Examples: 1199SEIU NATIONAL BENEFIT FUND, 1291 GROUP.
3.	Validated Certified Coverage (26%)
a.	2,227 organizations have at least one contact marked specifically as "Certified".
b.	Examples: 1010 CAPITAL, 1788 CAPITAL TRUST SA.

The “has_lp_user" column appears largely reliable, though there is a small 1.5% gap where data is missing. However, my more important mention is about the "Certified” status:

If we filter the dataset to only keep organisations with “Certified” LP contacts, we will drop approx. 72% of our potential LP organisations. Out of almost 96000 contacts, only 4275 are “Certified” and marked as LPs.

Am I missing something about the “certification_status_label” or is this the actual size of our usable dataset? Please feel free to give your two cents on this when you have the time.

Wishing you a great evening!

Gratefully,
Stefan

Kind regards,
 
Stefan Ciuta
Data Analyst
 
Phenix Capital Group BV
Phenix Capital Group B.V. I De Mondraatoren, Amstelplein 6 I 1096 BC I Amsterdam I The Netherlands
(Company) T : +31 20 240 2731
(Personal) T: +31627859380
W : http://www.phenixcapitalgroup.com
Let us know your biggest challenge with impact investing.
 
 
 
From: Stefan Ciuta <stefanciuta@phenixcapitalgroup.com>
Date: Wednesday, 10 December 2025 at 12:00
To: Geoffrey RAMDE <geoffrey.ramde@ipem-market.com>
Cc: Gauthier HUTTEAU <gauthier.hutteau@ipem-market.com>, Benjamin DELESPIERRE <benjamin.delespierre@ipem-market.com>
Subject: Re: [EXT] Global Export from the ERP
Thanks Geoffrey,

I agree it’s good to get all the raw data, just wanted to confirm that’s what I have here. Also completely agree with your point of lacking documentation, so we can keep this thread as a trace of what’s happening.

For now, I’ll finalise the foundational taxonomy for LP organisations & funds. When that is approved by Dirk & Antoine, I’ll start interpreting data from forms into the new format.

Regards,
Stefan

Kind regards,
 
Stefan Ciuta
Data Analyst
 
Phenix Capital Group BV
Phenix Capital Group B.V. I De Mondraatoren, Amstelplein 6 I 1096 BC I Amsterdam I The Netherlands
(Company) T : +31 20 240 2731
(Personal) T: +31627859380
W : http://www.phenixcapitalgroup.com
Let us know your biggest challenge with impact investing.
 
 
 
From: Geoffrey RAMDE <geoffrey.ramde@ipem-market.com>
Date: Tuesday, 9 December 2025 at 16:58
To: Stefan Ciuta <stefanciuta@phenixcapitalgroup.com>
Cc: Gauthier HUTTEAU <gauthier.hutteau@ipem-market.com>, Benjamin DELESPIERRE <benjamin.delespierre@ipem-market.com>
Subject: RE: [EXT] Global Export from the ERP
Hi Stefan,

Thank you for your excellent and detailled questions.
The goal is to give you as much data as possible. With this you will have ALL the users, companies and funds in our database.
Let me address each of your points:
1.	Companies
a.	We mostly use the "brand_name" (enseigne in db) as opposed to the legal "name" (raisonSociale).
b.	Indeed, this is by design. The form_answers column in the "Global Companies" and "Global Funds" tables contains answers to organization-level and fund-level questions. The data you are looking for for the firms (answers from the LPs) is in the form_answers column of the "Global Contacts".
c.	The “has_lp_user” column is reliable and check if a company has at least one user who is classified as an LP (not necessarily certified). In our database, a company may be an "Investor" type but not have any LPs. 
2.	Funds
a.	This is also by design. The "Funds" contains data specific to each individual fund. For firm-level characteristics of the manager (e.g., their overall company AUM, geographic expertise, or company overview), you should reference the "Global Company" by linking on the fund_manager_id.
3.	Form answers
a.	Indeed. This is to have a more human look at the questions and answers from the columns "form_answers".

In the end, after our talk yesterday, I believe it would be best for you to have as much of our raw data as possible instead of me trying to adapt it to you data model as much could be lost in translation.
From this, the only data missing should be the soft deleted ones.

I am okay with doing a catch-up if you have anymore questions but I also think keeping a written record like this is good. We are severly lacking in documentation concerning this so it's a good way to add some 😅.


Have a good evening,
Geoffrey

________________________________________
De : Stefan Ciuta <stefanciuta@phenixcapitalgroup.com>
Envoyé : mardi 9 décembre 2025 15:22
À : Geoffrey RAMDE <geoffrey.ramde@ipem-market.com>
Cc : Gauthier HUTTEAU <gauthier.hutteau@ipem-market.com>; Benjamin DELESPIERRE <benjamin.delespierre@ipem-market.com>
Objet : Re: [EXT] Global Export from the ERP 
 
Hi Geoffrey,

Thanks for putting this together so quickly!

Couple of things I’d like to clarify:

1.	Companies
a.	There are two name columns (“name” and “brand name”) with significant differences for some companies (name “G INVESTMENTS GROUP LLC” vs brand name “FO”). Do you recommend using a specific column here?
b.	I notice the companies table is much emptier than the old one (no associated contacts, type, main activity, asset classes, typical investment size, market, region, etc). I see some of this data is scattered in the “form_answers” column but there doesn’t seem to be any linear structure to that data. Is this by design? As in you didn’t add those columns so I can map data upstream according to the new taxonomy, from associated contacts and form answers to company level?
c.	How reliable is the “has_lp_user” column? If I filter that on “yes”, I’m left with 8551 companies, while your old investors table starts with 11178 entries. If that filter reliably gives me all the companies with an “LP” user, then it’s perfect, just wanted to point out the number discrepancy.
2.	Funds
a.	Same as point b) under companies about data points missing. I suppose the idea is also to leave it empty so data can be pushed upstream?
3.	Form answers
a.	This seems to be an overview of all the fields that appear in forms rather than a collection of answers. I suppose this is not relevant for my use-case and the answers (which I need) are under contact level and in the “form_answers” columns for companies & funds.
Overall, the feeling I’m getting here is that you tried to simplify company data as much as possible so I can start pushing things upstream from contacts & form answers. If I start pushing data upstream for LPs based on this global export, are we confident that I’m not missing out on any data?

Please let me know if you’d rather have a quick catch-up than continue this email thread.

Many thanks,
Stefan

Kind regards,
 
Stefan Ciuta
Data Analyst
 
Phenix Capital Group BV
Phenix Capital Group B.V. I De Mondraatoren, Amstelplein 6 I 1096 BC I Amsterdam I The Netherlands
(Company) T : +31 20 240 2731
(Personal) T: +31627859380
W : http://www.phenixcapitalgroup.com
Let us know your biggest challenge with impact investing.
 
 
 
From: Geoffrey RAMDE <geoffrey.ramde@ipem-market.com>
Date: Tuesday, 9 December 2025 at 10:12
To: Stefan Ciuta <stefanciuta@phenixcapitalgroup.com>
Cc: Gauthier HUTTEAU <gauthier.hutteau@ipem-market.com>, Benjamin DELESPIERRE <benjamin.delespierre@ipem-market.com>
Subject: [EXT] Global Export from the ERP
Hello Stefan,

As said yesterday, here is a Metabase containing the entirety of the Users, Companies and Funds as well as all the Form questions.
http://metabase.ipem-market.com/public/dashboard/75a7a9f7-bd9b-40c2-9c41-1b41ed1f0137


I also added the event participation as our current matchmaking is done only on LP users and Fund Manager companies and their funds participating in the same event.

A fund manager company is defined as a company with : 
the "Company Type" being "GP" or "Fund Manager"  
OR having the "Main Activities" 'GP'/'Asset Manager'/'Fund of Funds'


Have a nice day,
Geoffrey



________________________________________
________________________________________


For the MVP funds database and matchmaking, we would need:
1. Foundational fields:
a. Name
b. Country
c. Asset class(es)
d. Markets they invest in -> Developed, Emerging, Global, etc.
e. Regions or countries they target -> Western Europe, South Africa, Global, etc.
f. Target size value & currency
2. (Optional) Thematic fields:
a. SDGs targeted
b. Any qualitative data highlighting a fund’s investment strategy, ex. fields such as
"organization_sectors_expertise" in Metabase
3. Commitments mapping:
a. Data point that acts as a “key” of what investor “organisme” allocated capital to
this fund -> could be a unique ID that points to the right investor(s) for example
b. (optional) any other data pertaining to commitment(s) received by the fund
For the MVP investors database and matchmaking, we would need:
1. Foundational fields:
a. Name
b. Country
c. Asset class(es)
d. Markets they invest in -> Developed, Emerging, Global, etc.
e. Regions or countries they target -> Western Europe, South Africa, Global, etc.
f. AUM value & currency
g. Investor type: Family Office, Bank, Pension Fund, etc.
2. (Optional) Thematic fields:
a. Description (“about” section) for the investor
b. SDGs targeted
c. Any qualitative data highlighting an investor’s investment appetite, ex. fields such
as "organization_main_strategy_investment" in Metabase
3. Commitments mapping:
a. Data point that acts as a “key” of what fund this investor has allocated capital to
-> could be a unique ID that points to the right fund(s) for example
b. (optional) any other data pertaining to commitment(s) made by the investor




IMPORTANT: DO NOT CHANGE THE GOOGLE SHEET
DO NOT CHANGE EXTERNAL DATA

Metabase login
stefanciuta@phenixcapitalgroup.com
d5WhtLBcG3pdO3