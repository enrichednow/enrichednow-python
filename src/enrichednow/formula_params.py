"""The parameters of every formula this version of the library knows, one type each. Written from the API's parameter
schemas (`<Name>Params` in its OpenAPI document): do not edit by hand. A formula that is not here takes its
parameters as a plain map, as any formula does.

    from enrichednow import EnrichedNow
    from enrichednow.formula_params import JobOrderHunterParams

    params: JobOrderHunterParams = {"job_titles": ["Java Developer"], "locations": ["London"]}
    run = EnrichedNow().formulas.run("job-order-hunter", params)
"""
from __future__ import annotations

from typing import Any, Dict, List, Literal, Tuple, TypedDict, get_args

__all__ = [
    "FormulaId",
    "FORMULA_IDS",
    "IntRange",
    "AccountHiringCheckParams",
    "AccountResearchParams",
    "AcquisitionUniverseParams",
    "AdActivityTriggerParams",
    "AdCreativeResearchParams",
    "AgencyAdMiningParams",
    "AgencyListsParams",
    "AnnouncementTriggerParams",
    "AppIntelligenceParams",
    "AwardTeamingParams",
    "BrokenLinkProspectsParams",
    "BrokerDirectoryParams",
    "BusinessForSaleAlertsParams",
    "CandidateReverseMarketingParams",
    "ChampionTrackerParams",
    "CompanyDiligenceParams",
    "CompetitorPriceTrackerParams",
    "CompetitorReviewMiningParams",
    "CompoundSignalScoreParams",
    "ContractorLicenseWatchParams",
    "CrowdfundingLeadsParams",
    "DealSiteMonitorParams",
    "DirectoryToLeadsParams",
    "EcommercePanelParams",
    "EnterpriseAtsSweepParams",
    "EventOrganizerLeadsParams",
    "ExhibitorProspectsParams",
    "FootprintProspectsParams",
    "FreelanceGigFeedParams",
    "FundedAndHiringParams",
    "HiringSignalOutboundParams",
    "HiringVelocityParams",
    "HomeServicesProsParams",
    "HotelRateShopParams",
    "InfluencerDiscoveryParams",
    "JobOrderHunterParams",
    "JobSeekerTargetsParams",
    "KnowledgeBaseCrawlParams",
    "LandlordAgentLeadsParams",
    "LaunchBatchListsParams",
    "LinkIntersectParams",
    "ListingComplianceParams",
    "LiteratureSweepParams",
    "LocalBusinessLeadsParams",
    "LongOpenRolesParams",
    "LookalikeCompaniesParams",
    "MarketplaceFlipsParams",
    "MenuPriceTrackerParams",
    "OutOfStockOpportunityParams",
    "PeopleListWithOpenersParams",
    "PermitStatusWatchParams",
    "PermitTradeLeadsParams",
    "PriceSellerWatchParams",
    "PropertyCompsParams",
    "PropertyDistressSignalsParams",
    "RankTrackerParams",
    "ReverseSourcingParams",
    "ReviewMiningParams",
    "ReviewVelocityParams",
    "SalaryBenchmarkParams",
    "SecFilingMonitorParams",
    "SellerIdentityParams",
    "ShopifyNicheResearchParams",
    "SocialSentimentParams",
    "StaleListingsParams",
    "StorefrontResearchParams",
    "StrUnderwritingParams",
    "SupplierDiscoveryParams",
    "TalentSourcingParams",
    "TenderAlertsParams",
    "TenderChangeWatchParams",
    "UnlinkedMentionsParams",
    "UsedCarArbitrageParams",
    "VcDealSourcingParams",
    "WebRankTrackerParams",
    "WholesaleCatalogCheckParams",
]

FormulaId = Literal[
    "account-hiring-check",
    "account-research",
    "acquisition-universe",
    "ad-activity-trigger",
    "ad-creative-research",
    "agency-ad-mining",
    "agency-lists",
    "announcement-trigger",
    "app-intelligence",
    "award-teaming",
    "broken-link-prospects",
    "broker-directory",
    "business-for-sale-alerts",
    "candidate-reverse-marketing",
    "champion-tracker",
    "company-diligence",
    "competitor-price-tracker",
    "competitor-review-mining",
    "compound-signal-score",
    "contractor-license-watch",
    "crowdfunding-leads",
    "deal-site-monitor",
    "directory-to-leads",
    "ecommerce-panel",
    "enterprise-ats-sweep",
    "event-organizer-leads",
    "exhibitor-prospects",
    "footprint-prospects",
    "freelance-gig-feed",
    "funded-and-hiring",
    "hiring-signal-outbound",
    "hiring-velocity",
    "home-services-pros",
    "hotel-rate-shop",
    "influencer-discovery",
    "job-order-hunter",
    "job-seeker-targets",
    "knowledge-base-crawl",
    "landlord-agent-leads",
    "launch-batch-lists",
    "link-intersect",
    "listing-compliance",
    "literature-sweep",
    "local-business-leads",
    "long-open-roles",
    "lookalike-companies",
    "marketplace-flips",
    "menu-price-tracker",
    "out-of-stock-opportunity",
    "people-list-with-openers",
    "permit-status-watch",
    "permit-trade-leads",
    "price-seller-watch",
    "property-comps",
    "property-distress-signals",
    "rank-tracker",
    "reverse-sourcing",
    "review-mining",
    "review-velocity",
    "salary-benchmark",
    "sec-filing-monitor",
    "seller-identity",
    "shopify-niche-research",
    "social-sentiment",
    "stale-listings",
    "storefront-research",
    "str-underwriting",
    "supplier-discovery",
    "talent-sourcing",
    "tender-alerts",
    "tender-change-watch",
    "unlinked-mentions",
    "used-car-arbitrage",
    "vc-deal-sourcing",
    "web-rank-tracker",
    "wholesale-catalog-check",
]
"""The id of every formula this version of the library has a parameter type for."""
FORMULA_IDS: Tuple[str, ...] = get_args(FormulaId)


class IntRange(TypedDict):
    """A range of whole numbers, both ends included."""

    min: int
    max: int


class _AccountHiringCheckParamsRequired(TypedDict):
    accounts: List[str]
    """Accounts: Each account's website domain, as in your CRM (acme.com). Upload a CSV for many. 1 to 100 items.
    Required.
    """


class AccountHiringCheckParams(_AccountHiringCheckParamsRequired, total=False):
    """Account Hiring Check (`account-hiring-check`): Every account in your CRM flagged hiring or not, with its open
    roles, departments and the roles you care about.

    Only `accounts` is required; a key left out takes its default.
    """

    roles_of_interest: List[str]
    """Roles you care about: Openings whose title holds one of these as a whole word or phrase are counted apart, such
    as Data Engineer. At most 20 items. Default: [].
    """
    new_within_days: int
    """New within (days): An opening posted in the last this many days counts as new. From 1 to 180. Default: 30."""
    hiring_threshold: int
    """Hiring at this many openings: An account with at least this many openings is flagged hiring. At least 1.
    Default: 1.
    """
    verified_only: bool
    """Count only tracking-system openings: Counts only openings an applicant tracking system lists. What a careers
    page's own text shows is counted apart, as unconfirmed. Default: True.
    """
    max_results: int
    """Most rows: One row per account; the run stops at this many, most active first. From 1 to 5000. Default: 1000."""


class _AccountResearchParamsRequired(TypedDict):
    domains: List[str]
    """Company websites: Each company's domain or website address, typed or from a CSV. 1 to 500 items. Required."""


class AccountResearchParams(_AccountResearchParamsRequired, total=False):
    """Account Research (`account-research`): For each company domain, what its site and company page say, a line of
    research and a compliment built only from facts.

    Only `domains` is required; a key left out takes its default.
    """

    read_company_page: bool
    """Read their LinkedIn company page: When the site links to one; adds industry, size, headquarters and when it was
    founded. Default: True.
    """
    read_technologies: bool
    """Read the technologies of their site: The site's platform, analytics and tools, as its own pages reveal them.
    Default: True.
    """
    max_results: int
    """Most rows: The run stops at this many companies. From 1 to 500. Default: 500."""


class _AcquisitionUniverseParamsRequired(TypedDict):
    thesis: List[str]
    """Kinds of business: What you would buy, as you would search Google Maps for it, such as HVAC contractor or
    landscaping company. 1 to 5 items. Required.
    """
    metros: List[str]
    """Metros: A city or metro for each place, with its state. 1 to 10 items. Required."""


class AcquisitionUniverseParams(_AcquisitionUniverseParamsRequired, total=False):
    """Acquisition Universe (`acquisition-universe`): Every business of your acquisition thesis in your metros, off the
    market from Google Maps and on it from sale listings.

    Only `thesis`, `metros` are required; a key left out takes its default.
    """

    states: List[str]
    """States for listings: The US states, by name, whose businesses for sale are read. Empty reads none. At most 10
    items. Default: [].
    """
    listing_words: List[str]
    """Words a listing must hold: Whole words a for-sale listing's title or summary must hold, such as HVAC or air
    conditioning. Empty uses the kinds of business. At most 10 items. Default: [].
    """
    places_per_search: int
    """Places read per search: How many places Google Maps is read for, for each kind of business in each metro. From
    10 to 300. Default: 60.
    """
    min_reviews: int
    """Fewest reviews: Places with fewer reviews are left out; a business with none may be too small or not trading. At
    least 0. Default: 0.
    """
    max_reviews: int
    """Most reviews: Places with more reviews are left out; the largest are rarely owner-run. At least 0. Default:
    1000000.
    """
    exclude_chains: bool
    """Leave out chains: A name found five or more times in the results is taken for a chain and left out. Default:
    True.
    """
    include_vault: bool
    """Larger companies without their name: BusinessesForSale.com's M&A Vault describes larger companies without naming
    them, from any country. Default: False.
    """
    find_email: bool
    """Read each website for an address: The address each business's own website publishes, checked. Off saves one read
    a business. Default: True.
    """
    resurface_after_days: int
    """Show a business again after (days): For a saved formula, how long before a delivered business or listing may
    come back. From 1 to 365. Default: 180.
    """
    max_results: int
    """Most rows: The run stops at this many rows, listings first, then the places with the most reviews. From 1 to
    5000. Default: 300.
    """


class _AdActivityTriggerParamsRequired(TypedDict):
    keywords: List[str]
    """What the ads are about: Words the ads say, each searched in each library, such as "payroll software". 1 to 5
    items. Required.
    """


class AdActivityTriggerParams(_AdActivityTriggerParamsRequired, total=False):
    """Ad-Activity Trigger (`ad-activity-trigger`): Companies running ads about your topic on Meta and LinkedIn now,
    sized up, with their marketing lead to contact.

    Only `keywords` is required; a key left out takes its default.
    """

    countries: List[str]
    """Countries: Where the ads are shown, as two-letter codes such as US or GB. 1 to 5 items. Default: ["US"]."""
    platforms: List[Literal["meta", "linkedin"]]
    """Ad libraries: Meta covers Facebook and Instagram. Each one of "meta", "linkedin". At least 1 item. Default:
    ["meta", "linkedin"].
    """
    started_within_days: int
    """Ads started within (days): Meta says when each ad started; older ones are left out. LinkedIn's library does not
    say, and its ads are kept. From 1 to 365. Default: 90.
    """
    ads_per_search: int
    """Ads read per search: How many ads to read for each phrase, country and library. From 5 to 100. Default: 30."""
    min_ads: int
    """Least ads: Ads a company needs to be running to be listed. At least 1. Default: 1."""
    company_size: IntRange
    """Company size (employees): Companies whose size is not known are kept. Default: {"min": 2, "max": 10000}."""
    exclude_companies: List[str]
    """Companies to leave out: Names or domains, such as your existing customers. At most 5000 items. Default: []."""
    buyer_titles: List[str]
    """Who to contact: The roles a connected people provider looks for at each company. Default: ["Chief Marketing
    Officer", "VP Marketing", "Head of Marketing", "Marketing Director", "Head of Growth"].
    """
    contacts_per_company: int
    """Contacts per company: 0 keeps one row per company. From 0 to 5. Default: 2."""
    require_verified_email: bool
    """Only addresses that pass the check: Keeps addresses whose domain takes mail, and those a verification provider
    confirmed. Default: True.
    """
    max_results: int
    """Most rows: The run stops at this many rows, the most active advertisers first. From 1 to 2000. Default: 200."""


class _AdCreativeResearchParamsRequired(TypedDict):
    competitors: List[str]
    """Competitors: Each competitor's name as it advertises, such as Canva or HubSpot. Ads are kept where the
    advertiser's name holds it as a whole word. 1 to 10 items. Required.
    """


class AdCreativeResearchParams(_AdCreativeResearchParamsRequired, total=False):
    """Ad Creative Research (`ad-creative-research`): A competitor's ads on Meta, Google Ads and LinkedIn, with copy,
    landing page and how long each has run, longest first.

    Only `competitors` is required; a key left out takes its default.
    """

    domains: List[str]
    """Their websites: The competitors' websites, such as canva.com. Google Ads are found by the website they lead to,
    so Google Ads is searched only when you give one. At most 10 items. Default: [].
    """
    libraries: List[Literal["meta", "google", "linkedin"]]
    """Ad libraries: Meta covers Facebook, Instagram, Messenger and Threads; Google Ads covers Search, YouTube and the
    display network. Each one of "meta", "google", "linkedin". At least 1 item. Default: ["meta", "google",
    "linkedin"].
    """
    country: str
    """Country: Only ads shown in this country, as a two-letter code such as US or DE. Leave empty for every country.
    Default: "".
    """
    running_only: bool
    """Only ads running now: Leaves out ads that have stopped. Off, a stopped ad still shows how long an angle lasted.
    Default: False.
    """
    min_days_running: int
    """Least days running: Only ads that have run at least this many days; 30 keeps the angles an advertiser kept
    paying for. From 0 to 3650. Default: 0.
    """
    facebook_page_ids: List[str]
    """Facebook Page ids: For an exact Meta search, the competitor's Page id (the number after view_all_page_id= in the
    Ad Library's address). Every ad of the Page is read. At most 10 items. Default: [].
    """
    ads_per_search: int
    """Ads read per search: The most ads read for each competitor in each library. Each ad read is one unit. From 5 to
    120. Default: 30.
    """
    linkedin_ad_pages: bool
    """Read each LinkedIn ad's page: LinkedIn's search shows no dates or landing page; each ad's own page has them, for
    one unit an ad. Default: True.
    """
    max_results: int
    """Most rows: The run stops at this many ads, longest running first. From 1 to 2000. Default: 200."""


class _AgencyAdMiningParamsRequired(TypedDict):
    job_titles: List[str]
    """Job titles: The roles you work, each searched as you type it. 1 to 10 items. Required."""
    locations: List[str]
    """Locations: A city, region or country for each market you watch. 1 to 10 items. Required."""


class AgencyAdMiningParams(_AgencyAdMiningParamsRequired, total=False):
    """Agency Ad Mining (`agency-ad-mining`): Jobs competing agencies advertise, what they say about the client, and
    the employers posting the same job directly.

    Only `job_titles`, `locations` are required; a key left out takes its default.
    """

    posted_within_days: int
    """Posted within (days): Only postings from the last this many days. From 1 to 30. Default: 7."""
    agencies: List[str]
    """Only these agencies: Names of the competing agencies to watch. Leave empty for every agency. At most 50 items.
    Default: [].
    """
    sources: List[Literal["linkedin", "indeed", "reed", "totaljobs", "dice"]]
    """Job boards: Which boards to search. Reed and Dice say who placed a posting; Reed and Totaljobs cover the UK,
    Dice technology roles in the US. Each one of "linkedin", "indeed", "reed", "totaljobs", "dice". At least 1 item.
    Default: ["linkedin", "reed", "dice"].
    """
    results_per_search: int
    """Jobs read per search: How many postings to read for each title, place and board, agencies' and employers' alike.
    From 5 to 200. Default: 50.
    """
    postings_read: int
    """Agency postings read in full: The newest agency postings whose full text is read for what they say about the
    client. From 5 to 300. Default: 60.
    """
    client_phrases: List[str]
    """Words that describe the client: The first of these a posting uses is quoted with the sentence around it.
    Default: ["our client", "my client", "on behalf of", "client is", "client based in", "working with a", "a
    leading", "well-established"].
    """
    max_results: int
    """Most rows: The run stops at this many rows, best first. From 1 to 2000. Default: 100."""


class _AgencyListsParamsRequired(TypedDict):
    directories: List[str]
    """Clutch directories: Each as in its address on clutch.co, the service then the place: agencies/seo,
    web-developers/new-york, uk/agencies/digital-marketing/london, or the whole address. 1 to 10 items. Required.
    """


class AgencyListsParams(_AgencyListsParamsRequired, total=False):
    """Agency Lists (`agency-lists`): Agencies by service and place with size, age, rates, minimum project, services
    and reviews, for partnering or buying.

    Only `directories` is required; a key left out takes its default.
    """

    pages: int
    """Pages to read: Pages of each directory to read; a page lists about 50 to 80 agencies. From 1 to 10. Default: 2.
    """
    purpose: Literal["partner", "acquisition"]
    """What the list is for: Partner ranks agencies by rating, reviews and a published email. Acquisition ranks
    established agencies first: ten years or more in business, 10 to 249 staff, and a body of reviews. One of
    "partner", "acquisition". Default: "partner".
    """
    employees: IntRange
    """Head count: Agencies whose head count on Clutch falls outside this range are left out; an agency that does not
    say is kept. Default: {"min": 2, "max": 1000}.
    """
    founded_before: Dict[str, Any]
    """Founded in or before: Only agencies founded in this year or earlier, such as 2015 for ten years in business.
    Empty for any. From 1900 to 2100. Default: None.
    """
    max_hourly_rate: int
    """Highest hourly rate (USD): Agencies whose lowest hourly rate is above this are left out. 0 for any. From 0 to
    1000. Default: 0.
    """
    max_min_project: int
    """Largest minimum project (USD): Agencies that take no project smaller than this are left out. 0 for any. From 0
    to 10000000. Default: 0.
    """
    services: List[str]
    """Sells one of these services: Words from Clutch's service names, such as SEO, Pay Per Click or Web Development.
    Leave empty for any. At most 20 items. Default: [].
    """
    countries: List[str]
    """Office in these countries: Two-letter country codes (GB, US). A directory of a place also lists sponsors based
    elsewhere; this leaves them out. At most 50 items. Default: [].
    """
    min_rating: float
    """Lowest rating: Agencies rated below this on Clutch are left out. From 0 to 5. Default: 0."""
    min_reviews: int
    """Fewest reviews: Agencies with fewer Clutch reviews are left out. At least 0. Default: 0."""
    require_email: bool
    """Only agencies with an email: Keeps the agencies whose own website publishes an email address that passes the
    check. Default: False.
    """
    exclude_companies: List[str]
    """Agencies to leave out: Names or domains, such as agencies you already work with. At most 5000 items. Default:
    [].
    """
    max_results: int
    """Most rows: The run stops at this many agencies, best first. Each agency's profile and website are read, so this
    sets the cost. From 1 to 2000. Default: 100.
    """


class _AnnouncementTriggerParamsRequired(TypedDict):
    event_types: List[Literal["funding", "expansion", "product_launch", "executive_hire", "acquisition"]]
    """Kinds of news: Which announcements to look for. Each one of "funding", "expansion", "product_launch",
    "executive_hire", "acquisition". At least 1 item. Required.
    """


