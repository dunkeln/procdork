import { z } from 'zod';

export const artifactTypeSchema = z.enum([
	'web-page',
	'email-thread',
	'quote',
	'price-list',
	'coa',
	'sds',
	'spec-sheet',
	'certificate',
	'supplier-questionnaire',
	'other'
]).describe('Normalized kebab-case source artifact kind. Use other only when no listed kind fits.');

export const supplierTypeSchema = z
	.enum(['manufacturer', 'distributor', 'broker', 'unknown', 'other'])
	.describe('Normalized supplier role. Use unknown when evidence is missing and other when evidence names a different role.');

export const documentTypeSchema = z
	.enum(['coa', 'sds', 'spec-sheet', 'certificate', 'other'])
	.describe('Normalized kebab-case document kind available from the supplier evidence.');

export const sourceRefSchema = z
	.object({
		source_id: z.string().min(1).describe('Stable source identifier from the search, fetch, or ingestion system.'),
		artifact_type: artifactTypeSchema,
		title: z.string().min(1).describe('Human-readable source title.'),
		retrieved_at: z.iso.datetime().describe('ISO-8601 UTC datetime when this source was retrieved or ingested. Used to judge evidence freshness.'),
		url: z.string().optional().describe('Public URL when the source is web-backed.'),
		page: z.number().optional().describe('Page number for PDF or document evidence.'),
		row: z.number().optional().describe('Row number for spreadsheet or tabular evidence.'),
		text_span: z.string().optional().describe('Short quoted or paraphrased span supporting the extracted claim.')
	})
	.describe('Pointer to the exact evidence supporting a claim.')
	.strict();

export const supplierCandidateSchema = z
	.object({
		supplier_name: z.string().min(1).describe('Canonical supplier name as supported by the evidence.'),
		supplier_type: supplierTypeSchema.optional(),
		product_name: z.string().min(1).describe('Supplier-listed product or material name.'),
		grade: z.string().nullable().optional().describe('Grade or specification, such as USP, FCC, organic, or non-GMO.'),
		moq: z.string().nullable().optional().describe('Minimum order quantity exactly as represented by evidence, or null if not listed.'),
		lead_time_days: z.number().nullable().optional().describe('Normalized lead time in days when evidence supports a numeric value.'),
		lead_time_text: z.string().nullable().optional().describe('Original lead-time wording, or null if not listed.'),
		price: z.string().nullable().optional().describe('Price or pricing tier exactly as represented by evidence, or null if not listed.'),
		incoterms: z.string().nullable().optional().describe('Freight or commercial terms such as FOB, DDP, CIF, EXW, or null if not listed.'),
		certifications: z.array(z.string()).optional().describe('Certifications explicitly supported by evidence.'),
		documents_available: z.array(documentTypeSchema).optional(),
		missing_fields: z.array(z.string()).describe('Requested fields that were not supported by evidence.'),
		sources: z.array(sourceRefSchema).describe('Evidence references supporting this candidate.')
	})
	.describe('One supplier option extracted from web or private supplier evidence.')
	.strict();

export const supplierComparisonSchema = z
	.object({
		request: z
			.object({
				material: z.string().min(1).describe('Requested material or ingredient.'),
				grade: z.string().optional().describe('Requested grade or specification.'),
				quantity: z.string().optional().describe('Requested purchase quantity.'),
				baseline_lead_time_days: z.number().optional().describe('Buyer baseline lead time in days for comparison.')
			})
			.describe('Buyer request normalized from the prompt.')
			.strict(),
		candidates: z.array(supplierCandidateSchema).min(1).describe('Supplier candidates found in evidence.'),
		recommendation: z
			.object({
				supplier_name: z.string().min(1).describe('Recommended supplier from the candidate set.'),
				reason: z.string().min(1).describe('Evidence-backed recommendation rationale.'),
				risks: z.array(z.string()).describe('Known risks, gaps, or unknowns that should be verified.'),
				sources: z.array(sourceRefSchema).describe('Evidence references supporting the recommendation.')
			})
			.describe('Best available supplier choice and caveats.')
			.strict()
	})
	.describe('Structured supplier comparison for a sourcing request.')
	.strict();

export type ArtifactType = z.infer<typeof artifactTypeSchema>;
export type SourceRef = z.infer<typeof sourceRefSchema>;
export type SupplierCandidate = z.infer<typeof supplierCandidateSchema>;
export type SupplierComparison = z.infer<typeof supplierComparisonSchema>;

export const supplierComparisonJsonSchema = {
	...z.toJSONSchema(supplierComparisonSchema),
	$id: 'https://procdork.local/contracts/supplier-comparison.schema.json',
	title: 'SupplierComparison'
};
