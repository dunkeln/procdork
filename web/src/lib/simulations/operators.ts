export type ProcurementOperator = {
	id: string;
	name: string;
	company: string;
	profile: string;
	intent: string;
	prompt: string;
};

export const procurementOperators: ProcurementOperator[] = [
	{
		id: 'wade-backup-sourcing',
		name: 'Wade',
		company: 'Northline Foods',
		profile: 'CPG ops lead, backup-source biased, low tolerance for vague availability.',
		intent: 'Find a qualified US backup supplier with lead-time evidence.',
		prompt:
			'Act as Wade from Northline Foods. We need a backup US supplier for USP-grade citric acid because our primary source is constrained. Find independent distributors, prioritize listed bulk lead times and qualification evidence, compare against a 5-day internal baseline, and call out what still needs official confirmation.'
	},
	{
		id: 'clark-certification-sourcing',
		name: 'Clark',
		company: 'Harbor CPG',
		profile: 'Procurement manager for regulated ingredients, certification-first.',
		intent: 'Source suppliers with document-backed quality signals.',
		prompt:
			'Act as Clark from Harbor CPG. We are sourcing xanthan gum for a regulated product line. Find US distributors with public quality documents or certification signals such as SDS, COA, spec sheet, kosher, halal, or allergen documentation. Summarize supplier fit, evidence freshness, and gaps.'
	},
	{
		id: 'miles-cost-sourcing',
		name: 'Miles',
		company: 'Ridgeline Snacks',
		profile: 'Cost-sensitive buyer, cares about MOQ, packaging, freight practicality.',
		intent: 'Compare practical purchase options for bulk ingredient sourcing.',
		prompt:
			'Act as Miles from Ridgeline Snacks. We need bulk sodium citrate options from US suppliers. Look for published MOQ, packaging, price breaks, lead time, and distributor contact paths. Compare practical buying friction and recommend the lowest-risk next outreach.'
	}
];