class AnnouncementTriggerParams(_AnnouncementTriggerParamsRequired, total=False):
    """Funding and Announcement Trigger (`announcement-trigger`): Companies that just announced funding, an expansion,
    a launch or a senior hire, with who to contact and the fact.

    Only `event_types` is required; a key left out takes its default.
    """

    keywords: List[str]
    """Words in the news: Only releases that hold one of these words, such as fintech or healthcare. Leave empty for
    any. At most 5 items. Default: [].
    """
    published_within_days: int
    """Published within (days): Only releases from the last this many days. From 1 to 30. Default: 3."""
    sources: List[Literal["prnewswire", "globenewswire", "google_news"]]
    """News sources: The press-release wires, and Google News for stories as well as releases. Each one of
    "prnewswire", "globenewswire", "google_news". At least 1 item. Default: ["prnewswire", "globenewswire"].
    """
    releases_to_read: int
    """Releases read in full: How many of the newest matching releases are opened to read who, how much and who
    invested. From 5 to 200. Default: 60.
    """
    regions: List[str]
    """Places: Countries, states or cities the company or the release is from. Leave empty for anywhere. Default: []."""
    company_size: IntRange
    """Company size (employees): Companies whose size is not known are kept. Default: {"min": 1, "max": 10000}."""
    industries_include: List[str]
    """Only these industries: Leave empty for any. Default: []."""
    exclude_companies: List[str]
    """Companies to leave out: Names or domains, such as customers. At most 5000 items. Default: []."""
    buyer_titles: List[str]
    """Who to contact: The roles of the people to find at each company. Default: ["Chief Executive Officer", "Founder",
    "VP Sales"].
    """
    contact_new_executive: bool
    """Contact the new executive: For a senior hire, look for the person in the new role rather than the roles above.
    Default: False.
    """
    contacts_per_company: int
    """Contacts per company: 0 turns contacts off. From 0 to 5. Default: 1."""
    require_verified_email: bool
    """Only addresses that pass the check: Keeps addresses whose domain takes mail, and those a verification provider
    confirmed. Default: True.
    """
    max_results: int
    """Most rows: The run stops at this many rows, newest first. From 1 to 1000. Default: 100."""


class _AppIntelligenceParamsRequired(TypedDict):
    apps: List[str]
    """Apps: App Store apps by their number (the digits after id in the app's address) or their App Store link; Google
    Play apps by their package name, such as com.spotify.music. 1 to 100 items. Required.
    """


class AppIntelligenceParams(_AppIntelligenceParamsRequired, total=False):
    """App Intelligence (`app-intelligence`): Ratings, versions, release notes and chart ranks of apps on the App Store
    and Google Play, with what changed since last run.

    Only `apps` is required; a key left out takes its default.
    """

    search_terms: List[str]
    """Search words: Also the apps that rank in the stores' search for these words, such as habit tracker. At most 10
    items. Default: [].
    """
    chart_category: Literal["none", "all", "books", "business", "education", "entertainment", "finance", "food_and_drink", "games", "health_and_fitness", "lifestyle", "medical", "music", "navigation", "news", "photo_and_video", "productivity", "shopping", "social_networking", "sports", "travel", "utilities", "weather"]
    """Top chart: Also the top apps of this category's chart, with their rank. An app you named gets its rank when it
    is on the chart. One of "none", "all", "books", "business", "education", "entertainment", "finance",
    "food_and_drink", "games", "health_and_fitness", "lifestyle", "medical", "music", "navigation", "news",
    "photo_and_video", "productivity", "shopping", "social_networking", "sports", "travel", "utilities", "weather".
    Default: "none".
    """
    stores: List[Literal["app_store", "google_play"]]
    """Stores: The stores searched and charted. Apps you name are read in their own store. Each one of "app_store",
    "google_play". At least 1 item. Default: ["app_store", "google_play"].
    """
    chart: Literal["free", "paid", "grossing"]
    """Chart: Top free, top paid or top grossing. One of "free", "paid", "grossing". Default: "free"."""
    chart_size: int
    """Chart places read: How many of the chart's top apps are read in each store. From 5 to 100. Default: 25."""
    apps_per_search: int
    """Apps read per search: How many of the top results of each search word are read in each store. From 1 to 50.
    Default: 10.
    """
    country: str
    """Store country: The country's store, as a two-letter code such as us, gb or de. Ratings and charts differ by
    country. Default: "us".
    """
    min_rating: float
    """Lowest rating: Leaves out apps rated below this. Apps you name are always kept. From 0 to 5. Default: 0."""
    recent_reviews: int
    """Recent reviews read per app: Reads this many of each app's newest reviews for its recent rating and the share of
    one- and two-star reviews. Each review read is one unit; 0 turns it off. From 0 to 100. Default: 0.
    """
    max_results: int
    """Most rows: The run stops at this many apps, those with the biggest changes first. From 1 to 1000. Default: 200.
    """



class AwardTeamingParams(TypedDict, total=False):
    """Award Teaming Leads (`award-teaming`): Companies that just won government contracts in your field, with what
    they won, their website and the email they publish.

    Every key is optional; a key left out takes its default.
    """

    naics_codes: List[str]
    """NAICS codes: The industry codes of the work, 2 to 6 digits, such as 541512 (computer systems design). Each is
    searched on its own. At most 10 items. Default: [].
    """
    keywords: List[str]
    """Words: Words in the award's description, such as cybersecurity or janitorial. Each is searched on its own. At
    most 10 items. Default: [].
    """
    agencies: List[str]
    """Awarding departments: US departments by their full name, such as Department of Defense or Department of Veterans
    Affairs. At most 5 items. Default: [].
    """
    awarded_within_days: int
    """Awarded within (days): Awards whose work started, or whose notice was published, in the last this many days.
    Recently signed work that starts later is kept. From 7 to 364. Default: 30.
    """
    sources: List[Literal["usaspending", "sam_gov", "ted"]]
    """Where awards are read: USAspending.gov (US federal contracts), SAM.gov award notices where offered, and TED (EU
    contract awards). Each one of "usaspending", "sam_gov", "ted". At least 1 item. Default: ["usaspending",
    "sam_gov"].
    """
    us_states: List[str]
    """Places of performance: Only US awards for work done in these states, as two letters, such as VA or TX. At most
    10 items. Default: [].
    """
    countries: List[str]
    """Buyers' countries (TED): Only EU awards made by buyers in these countries, as three letters, such as DEU or FRA.
    At most 10 items. Default: [].
    """
    min_award_amount: float
    """Smallest award: Awards below this amount, in the award's currency, are left out. An award that states no amount
    is kept. At least 0. Default: 100000.
    """
    winner_size: Literal["any", "small_business", "other_than_small"]
    """Winner's size: Small businesses or large primes, as USAspending records them. A winner it has no record of is
    kept only for any. One of "any", "small_business", "other_than_small". Default: "any".
    """
    exclude_companies: List[str]
    """Companies to leave out: Names, such as your competitors or the partners you already have. At most 1000 items.
    Default: [].
    """
    require_email: bool
    """Only companies with an email: Keeps the companies whose own website publishes an email address that passes the
    check. Default: True.
    """
    pages_per_search: int
    """Pages read per search: Each page is the next 100 awards, newest first. Raise it for a busy code or a long
    window. From 1 to 5. Default: 2.
    """
    max_results: int
    """Most rows: The run stops at this many companies, the biggest winners first. From 1 to 1000. Default: 100."""


class _BrokenLinkProspectsParamsRequired(TypedDict):
    topic: str
    """Topic: The subject of the resource pages, as people search for it, such as genealogy or home schooling.
    Required.
    """


class BrokenLinkProspectsParams(_BrokenLinkProspectsParamsRequired, total=False):
    """Broken Link Prospects (`broken-link-prospects`): Resource pages on your topic that link to pages or sites that
    are gone, each with the dead link and the site's email.

    Only `topic` is required; a key left out takes its default.
    """

    footprints: List[str]
    """Footprints: Words searched beside the topic to find resource pages, each its own search. Quote a phrase to find
    it exactly. 1 to 12 items. Default: ["\"useful links\"", "\"helpful resources\"", "\"recommended resources\"",
    "\"helpful links\"", "\"resource list\"", "resources"].
    """
    pages_to_read: int
    """Resource pages to check: How many resource pages are read and have their links checked, one page per site, best
    placed first. From 1 to 30. Default: 10.
    """
    links_per_page: int
    """Links looked at per page: The first this many links of each page are looked at, and those to other sites are
    checked, one unit each. From 10 to 100. Default: 80.
    """
    search_pages: int
    """Results pages per search: How many pages of results to read for each footprint, about ten results a page. From 1
    to 3. Default: 1.
    """
    exclude_domains: List[str]
    """Sites to leave out: Domains whose pages are not read and whose links are not checked, such as social networks
    and share buttons. At most 2000 items. Default: a list of 22 values, which `get` on the formula shows.
    """
    country: str
    """Search country: The two-letter country whose search results are read, such as us, gb or de. Default: "us"."""
    language: str
    """Search language: The language of the results, such as en or de. Default: "en"."""
    require_email: bool
    """Only sites with an email: Keeps the pages whose site publishes an email address that passes the check. Default:
    False.
    """
    resurface_after_days: int
    """Show a broken link again after (days): For a saved formula, how long before a delivered broken link may come
    back. From 1 to 365. Default: 90.
    """
    max_results: int
    """Most rows: The run stops at this many broken links, gone sites first. From 1 to 2000. Default: 200."""


class _BrokerDirectoryParamsRequired(TypedDict):
    states: List[str]
    """States: US states or Canadian provinces, by name or two-letter code. Listings are read for US states only. 1 to
    10 items. Required.
    """


class BrokerDirectoryParams(_BrokerDirectoryParamsRequired, total=False):
    """Broker Directory (`broker-directory`): The business brokers of your states, one row for each firm, with
    specialties, designations and their current listings.

    Only `states` is required; a key left out takes its default.
    """

    specialties: List[Literal["accommodations", "agriculture", "arts", "auto-related-business", "business-services", "construction", "ecommerce", "education-services", "entertainment-recreation", "finance-insurance", "food-beverage", "health-care-social-assistance", "industrial-services", "information", "logistics", "manufacturing", "print-and-media", "public-administration", "real-estate-rental-leasing", "retail-trade", "technical-services", "transportation", "waste-management", "wholesale-trade"]]
    """Specialties: IBBA brokers who list one of these industries. Empty keeps every broker. Each one of
    "accommodations", "agriculture", "arts", "auto-related-business", "business-services", "construction",
    "ecommerce", "education-services", "entertainment-recreation", "finance-insurance", "food-beverage",
    "health-care-social-assistance", "industrial-services", "information", "logistics", "manufacturing",
    "print-and-media", "public-administration", "real-estate-rental-leasing", "retail-trade", "technical-services",
    "transportation", "waste-management", "wholesale-trade". Default: [].
    """
    certification: Literal["any", "cbi", "mami", "master_cbi", "cbi_or_mami"]
    """Designation: IBBA brokers holding this designation, such as CBI (Certified Business Intermediary) or M&AMI. One
    of "any", "cbi", "mami", "master_cbi", "cbi_or_mami". Default: "any".
    """
    include_listings: bool
    """Add the firms selling businesses now: Reads the state's businesses for sale on BusinessesForSale.com, and each
    brokered one's page for its firm. Default: True.
    """
    listing_pages: int
    """Listing pages read a state: BusinessesForSale.com's pages of 25, newest first. From 1 to 4. Default: 2."""
    min_listings: int
    """Fewest listings now: Keep firms with at least this many of the listings read. 0 keeps every broker. At least 0.
    Default: 0.
    """
    firms_only: bool
    """Only brokers who name a firm: Leaves out IBBA members whose profile names no firm. Default: False."""
    find_email: bool
    """Read each website for an address: The address each firm's own website publishes, checked. Off saves one read a
    firm. Default: True.
    """
    resurface_after_days: int
    """Show a firm again after (days): For a saved formula, how long before a delivered firm may come back. From 1 to
    365. Default: 180.
    """
    max_results: int
    """Most rows: The run stops at this many firms, those with the most listings and brokers first. From 1 to 2000.
    Default: 200.
    """


class _BusinessForSaleAlertsParamsRequired(TypedDict):
    states: List[str]
    """States: US states, by name, such as Texas or North Carolina. 1 to 10 items. Required."""


class BusinessForSaleAlertsParams(_BusinessForSaleAlertsParamsRequired, total=False):
    """Business-for-Sale Alerts (`business-for-sale-alerts`): Businesses newly listed for sale in your states and
    sectors, with asking price, revenue, cash flow, sector and broker.

    Only `states` is required; a key left out takes its default.
    """

    keywords: List[str]
    """Kinds of business: Words a listing's title or summary must hold as whole words, such as laundromat or HVAC.
    Empty keeps every kind. At most 10 items. Default: [].
    """
    min_cash_flow: int
    """Least cash flow ($): The yearly cash flow or net profit a listing must state. 0 keeps every listing. At least 0.
    Default: 0.
    """
    max_asking_price: int
    """Highest asking price ($): Listings asking more are left out. 0 sets no limit. At least 0. Default: 0."""
    min_asking_price: int
    """Lowest asking price ($): Listings asking less are left out. At least 0. Default: 0."""
    min_revenue: int
    """Least revenue ($): The yearly revenue a listing must state. 0 keeps every listing. At least 0. Default: 0."""
    keep_undisclosed: bool
    """Keep listings that withhold a figure: A listing whose cash flow, revenue or price is on request is kept rather
    than judged by a number it does not give. Default: True.
    """
    seller: Literal["any", "broker", "owner"]
    """Sold by: Every listing, only those a broker sells, or only those the owner sells. One of "any", "broker",
    "owner". Default: "any".
    """
    sources: List[Literal["businessesforsale", "businessbroker"]]
    """Marketplaces: BusinessesForSale.com and BusinessBroker.net. Each one of "businessesforsale", "businessbroker".
    At least 1 item. Default: ["businessesforsale", "businessbroker"].
    """
    pages: int
    """Pages read a state: BusinessesForSale.com's pages of 25, newest first; BusinessBroker.net's first page of about
    30 is read either way. From 1 to 4. Default: 2.
    """
    include_vault: bool
    """Larger companies without their name: BusinessesForSale.com's M&A Vault describes larger companies without naming
    them, from any country, among a state's listings. Default: False.
    """
    read_listings: bool
    """Read each listing's page: For the sector, employees, year founded, premises, reason for selling and the broker.
    Off saves one read a listing. Default: True.
    """
    resurface_after_days: int
    """Show a listing again after (days): For a saved formula, how long before a delivered listing may come back. From
    1 to 365. Default: 365.
    """
    max_results: int
    """Most rows: The run stops at this many listings, highest cash flow first. From 1 to 1000. Default: 100."""


class _CandidateReverseMarketingParamsRequired(TypedDict):
    candidate_titles: List[str]
    """Roles the candidate fits: The job titles your candidate would be hired as, each searched as you type it. 1 to 5
    items. Required.
    """
    skills: List[str]
    """The candidate's skills: Tools, methods or certificates the candidate has. A posting is kept when it asks for
    enough of them. 1 to 15 items. Required.
    """
    locations: List[str]
    """Where they will work: A city, region or country for each place the candidate would work. 1 to 5 items. Required.
    """


class CandidateReverseMarketingParams(_CandidateReverseMarketingParamsRequired, total=False):
    """Candidate Reverse Marketing (`candidate-reverse-marketing`): Companies hiring for what your best candidate does,
    with the skills they ask for, who decides, and an opening line.

    Only `candidate_titles`, `skills`, `locations` are required; a key left out takes its default.
    """

    posted_within_days: int
    """Posted within (days): Only postings from the last this many days; a fresh posting is still unfilled. From 1 to
    30. Default: 7.
    """
    sources: List[Literal["linkedin", "indeed", "reed", "totaljobs", "dice"]]
    """Job boards: Which boards to search. Reed and Totaljobs cover the UK; Dice is technology roles in the US. Each
    one of "linkedin", "indeed", "reed", "totaljobs", "dice". At least 1 item. Default: ["linkedin", "indeed"].
    """
    results_per_search: int
    """Jobs read per search: How many postings to read for each role, place and board. From 5 to 100. Default: 25."""
    min_skills_matched: int
    """Least skills a posting must ask for: Of the candidate's skills, how many a posting has to name to be kept. From
    1 to 10. Default: 2.
    """
    postings_read: int
    """Postings read in full: The newest postings whose full text is read to match skills; each costs a unit when the
    board gave only a summary. From 10 to 300. Default: 80.
    """
    company_size: IntRange
    """Company size (employees): Companies whose size is not known are kept. Default: {"min": 11, "max": 10000}."""
    exclude_companies: List[str]
    """Companies to leave out: Names or domains, such as the candidate's current employer or companies they already
    applied to. At most 5000 items. Default: [].
    """
    title_exclude_keywords: List[str]
    """Words to leave out of titles: For example junior or intern. Default: []."""
    contact_titles: List[str]
    """Who to contact: Leave empty to look for whoever decides on that kind of hire, such as the VP Engineering for a
    developer. Default: [].
    """
    contacts_per_company: int
    """Contacts per company: 0 turns contacts off. From 0 to 5. Default: 1."""
    require_verified_email: bool
    """Only addresses that pass the check: Keeps addresses whose domain takes mail, and those a verification provider
    confirmed. Default: True.
    """
    max_results: int
    """Most rows: The run stops at this many rows, best first. From 1 to 1000. Default: 50."""


class _ChampionTrackerParamsRequired(TypedDict):
    accounts: List[str]
    """Accounts: The website domains of the accounts where your champions work or worked, such as your customers. 1 to
    100 items. Required.
    """
    champion_titles: List[str]
    """Champion roles: The roles your champions held, such as VP Sales. 1 to 10 items. Required."""


class ChampionTrackerParams(_ChampionTrackerParamsRequired, total=False):
    """Champion Tracker (`champion-tracker`): People who held your champions' roles at your accounts and moved on,
    found at their new company, with contact details.

    Only `accounts`, `champion_titles` are required; a key left out takes its default.
    """

    track: Literal["moved", "successor"]
    """Who to find: moved: people who held these roles at the account and left, where they are now. successor: who
    holds them at the account today. One of "moved", "successor". Default: "moved".
    """
    min_employees: int
    """Least employees at the new company: Only follow people to companies at least this big. 1 follows everyone. At
    least 1. Default: 1.
    """
    exclude_companies: List[str]
    """New companies to leave out: Domains of companies not to follow people to, such as competitors or customers
    already won. At most 5000 items. Default: [].
    """
    people_per_account: int
    """People per account: The most people to find for each account. From 1 to 10. Default: 3."""
    require_verified_email: bool
    """Only addresses that pass the check: Keeps addresses whose domain takes mail, and those a verification provider
    confirmed. Default: True.
    """
    resurface_after_days: int
    """Show a person again after (days): For a saved formula, how long before a person already delivered may come back.
    From 1 to 365. Default: 180.
    """
    max_results: int
    """Most rows: The run stops at this many people, best first. From 1 to 2000. Default: 200."""


class _CompanyDiligenceParamsRequired(TypedDict):
    companies: List[str]
    """Companies: Each company by its name, its register number (a UK company number such as 09446231, a Swedish
    organisation number such as 556703-7485) or its website's domain. A name is searched as written, in the news
    too, so give the name the company is known by (Thames Water, not Thames Water Utilities Limited); a domain also
    lets its reviews and website be read. 1 to 200 items. Required.
    """


class CompanyDiligenceParams(_CompanyDiligenceParamsRequired, total=False):
    """Company Diligence (`company-diligence`): Each company you name checked on its register, in adverse news, reviews
    and complaints, and its website, with red flags.

    Only `companies` is required; a key left out takes its default.
    """

    country: Literal["GB", "US", "CA", "SE", "IE", "AU", "other"]
    """Country: Where the companies are registered. The UK and Sweden have their register read; the US and Canada have
    the Better Business Bureau read. The news, reviews and website checks run everywhere. One of "GB", "US", "CA",
    "SE", "IE", "AU", "other". Default: "GB".
    """
    location: str
    """Place, for the Better Business Bureau: The city or state the companies trade in (Austin, TX). Only used in the
    US and Canada, to find the right business. Default: "".
    """
    checks: List[Literal["register", "news", "press_releases", "reviews", "website"]]
    """Checks: Which checks to run. Each costs about one unit a company; finding a company's website from its name
    costs a few more. Each one of "register", "news", "press_releases", "reviews", "website". At least 1 item.
    Default: ["register", "news", "press_releases", "reviews", "website"].
    """
    adverse_words: List[str]
    """Adverse words: The news is searched for the company together with these words, and a headline that holds one is
    counted as adverse. 1 to 30 items. Default: a list of 18 values, which `get` on the formula shows.
    """
    focus: Literal["counterparty", "acquisition"]
    """What the check is for: Counterparty weighs the register and adverse news most. Acquisition also weighs customer
    reviews and complaints, which say most about a small business a buyer is about to take on. One of
    "counterparty", "acquisition". Default: "counterparty".
    """
    window_days: int
    """News within (days): How far back the news and the press releases are read. From 30 to 1825. Default: 365."""
    max_results: int
    """Most rows: The run stops at this many companies, riskiest first. From 1 to 2000. Default: 200."""


