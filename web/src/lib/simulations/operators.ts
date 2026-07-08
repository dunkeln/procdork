export type ProcurementOperator = {
	id: string;
	name: string;
	company: string;
	profile: string;
	intent: string;
	openingMessage: string;
	requirements: {
		id: string;
		description: string;
		doneWhen: string;
	}[];
};

export const procurementOperators: ProcurementOperator[] = [
	{
		id: 'wade-backup-sourcing',
		name: 'John Doe',
		company: 'Northline Foods',
		profile: 'CPG ops lead, backup-source biased, low tolerance for vague availability.',
		intent: 'Backup-source qualification with lead-time pressure.',
		openingMessage:
			'We need a backup US supplier for USP-grade citric acid because our primary source is constrained. Start by finding independent distributors with public evidence for grade, packaging, and availability. Compare anything you find against our 5-day internal lead-time baseline.',
		requirements: [
			{
				id: 'independent-us-distributors',
				description: 'Find independent US distributor candidates, not marketplaces or manufacturers only.',
				doneWhen: 'At least two candidates are identified with source-backed distributor evidence.'
			},
			{
				id: 'grade-and-packaging',
				description: 'Confirm USP or USP/FCC citric acid fit and practical bulk packaging signals.',
				doneWhen: 'Each leading candidate has grade and packaging marked as found, not found, or not listed.'
			},
			{
				id: 'lead-time-baseline',
				description: 'Compare public lead-time or availability evidence against a 5-day baseline.',
				doneWhen: 'Lead time is either source-backed or explicitly marked as requiring official quote confirmation.'
			},
			{
				id: 'quote-path',
				description: 'Identify the best quote/contact path for 15,000 kg.',
				doneWhen: 'One preferred supplier has a concrete sales, RFQ, or inquiry path and open questions listed.'
			}
		]
	},
	{
		id: 'clark-certification-sourcing',
		name: 'Jane Doe',
		company: 'Harbor CPG',
		profile: 'Procurement manager for regulated ingredients, certification-first.',
		intent: 'Regulated-ingredient sourcing with document gates.',
		openingMessage:
			'I am sourcing xanthan gum for a regulated product line. Find US distributors with public quality-document signals: SDS, COA, spec sheet, kosher, halal, allergen, or equivalent documentation. I need evidence freshness where possible.',
		requirements: [
			{
				id: 'quality-documents',
				description: 'Find public SDS, COA, spec sheet, kosher, halal, allergen, or equivalent quality signals.',
				doneWhen: 'Candidates have document evidence or clear document gaps, with retrieval freshness when available.'
			},
			{
				id: 'regulated-fit',
				description: 'Assess likely food or regulated-product suitability without inventing unsupported certifications.',
				doneWhen: 'Each leading supplier has fit stated as supported, uncertain, or not found.'
			},
			{
				id: 'us-distribution',
				description: 'Prefer US distributor paths over generic global manufacturer pages.',
				doneWhen: 'A US distribution/contact path is found or the lack of one is explicit.'
			},
			{
				id: 'qualification-gaps',
				description: 'Name what must be confirmed before supplier qualification.',
				doneWhen: 'The final candidate list includes missing documents or claims to request.'
			}
		]
	},
	{
		id: 'miles-cost-sourcing',
		name: 'Just Bob',
		company: 'Ridgeline Snacks',
		profile: 'Cost-sensitive buyer, cares about MOQ, packaging, freight practicality.',
		intent: 'Cost-and-friction sourcing for bulk buys.',
		openingMessage:
			'We need bulk sodium citrate options from US suppliers. Start with distributors that publish at least one practical buying signal: MOQ, packaging, price breaks, lead time, or a clear RFQ path.',
		requirements: [
			{
				id: 'buying-signals',
				description: 'Find suppliers with MOQ, packaging, price break, lead-time, or RFQ-path evidence.',
				doneWhen: 'At least three options are compared or the search explains why fewer credible options surfaced.'
			},
			{
				id: 'cost-friction',
				description: 'Compare pricing visibility, quote requirement, MOQ friction, and packaging fit.',
				doneWhen: 'Each candidate has practical buying friction summarized without hiding unknowns.'
			},
			{
				id: 'freight-practicality',
				description: 'Consider whether packaging and supplier path make sense for bulk snack ingredient sourcing.',
				doneWhen: 'Freight or packaging practicality is stated as good, uncertain, or poor for leading options.'
			},
			{
				id: 'next-outreach',
				description: 'Recommend the lowest-risk outreach plus backups.',
				doneWhen: 'One primary option and two backups are named with what to confirm next.'
			}
		]
	}
];