class _CompetitorPriceTrackerParamsRequired(TypedDict):
    stores: List[str]
    """Competitor stores: Shopify stores by domain, such as allbirds.com. Each store's whole catalogue is read. At most
    20 items. Required.
    """


class CompetitorPriceTrackerParams(_CompetitorPriceTrackerParamsRequired, total=False):
    """Competitor Price Tracker (`competitor-price-tracker`): Every product and price of competitors' Shopify stores
    and Amazon listings, read on a schedule, with what changed since last time.

    Only `stores` is required; a key left out takes its default.
    """

    asins: List[str]
    """Amazon listings: Competitors' Amazon products by ASIN, read one by one. At most 100 items. Default: []."""
    keywords: List[str]
    """Only products about: Keep products whose title or type holds one of these. Empty keeps every product. At most 20
    items. Default: [].
    """
    collection: str
    """Store collection: Read only this collection of each store, by its handle (the name in /collections/<handle>).
    Empty reads the whole catalogue. Default: "".
    """
    products_per_store: int
    """Products read per store: A store's catalogue is read 250 products at a time; this many are read. From 10 to 250.
    Default: 250.
    """
    amazon_marketplace: Literal["us", "uk", "de", "fr", "it", "es", "ca"]
    """Amazon marketplace: Which Amazon the listings are on. One of "us", "uk", "de", "fr", "it", "es", "ca". Default:
    "us".
    """
    only_changes: bool
    """Only what changed: Show only products that are new or whose price, compare-at price or stock changed since the
    last run. Default: False.
    """
    max_results: int
    """Most rows: The run stops at this many products, changes first. From 1 to 5000. Default: 1000."""


class _CompetitorReviewMiningParamsRequired(TypedDict):
    competitors: List[str]
    """Competitors: Each competitor's website domain, as Trustpilot lists it, such as gusto.com. 1 to 20 items.
    Required.
    """


class CompetitorReviewMiningParams(_CompetitorReviewMiningParamsRequired, total=False):
    """Competitor Review Mining (`competitor-review-mining`): Your competitors' newest one- and two-star reviews, each
    with what went wrong, to sell against and to win their customers.

    Only `competitors` is required; a key left out takes its default.
    """

    stars: List[int]
    """Stars: Which reviews to read, by their stars. At least 1 item. Default: [1, 2]."""
    phrases: List[str]
    """Phrases to look for: Words you can answer, such as "customer service" or "hidden fees"; each match is quoted. At
    most 30 items. Default: [].
    """
    published_within_days: int
    """Written within (days): Only reviews written in the last this many days. From 1 to 730. Default: 180."""
    pages_per_competitor: int
    """Pages per competitor: Twenty reviews a page, newest first. From 1 to 3. Default: 2."""
    only_matching: bool
    """Only reviews with a phrase: Keeps only the reviews that contain one of your phrases. Default: False."""
    resurface_after_days: int
    """Show a review again after (days): For a saved formula, a review once delivered is not delivered again before
    this. From 1 to 365. Default: 365.
    """
    max_results: int
    """Most rows: The run stops at this many reviews, the best matches first. From 1 to 2000. Default: 200."""


class _CompoundSignalScoreParamsRequired(TypedDict):
    accounts: List[str]
    """Accounts: The companies to score, by name, by domain, or both as Rippling (rippling.com); a domain given needs
    no search to match. 1 to 50 items. Required.
    """


class CompoundSignalScoreParams(_CompoundSignalScoreParamsRequired, total=False):
    """Compound Signal Score (`compound-signal-score`): Your target accounts scored by what they are doing now: hiring,
    raising, new leaders, expanding and advertising.

    Only `accounts` is required; a key left out takes its default.
    """

    window_days: int
    """Look back (days): How recent news, postings and ads must be to count. From 7 to 180. Default: 30."""
    signals: List[Literal["hiring", "announcements", "ads"]]
    """Signals to read: What to read for each account. Each costs units for every account. Each one of "hiring",
    "announcements", "ads". At least 1 item. Default: ["hiring", "announcements", "ads"].
    """
    weight_hiring: int
    """Weight of hiring: Points for open roles on its careers page, in full at ten roles or more. From 0 to 100.
    Default: 30.
    """
    weight_funding: int
    """Weight of funding: Points for a funding announcement in the window. From 0 to 100. Default: 25."""
    weight_executive: int
    """Weight of a senior hire: Points for an announced executive hire in the window. From 0 to 100. Default: 15."""
    weight_expansion: int
    """Weight of an expansion: Points for an announced expansion or new office in the window. From 0 to 100. Default:
    10.
    """
    weight_launch: int
    """Weight of a launch: Points for an announced product launch in the window. From 0 to 100. Default: 5."""
    weight_ads: int
    """Weight of advertising: Points for ads shown in the window. From 0 to 100. Default: 15."""
    max_open_roles: int
    """Most open roles: Leave out accounts with more open roles than this, to find those that will hire before they
    post. At least 0. Default: 100000.
    """
    ads_read: int
    """Ads read per account: How many of an account's newest ads are read; each costs a unit. From 1 to 40. Default:
    10.
    """
    min_score: float
    """Least score: Accounts scoring below this are left out. At least 0. Default: 0."""
    max_results: int
    """Most rows: The run stops at this many accounts, best first. From 1 to 50. Default: 50."""


class _ContractorLicenseWatchParamsRequired(TypedDict):
    register: Literal["washington", "texas", "oregon", "chicago", "buffalo", "new_york_mold", "new_york_elevator"]
    """Register: Washington L&I, Texas TDLR, Oregon CCB (with bond and insurance dates), Chicago home repair, Buffalo,
    or New York's mold and elevator contractors. One of "washington", "texas", "oregon", "chicago", "buffalo",
    "new_york_mold", "new_york_elevator". Required.
    """


class ContractorLicenseWatchParams(_ContractorLicenseWatchParamsRequired, total=False):
    """Contractor Licence Watch (`contractor-license-watch`): Contractor businesses whose licence, bond or insurance
    expires in the next weeks, from official state and city registers.

    Only `register` is required; a key left out takes its default.
    """

    expiring_within_days: int
    """Expiring within (days): Licences that run out between today and this many days from now. From 1 to 180. Default:
    30.
    """
    trades: List[str]
    """Trades: Words in the licence's type or trade, such as electrical, plumbing or roofing. Each is one search. Empty
    reads every trade. At most 8 items. Default: [].
    """
    active_only: bool
    """Only licences in good standing: Leave out licences the register shows as suspended, revoked, cancelled or
    expired. Default: True.
    """
    licences_to_read: int
    """Licences read per search: The register is read up to this many licences for each trade word. From 10 to 200.
    Default: 200.
    """
    resurface_after_days: int
    """Show a licence again after (days): For a saved formula, how long before the same licence and expiry date may
    come back. From 1 to 365. Default: 300.
    """
    max_results: int
    """Most rows: The run stops at this many licences, soonest expiry first. From 1 to 2000. Default: 500."""


class _CrowdfundingLeadsParamsRequired(TypedDict):
    keywords: List[str]
    """Keywords: What the projects make or are about, each searched on each platform, such as e-bike or tabletop game.
    1 to 10 items. Required.
    """


class CrowdfundingLeadsParams(_CrowdfundingLeadsParamsRequired, total=False):
    """Crowdfunding Leads (`crowdfunding-leads`): Kickstarter and Indiegogo projects with traction, each with funding,
    backers, the creator's website and the email it publishes.

    Only `keywords` is required; a key left out takes its default.
    """

    stage: Literal["live", "funded", "any"]
    """Campaign stage: Live campaigns, campaigns that ended funded (the ones that now have to make and ship), or both.
    One of "live", "funded", "any". Default: "live".
    """
    platforms: List[Literal["kickstarter", "indiegogo"]]
    """Platforms: Where to search. Each one of "kickstarter", "indiegogo". At least 1 item. Default: ["kickstarter",
    "indiegogo"].
    """
    min_backers: int
    """Fewest backers: Projects with fewer backers are left out. At least 0. Default: 10."""
    min_percent_funded: int
    """Least funded (% of goal): 100 keeps the projects that reached their goal. A project that states no goal is kept.
    From 0 to 100000. Default: 0.
    """
    ended_within_days: int
    """Ended within (days): For funded projects, how recently the campaign ended. Live campaigns always pass. From 1 to
    3650. Default: 120.
    """
    categories: List[str]
    """Only these categories: The platform's categories or tags, or part of them, such as 3D Printing, Product Design
    or Home. Leave empty for any. At most 30 items. Default: [].
    """
    countries: List[str]
    """Only these countries (Kickstarter): Two-letter codes such as US or GB. Kickstarter states a project's country;
    Indiegogo does not, so its projects are kept. At most 50 items. Default: [].
    """
    pages: int
    """Pages read per keyword: Each page holds about 12 Kickstarter or 24 Indiegogo projects. From 1 to 5. Default: 2.
    """
    require_email: bool
    """Only creators with an email: Keeps the projects whose creator's own website publishes an email address that
    passes the check. Default: True.
    """
    max_results: int
    """Most projects: How many projects, best backed first, are matched to a website; with Only creators with an email,
    fewer rows may remain. From 1 to 500. Default: 100.
    """


class _DealSiteMonitorParamsRequired(TypedDict):
    queries: List[str]
    """Words to watch: Products, brands or stores, such as lego, airpods or costco. Each is one search, newest deals
    first. 1 to 10 items. Required.
    """


class DealSiteMonitorParams(_DealSiteMonitorParamsRequired, total=False):
    """Deal-Site Monitor (`deal-site-monitor`): New Slickdeals posts for your words, matched to Amazon, with the deal's
    price against Amazon's and the resale margin.

    Only `queries` is required; a key left out takes its default.
    """

    stores: List[str]
    """Only deals at: Store names as Slickdeals shows them, such as Walmart or Target. Empty keeps every store. At most
    30 items. Default: [].
    """
    min_score: int
    """Least deal score: The community's votes on the deal. From -50 to 1000. Default: 0."""
    compare_on_amazon: bool
    """Compare with Amazon: Read each deal's page and find the product on Amazon. Two reads a deal. Default: True."""
    referral_fee_pct: float
    """Amazon referral fee (%). From 0 to 50. Default: 15."""
    fulfilment_cost: float
    """Fulfilment and shipping a unit (USD). From 0 to 100. Default: 5."""
    resurface_after_days: int
    """Show a deal again after (days). From 1 to 365. Default: 365."""
    max_results: int
    """Most rows: The run stops at this many deals, newest first. Each is two reads when compared with Amazon. From 1
    to 500. Default: 40.
    """


class _DirectoryToLeadsParamsRequired(TypedDict):
    directory: Literal["bbb", "gelbeseiten", "checkatrade", "clutch", "web_page"]
    """Directory: Which directory to read; a web page is any directory page of your own, such as a chamber of
    commerce's members. One of "bbb", "gelbeseiten", "checkatrade", "clutch", "web_page". Required.
    """
    what: str
    """Kind of business: As the directory names it: plumber on BBB or Checkatrade, Zahnarzt on Gelbe Seiten, a Clutch
    directory with its place such as web-developers/london, or the address of the directory page. Required.
    """


class DirectoryToLeadsParams(_DirectoryToLeadsParamsRequired, total=False):
    """Directory to Leads (`directory-to-leads`): The businesses a directory lists, each with its website and the email
    that site publishes, checked.

    Only `directory`, `what` are required; a key left out takes its default.
    """

    where: str
    """Place: A town, city or postcode. Not needed for Clutch, whose place is in its directory, or for a web page.
    Default: "".
    """
    pages: int
    """Pages to read: How many pages of the directory to read; for a web page, how many of its pages to follow. From 1
    to 10. Default: 3.
    """
    require_email: bool
    """Only businesses with an email: Keeps the businesses whose own website publishes an email address that passes the
    check. Default: True.
    """
    exclude_role_addresses: bool
    """Only named addresses: Leaves out shared inboxes such as info@. Default: False."""
    min_reviews: int
    """Fewest reviews: Businesses with fewer reviews on the directory are left out. At least 0. Default: 0."""
    exclude_companies: List[str]
    """Businesses to leave out: Names or domains, such as your existing customers. At most 5000 items. Default: []."""
    resurface_after_days: int
    """Show a business again after (days): For a saved formula, how long before a delivered business may come back.
    From 1 to 365. Default: 180.
    """
    max_results: int
    """Most rows: The run stops at this many businesses. From 1 to 5000. Default: 200."""


class _EcommercePanelParamsRequired(TypedDict):
    queries: List[str]
    """Brands or products: Each is searched on every retailer you choose, as you type it, such as a brand or a brand
    and a product line. 1 to 20 items. Required.
    """


class EcommercePanelParams(_EcommercePanelParamsRequired, total=False):
    """E-commerce Panel (`ecommerce-panel`): A brand's listings on Amazon, Walmart and Target, with price, stock,
    rating and ratings count, and what changed since the last run.

    Only `queries` is required; a key left out takes its default.
    """

    brands: List[str]
    """Only these brands: Keeps the listings whose brand or title names one of these, so that other brands a search
    shows are left out. Leave empty to keep every listing. At most 20 items. Default: [].
    """
    retailers: List[Literal["amazon", "walmart", "target"]]
    """Retailers: Where to search. Walmart and Target are their US stores. Each one of "amazon", "walmart", "target".
    At least 1 item. Default: ["amazon", "walmart", "target"].
    """
    results_per_search: int
    """Listings per search: How many listings to read from the top of each retailer's results for each brand or
    product. From 1 to 40. Default: 20.
    """
    include_sponsored: bool
    """Include sponsored listings: Paid placements are left out by default, so that a position is the retailer's own
    ranking. Default: False.
    """
    amazon_marketplace: Literal["us", "uk", "de", "ca", "it", "es", "nl", "jp", "au", "mx", "br", "in", "ae"]
    """Amazon marketplace: Which Amazon store to read. One of "us", "uk", "de", "ca", "it", "es", "nl", "jp", "au",
    "mx", "br", "in", "ae". Default: "us".
    """
    amazon_bestseller_categories: List[str]
    """Amazon Best Sellers lists: Categories as their Best Sellers address names them, such as kitchen, beauty or
    electronics/172456. A listing in their top 100 gets its rank, and a best seller of your brands is added. At most
    10 items. Default: [].
    """
    check_stock: bool
    """Check stock on Amazon and Target: Their search results do not say whether a product is in stock, so each Amazon
    and Target listing's page is read, one unit a listing. Default: True.
    """
    max_results: int
    """Most rows: The run stops at this many listings, the biggest changes first. From 1 to 2000. Default: 200."""


class _EnterpriseAtsSweepParamsRequired(TypedDict):
    target_companies: List[str]
    """Target companies: A domain (acme.com) or a careers page address for each company. 1 to 100 items. Required."""


class EnterpriseAtsSweepParams(_EnterpriseAtsSweepParamsRequired, total=False):
    """Enterprise ATS Sweep (`enterprise-ats-sweep`): The new openings at your target companies, read from their own
    careers pages, with the companies hiring hardest flagged P1.

    Only `target_companies` is required; a key left out takes its default.
    """

    job_keywords: List[str]
    """Job keywords: Openings whose title holds one of these as a whole word or phrase. Leave empty for every opening.
    At most 20 items. Default: [].
    """
    locations: List[str]
    """Locations: Openings in one of these places; remote openings are kept too. Leave empty for anywhere. At most 20
    items. Default: [].
    """
    posted_within_days: int
    """Posted within (days): Only openings posted in the last this many days. An opening with no date is kept. From 1
    to 365. Default: 30.
    """
    exclude_keywords: List[str]
    """Words to leave out of titles: For example intern or graduate. Default: []."""
    verified_only: bool
    """Only openings from the tracking system: Leaves out what was read from a careers page's own text, where a heading
    or a name can pass for an opening. Off reads those too. Default: True.
    """
    min_matching_roles: int
    """Least matching openings: A company with fewer matching openings is left out. At least 1. Default: 1."""
    p1_min_roles: int
    """P1 at this many recent openings: A company with at least this many matching openings posted in the P1 window is
    flagged P1. At least 1. Default: 5.
    """
    p1_within_days: int
    """P1 window (days): How recent an opening must be to count towards P1. From 1 to 90. Default: 7."""
    resurface_after_days: int
    """Show an opening again after (days): For a saved formula, how long before a delivered opening may come back. From
    1 to 365. Default: 30.
    """
    max_results: int
    """Most rows: The run stops at this many rows, best first. From 1 to 5000. Default: 500."""


class _EventOrganizerLeadsParamsRequired(TypedDict):
    topics: List[str]
    """Topics: What the events are about, as you would search for them, such as startup, python or yoga. 1 to 8 items.
    Required.
    """
    city: str
    """City: One city, by its name alone. Required."""
    region: str
    """State or province: For a city in the United States or Canada, its state or province in two letters, which both
    sites need there; leave it empty elsewhere. Required.
    """


class EventOrganizerLeadsParams(_EventOrganizerLeadsParamsRequired, total=False):
    """Event Organizer Leads (`event-organizer-leads`): The groups and organisers running events on your topics in a
    city, from Meetup and Eventbrite, busiest first.

    Only `topics`, `city`, `region` are required; a key left out takes its default.
    """

    country: str
    """Country: The country, in two letters, such as US, GB or DE. Default: "US"."""
    sources: List[Literal["meetup", "eventbrite"]]
    """Where to look: Meetup's groups and Eventbrite's organisers. Each one of "meetup", "eventbrite". At least 1 item.
    Default: ["meetup", "eventbrite"].
    """
    eventbrite_place: str
    """Eventbrite's name for the place: Outside the United States and Canada, the place as Eventbrite's addresses write
    it, such as united-kingdom--london. Empty there leaves Eventbrite out. Default: "".
    """
    within_days: int
    """Events within (days): Only events starting in the next this many days count. From 1 to 365. Default: 90."""
    min_members: int
    """Fewest group members: Meetup groups with fewer members are left out. Eventbrite does not count followers, so its
    organisers are kept. At least 0. Default: 0.
    """
    min_events: int
    """Fewest events found: Organisers with fewer of the events found are left out. At least 1. Default: 1."""
    resurface_after_days: int
    """Show an organiser again after (days): For a saved formula, how long before a delivered organiser may come back.
    From 1 to 365. Default: 90.
    """
    max_results: int
    """Most rows: The run stops at this many organisers, best first. From 1 to 1000. Default: 200."""


class _ExhibitorProspectsParamsRequired(TypedDict):
    event_urls: List[str]
    """Shows: The address of each show's exhibitor list or floor plan on its a2z site (a2zinc.net), as your browser
    shows it. 1 to 10 items. Required.
    """


class ExhibitorProspectsParams(_ExhibitorProspectsParamsRequired, total=False):
    """Exhibitor Prospects (`exhibitor-prospects`): The companies exhibiting at the trade shows you name, with booth,
    website, location, categories and contact address.

    Only `event_urls` is required; a key left out takes its default.
    """

    keywords: List[str]
    """Categories or words: Keep exhibitors whose categories, products, brands or description name one of these, as
    whole words. Empty keeps every exhibitor. At most 20 items. Default: [].
    """
    your_event_url: str
    """Your show: The a2z address of your own show. Its exhibitors are left out, to find the companies that exhibit
    elsewhere but not with you. Default: "".
    """
    countries: List[str]
    """Countries: Keep exhibitors from these countries, in words as the shows write them, such as United States or
    Canada. Empty keeps all. At most 50 items. Default: [].
    """
    enhanced_only: bool
    """Only upgraded listings: Keep exhibitors who paid the show for an enhanced listing, a sign of a bigger exhibiting
    budget. Default: False.
    """
    min_shows: int
    """Fewest shows: With several shows, keep companies that exhibit at least at this many of them. From 1 to 10.
    Default: 1.
    """
    crm_companies: List[str]
    """Your accounts: Company names or domains from your CRM, matched against each exhibitor's name and website. At
    most 5000 items. Default: [].
    """
    crm_match: Literal["ignore", "only_accounts", "leave_out_accounts"]
    """Your accounts are: Use your accounts to keep only those exhibiting, or to leave them out and see only new
    companies. One of "ignore", "only_accounts", "leave_out_accounts". Default: "ignore".
    """
    include_site_contact: bool
    """Read each website for an address: The address the company's own website publishes, checked. Off saves one read a
    company. Default: True.
    """
    resurface_after_days: int
    """Show a company again after (days): For a saved formula, how long before a delivered company may come back. From
    1 to 365. Default: 120.
    """
    max_results: int
    """Most exhibitors read: The exhibitors whose show pages are read, most shows and upgraded listings first; words
    and countries then keep those that match. A show page and a website are one read each. From 1 to 1000. Default:
    100.
    """


class _FootprintProspectsParamsRequired(TypedDict):
    topic: str
    """Topic: The subject, as people search for it, such as gardening or personal finance. Required."""


class FootprintProspectsParams(_FootprintProspectsParamsRequired, total=False):
    """Footprint Prospects (`footprint-prospects`): Sites on your topic that take guest posts or keep resource pages,
    found by search footprints, each with its email.

    Only `topic` is required; a key left out takes its default.
    """

    footprints: List[str]
    """Footprints: Words searched beside the topic, each its own search. Quote a phrase to find it exactly. Search
    operators such as intitle: work too. 1 to 20 items. Default: ["\"write for us\"", "\"guest post guidelines\"",
    "\"submit a guest post\"", "\"become a contributor\"", "\"accepting guest posts\"", "\"contribute an
    article\""].
    """
    search_pages: int
    """Results pages per search: How many pages of results to read for each footprint, about ten results a page. From 1
    to 3. Default: 1.
    """
    exclude_domains: List[str]
    """Sites to leave out: Domains never shown, such as social networks, marketplaces and your own sites. At most 2000
    items. Default: a list of 21 values, which `get` on the formula shows.
    """
    country: str
    """Search country: The two-letter country whose search results are read, such as us, gb or de. Default: "us"."""
    language: str
    """Search language: The language of the results, such as en or de. Default: "en"."""
    read_articles: bool
    """Read each page for its author: Reads each page found as an article, for its author and the day it was published.
    Default: False.
    """
    require_author: bool
    """Only pages with a named author: When pages are read, keeps the sites whose page names who wrote it. Default:
    False.
    """
    require_email: bool
    """Only sites with an email: Keeps the sites whose own website publishes an email address that passes the check.
    Default: False.
    """
    resurface_after_days: int
    """Show a site again after (days): For a saved formula, how long before a delivered site may come back. From 1 to
    365. Default: 90.
    """
    max_results: int
    """Most rows: The run stops at this many sites, those matching the most footprints first. From 1 to 1000. Default:
    100.
    """


class _FreelanceGigFeedParamsRequired(TypedDict):
    keywords: List[str]
    """Keywords: The skills or kinds of project to look for. Each is searched, and a project must mention one of them.
    1 to 10 items. Required.
    """


class FreelanceGigFeedParams(_FreelanceGigFeedParamsRequired, total=False):
    """Freelance Gig Feed (`freelance-gig-feed`): New projects on Upwork and Freelancer that match your skills, with
    budget and applicants, only the ones you have not seen.

    Only `keywords` is required; a key left out takes its default.
    """

    posted_within_days: int
    """Posted within (days): Only projects posted in the last this many days. From 1 to 30. Default: 2."""
    min_fixed_budget: float
    """Least fixed budget: A fixed-price project must offer at least this much, in its own currency. A project with no
    budget shown is kept. At least 0. Default: 0.
    """
    min_hourly_rate: float
    """Least hourly rate: An hourly project must offer up to at least this much an hour, in its own currency. One with
    no rate shown is kept. At least 0. Default: 0.
    """
    platforms: List[Literal["upwork", "freelancer"]]
    """Marketplaces: Where to look. Each one of "upwork", "freelancer". At least 1 item. Default: ["upwork",
    "freelancer"].
    """
    payment_types: List[Literal["fixed", "hourly"]]
    """How it pays: Fixed price, hourly, or leave empty for both. Each one of "fixed", "hourly". Default: []."""
    exclude_keywords: List[str]
    """Words to leave out: A project whose title or description holds one of these is left out, such as wordpress or
    unpaid. Default: [].
    """
    max_applicants: int
    """Most bids so far: Leave out a project with more bids than this, where the count is known. 0 for any. At least 0.
    Default: 0.
    """
    resurface_after_days: int
    """Show a project again after (days): For a saved formula, how long before a delivered project may come back. From
    1 to 365. Default: 30.
    """
    max_results: int
    """Most rows: The run stops at this many rows, best first. From 1 to 1000. Default: 100."""



class FundedAndHiringParams(TypedDict, total=False):
    """Funded and Hiring (`funded-and-hiring`): Companies that just raised a round and are hiring on their own careers
    page, with the founder or talent lead to contact.

    Every key is optional; a key left out takes its default.
    """

    industries: List[str]
    """Industry words: Keep announcements whose headline or text holds one of these words. Leave empty for any. At most
    20 items. Default: [].
    """
    published_within_days: int
    """Announced within (days): Only rounds announced in the last this many days. From 1 to 60. Default: 14."""
    min_open_roles: int
    """Least open roles: Openings the company's careers page must list. 0 keeps companies with none. At least 0.
    Default: 1.
    """
    count_unconfirmed: bool
    """Count openings no tracking system confirms: Many young companies list jobs on a plain careers page. Those count
    towards the least open roles, and are shown apart. Default: True.
    """
    search_terms: List[str]
    """Searches: The words each wire is searched for. Each search reads the newest 50 releases that hold them. 1 to 8
    items. Default: ["raises Series A", "seed funding", "raises Series B", "funding round"].
    """
    wires: List[Literal["prnewswire", "globenewswire"]]
    """Newswires: Which newswires to read. Each one of "prnewswire", "globenewswire". At least 1 item. Default:
    ["prnewswire", "globenewswire"].
    """
    releases_read: int
    """Releases read: How many of the newest likely funding releases are read in full. From 5 to 100. Default: 50."""
    contact_titles: List[str]
    """Who to contact: The roles of the people to find at each company. Default: ["Founder", "CEO", "Head of Talent",
    "Head of People"].
    """
    contacts_per_company: int
    """Contacts per company: 0 turns contacts off. From 0 to 5. Default: 2."""
    require_verified_email: bool
    """Only addresses that pass the check: Keeps addresses whose domain takes mail, and those a verification provider
    confirmed. Default: True.
    """
    resurface_after_days: int
    """Show a company again after (days): For a saved formula, how long before a delivered company may come back. From
    1 to 365. Default: 90.
    """
    max_results: int
    """Most rows: The run stops at this many rows, best first. From 1 to 1000. Default: 100."""


class _HiringSignalOutboundParamsRequired(TypedDict):
    signal_terms: List[str]
    """Roles, tools or phrases: What the postings must name. Each is searched on the boards and looked for in the
    posting's text. 1 to 10 items. Required.
    """
    locations: List[str]
    """Locations: A city, region or country for each place to search. 1 to 10 items. Required."""


class HiringSignalOutboundParams(_HiringSignalOutboundParamsRequired, total=False):
    """Hiring-Signal Outbound (`hiring-signal-outbound`): Companies whose job posts reveal a need for what you sell,
    with the decision-maker and a true line to open with.

    Only `signal_terms`, `locations` are required; a key left out takes its default.
    """

    signal_type: Literal["role", "technology", "pain", "growth"]
    """Signal: role: companies hiring these roles. technology: postings that name these tools. pain: postings that
    describe these problems. growth: a department hiring several people. One of "role", "technology", "pain",
    "growth". Default: "technology".
    """
    posted_within_days: int
    """Posted within (days): Only postings from the last this many days. From 1 to 30. Default: 7."""
    sources: List[Literal["linkedin", "indeed", "dice", "reed", "totaljobs"]]
    """Job boards: Which boards to search. Reed and Totaljobs cover the UK; Dice is technology roles. Each one of
    "linkedin", "indeed", "dice", "reed", "totaljobs". At least 1 item. Default: ["linkedin", "indeed"].
    """
    results_per_search: int
    """Postings read per search: How many postings to read for each term, place and board. From 5 to 100. Default: 25.
    """
    postings_to_read: int
    """Postings read in full: How many of the newest postings are opened to read their whole text, where the search
    gave only a title. From 5 to 300. Default: 60.
    """
    growth_min_postings: int
    """Postings for growth: For the growth signal, how many postings one department of a company needs in the window.
    From 2 to 50. Default: 3.
    """
    company_size: IntRange
    """Company size (employees): Companies whose size is not known are kept. Default: {"min": 11, "max": 5000}."""
    industries_include: List[str]
    """Only these industries: Leave empty for any. Default: []."""
    industries_exclude: List[str]
    """Not these industries: Companies in these industries are left out. Default: []."""
    exclude_companies: List[str]
    """Companies to leave out: Names or domains, such as customers and open deals. At most 5000 items. Default: []."""
    buyer_titles: List[str]
    """Who to contact: The roles of the people to find. Leave empty to look for whoever decides for the role being
    hired, such as the VP Sales for an SDR. Default: [].
    """
    contact_seniority: List[Literal["manager", "director", "vp", "c_level"]]
    """Contact seniority: How senior the people to find should be. Each one of "manager", "director", "vp", "c_level".
    Default: ["director", "vp", "c_level"].
    """
    contacts_per_company: int
    """Contacts per company: 0 turns contacts off. From 0 to 5. Default: 1."""
    require_verified_email: bool
    """Only addresses that pass the check: Keeps addresses whose domain takes mail, and those a verification provider
    confirmed. Default: True.
    """
    resurface_after_days: int
    """Show a company again after (days): For a saved formula, how long before a company already delivered may come
    back. From 1 to 365. Default: 90.
    """
    max_results: int
    """Most rows: The run stops at this many rows, best first. From 1 to 2000. Default: 100."""


class _HiringVelocityParamsRequired(TypedDict):
    companies: List[str]
    """Companies: Each company as a stock ticker in capitals (DUOL), a domain (janestreet.com), or the address of its
    careers page or job board (https://boards.greenhouse.io/wehrtyou). A job board address is the most exact. 1 to
    100 items. Required.
    """


class HiringVelocityParams(_HiringVelocityParamsRequired, total=False):
    """Hiring Velocity (`hiring-velocity`): Open roles at the companies you watch, counted by department from their own
    careers sites, with the change since the last run.

    Only `companies` is required; a key left out takes its default.
    """

    recent_days: int
    """Recent means posted within (days): A role posted in the last this many days counts as a recent role. From 1 to
    90. Default: 30.
    """
    departments: List[Literal["engineering", "data", "research", "trading", "investments", "risk", "product", "design", "sales", "marketing", "customer_support", "finance", "legal", "people", "it", "operations", "healthcare", "education", "skilled_trades", "retail_hospitality", "other"]]
    """Only these departments: Leave empty for every department. Each one of "engineering", "data", "research",
    "trading", "investments", "risk", "product", "design", "sales", "marketing", "customer_support", "finance",
    "legal", "people", "it", "operations", "healthcare", "education", "skilled_trades", "retail_hospitality",
    "other". Default: [].
    """
    min_open_roles: int
    """Fewest open roles: A department with fewer open roles than this is left out. From 1 to 1000. Default: 1."""
    exclude_title_words: List[str]
    """Postings to leave out: Postings whose title holds one of these words are not counted; by default, evergreen
    talent lists and recruiting events, which are not roles. At most 50 items. Default: a list of 12 values, which
    `get` on the formula shows.
    """
    include_page_reads: bool
    """Count jobs read from the careers page itself: Off: only jobs from the company's applicant tracking system are
    counted, which is exact. On: jobs read from the text of a careers page that has none are counted too; such a
    page can list things that are not jobs, or show only some. Default: False.
    """
    max_results: int
    """Most rows: The run stops at this many departments, biggest movers first. From 1 to 5000. Default: 500."""


class _HomeServicesProsParamsRequired(TypedDict):
    trade: str
    """Trade: The trade in the plural, as the sites write it, such as plumbers, electricians or house cleaning.
    Required.
    """
    city: str
    """Town or city: One town or city. Required."""


class HomeServicesProsParams(_HomeServicesProsParamsRequired, total=False):
    """Home-Services Pros (`home-services-pros`): The plumbers, electricians or cleaners of a place, with ratings,
    licences, years in business and an email.

    Only `trade`, `city` are required; a key left out takes its default.
    """

    region: str
    """State or county: For the United States, the two-letter state, which Thumbtack needs. For the United Kingdom,
    leave empty or give the county. Default: "".
    """
    country: Literal["US", "GB"]
    """Country: The United States or the United Kingdom; the marketplaces read depend on it. One of "US", "GB".
    Default: "US".
    """
    sources: List[Literal["thumbtack", "bbb", "checkatrade", "google_maps"]]
    """Where to look: Each is read only for the country it covers. Each one of "thumbtack", "bbb", "checkatrade",
    "google_maps". At least 1 item. Default: ["thumbtack", "bbb", "checkatrade", "google_maps"].
    """
    min_rating: float
    """Lowest rating: Out of 5 on most sites and of 10 on Checkatrade; 0 keeps those with no rating. From 0 to 10.
    Default: 0.
    """
    min_reviews: int
    """Fewest reviews: Businesses with fewer reviews are left out. At least 0. Default: 0."""
    require_email: bool
    """Only businesses with an email: Keeps the businesses whose own website publishes an email address that passes the
    check. Default: False.
    """
    read_profiles: bool
    """Read each marketplace profile: Years in business, licences and background checks on Thumbtack; website and
    accreditations on Checkatrade. Default: True.
    """
    resurface_after_days: int
    """Show a business again after (days): For a saved formula, how long before a delivered business may come back.
    From 1 to 365. Default: 120.
    """
    max_results: int
    """Most rows: The run stops at this many businesses, most reviewed first. From 1 to 2000. Default: 150."""


class _HotelRateShopParamsRequired(TypedDict):
    hotels: List[str]
    """Hotels: Each hotel's name as Google Hotels shows it. Its rate there is read when the first hotel Google Hotels
    finds has that name. 1 to 20 items. Required.
    """


class HotelRateShopParams(_HotelRateShopParamsRequired, total=False):
    """Hotel Rate Shop (`hotel-rate-shop`): What your competing hotels charge a night for the same stays, from Google
    Hotels, Booking.com and MakeMyTrip, with each change.

    Only `hotels` is required; a key left out takes its default.
    """

    city: str
    """Town: The town the hotels are in, added to each name when it is searched, such as London. Leave empty when the
    names say it. Default: "".
    """
    days_ahead: List[int]
    """Stays starting in (days): How many days after each run the stays begin. A saved formula asks the same distances
    every time it runs. 1 to 6 items. Default: [7, 14, 30].
    """
    booking_pages: List[str]
    """Booking.com pages: The hotels' pages on Booking.com, such as https://www.booking.com/hotel/gb/strandpalace.html,
    to read their room prices there too. At most 20 items. Default: [].
    """
    makemytrip_hotels: List[str]
    """MakeMyTrip hotels: The hotels' pages on MakeMyTrip, or their hotel ids there, to read their rates in rupees too.
    At most 20 items. Default: [].
    """
    nights: int
    """Nights: How long each stay is. Prices are shown a night. From 1 to 14. Default: 1."""
    adults: int
    """Guests: Adults in one room. On Booking.com only the offers for at least this many guests count. From 1 to 8.
    Default: 2.
    """
    currency: Literal["USD", "EUR", "GBP", "AED", "INR", "AUD", "CAD", "JPY", "CHF", "SGD"]
    """Currency: The currency of the Google Hotels and Booking.com prices. MakeMyTrip prices are in rupees. One of
    "USD", "EUR", "GBP", "AED", "INR", "AUD", "CAD", "JPY", "CHF", "SGD". Default: "USD".
    """
    max_results: int
    """Most rows: The run stops at this many rates, changes and sold-out hotels first. From 1 to 2000. Default: 500."""


class _InfluencerDiscoveryParamsRequired(TypedDict):
    topics: List[str]
    """Topics: What the creators make videos about, as a viewer would search it, such as home espresso. A hashtag works
    too. 1 to 10 items. Required.
    """


class InfluencerDiscoveryParams(_InfluencerDiscoveryParamsRequired, total=False):
    """Influencer Discovery (`influencer-discovery`): Creators who make videos about your topic, with followers, views,
    engagement, their links and a published business email.

    Only `topics` is required; a key left out takes its default.
    """

    subscribers: IntRange
    """Subscribers: The size of creator to keep, by YouTube subscribers. Default: {"min": 10000, "max": 1000000}."""
    countries: List[str]
    """Countries: Only creators whose channel states one of these countries, as YouTube writes it (United States,
    Germany). Leave empty for any; a channel that states none is then kept. At most 20 items. Default: [].
    """
    min_topic_videos: int
    """Least videos on the topic: How many of a creator's videos must turn up in the topic searches; 2 or more keeps
    creators who cover it regularly. From 1 to 10. Default: 1.
    """
    exclude_channels: List[str]
    """Creators to leave out: Handles (@name) or channel ids of creators you already work with. At most 1000 items.
    Default: [].
    """
    videos_per_topic: int
    """Videos read per topic: How many of each topic's videos are read to find creators. Each video read is one unit.
    From 10 to 100. Default: 40.
    """
    max_creators: int
    """Creators read: How many creators' channels are read, the most on topic first; each channel, profile and website
    read is one unit. From 5 to 200. Default: 40.
    """
    other_platforms: List[Literal["instagram", "tiktok"]]
    """Also read: The creator's Instagram and TikTok accounts, where their channel links to them. Each one of
    "instagram", "tiktok". Default: ["instagram", "tiktok"].
    """
    website_email: bool
    """Business email from their website: Reads the creator's own website, where their channel links to one, for the
    business address it publishes. Default: True.
    """
    max_results: int
    """Most rows: The run stops at this many creators, best fit first. From 1 to 1000. Default: 100."""


class _JobOrderHunterParamsRequired(TypedDict):
    job_titles: List[str]
    """Job titles: The roles you recruit for, each searched as you type it. 1 to 10 items. Required."""
    locations: List[str]
    """Locations: A city, region or country for each place you cover. 1 to 10 items. Required."""


class JobOrderHunterParams(_JobOrderHunterParamsRequired, total=False):
    """Job Order Hunter (`job-order-hunter`): Companies newly hiring for your roles and places, qualified by size and
    industry, with the person to contact.

    Only `job_titles`, `locations` are required; a key left out takes its default.
    """

    posted_within_days: int
    """Posted within (days): Only jobs posted in the last this many days. From 1 to 30. Default: 1."""
    sources: List[Literal["linkedin", "indeed", "google_jobs", "dice", "reed", "totaljobs", "stepstone", "seek", "simplyhired", "wellfound", "xing", "irishjobs", "ycombinator", "ats_boards"]]
    """Job boards: Which boards to search. The careers pages of target companies are read when you choose them and name
    the companies. Each one of "linkedin", "indeed", "google_jobs", "dice", "reed", "totaljobs", "stepstone",
    "seek", "simplyhired", "wellfound", "xing", "irishjobs", "ycombinator", "ats_boards". At least 1 item. Default:
    ["linkedin", "indeed", "google_jobs"].
    """
    title_synonyms: bool
    """Search other names of the same job: Also searches the names the same job is often advertised under, such as RN
    for Registered Nurse. Default: False.
    """
    target_companies: List[str]
    """Target companies: Domains or careers pages whose own openings are read when Careers pages is chosen as a board.
    At most 100 items. Default: [].
    """
    results_per_search: int
    """Jobs read per search: How many jobs to read for each title, place and board. From 5 to 200. Default: 50."""
    employment_types: List[Literal["full_time", "part_time", "contract", "temporary"]]
    """Employment types: Leave empty for any. Each one of "full_time", "part_time", "contract", "temporary". Default:
    [].
    """
    company_size: IntRange
    """Company size (employees): Companies whose size is not known are kept. Default: {"min": 11, "max": 5000}."""
    industries_include: List[str]
    """Only these industries: Leave empty for any. Default: []."""
    industries_exclude: List[str]
    """Not these industries: Companies in these industries are left out. Default: []."""
    exclude_staffing_agencies: bool
    """Leave out staffing agencies: Recruiters' own postings are rarely a job order. Default: True."""
    exclude_companies: List[str]
    """Companies to leave out: Names or domains, such as your existing clients. At most 5000 items. Default: []."""
    min_open_roles: int
    """Least open roles: Matching roles a company needs to have open. At least 1. Default: 1."""
    title_exclude_keywords: List[str]
    """Words to leave out of titles: For example intern or unpaid. Default: []."""
    check_careers_pages: bool
    """Check their careers pages: Reads the careers page of the companies with the most matching roles; a role listed
    there ranks higher. Default: True.
    """
    careers_pages_max: int
    """Careers pages to read: How many companies' careers pages to read, those with the most matching roles first. From
    1 to 100. Default: 25.
    """
    contact_titles: List[str]
    """Who to contact: The roles of the people to find at each company. Default: ["Talent Acquisition", "HR Manager",
    "Hiring Manager"].
    """
    contact_seniority: List[Literal["manager", "director", "vp", "c_level"]]
    """Contact seniority: How senior the people to find should be. Each one of "manager", "director", "vp", "c_level".
    Default: ["manager", "director", "vp", "c_level"].
    """
    contacts_per_company: int
    """Contacts per company: 0 turns contacts off. From 0 to 5. Default: 2."""
    require_verified_email: bool
    """Only addresses that pass the check: Keeps addresses whose domain takes mail, and those a verification provider
    confirmed. Default: True.
    """
    resurface_after_days: int
    """Show a company again after (days): For a saved formula, how long before a delivered row may come back. From 1 to
    365. Default: 45.
    """
    max_results: int
    """Most rows: The run stops at this many rows, best first. From 1 to 5000. Default: 200."""


class _JobSeekerTargetsParamsRequired(TypedDict):
    target_titles: List[str]
    """Jobs you want: The job titles you are applying for, each searched as you type it. 1 to 5 items. Required."""
    locations: List[str]
    """Where: A city, region or country for each place you would work, or Remote. 1 to 5 items. Required."""


class JobSeekerTargetsParams(_JobSeekerTargetsParamsRequired, total=False):
    """Job Seeker Targets (`job-seeker-targets`): Employers hiring now for the job you want, with the person who
    decides, their address and a first line to send.

    Only `target_titles`, `locations` are required; a key left out takes its default.
    """

    posted_within_days: int
    """Posted within (days): Only postings from the last this many days, while the role is still open. From 1 to 30.
    Default: 3.
    """
    sources: List[Literal["linkedin", "indeed", "reed", "totaljobs", "dice"]]
    """Job boards: Which boards to search. Reed and Totaljobs cover the UK; Dice is technology roles in the US. Each
    one of "linkedin", "indeed", "reed", "totaljobs", "dice". At least 1 item. Default: ["linkedin", "indeed"].
    """
    results_per_search: int
    """Jobs read per search: How many postings to read for each job, place and board. From 5 to 100. Default: 25."""
    company_size: IntRange
    """Company size (employees): Companies whose size is not known are kept. Default: {"min": 1, "max": 100000}."""
    industries_include: List[str]
    """Only these industries: Leave empty for any. Default: []."""
    exclude_companies: List[str]
    """Employers to leave out: Names or domains, such as your current employer or places you already applied to. At
    most 2000 items. Default: [].
    """
    title_must_match: bool
    """Only titles that name the job: Keeps postings whose title names one of your jobs as whole words; boards also
    return near matches. Default: True.
    """
    title_exclude_keywords: List[str]
    """Words to leave out of titles: For example intern, senior or contract. Default: []."""
    contact_titles: List[str]
    """Who to write to: Leave empty to look for whoever decides on that kind of hire, such as the CTO for a developer.
    Default: [].
    """
    contacts_per_company: int
    """People per employer: 0 turns contacts off. From 0 to 3. Default: 1."""
    require_verified_email: bool
    """Only addresses that pass the check: Keeps addresses whose domain takes mail, and those a verification provider
    confirmed. Default: True.
    """
    max_results: int
    """Most rows: The run stops at this many rows, newest postings first. From 1 to 500. Default: 50."""


class _KnowledgeBaseCrawlParamsRequired(TypedDict):
    start_url: str
    """Start address: The address of the site or the documentation, such as https://docs.example.com/guide/. Only pages
    of the same site are read. Required.
    """


class KnowledgeBaseCrawlParams(_KnowledgeBaseCrawlParamsRequired, total=False):
    """Knowledge Base Crawl (`knowledge-base-crawl`): A site's or docs' pages as clean Markdown, one row a page; saved,
    it returns only the pages that are new, changed or gone.

    Only `start_url` is required; a key left out takes its default.
    """

    max_pages: int
    """Most pages read: Each page read is one unit. Following links reads at most 100 pages a run; with a sitemap, up
    to 2000. From 1 to 2000. Default: 50.
    """
    include_paths: List[str]
    """Only these sections: Read only pages whose path starts with one of these, such as /docs/. Leave empty for the
    whole site below the start address. At most 20 items. Default: [].
    """
    sitemap_url: str
    """Sitemap: To read the pages a sitemap lists instead of following links, its address
    (https://example.com/sitemap.xml) or the site's bare address. Only listed pages under the start address are
    read. Default: "".
    """
    exclude_paths: List[str]
    """Leave out these sections: Pages whose path starts with one of these are not read, such as /blog/ or /changelog/.
    At most 20 items. Default: [].
    """
    max_depth: int
    """Link depth: How many links away from the start address a page may be when links are followed. From 0 to 10.
    Default: 3.
    """
    whole_page: bool
    """Keep menus, headers and footers: Off, each page's Markdown is its main content only, which is what an index
    wants. Default: False.
    """
    min_words: int
    """Least words on a page: Leaves out near-empty pages, such as redirects and section stubs. From 0 to 5000.
    Default: 20.
    """
    report_removed: bool
    """Report pages that are gone: A saved formula also returns the pages the last run read that this one did not find.
    Turn it off when the site has more pages than a run reads. Default: True.
    """
    max_results: int
    """Most rows: The run stops at this many pages, changed ones first. From 1 to 2000. Default: 500."""


class _LandlordAgentLeadsParamsRequired(TypedDict):
    locations: List[str]
    """Places: UK towns, areas or postcodes, such as Manchester, Leeds or SW11. 1 to 10 items. Required."""


class LandlordAgentLeadsParams(_LandlordAgentLeadsParamsRequired, total=False):
    """Letting Agent Leads (UK) (`landlord-agent-leads`): The letting agents and letting businesses with the most
    rentals on Rightmove and OnTheMarket in a UK area, with their branch phone.

    Only `locations` is required; a key left out takes its default.
    """

    min_listings: int
    """Least rentals on the market: Only agents advertising at least this many of the rentals read. From 1 to 100.
    Default: 1.
    """
    portals: List[Literal["rightmove", "onthemarket"]]
    """Portals: Where to read the rentals. Each one of "rightmove", "onthemarket". At least 1 item. Default:
    ["rightmove", "onthemarket"].
    """
    pages: List[Literal[1, 2, 3, 4, 5]]
    """Result pages read: Which pages of each portal's results to read for each place, about 25 rentals a page. Each
    one of 1, 2, 3, 4, 5. At least 1 item. Default: [1, 2, 3].
    """
    radius_miles: Literal[0, 0.25, 0.5, 1, 3, 5, 10]
    """Radius (miles): Also read rentals this far around each place. One of 0, 0.25, 0.5, 1, 3, 5, 10. Default: 0."""
    max_rent: int
    """Most rent a month (GBP): 0 for no ceiling. At least 0. Default: 0."""
    exclude_agents: List[str]
    """Agents to leave out: Agents you already work with, by the name the portal shows. At most 2000 items. Default:
    [].
    """
    resurface_after_days: int
    """Show an agent again after (days): For a saved formula, how long before a delivered agent may come back. From 1
    to 365. Default: 60.
    """
    max_results: int
    """Most rows: The run stops at this many agents, most rentals first. From 1 to 1000. Default: 100."""


class _LaunchBatchListsParamsRequired(TypedDict):
    batch: str
    """Batch: As Y Combinator writes it, such as Fall 2026 or F26. Required."""


class LaunchBatchListsParams(_LaunchBatchListsParamsRequired, total=False):
    """Launch and Batch Lists (`launch-batch-lists`): The startups of a Y Combinator batch, newest launches first, with
    their founders and a way to reach each one.

    Only `batch` is required; a key left out takes its default.
    """

    industry: str
    """Industry: As the directory names it, such as Fintech, Healthcare or B2B. Leave empty for every industry."""
    hiring_only: bool
    """Only companies that are hiring: Keeps the companies the directory marks as hiring. Default: False."""
    exclude_companies: List[str]
    """Companies to leave out: Names or domains, such as your existing customers. At most 5000 items. Default: []."""
    max_team_size: int
    """Largest team: Companies with a bigger team are left out. At least 1. Default: 500."""
    contact_titles: List[str]
    """Who to contact: The roles a connected people provider looks for at each company. Default: ["Founder",
    "Co-Founder", "CEO"].
    """
    contacts_per_company: int
    """Contacts per company: People a connected provider finds at each company. 0 keeps one row per company. From 0 to
    5. Default: 1.
    """
    max_results: int
    """Most companies: How many companies of the batch to read, newest launches first. From 1 to 500. Default: 100."""


class _LinkIntersectParamsRequired(TypedDict):
    your_domain: str
    """Your domain: Your site's domain, such as example.com. Pages that already link to it are left out. Required."""
    competitors: List[str]
    """Competitors' domains: Two to six domains, such as rival.com. Every pair of them is searched for, so each one
    added costs more. 2 to 6 items. Required.
    """


class LinkIntersectParams(_LinkIntersectParamsRequired, total=False):
    """Link Intersect (`link-intersect`): Sites that link to two or more of your competitors but not to you, each with
    the page and the email the site publishes.

    Only `your_domain`, `competitors` are required; a key left out takes its default.
    """

    topic: str
    """Topic words: Words added to every search to keep it on your subject, such as crm. Leave empty to search the
    domains alone. Default: "".
    """
    min_competitors: int
    """Competitors linked, at least: A page must link to at least this many of your competitors. With 1, each
    competitor is also searched for alone. From 1 to 6. Default: 2.
    """
    count_named: bool
    """Count a competitor named without a link: A page that writes a competitor's domain in its text without linking to
    it counts toward the least number. Default: True.
    """
    search_pages: int
    """Results pages per search: How many pages of results to read for each search, about ten results a page. From 1 to
    3. Default: 1.
    """
    pages_to_read: int
    """Pages to check: How many of the pages found are read to see whom they link to, those found by the most searches
    first; never more than the most rows. From 5 to 100. Default: 30.
    """
    exclude_domains: List[str]
    """Sites to leave out: Domains never shown, such as social networks and review sites where no editor can add your
    link. At most 2000 items. Default: a list of 19 values, which `get` on the formula shows.
    """
    country: str
    """Search country: The two-letter country whose search results are read, such as us, gb or de. Default: "us"."""
    language: str
    """Search language: The language of the results, such as en or de. Default: "en"."""
    require_email: bool
    """Only sites with an email: Keeps the sites whose own website publishes an email address that passes the check.
    Default: False.
    """
    resurface_after_days: int
    """Show a site again after (days): For a saved formula, how long before a delivered site may come back. From 1 to
    365. Default: 90.
    """
    max_results: int
    """Most rows: The run stops at this many sites, those linking to the most competitors first. From 1 to 1000.
    Default: 100.
    """


class _ListingComplianceParamsRequired(TypedDict):
    asins: List[str]
    """Your listings: The ASINs to check. 1 to 200 items. Required."""


class ListingComplianceParams(_ListingComplianceParamsRequired, total=False):
    """Listing Compliance (`listing-compliance`): Your Amazon listings checked against your own content rules (brand,
    title words, images, bullets, Buy Box seller), with changes.

    Only `asins` is required; a key left out takes its default.
    """

    brand: str
    """Brand the listing must show: As your brand is written, such as JBL. Empty skips the check. Default: ""."""
    required_title_words: List[str]
    """Words every title must hold: Such as your brand or the product line. At most 20 items. Default: []."""
    marketplace: Literal["us", "uk", "de", "fr", "it", "es", "ca"]
    """Amazon marketplace. One of "us", "uk", "de", "fr", "it", "es", "ca". Default: "us"."""
    forbidden_words: List[str]
    """Words no title may hold. At most 30 items. Default: ["refurbished", "renewed", "used", "replica", "compatible
    with", "generic", "unbranded"].
    """
    min_images: int
    """Least images. From 0 to 20. Default: 6."""
    min_bullets: int
    """Least bullet points. From 0 to 10. Default: 5."""
    max_title_length: int
    """Longest title (characters). From 50 to 500. Default: 200."""
    buy_box_sellers: List[str]
    """Sellers who may hold the Buy Box: Such as Amazon.com and your own storefront. Empty skips the check. At most 100
    items. Default: [].
    """
    only_breaches: bool
    """Only listings with a breach or a change. Default: False."""
    max_results: int
    """Most rows: The run stops at this many listings, most breaches first. From 1 to 500. Default: 200."""


class _LiteratureSweepParamsRequired(TypedDict):
    query: str
    """Subject: Words that describe the subject; every word must appear in a paper's listing. PubMed also reads its own
    field tags, such as review[pt], when the words are not searched as one phrase. Required.
    """


class LiteratureSweepParams(_LiteratureSweepParamsRequired, total=False):
    """Literature Sweep (`literature-sweep`): New papers on your subject from PubMed, arXiv and Crossref, each paper
    once, with its abstract, DOI and free full text.

    Only `query` is required; a key left out takes its default.
    """

    exact_phrase: bool
    """Search the words as one phrase: Finds protein language model only where those words stand together, as a term of
    the field. Crossref reads the words alone either way. Default: False.
    """
    published_within_days: int
    """Published within (days): Only papers that appeared in the last this many days; 0 for any date. PubMed counts the
    day a paper was added to it. From 0 to 3650. Default: 30.
    """
    sources: List[Literal["pubmed", "arxiv", "crossref", "openalex", "semanticscholar"]]
    """Where to search: PubMed for medicine and life sciences, arXiv for preprints in physics, maths and computing,
    Crossref for journals of every field. Each one of "pubmed", "arxiv", "crossref", "openalex", "semanticscholar".
    At least 1 item. Default: ["pubmed", "arxiv", "crossref"].
    """
    authors: List[str]
    """Only papers by these authors: A surname, or a name as papers print it (Doudna, Liu DR). Leave empty for any
    author. At most 50 items. Default: [].
    """
    journals: List[str]
    """Only these journals: Part of a journal's or server's name; Nature also keeps Nature Methods. Leave empty for
    any. At most 50 items. Default: [].
    """
    include_preprints: bool
    """Include preprints: Papers not yet peer reviewed, from arXiv, bioRxiv and medRxiv. Default: True."""
    open_access_only: bool
    """Only papers free to read: Keeps the papers with a link to free full text. Default: False."""
    pages: int
    """Pages read per source: Each page is the 100 newest (Crossref, the 100 best matching) papers of one source; raise
    it for a busy subject or a long window. From 1 to 3. Default: 1.
    """
    read_abstracts: bool
    """Read PubMed abstracts: PubMed lists papers without their abstracts; this reads each PubMed paper's own page for
    its abstract and the day it went online. Default: True.
    """
    max_results: int
    """Most rows: The run stops at this many papers, best matching first. From 1 to 500. Default: 100."""


class _LocalBusinessLeadsParamsRequired(TypedDict):
    business_types: List[str]
    """Kinds of business: What to search for, as you would type it into Google Maps, such as roofer or vegan
    restaurant. 1 to 10 items. Required.
    """
    locations: List[str]
    """Places: A city, district or region for each place, with its state or country when the name is common. 1 to 10
    items. Required.
    """


class LocalBusinessLeadsParams(_LocalBusinessLeadsParamsRequired, total=False):
    """Local Business Leads (`local-business-leads`): Businesses of a kind in your places, with the email their own
    website publishes and facts to open with.

    Only `business_types`, `locations` are required; a key left out takes its default.
    """

    expand_locations: bool
    """Search each neighbourhood too: Searches again in the neighbourhoods and postcodes the first search found, to
    reach past its few hundred results. Default: True.
    """
    max_sub_areas: int
    """Neighbourhoods per search: How many neighbourhoods or postcodes to search again, those with the most places
    first. From 1 to 40. Default: 8.
    """
    places_per_search: int
    """Places read per search: How many places to read from each search. From 10 to 300. Default: 60."""
    website: Literal["any", "has", "missing"]
    """Website: Keep every business, only those with a website, or only those without one. One of "any", "has",
    "missing". Default: "any".
    """
    min_rating: float
    """Lowest rating: Businesses rated below this are left out. 0 keeps those with no rating. From 0 to 5. Default: 0.
    """
    max_rating: float
    """Highest rating: Businesses rated above this are left out. From 0 to 5. Default: 5."""
    min_reviews: int
    """Fewest reviews: Businesses with fewer reviews are left out. At least 0. Default: 0."""
    max_reviews: int
    """Most reviews: Businesses with more reviews are left out. At least 0. Default: 1000000."""
    exclude_chains: bool
    """Leave out chains: A name found five or more times in the results is taken for a chain and left out. Default:
    True.
    """
    require_email: bool
    """Only businesses with an email: Keeps the businesses whose own website publishes an email address that passes the
    check. Default: True.
    """
    exclude_role_addresses: bool
    """Only named addresses: Leaves out shared inboxes such as info@ and keeps addresses that passed every check.
    Default: False.
    """
    require_socials: bool
    """Only businesses with social profiles: Keeps the businesses whose website links to at least one social profile.
    Default: False.
    """
    include_site_facts: bool
    """Site facts: What each website is built on, and its speed score on a phone. Default: False."""
    max_speed_score: int
    """Slowest site score kept: With site facts, keeps the sites scoring this or less; 50 keeps the slow ones. From 0
    to 100. Default: 100.
    """
    include_firmographics: bool
    """Company facts: Industry and size from the company's LinkedIn page, when its website links to one. Default:
    False.
    """
    resurface_after_days: int
    """Show a business again after (days): For a saved formula, how long before a delivered business may come back.
    From 1 to 365. Default: 180.
    """
    max_results: int
    """Most rows: The run stops at this many businesses, most reviewed first. From 1 to 5000. Default: 500."""


class _LongOpenRolesParamsRequired(TypedDict):
    job_titles: List[str]
    """Job titles: The roles you place, each searched as you type it. 1 to 10 items. Required."""
    locations: List[str]
    """Locations: A city, region or country for each place you cover. 1 to 10 items. Required."""


class LongOpenRolesParams(_LongOpenRolesParamsRequired, total=False):
    """Long-Open Roles (`long-open-roles`): Jobs open for a month or more at companies that are struggling to fill
    them, with who decides on the hire.

    Only `job_titles`, `locations` are required; a key left out takes its default.
    """

    min_days_open: int
    """Open at least (days): Only jobs that have been posted at least this many days. From 7 to 180. Default: 30."""
    max_days_open: int
    """Open at most (days): Older postings are often forgotten rather than open; they are left out. From 14 to 365.
    Default: 120.
    """
    sources: List[Literal["linkedin", "indeed", "reed", "totaljobs", "dice"]]
    """Job boards: Which boards to search. Indeed lists jobs of the last 30 days only. Reed and Totaljobs cover the UK;
    Dice is technology roles in the US. Each one of "linkedin", "indeed", "reed", "totaljobs", "dice". At least 1
    item. Default: ["linkedin", "indeed"].
    """
    results_per_search: int
    """Jobs read per search: How many postings to read for each title, place and board; most are newer than you want,
    so read more. From 5 to 200. Default: 50.
    """
    company_size: IntRange
    """Company size (employees): Companies whose size is not known are kept. Default: {"min": 11, "max": 10000}."""
    exclude_companies: List[str]
    """Companies to leave out: Names or domains, such as your existing clients. At most 5000 items. Default: []."""
    title_exclude_keywords: List[str]
    """Words to leave out of titles: For example intern or volunteer. Default: []."""
    contact_titles: List[str]
    """Who to contact: Leave empty to look for whoever decides on that kind of hire, such as the Director of Nursing
    for a nurse. Default: [].
    """
    contacts_per_company: int
    """Contacts per company: 0 turns contacts off. From 0 to 5. Default: 1."""
    require_verified_email: bool
    """Only addresses that pass the check: Keeps addresses whose domain takes mail, and those a verification provider
    confirmed. Default: True.
    """
    max_results: int
    """Most rows: The run stops at this many rows, the longest-open first. From 1 to 2000. Default: 100."""


class _LookalikeCompaniesParamsRequired(TypedDict):
    seed_companies: List[str]
    """Accounts you won: Company names as the Y Combinator directory lists them. 1 to 20 items. Required."""


class LookalikeCompaniesParams(_LookalikeCompaniesParamsRequired, total=False):
    """Lookalike Companies (`lookalike-companies`): Startups like the accounts you won, found where the Y Combinator
    directory files them, with the people to contact.

    Only `seed_companies` is required; a key left out takes its default.
    """

    regions: List[str]
    """Places: As the directory names them, such as United States of America or Europe. Leave empty for anywhere.
    Default: [].
    """
    team_size: IntRange
    """Team size: Companies whose size is not known are kept. Default: {"min": 2, "max": 1000}."""
    active_only: bool
    """Only active companies: Leaves out companies the directory marks as acquired, public or inactive. Default: True.
    """
    peers_per_account: int
    """Companies read per account: How many companies to read from the directory for each account you won. From 5 to
    100. Default: 40.
    """
    exclude_companies: List[str]
    """Companies to leave out: Names or domains, such as your existing customers. At most 5000 items. Default: []."""
    buyer_titles: List[str]
    """Who to contact: The roles a connected people provider looks for at each company. Default: ["CEO", "Founder", "VP
    Sales", "Head of Operations"].
    """
    contacts_per_company: int
    """Contacts per company: 0 keeps one row per company. From 0 to 5. Default: 1."""
    max_results: int
    """Most companies: The run stops at this many companies, the most alike first. From 1 to 1000. Default: 100."""


class _MarketplaceFlipsParamsRequired(TypedDict):
    queries: List[str]
    """Search words: Searched on the Amazon you buy from, such as lego technic. Not needed when ASINs are given. At
    most 10 items. Required.
    """


class MarketplaceFlipsParams(_MarketplaceFlipsParamsRequired, total=False):
    """Amazon Marketplace Flips (Europe) (`marketplace-flips`): Products cheaper on one European Amazon than another,
    by the same ASIN, with the price gap and margin in euros.

    Only `queries` is required; a key left out takes its default.
    """

    buy_marketplace: Literal["de", "it", "es", "nl"]
    """Buy on: The Amazon you buy from (amazon.de, .it, .es or .nl). One of "de", "it", "es", "nl". Default: "de"."""
    sell_marketplaces: List[Literal["de", "fr", "it", "es", "nl"]]
    """Sell on: The Amazons whose price is compared. The one you buy on is skipped. Each one of "de", "fr", "it", "es",
    "nl". At least 1 item. Default: ["fr", "it", "es"].
    """
    asins: List[str]
    """ASINs: Products to compare, instead of a search. At most 50 items. Default: []."""
    min_gap_pct: float
    """Least price gap (%): The selling price above the buying price, as a share of the buying price. From 0 to 500.
    Default: 15.
    """
    referral_fee_pct: float
    """Referral fee (%): The share of the sale price Amazon keeps. From 0 to 50. Default: 15."""
    fulfilment_cost: float
    """Fulfilment and shipping a unit (EUR): Your fulfilment fee and the cost of moving a unit between countries. From
    0 to 100. Default: 4.
    """
    results_per_search: int
    """Products per search: How many products of each search are compared. From 1 to 48. Default: 15."""
    max_results: int
    """Most rows: The run stops at this many pairs, widest gap first. From 1 to 1000. Default: 100."""


class _MenuPriceTrackerParamsRequired(TypedDict):
    restaurants: List[str]
    """Restaurants: The restaurants' pages on Uber Eats, TheFork or Zomato, one address each. 1 to 50 items. Required.
    """


class MenuPriceTrackerParams(_MenuPriceTrackerParamsRequired, total=False):
    """Menu Price Tracker (`menu-price-tracker`): Every dish and price on the menus of the restaurants you watch, on
    Uber Eats, TheFork and Zomato, with each price change.

    Only `restaurants` is required; a key left out takes its default.
    """

    sections: List[str]
    """Only these menu sections: Words of the sections to keep, such as Mains or Pizza. Leave empty for the whole menu.
    At most 30 items. Default: [].
    """
    dish_words: List[str]
    """Only dishes named with: Keeps the dishes whose name holds one of these words, such as burger or margherita.
    Leave empty for every dish. At most 30 items. Default: [].
    """
    include_set_menus: bool
    """Include set menus: TheFork's set menus and their prices, beside the à la carte dishes. Default: True."""
    max_items_per_restaurant: int
    """Most dishes per restaurant: The first this many dishes of each menu, in the menu's own order. From 1 to 500.
    Default: 300.
    """
    max_results: int
    """Most rows: The run stops at this many dishes, price changes first. From 1 to 10000. Default: 2000."""


class _OutOfStockOpportunityParamsRequired(TypedDict):
    categories: List[str]
    """Best Sellers categories: As the list's address names them, such as toys-and-games, electronics, kitchen, or
    electronics/172456 for a category further down. 1 to 10 items. Required.
    """


class OutOfStockOpportunityParams(_OutOfStockOpportunityParamsRequired, total=False):
    """Out-of-Stock Opportunity (`out-of-stock-opportunity`): Amazon best sellers that are out of stock on Amazon, and
    the US retailers that have the same product in stock now.

    Only `categories` is required; a key left out takes its default.
    """

    retailers: List[Literal["target", "bestbuy", "newegg", "walmart"]]
    """Retailers: Where to look for stock. Walmart often answers automated visits with a check, so its products may be
    missing. Each one of "target", "bestbuy", "newegg", "walmart". At least 1 item. Default: ["target", "bestbuy"].
    """
    pages: List[Literal[1, 2]]
    """List pages: Page 1 is ranks 1 to 50, page 2 ranks 51 to 100. Each one of 1, 2. At least 1 item. Default: [1, 2].
    """
    candidates_per_retailer: int
    """Results compared per retailer. From 1 to 5. Default: 2."""
    max_results: int
    """Most rows: The run stops at this many product and retailer pairs, best rank first. From 1 to 500. Default: 100.
    """


class _PeopleListWithOpenersParamsRequired(TypedDict):
    companies: List[str]
    """Companies: The website domains of the companies to find people at. 1 to 500 items. Required."""
    titles: List[str]
    """Roles: The roles of the people to find. 1 to 10 items. Required."""


class PeopleListWithOpenersParams(_PeopleListWithOpenersParamsRequired, total=False):
    """People List with Openers (`people-list-with-openers`): The people in the roles you sell to at your target
    companies, with checked addresses and a line from their own site.

    Only `companies`, `titles` are required; a key left out takes its default.
    """

    seniority: List[Literal["manager", "director", "vp", "c_level"]]
    """Seniority: How senior the people should be. Each one of "manager", "director", "vp", "c_level". Default:
    ["director", "vp", "c_level"].
    """
    people_per_company: int
    """People per company: The most people to find at each company. From 1 to 10. Default: 2."""
    require_verified_email: bool
    """Only addresses that pass the check: Keeps addresses whose domain takes mail, and those a verification provider
    confirmed. Default: True.
    """
    max_results: int
    """Most rows: The run stops at this many people. From 1 to 5000. Default: 500."""


class _PermitStatusWatchParamsRequired(TypedDict):
    city: Literal["austin", "chicago", "new_york", "los_angeles", "san_francisco", "seattle", "dallas", "new_orleans", "cincinnati", "baton_rouge", "montgomery_county_md", "prince_georges_county_md", "norfolk", "buffalo", "orlando", "mesa", "raleigh", "washington_dc", "minneapolis", "detroit"]
    """City: The US city or county whose permits are watched. One of "austin", "chicago", "new_york", "los_angeles",
    "san_francisco", "seattle", "dallas", "new_orleans", "cincinnati", "baton_rouge", "montgomery_county_md",
    "prince_georges_county_md", "norfolk", "buffalo", "orlando", "mesa", "raleigh", "washington_dc", "minneapolis",
    "detroit". Required.
    """


class PermitStatusWatchParams(_PermitStatusWatchParamsRequired, total=False):
    """Permit Status Watch (`permit-status-watch`): Building permits in a US city read again on a schedule, with each
    status change and each newly issued permit.

    Only `city` is required; a key left out takes its default.
    """

    permit_numbers: List[str]
    """Permit numbers: The permits to watch, by their number at the city. Leave empty to watch the permits issued in an
    area instead. At most 50 items. Default: [].
    """
    address_contains: str
    """Address holds: Without permit numbers, only permits whose address holds this text, such as a street name. Empty
    watches the whole city. Default: "".
    """
    within_days: int
    """Issued within (days): Without permit numbers, the permits issued in the last this many days are watched. From 1
    to 365. Default: 30.
    """
    keyword: str
    """Work words: Without permit numbers, only permits whose type, work or description holds this, such as ROOF or
    SOLAR. Default: "".
    """
    permits_to_read: int
    """Permits read: Without permit numbers, the newest this many permits of the area are read on each run. From 10 to
    200. Default: 200.
    """
    only_changes: bool
    """Only what changed: On a saved formula's later runs, show only permits that are new or whose status changed. The
    first run shows every permit. Default: True.
    """
    max_results: int
    """Most rows: The run stops at this many permits, changes first. From 1 to 1000. Default: 200."""


class _PermitTradeLeadsParamsRequired(TypedDict):
    city: Literal["austin", "chicago", "new_york", "los_angeles", "san_francisco", "seattle", "dallas", "new_orleans", "cincinnati", "baton_rouge", "montgomery_county_md", "prince_georges_county_md", "norfolk", "buffalo", "orlando", "mesa", "raleigh", "washington_dc", "minneapolis", "detroit"]
    """City: The US city or county whose permits are read. Contractor names are published by Austin, Seattle, New York,
    Dallas, Cincinnati, Baton Rouge, Orlando, Mesa, Raleigh and Chicago. One of "austin", "chicago", "new_york",
    "los_angeles", "san_francisco", "seattle", "dallas", "new_orleans", "cincinnati", "baton_rouge",
    "montgomery_county_md", "prince_georges_county_md", "norfolk", "buffalo", "orlando", "mesa", "raleigh",
    "washington_dc", "minneapolis", "detroit". Required.
    """
    trades: List[str]
    """Trades: Words in a permit's type, work or description, such as roof, solar, hvac, deck or addition. Each is one
    search. 1 to 8 items. Required.
    """


class PermitTradeLeadsParams(_PermitTradeLeadsParamsRequired, total=False):
    """Permit Trade Leads (`permit-trade-leads`): Building permits just issued for your trades in a US city, with each
    job's contractor, or the busiest contractors ranked.

    Only `city`, `trades` are required; a key left out takes its default.
    """

    issued_within_days: int
    """Issued within (days): Only permits issued in the last this many days. From 1 to 365. Default: 30."""
    view: Literal["permits", "contractors"]
    """Rows are: One row a permit, or one row a contractor with how many permits it pulled. One of "permits",
    "contractors". Default: "permits".
    """
    min_value: float
    """Least job value (USD): Only permits whose declared value is at least this. Permits with no value are kept when
    this is 0. At least 0. Default: 0.
    """
    require_contractor: bool
    """Only permits that name a contractor: Leave out permits the city published without a contractor. Default: False.
    """
    exclude_contractors: List[str]
    """Contractors to leave out: Names of contractors, such as your own business or current customers. At most 2000
    items. Default: [].
    """
    permits_per_trade: int
    """Permits read per trade: The newest this many permits are read for each trade word. From 10 to 200. Default: 200.
    """
    resurface_after_days: int
    """Show a row again after (days): For a saved formula, how long before a delivered permit or contractor may come
    back. From 1 to 365. Default: 90.
    """
    max_results: int
    """Most rows: The run stops at this many rows, newest permits or busiest contractors first. From 1 to 2000.
    Default: 300.
    """


class _PriceSellerWatchParamsRequired(TypedDict):
    products: List[Dict[str, Any]]
    """Products: One product an entry: its name as shoppers search it, and where you have them its UPC or EAN (code),
    Amazon ASIN, brand, model and minimum advertised price (min_price). 1 to 50 items. Required.
    """


class PriceSellerWatchParams(_PriceSellerWatchParamsRequired, total=False):
    """Price and Seller Watch (`price-seller-watch`): Who sells each of your products on Amazon, Best Buy, Target and
    Newegg, at what price, what changed, and who is under your minimum.

    Only `products` is required; a key left out takes its default.
    """

    marketplaces: List[Literal["amazon", "bestbuy", "target", "newegg", "walmart"]]
    """Marketplaces: Where to look. Walmart often answers automated visits with a check, so its listings may be missing
    from a run. Each one of "amazon", "bestbuy", "target", "newegg", "walmart". At least 1 item. Default: ["amazon",
    "bestbuy", "target"].
    """
    authorised_sellers: List[str]
    """Authorised sellers: Seller names as the marketplaces show them, such as Amazon.com or Best Buy. Empty treats
    every seller as authorised. At most 500 items. Default: [].
    """
    price_change_pct: float
    """Price change worth an alert (%): A price that moved by at least this much since the last run raises an alert.
    From 0 to 100. Default: 5.
    """
    amazon_marketplace: Literal["us", "uk", "de", "fr", "it", "es", "ca"]
    """Amazon marketplace: Which Amazon to read. Best Buy, Target, Newegg and Walmart are read in the United States.
    One of "us", "uk", "de", "fr", "it", "es", "ca". Default: "us".
    """
    candidates_per_marketplace: int
    """Listings compared per marketplace: How many search results of each marketplace are checked against each product.
    From 1 to 5. Default: 2.
    """
    alerts_only: bool
    """Only rows with an alert: Leave out the offers that raise no alert. Default: False."""
    max_results: int
    """Most rows: The run stops at this many offers, alerts first. From 1 to 2000. Default: 500."""


class _PropertyCompsParamsRequired(TypedDict):
    locations: List[str]
    """Places: ZIP codes, cities with their state ("Austin, TX") or neighbourhoods, as Zillow names them. 1 to 10
    items. Required.
    """


class PropertyCompsParams(_PropertyCompsParamsRequired, total=False):
    """Property Comps (`property-comps`): Recently sold and listed homes like yours in a US area, with sale price,
    price per square foot and the ZIP code average.

    Only `locations` is required; a key left out takes its default.
    """

    home_types: List[Literal["house", "condo", "townhouse", "multi_family", "manufactured"]]
    """Kinds of home: The kinds of home that count as comparable. Each one of "house", "condo", "townhouse",
    "multi_family", "manufactured". Default: ["house"].
    """
    min_beds: int
    """Least bedrooms: 0 for any. From 0 to 5. Default: 0."""
    living_area: IntRange
    """Living area (sq ft): The size range of a comparable home, such as 1200 to 1800 for a 1500 sq ft home. Default:
    {"min": 0, "max": 20000}.
    """
    include_for_sale: bool
    """Show homes for sale too: The matching homes on the market now, as the competition. Default: True."""
    sold_within_days: int
    """Sold within (days): Only homes sold in the last this many days. From 7 to 730. Default: 180."""
    homes_per_place: int
    """Homes read per place and kind: Zillow's first page of each place is read, up to this many homes, for sold and
    for sale each. From 5 to 41. Default: 41.
    """
    max_results: int
    """Most rows: The run stops at this many homes, newest sales first. Each sold home's page is read for its price.
    From 1 to 500. Default: 60.
    """


class _PropertyDistressSignalsParamsRequired(TypedDict):
    city: Literal["austin", "chicago", "new_york", "los_angeles", "seattle", "new_orleans", "cincinnati", "montgomery_county_md", "norfolk", "buffalo"]
    """City: The US city or county whose open data is read. These publish both code cases and permits. One of "austin",
    "chicago", "new_york", "los_angeles", "seattle", "new_orleans", "cincinnati", "montgomery_county_md", "norfolk",
    "buffalo". Required.
    """


class PropertyDistressSignalsParams(_PropertyDistressSignalsParamsRequired, total=False):
    """Property Distress Signals (`property-distress-signals`): Properties in a US city with recent code violations,
    distress permits or a stale listing, stacked by address and ranked.

    Only `city` is required; a key left out takes its default.
    """

    within_days: int
    """Opened or issued within (days): Only cases opened, and permits issued, in the last this many days. From 1 to
    365. Default: 60.
    """
    min_lists: int
    """Least lists a property is on: 2 keeps only properties on two lists or more (a code case and a distress permit,
    or either and a listing). From 1 to 3. Default: 1.
    """
    case_keywords: List[str]
    """Case words: Only cases whose type or description holds one of these, such as structure, vacant or abatement.
    Each word is one search; empty reads the newest cases of any kind. At most 8 items. Default: [].
    """
    open_cases_only: bool
    """Only cases still open: Leave out cases the city has closed. Default: False."""
    permit_keywords: List[str]
    """Distress permit words: Permits whose type, work or description holds one of these are a signal. Each word is one
    search. Empty leaves permits out. At most 8 items. Default: ["demoli", "fire damage", "vacant", "unsafe"].
    """
    cases_to_read: int
    """Cases read: The newest this many code cases are read. From 10 to 200. Default: 200."""
    permits_per_word: int
    """Permits read per word: The newest this many permits are read for each permit word. From 10 to 200. Default: 100.
    """
    check_listings: bool
    """Check each property on Zillow: Whether the home is listed, how long and at what price, with its size and value
    estimate. One lookup a property. Default: True.
    """
    resurface_after_days: int
    """Show a property again after (days): For a saved formula, how long before a delivered property may come back.
    From 1 to 365. Default: 30.
    """
    max_results: int
    """Most rows: The run stops at this many properties, most signals first. From 1 to 1000. Default: 100."""


class _RankTrackerParamsRequired(TypedDict):
    keywords: List[str]
    """Keywords: The searches to track, each as people type it. 1 to 100 items. Required."""
    your_domain: str
    """Your domain: Your site's domain, such as example.com; its subdomains count as it. Required."""


class RankTrackerParams(_RankTrackerParamsRequired, total=False):
    """Rank Tracker (`rank-tracker`): Your domain's and your competitors' Google Search positions for each keyword,
    with the top results and what moved since last run.

    Only `keywords`, `your_domain` are required; a key left out takes its default.
    """

    competitors: List[str]
    """Competitors' domains: Up to ten domains, such as rival.com, each tracked for every keyword. At most 10 items.
    Default: [].
    """
    country: str
    """Country: The two-letter country whose results are read, such as us, gb or de. Default: "us"."""
    pages: int
    """Results pages read: 1 reads the top 10 results of each keyword, 2 the top 20, 3 the top 30; each page is one
    search. From 1 to 3. Default: 1.
    """
    language: str
    """Language: The language of the results, such as en or de. Default: "en"."""
    top_results: int
    """Top results shown: How many of the domains at the top of each keyword's results are listed on its rows. From 0
    to 10. Default: 3.
    """
    max_results: int
    """Most rows: The run stops at this many rows, one for each keyword and domain. From 1 to 1100. Default: 500."""


class _ReverseSourcingParamsRequired(TypedDict):
    queries: List[str]
    """Search words: Searched on Amazon (reverse, without ASINs) or on each retailer (forward), such as lego duplo or
    air fryer. At most 10 items. Required.
    """


class ReverseSourcingParams(_ReverseSourcingParamsRequired, total=False):
    """Reverse Sourcing (`reverse-sourcing`): Products that sell on Amazon for more than Target, Best Buy, Newegg or
    Walmart charge, with profit and ROI after your fees.

    Only `queries` is required; a key left out takes its default.
    """

    mode: Literal["reverse", "forward"]
    """Start from: reverse starts from Amazon products and looks for them at the retailers; forward starts from the
    retailers' search and looks for each product on Amazon. One of "reverse", "forward". Default: "reverse".
    """
    asins: List[str]
    """Amazon products: For reverse, the ASINs to source. Leave empty to search Amazon for the words below instead. At
    most 50 items. Default: [].
    """
    retailers: List[Literal["target", "bestbuy", "newegg", "walmart"]]
    """Retailers: Where to buy. Walmart often answers automated visits with a check, so its products may be missing
    from a run. Each one of "target", "bestbuy", "newegg", "walmart". At least 1 item. Default: ["target",
    "bestbuy"].
    """
    referral_fee_pct: float
    """Amazon referral fee (%): The share of the sale price Amazon keeps; 15% in most categories, 8% in some. From 0 to
    50. Default: 15.
    """
    fulfilment_cost: float
    """Fulfilment and shipping a unit (USD): Your FBA fee, prep and inbound shipping for one unit. From 0 to 100.
    Default: 5.
    """
    min_roi_pct: float
    """Least return on cost (%): Profit as a share of the retailer's price. From -100 to 1000. Default: 15."""
    min_profit: float
    """Least profit a unit (USD): Profit after the referral fee and fulfilment cost. At least -1000. Default: 2."""
    bestbuy_sort: Literal["best_match", "best_discount", "best_selling"]
    """Best Buy order: For forward, the order of Best Buy's results; best_discount reads its deepest reductions first.
    One of "best_match", "best_discount", "best_selling". Default: "best_match".
    """
    candidates_per_retailer: int
    """Results compared per search: How many search results are checked against each product. From 1 to 5. Default: 2.
    """
    amazon_results: int
    """Amazon products per search: For reverse without ASINs, how many products of each Amazon search are sourced. From
    1 to 48. Default: 10.
    """
    retailer_results: int
    """Retailer products per search: For forward, how many products of each retailer search are looked up on Amazon.
    From 1 to 48. Default: 12.
    """
    max_results: int
    """Most rows: The run stops at this many pairs, best return first. From 1 to 1000. Default: 100."""


class _ReviewMiningParamsRequired(TypedDict):
    products: List[str]
    """Product pages: The address of each product's page on Target, Walmart, or an Amazon outside the US (amazon.co.uk,
    .de, .ca ...). 1 to 30 items. Required.
    """


class ReviewMiningParams(_ReviewMiningParamsRequired, total=False):
    """Review Mining (`review-mining`): The complaints in your products' or competitors' reviews on Target, Walmart and
    Amazon, by topic, with the buyer's own words.

    Only `products` is required; a key left out takes its default.
    """

    topics: List[str]
    """Topics: Phrases to look for, matched as words and their forms ("broke" also finds "broken"). 1 to 40 items.
    Default: a list of 20 values, which `get` on the formula shows.
    """
    max_stars: int
    """Most stars: Only reviews of this many stars or fewer. 5 reads every review. From 1 to 5. Default: 3."""
    order: Literal["lowest_rating", "newest", "most_helpful"]
    """Reviews read first: Target and Walmart read their reviews in this order; Amazon reads the page's own. One of
    "lowest_rating", "newest", "most_helpful". Default: "lowest_rating".
    """
    only_with_topics: bool
    """Only reviews that mention a topic. Default: True."""
    max_results: int
    """Most rows: The run stops at this many reviews, the most topics first. From 1 to 2000. Default: 300."""


class _ReviewVelocityParamsRequired(TypedDict):
    apps: List[str]
    """Apps: An App Store app's address or its number (368677368 for Uber), or a Google Play app's package name, as its
    address shows it after id= (com.ubercab). An app on both stores is given twice, once for each. At most 50 items.
    Required.
    """


class ReviewVelocityParams(_ReviewVelocityParamsRequired, total=False):
    """Review Velocity (`review-velocity`): Ratings and reviews of the apps, companies and games you follow, with how
    many were added since the last run and per day.

    Only `apps` is required; a key left out takes its default.
    """

    companies: List[str]
    """Companies on Trustpilot: The company's website domain, such as chewy.com, for its Trustpilot reviews. At most 50
    items. Default: [].
    """
    games: List[str]
    """Games on Steam: A Steam game's number or its store address, such as 1091500 for Cyberpunk 2077. At most 50
    items. Default: [].
    """
    country: str
    """Store country: The country whose App Store, Google Play and Steam store are read, as a two-letter code. Their
    counts and ratings are per country. Default: "us".
    """
    max_results: int
    """Most rows: The run stops at this many rows, the biggest moves first. From 1 to 200. Default: 200."""


class _SalaryBenchmarkParamsRequired(TypedDict):
    job_titles: List[str]
    """Job: The job to benchmark, and up to two other names it is advertised under. 1 to 3 items. Required."""
    locations: List[str]
    """Places: Each city, region or country to compare. 1 to 10 items. Required."""


class SalaryBenchmarkParams(_SalaryBenchmarkParamsRequired, total=False):
    """Salary Benchmark (`salary-benchmark`): The pay employers advertise for a job in each place, as yearly ranges per
    place, with every posting behind them.

    Only `job_titles`, `locations` are required; a key left out takes its default.
    """

    posted_within_days: int
    """Posted within (days): Only postings from the last this many days, so the figures are today's. From 1 to 60.
    Default: 30.
    """
    sources: List[Literal["indeed", "linkedin", "reed", "totaljobs", "dice", "seek", "stepstone"]]
    """Job boards: Which boards to read. Reed and Totaljobs cover the UK (Reed states pay on most postings), Dice
    technology roles in the US, Seek Australia, StepStone Germany. Each one of "indeed", "linkedin", "reed",
    "totaljobs", "dice", "seek", "stepstone". At least 1 item. Default: ["indeed", "linkedin"].
    """
    results_per_search: int
    """Jobs read per search: How many postings to read for each job name, place and board; many do not state pay. From
    5 to 200. Default: 50.
    """
    title_must_match: bool
    """Only titles that name the job: Keeps postings whose title names the job as whole words; boards also return near
    matches, which would blur the figures. Default: True.
    """
    exclude_agencies: bool
    """Leave out agencies' postings: Agencies often advertise a wide range; leave them out to see only what employers
    state. Default: False.
    """
    levels_companies: List[str]
    """Companies to add from Levels.fyi: Company names as Levels.fyi writes them; their pay for the job is added by
    level, from what people reported. At most 20 items. Default: [].
    """
    levels_role: str
    """The job as Levels.fyi names it: Such as Software Engineer or Data Scientist. Empty uses the first job name.
    Default: "".
    """
    max_results: int
    """Most rows: The run stops at this many rows, best paid first. From 1 to 2000. Default: 200."""


class _SecFilingMonitorParamsRequired(TypedDict):
    companies: List[str]
    """Companies: Tickers (AAPL, BRK-B) or EDGAR's CIK numbers; a fund or a person who files is named by CIK. 1 to 100
    items. Required.
    """


class SecFilingMonitorParams(_SecFilingMonitorParamsRequired, total=False):
    """SEC Filing Monitor (`sec-filing-monitor`): New SEC filings of the companies you follow, insider trades, 8-Ks and
    activist stakes first, each linked to the filing.

    Only `companies` is required; a key left out takes its default.
    """

    forms: List[str]
    """Form types: The forms to watch, as EDGAR writes them. Leave empty for every form. At most 20 items. Default: a
    list of 10 values, which `get` on the formula shows.
    """
    filed_within_days: int
    """Filed within (days): Only filings made in the last this many days. From 1 to 90. Default: 7."""
    eight_k_items: List[str]
    """Only 8-Ks reporting these items: For example 5.02 (officers leaving or joining) or 1.01 (a material agreement).
    Leave empty for every 8-K. Default: [].
    """
    include_amendments: bool
    """Include amendments: Amended filings, whose form ends in /A. Default: True."""
    per_company: int
    """Filings read per company: The newest filings read for each company; raise it for a long window on a company that
    files often. From 1 to 100. Default: 40.
    """
    max_results: int
    """Most rows: The run stops at this many filings, most significant first. From 1 to 2000. Default: 200."""


class _SellerIdentityParamsRequired(TypedDict):
    asins: List[str]
    """Your products on Amazon: ASINs whose sellers to identify. Every seller with an offer on them is read. At most 30
    items. Required.
    """


class SellerIdentityParams(_SellerIdentityParamsRequired, total=False):
    """Seller Identity (`seller-identity`): The legal business behind each marketplace seller of your products, with
    its address, website, domain record and register entry.

    Only `asins` is required; a key left out takes its default.
    """

    seller_ids: List[str]
    """Amazon seller ids: Sellers to identify directly, by the id in their storefront's address (seller=...). At most
    100 items. Default: [].
    """
    walmart_sellers: List[str]
    """Walmart sellers: Walmart Marketplace sellers by id or storefront address. At most 100 items. Default: []."""
    marketplace: Literal["us", "uk", "de", "fr", "it", "es", "ca"]
    """Amazon marketplace: Which Amazon the products and sellers are on. One of "us", "uk", "de", "fr", "it", "es",
    "ca". Default: "us".
    """
    authorised_sellers: List[str]
    """Authorised sellers: Storefront names to leave out, such as your own and your distributors'. At most 500 items.
    Default: ["Amazon.com", "Amazon"].
    """
    find_website: bool
    """Find each business's website and its domain record: Looks the business up by name, and reads the registration of
    the domain it finds. Default: True.
    """
    check_company_register: bool
    """Look UK businesses up at Companies House: For a seller whose address is in the United Kingdom. Default: True."""
    max_results: int
    """Most rows: The run stops at this many sellers, the most identified first. From 1 to 500. Default: 100."""


class _ShopifyNicheResearchParamsRequired(TypedDict):
    stores: List[str]
    """Shopify stores: The stores of the niche, by domain. 1 to 20 items. Required."""


class ShopifyNicheResearchParams(_ShopifyNicheResearchParamsRequired, total=False):
    """Shopify Niche Research (`shopify-niche-research`): The products of a niche's Shopify stores, with price, newness
    and reductions, and similar products on AliExpress with the margin.

    Only `stores` is required; a key left out takes its default.
    """

    niche_words: List[str]
    """Niche words: Keep products whose title, type or tags hold one of these. Empty keeps every product. At most 20
    items. Default: [].
    """
    collection: str
    """Collection: A collection to read in each store, by its handle, such as best-sellers. Empty reads the catalogue.
    Default: "".
    """
    find_suppliers: bool
    """Look for similar products on AliExpress: One search a product. Default: True."""
    products_per_store: int
    """Products read per store. From 10 to 250. Default: 250."""
    max_results: int
    """Most rows: The run stops at this many products, newest and reduced first. Each is one AliExpress search. From 1
    to 500. Default: 30.
    """


class _SocialSentimentParamsRequired(TypedDict):
    terms: List[str]
    """Tickers or brands: Each is searched as you type it and counted where a post names it as a whole word, such as
    Nvidia or $NVDA. Mastodon is searched by hashtag, so only one-word terms are read there. 1 to 10 items.
    Required.
    """


class SocialSentimentParams(_SocialSentimentParamsRequired, total=False):
    """Social Sentiment (`social-sentiment`): How often the tickers and brands you follow are mentioned on social
    sources, in what tone, and how both moved since the last run.

    Only `terms` is required; a key left out takes its default.
    """

    sources: List[Literal["hackernews", "mastodon", "youtube", "telegram", "x", "bluesky", "stackoverflow"]]
    """Sources: Where to look. Telegram, X and Bluesky are read through the channels and accounts named below. Each one
    of "hackernews", "mastodon", "youtube", "telegram", "x", "bluesky", "stackoverflow". At least 1 item. Default:
    ["hackernews", "mastodon", "youtube", "telegram", "x", "bluesky"].
    """
    window_days: int
    """Mentions of the last (days): Only mentions posted in the last this many days are counted. YouTube comments carry
    no date and are not cut. From 1 to 30. Default: 7.
    """
    per_source_limit: int
    """Posts read per term on Mastodon and Telegram: The most posts read for one term on Mastodon and in each Telegram
    channel, newest first. Hacker News and Stack Overflow are read 100 deep. From 5 to 100. Default: 40.
    """
    telegram_channels: List[str]
    """Telegram channels: Public channels whose posts are searched for each term, by name (WatcherGuru) or address. At
    most 10 items. Default: ["WatcherGuru", "financialjuice"].
    """
    x_accounts: List[str]
    """X accounts: Accounts whose latest posts (X shows the newest five of each) are read for mentions. At most 20
    items. Default: ["DeItaone", "unusual_whales", "zerohedge", "StockMKTNewz", "WatcherGuru"].
    """
    bluesky_accounts: List[str]
    """Bluesky accounts: Accounts by handle, such as reuters.com, whose latest posts are read for mentions. At most 20
    items. Default: ["bloomberg.com", "reuters.com", "wsj.com"].
    """
    posts_per_account: int
    """Bluesky posts read per account: The newest posts read from each Bluesky account. From 5 to 100. Default: 30."""
    videos_per_term: int
    """YouTube videos per term: How many of the videos a YouTube search for the term finds first have their comments
    read. From 1 to 5. Default: 2.
    """
    comments_per_video: int
    """Comments read per video: The newest comments read on each video. From 5 to 100. Default: 20."""
    mastodon_server: str
    """Mastodon server: The server whose view of a hashtag is read; a large one sees the posts of many others. Default:
    "mastodon.social".
    """
    positive_words: List[str]
    """Positive words: A mention that uses one of these as a whole word, and none of the negative ones, counts as
    positive. At most 100 items. Default: a list of 44 values, which `get` on the formula shows.
    """
    negative_words: List[str]
    """Negative words: A mention that uses one of these as a whole word, and none of the positive ones, counts as
    negative. At most 100 items. Default: a list of 52 values, which `get` on the formula shows.
    """
    max_results: int
    """Most rows: The run stops at this many rows, the biggest moves first. From 1 to 100. Default: 100."""


class _StaleListingsParamsRequired(TypedDict):
    locations: List[str]
    """Places: Cities with their state ("Austin, TX"), ZIP codes or counties, as Zillow names them. 1 to 20 items.
    Required.
    """


class StaleListingsParams(_StaleListingsParamsRequired, total=False):
    """Stale Listings (`stale-listings`): Homes for sale that have sat on Zillow for months or been cut in price, with
    list price, Zestimate and the listing agent.

    Only `locations` is required; a key left out takes its default.
    """

    min_days_on_market: int
    """Least days on Zillow: Homes listed at least this long. A home with a price cut is kept sooner when the next
    option is on. From 1 to 730. Default: 90.
    """
    price_cut_counts: bool
    """A price cut makes a listing stale too: Keep a home whose price was cut, however long it has been listed.
    Default: True.
    """
    home_types: List[Literal["house", "condo", "townhouse", "multi_family", "manufactured", "land"]]
    """Kinds of home: Which kinds of home to search. Each one of "house", "condo", "townhouse", "multi_family",
    "manufactured", "land". Default: ["house", "townhouse", "multi_family"].
    """
    min_price: int
    """Least price (USD): 0 for no floor. At least 0. Default: 0."""
    max_price: int
    """Most price (USD): 0 for no ceiling. At least 0. Default: 0."""
    listings_per_place: int
    """Listings read per place: Zillow's first page of each place is read, up to this many homes. From 5 to 41.
    Default: 41.
    """
    with_agent: bool
    """Read each listing's agent and history: The listing agent and brokerage, the Zestimate and the price history. One
    page a listing. Default: True.
    """
    resurface_after_days: int
    """Show a listing again after (days): For a saved formula, how long before a delivered listing may come back. From
    1 to 365. Default: 30.
    """
    max_results: int
    """Most rows: The run stops at this many listings, longest listed first. From 1 to 1000. Default: 100."""


class _StorefrontResearchParamsRequired(TypedDict):
    seller_ids: List[str]
    """Competitors' seller ids: The id in a storefront's address (seller=...). 1 to 10 items. Required."""
    queries: List[str]
    """Niche search words: Searched on Amazon; the listings found are checked for the competitor's offers. At most 10
    items. Required.
    """


class StorefrontResearchParams(_StorefrontResearchParamsRequired, total=False):
    """Storefront Research (`storefront-research`): What a competing Amazon seller sells in your niche, its prices and
    Buy Box, the sellers it competes with, and where to source it.

    Only `seller_ids`, `queries` are required; a key left out takes its default.
    """

    categories: List[str]
    """Best-seller lists: Also check the products of these Best Sellers lists, such as toys-and-games. At most 5 items.
    Default: [].
    """
    results_per_search: int
    """Listings per search: Each listing is one read of its offers. From 1 to 48. Default: 20."""
    source_at_retailers: bool
    """Look for each product at Target and Best Buy. Default: True."""
    referral_fee_pct: float
    """Amazon referral fee (%). From 0 to 50. Default: 15."""
    fulfilment_cost: float
    """Fulfilment and shipping a unit (USD). From 0 to 100. Default: 5."""
    max_results: int
    """Most rows: The run stops at this many products, Buy Box first. From 1 to 500. Default: 100."""


class _StrUnderwritingParamsRequired(TypedDict):
    location: str
    """Place: Where, as you would type it into Airbnb, with the country, such as "Nashville, Tennessee, United States".
    Required.
    """
    checkin: str
    """Check-in: The first night, YYYY-MM-DD. Rates are for this stay. Required."""
    checkout: str
    """Check-out: The day of departure, YYYY-MM-DD. Required."""


class StrUnderwritingParams(_StrUnderwritingParamsRequired, total=False):
    """Short-Term Rental Comps (`str-underwriting`): Airbnb and Vrbo rentals in an area for your dates, with nightly
    rate, rating, reviews and the area's average rate.

    Only `location`, `checkin`, `checkout` are required; a key left out takes its default.
    """

    guests: int
    """Guests: Adults staying; rentals too small for them are not offered. From 1 to 16. Default: 2."""
    platforms: List[Literal["airbnb", "vrbo"]]
    """Platforms: Where to look. Each one of "airbnb", "vrbo". At least 1 item. Default: ["airbnb", "vrbo"]."""
    currency: Literal["USD", "EUR", "GBP", "CAD", "AUD"]
    """Airbnb currency: The currency Airbnb shows prices in. Vrbo shows the destination's own. One of "USD", "EUR",
    "GBP", "CAD", "AUD". Default: "USD".
    """
    min_reviews: int
    """Least reviews: Leave out rentals with fewer reviews, such as new listings. At least 0. Default: 0."""
    max_results: int
    """Most rows: The run stops at this many rentals, most reviewed first. From 1 to 500. Default: 150."""


class _SupplierDiscoveryParamsRequired(TypedDict):
    products: List[str]
    """Products: What you buy, as a supplier would list it, such as CNC machined parts or corrugated boxes. Each is
    searched on its own. 1 to 5 items. Required.
    """


class SupplierDiscoveryParams(_SupplierDiscoveryParamsRequired, total=False):
    """Supplier Discovery (`supplier-discovery`): Suppliers of a product from IndiaMART, Google Maps, Gelbe Seiten and
    ThomasNet, each with location, website and email.

    Only `products` is required; a key left out takes its default.
    """

    places: List[str]
    """Places: Towns or regions to find suppliers in on Google Maps and Gelbe Seiten, such as Cleveland, OH or
    Stuttgart. IndiaMART is searched across India whatever is given here. At most 5 items. Default: [].
    """
    sources: List[Literal["indiamart", "google_maps", "gelbeseiten", "thomasnet"]]
    """Directories: IndiaMART (India), Google Maps (anywhere, by place), Gelbe Seiten (Germany, by town) and ThomasNet
    (the profiles you give). Each one of "indiamart", "google_maps", "gelbeseiten", "thomasnet". At least 1 item.
    Default: ["indiamart", "google_maps"].
    """
    thomasnet_profiles: List[str]
    """ThomasNet profiles: The links or ids of ThomasNet supplier profiles you have shortlisted, read in full when
    ThomasNet is chosen. At most 50 items. Default: [].
    """
    per_search: int
    """Map listings per search: How many Google Maps listings are read for each product and place. From 5 to 60.
    Default: 20.
    """
    verified_only: bool
    """Only verified IndiaMART sellers: Keeps the IndiaMART sellers it shows as verified or holding its TrustSEAL.
    Default: False.
    """
    min_rating: float
    """Lowest rating: Leaves out suppliers rated lower by their buyers or reviewers. A supplier with no rating is kept.
    From 0 to 5. Default: 0.
    """
    exclude_companies: List[str]
    """Suppliers to leave out: Names, such as the suppliers you already buy from. At most 1000 items. Default: []."""
    exclude_domains: List[str]
    """Websites to leave out: Domains, such as acme.com, of the suppliers you already buy from. At most 1000 items.
    Default: [].
    """
    indiamart_details: bool
    """Read each IndiaMART product page: Adds the supplier's town and business type, such as manufacturer or exporter.
    One unit for each IndiaMART supplier. Default: True.
    """
    require_email: bool
    """Only suppliers with an email: Keeps the suppliers whose own website publishes an email address that passes the
    check. Default: False.
    """
    max_results: int
    """Most rows: The run stops at this many suppliers. From 1 to 1000. Default: 100."""


class _TalentSourcingParamsRequired(TypedDict):
    job_title: str
    """Job title: The role you are hiring for, as people would write it about themselves. Required."""
    location: str
    """Location: The city, region or country the people should be in. Write Remote for anywhere. Required."""


class TalentSourcingParams(_TalentSourcingParamsRequired, total=False):
    """Talent Sourcing (`talent-sourcing`): People who posted that they want to be hired, or show their work, in your
    role and place, scored on the skills you need.

    Only `job_title`, `location` are required; a key left out takes its default.
    """

    skills: List[str]
    """Skills: What the role asks for. They score each person, and pick the GitHub projects to look through. At most 10
    items. Default: [].
    """
    sources: List[Literal["hackernews", "github"]]
    """Where to look: GitHub finds only developers whose profile gives the place, and is searched only when skills are
    given. Each one of "hackernews", "github". At least 1 item. Default: ["hackernews"].
    """
    more_results: bool
    """Read more posts: Reads the newest 300 posts that name the place instead of 200, reaching further back. Default:
    False.
    """
    posted_within_days: int
    """Posted within (days): Only posts from the last this many days; an older post may no longer be true. From 7 to
    730. Default: 365.
    """
    github_profiles: int
    """GitHub profiles to read: How many developers' profiles to open, from the projects that use the skills. From 1 to
    50. Default: 15.
    """
    min_skills: int
    """Least skills named: Leave out a person who names fewer of the skills than this. From 0 to 10. Default: 0."""
    resurface_after_days: int
    """Show a person again after (days): For a saved formula, how long before a delivered person may come back. From 1
    to 365. Default: 90.
    """
    max_results: int
    """Most rows: The run stops at this many people, best first. From 1 to 500. Default: 50."""



class TenderAlertsParams(TypedDict, total=False):
    """Tender Alerts (`tender-alerts`): New public tenders that match your words and codes, from the EU, UK and US,
    with buyer, deadline, value and link.

    Every key is optional; a key left out takes its default.
    """

    keywords: List[str]
    """Words: What you sell, as a buyer would write it, such as cybersecurity or road resurfacing. Each is searched on
    its own. Leave empty to take every notice of the window, or to match on CPV codes alone. At most 10 items.
    Default: [].
    """
    sources: List[Literal["ted", "find_a_tender", "contracts_finder", "grants_gov", "new_york_city", "chicago", "ny_mta", "sam_gov"]]
    """Notice boards: TED (European Union), Find a Tender and Contracts Finder (United Kingdom), Grants.gov, New York
    City's City Record, Chicago's and the MTA's contracts (awards only), and SAM.gov, which is read where it is
    offered. Each one of "ted", "find_a_tender", "contracts_finder", "grants_gov", "new_york_city", "chicago",
    "ny_mta", "sam_gov". At least 1 item. Default: ["ted", "find_a_tender", "contracts_finder", "grants_gov",
    "new_york_city", "sam_gov"].
    """
    notice_types: List[Literal["planning", "tender", "award"]]
    """Notice stages: Pre-RFP notices (prior information, sources sought, presolicitation, forecasted grants and UK
    notices of planned procurements), open tenders, or awards. Each one of "planning", "tender", "award". At least 1
    item. Default: ["tender"].
    """
    published_within_days: int
    """Published within (days): Only notices published in the last this many days, today included. Run daily, 3 covers
    a weekend. From 1 to 30. Default: 3.
    """
    cpv_codes: List[str]
    """CPV codes: Eight-digit CPV codes, such as 72000000 for IT services. TED is searched by them; a UK notice is kept
    when its main code is one of them. A notice matching your words or your codes is kept. At most 10 items.
    Default: [].
    """
    countries: List[str]
    """Buyers' countries: Three-letter codes, such as DEU, FRA, GBR or USA. Leave empty for every country of the boards
    you chose. At most 30 items. Default: [].
    """
    naics_codes: List[str]
    """NAICS codes (SAM.gov): Only SAM.gov notices in these industry codes, 2 to 6 digits, such as 541512. At most 10
    items. Default: [].
    """
    set_asides: List[str]
    """Set-asides (SAM.gov): Only SAM.gov notices set aside for these, by SAM.gov's codes, such as SBA, 8A, HZC,
    SDVOSBC or WOSB. At most 10 items. Default: [].
    """
    us_states: List[str]
    """Places of performance (SAM.gov): Only SAM.gov notices for work in these US states, as two letters. At most 10
    items. Default: [].
    """
    min_days_left: int
    """At least this many days to respond: Leaves out notices due sooner. A notice past its deadline is always left
    out; one that states no deadline is kept. From 0 to 365. Default: 0.
    """
    due_within_days: int
    """Due within (days): Only notices due within this many days. 0 keeps every deadline, and notices that state none.
    From 0 to 730. Default: 0.
    """
    exclude_words: List[str]
    """Leave out titles with: Notices whose title holds one of these words are left out, such as cleaning or catering.
    At most 30 items. Default: [].
    """
    grant_details: bool
    """Read each grant in full: Adds a Grants.gov opportunity's funding, largest award, eligibility and description.
    One more unit for each grant. Default: True.
    """
    max_results: int
    """Most rows: The run stops at this many notices, best matches first. From 1 to 2000. Default: 200."""


class _TenderChangeWatchParamsRequired(TypedDict):
    watch: List[str]
    """Notices to watch: A Grants.gov opportunity's id or link, a USAspending.gov award's id or link, or a UK
    procurement's Open Contracting id (ocds-…, shown on its Find a Tender or Contracts Finder notice). Anything else
    is left out. 1 to 150 items. Required.
    """


class TenderChangeWatchParams(_TenderChangeWatchParamsRequired, total=False):
    """Tender Change Watch (`tender-change-watch`): The tenders, grants and awards you watch, read again each run, with
    a row only when a deadline, status or value changed.

    Only `watch` is required; a key left out takes its default.
    """

    uk_days: int
    """UK notices read (days): For UK procurements, how many days of new notices are read for their updates. Run daily,
    3 is enough. From 1 to 30. Default: 7.
    """
    max_results: int
    """Most rows: The run stops at this many changed notices. From 1 to 1000. Default: 200."""


class _UnlinkedMentionsParamsRequired(TypedDict):
    brand: str
    """Brand name: The name as people write it. A name that is also a common word finds pages using the word as well.
    Required.
    """
    brand_domain: str
    """Your domain: The domain a link should lead to, such as example.com. Pages on it are left out. Required."""


class UnlinkedMentionsParams(_UnlinkedMentionsParamsRequired, total=False):
    """Unlinked Mentions (`unlinked-mentions`): Pages that name your brand but do not link to your site, each read to
    be sure, with the email the site publishes.

    Only `brand`, `brand_domain` are required; a key left out takes its default.
    """

    search_terms: List[str]
    """Searches: Words searched with the name, each its own search; an empty one searches the name alone. 1 to 10
    items. Default: ["", "review", "alternatives", "pricing", "integration"].
    """
    include_news: bool
    """Include news stories: Also reads the stories the news search lists for the name. Default: True."""
    other_domains: List[str]
    """Your other domains: Other domains of yours; a link to any of them counts as a link, and pages on them are left
    out. At most 20 items. Default: [].
    """
    pages_to_read: int
    """Pages to read: How many of the pages found are read, news first, then the best placed in search. From 5 to 150.
    Default: 40.
    """
    search_pages: int
    """Results pages per search: How many pages of results to read for each search, about ten results a page. From 1 to
    3. Default: 1.
    """
    exclude_domains: List[str]
    """Sites to leave out: Domains never shown, such as social networks and review sites where no editor adds links. At
    most 2000 items. Default: a list of 22 values, which `get` on the formula shows.
    """
    country: str
    """Search country: The two-letter country whose search results are read, such as us, gb or de. Default: "us"."""
    language: str
    """Search language: The language of the results, such as en or de. Default: "en"."""
    require_email: bool
    """Only sites with an email: Keeps the pages whose site publishes an email address that passes the check. Default:
    False.
    """
    resurface_after_days: int
    """Show a page again after (days): For a saved formula, how long before a delivered page may come back. From 1 to
    365. Default: 180.
    """
    max_results: int
    """Most rows: The run stops at this many pages, news and pages naming the brand in their title first. From 1 to
    1000. Default: 100.
    """


class _UsedCarArbitrageParamsRequired(TypedDict):
    make: str
    """Make: The make, such as Toyota or Ford. Required."""
    models: List[str]
    """Models: The models of that make, named as Copart names them, such as Camry or RAV4. 1 to 10 items. Required."""
    zip: str
    """Your ZIP code: Where you would sell the cars. Retail comparables are the listings around it. Required."""


class UsedCarArbitrageParams(_UsedCarArbitrageParamsRequired, total=False):
    """Used-Car Arbitrage (`used-car-arbitrage`): Copart lots selling well below what the same make, model and year
    fetch at retail near you, ranked by the spread, with bid moves.

    Only `make`, `models`, `zip` are required; a key left out takes its default.
    """

    years: IntRange
    """Model years: The model years to search. Each year of each model is one search for retail comparables. Default:
    {"min": 2018, "max": 2022}.
    """
    watch_lots: List[str]
    """Lots to watch: Copart lot numbers or lot pages you follow, read on every run whether or not a search finds them.
    At most 50 items. Default: [].
    """
    states: List[str]
    """Yard states: Two-letter codes of the states whose yards you buy from, such as TX. Leave empty for all. At most
    60 items. Default: [].
    """
    max_odometer: int
    """Most miles: Lots with more miles on the odometer are left out. 0 for any mileage. From 0 to 500000. Default: 0.
    """
    exclude_titles: List[str]
    """Leave out titles: Words of the titles to leave out. By default the cars that can never be titled for the road
    again, which no retail price fits. At most 20 items. Default: ["NON-REPAIRABLE", "DESTRUCTION", "SCRAP", "JUNK",
    "PARTS ONLY"].
    """
    clean_title_only: bool
    """Clean titles only: Leaves out salvage and other branded titles. Default: False."""
    runs_and_drives_only: bool
    """Runs and drives only: Keeps the lots Copart marks as running and driving. Default: False."""
    exclude_damage: List[str]
    """Leave out damage: Words of the main damage to leave out, such as FLOOD, BURN or ALL OVER. At most 20 items.
    Default: [].
    """
    min_bid: int
    """Least current bid ($): Leaves out lots whose bidding has barely begun, whose spread on a first small bid says
    little. A lot with a buy-it-now price is kept. 0 keeps every lot. From 0 to 100000. Default: 1000.
    """
    serious_bid_pct: int
    """A bid that counts (% of retail): A lot whose current bid is under this share of its retail median ranks after
    the others, since bidding usually goes well past it. A buy-it-now price always counts. From 0 to 90. Default:
    25.
    """
    include_sale_day: bool
    """Include lots selling today: Lots whose sale is on the day of the run, which may be over when the rows arrive.
    Days are whole calendar days (UTC). A lot you watch is kept on its sale day. Default: False.
    """
    lots_per_model: Literal[20, 50, 100]
    """Lots read per model: How many of Copart's lots to read for each model, the soonest sales first. One of 20, 50,
    100. Default: 100.
    """
    min_spread: int
    """Least spread ($): Lots whose retail median is less than this above their price are left out. From 0 to 100000.
    Default: 2000.
    """
    comp_sources: List[Literal["cargurus", "autotrader"]]
    """Retail comparables from: The sites whose dealer listings price each lot. A car listed on both counts once. Each
    one of "cargurus", "autotrader". At least 1 item. Default: ["cargurus", "autotrader"].
    """
    radius: Literal[25, 50, 75, 100, 200, 500]
    """Comparables within (miles): How far from your ZIP code a retail listing may be. One of 25, 50, 75, 100, 200,
    500. Default: 100.
    """
    mileage_band: int
    """Similar mileage (miles either way): Comparables within this many miles of the lot's odometer are preferred. 0
    compares every mileage. From 0 to 100000. Default: 30000.
    """
    any_mileage_fallback: bool
    """Price on any mileage when few are similar: When too few comparables have a similar mileage, price the lot on
    every mileage instead of leaving it out. A lot with far more miles than most listings then looks better than it
    is. Default: False.
    """
    min_comps: int
    """Least comparables: A lot priced on fewer retail listings than this is left out. From 1 to 20. Default: 3."""
    comp_searches: int
    """Comparables searches: The most retail searches for each site, one for each make, model and year found. From 1 to
    100. Default: 40.
    """
    max_results: int
    """Most rows: The run stops at this many lots, widest spread first. From 1 to 2000. Default: 200."""



class VcDealSourcingParams(TypedDict, total=False):
    """VC Deal Sourcing (`vc-deal-sourcing`): Young startups gaining traction on GitHub, Hacker News and Y Combinator,
    one row each with its signals and website.

    Every key is optional; a key left out takes its default.
    """

    topics: List[str]
    """Topics: What you invest in, as words a startup would describe itself with (agents, database, robotics). Leave
    empty for everything. At most 10 items. Default: [].
    """
    within_days: int
    """Within the last (days): How new a repository, a Show HN or a Y Combinator launch may be. From 1 to 90. Default:
    30.
    """
    sources: List[Literal["github", "hacker_news", "ycombinator"]]
    """Where to look: GitHub's new and trending repositories, Show HN on Hacker News, and Y Combinator's directory.
    Each one of "github", "hacker_news", "ycombinator". At least 1 item. Default: ["github", "hacker_news",
    "ycombinator"].
    """
    min_stars: int
    """Fewest GitHub stars: A repository with fewer stars is left out. From 0 to 100000. Default: 200."""
    min_hn_points: int
    """Fewest Show HN points: A Show HN with fewer points is left out. From 0 to 10000. Default: 50."""
    exclude: List[str]
    """Leave out: GitHub accounts, domains or company names to leave out; by default, large companies whose
    repositories trend. At most 1000 items. Default: a list of 47 values, which `get` on the formula shows.
    """
    results_per_search: int
    """Results read per search: How many repositories, Show HN posts and Y Combinator companies to read for each topic.
    From 5 to 100. Default: 30.
    """
    max_results: int
    """Most rows: The run stops at this many startups, strongest signals first. From 1 to 2000. Default: 200."""


class _WebRankTrackerParamsRequired(TypedDict):
    domains: List[str]
    """Websites: The domains to follow, such as etsy.com. 1 to 30 items. Required."""


class WebRankTrackerParams(_WebRankTrackerParamsRequired, total=False):
    """Web Rank Tracker (`web-rank-tracker`): Where the websites you follow rank in Similarweb's most-visited rankings,
    by country and category, and how they moved since last run.

    Only `domains` is required; a key left out takes its default.
    """

    countries: List[Literal["worldwide", "US", "GB", "DE", "FR", "CA", "AU", "JP", "IN", "BR", "MX", "IT", "ES", "NL", "SE", "CH", "KR", "SG", "AE", "SA", "ZA", "TR", "PL", "ID", "PH", "TH", "VN", "IL", "IE", "NZ"]]
    """Countries: The countries whose rankings to read, or worldwide. Each one of "worldwide", "US", "GB", "DE", "FR",
    "CA", "AU", "JP", "IN", "BR", "MX", "IT", "ES", "NL", "SE", "CH", "KR", "SG", "AE", "SA", "ZA", "TR", "PL",
    "ID", "PH", "TH", "VN", "IL", "IE", "NZ". 1 to 4 items. Default: ["US"].
    """
    categories: List[Literal["all", "ai-chatbots-and-tools", "arts-and-entertainment", "business-and-consumer-services", "community-and-society", "computers-electronics-and-technology", "crypto-and-blockchain", "e-commerce-and-shopping", "finance", "food-and-drink", "gambling", "games", "health", "heavy-industry-and-engineering", "hobbies-and-leisure", "home-and-garden", "jobs-and-career", "law-and-government", "lifestyle", "news-and-media", "pets-and-animals", "reference-materials", "science-and-education", "sports", "travel-and-tourism", "vehicles"]]
    """Categories: The rankings to read in each country. All is the ranking of every category together, 50 places deep;
    a category's ranking shows 50 places worldwide and 5 in one country. Each one of "all", "ai-chatbots-and-tools",
    "arts-and-entertainment", "business-and-consumer-services", "community-and-society",
    "computers-electronics-and-technology", "crypto-and-blockchain", "e-commerce-and-shopping", "finance",
    "food-and-drink", "gambling", "games", "health", "heavy-industry-and-engineering", "hobbies-and-leisure",
    "home-and-garden", "jobs-and-career", "law-and-government", "lifestyle", "news-and-media", "pets-and-animals",
    "reference-materials", "science-and-education", "sports", "travel-and-tourism", "vehicles". 1 to 4 items.
    Default: ["all"].
    """
    max_results: int
    """Most rows: The run stops at this many rows, the biggest moves first. From 1 to 500. Default: 500."""


class _WholesaleCatalogCheckParamsRequired(TypedDict):
    catalog: List[Dict[str, Any]]
    """Supplier catalogue: One line a product, from the supplier's sheet - its UPC or EAN (code), your cost, the name,
    and the case pack when the cost is for a case. 1 to 500 items. Required.
    """


class WholesaleCatalogCheckParams(_WholesaleCatalogCheckParamsRequired, total=False):
    """Wholesale Catalogue Check (`wholesale-catalog-check`): Your supplier's price list checked against Amazon line by
    line, with Amazon's price, reviews and your margin after fees.

    Only `catalog` is required; a key left out takes its default.
    """

    marketplace: Literal["us", "uk", "de", "it", "es", "ca"]
    """Amazon marketplace: Where you sell. One of "us", "uk", "de", "it", "es", "ca". Default: "us"."""
    cost_currency: Literal["USD", "GBP", "EUR", "CAD"]
    """Currency of your costs: Costs are compared only with Amazon prices in this currency. One of "USD", "GBP", "EUR",
    "CAD". Default: "USD".
    """
    min_roi_pct: float
    """Least return on cost (%): Lines below this are left out. 0 keeps every line that makes money; -100 keeps every
    line found. From -100 to 1000. Default: 0.
    """
    referral_fee_pct: float
    """Amazon referral fee (%): The share of the sale price Amazon keeps. From 0 to 50. Default: 15."""
    fulfilment_cost: float
    """Fulfilment and shipping a unit: Your FBA fee, prep and inbound shipping for one unit, in the currency of your
    costs. From 0 to 100. Default: 4.
    """
    check_offer: bool
    """Read each listing's page: Its Buy Box price, whether Amazon sells it, and stock. One page a line found. Default:
    True.
    """
    max_results: int
    """Most rows: The run stops at this many lines, best return first. From 1 to 500. Default: 500."""
