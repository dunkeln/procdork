import { z } from 'zod';
import { artifactTypeSchema, sourceRefSchema } from './supplier-comparison';

export const confidenceSchema = z
	.enum(['high', 'medium', 'low', 'unknown', 'other'])
	.describe('Normalized confidence label. Use other only when the source names a different confidence class.');

export const extractionMethodSchema = z
	.enum(['web-search', 'web-fetch', 'document-ingestion', 'email-ingestion', 'manual-review', 'other'])
	.describe('Normalized kebab-case method that produced the observation or claim.');

export const observedSupplierSchema = z
	.object({
		observed_supplier_id: z.string().min(1).describe('Stable ID for this exact observed supplier mention.'),
		name: z.string().min(1).describe('Supplier name exactly as represented by the source.'),
		source: sourceRefSchema,
		extraction_method: extractionMethodSchema,
		confidence: confidenceSchema
	})
	.describe('A supplier mention exactly as one source presents it.')
	.strict();

export const canonicalSupplierSchema = z
	.object({
		canonical_supplier_id: z.string().min(1).describe('Stable ID for the normalized supplier entity.'),
		name: z.string().min(1).describe('Current best normalized supplier name.'),
		observed_supplier_ids: z
			.array(z.string().min(1))
			.describe('Observed supplier mentions currently mapped to this canonical supplier.'),
		confidence: confidenceSchema,
		updated_at: z.iso.datetime().describe('ISO-8601 UTC datetime when this canonical record was last updated.')
	})
	.describe('Current best normalized supplier entity assembled from one or more observed mentions.')
	.strict();

export const sourceClaimSchema = z
	.object({
		claim_id: z.string().min(1).describe('Stable ID for this extracted claim.'),
		canonical_supplier_id: z.string().min(1).optional(),
		observed_supplier_id: z.string().min(1).optional(),
		field: z.string().min(1).describe('Normalized kebab-case field name, such as moq or lead-time-days.'),
		value: z.unknown().describe('Extracted value. Keep original text when normalization is unsupported.'),
		source: sourceRefSchema,
		extraction_method: extractionMethodSchema,
		confidence: confidenceSchema,
		retrieved_at: z.iso.datetime().describe('ISO-8601 UTC datetime when the source was retrieved or ingested.')
	})
	.describe('One evidence-backed supplier fact. Do not overwrite conflicting facts with this shape.')
	.strict();

export const supplierConflictSchema = z
	.object({
		conflict_id: z.string().min(1).describe('Stable ID for the conflict.'),
		canonical_supplier_id: z.string().min(1).optional(),
		field: z.string().min(1).describe('Claim field with disagreement.'),
		claim_ids: z.array(z.string().min(1)).min(2).describe('Claims that disagree.'),
		status: z.enum(['open', 'resolved', 'other']).describe('Conflict review state.'),
		note: z.string().optional().describe('Short reason when the conflict is resolved or deprioritized.')
	})
	.describe('A disagreement between claims that should not be silently collapsed.')
	.strict();

export const documentIngestionRequestSchema = z
	.object({
		source_id: z.string().min(1).describe('Stable source identifier from web search, fetch, upload, or email ingestion.'),
		artifact_type: artifactTypeSchema,
		url: z.string().optional().describe('Public URL when the document is web-backed.'),
		mime_hint: z.string().optional().describe('MIME type or extension hint, such as application/pdf.'),
		title: z.string().min(1).describe('Human-readable document title.'),
		retrieved_at: z.iso.datetime().describe('ISO-8601 UTC datetime when the document pointer was retrieved.'),
		reason: z.string().optional().describe('Why this artifact should be read by the ingestion service.')
	})
	.describe('Handoff request for a document/email ingestion service. The web app creates pointers, not parsed document facts.')
	.strict();

export type Confidence = z.infer<typeof confidenceSchema>;
export type ExtractionMethod = z.infer<typeof extractionMethodSchema>;
export type ObservedSupplier = z.infer<typeof observedSupplierSchema>;
export type CanonicalSupplier = z.infer<typeof canonicalSupplierSchema>;
export type SourceClaim = z.infer<typeof sourceClaimSchema>;
export type SupplierConflict = z.infer<typeof supplierConflictSchema>;
export type DocumentIngestionRequest = z.infer<typeof documentIngestionRequestSchema>;

export const supplierEntityJsonSchema = {
	$id: 'https://procdork.local/contracts/supplier-entity.schema.json',
	title: 'SupplierEntity',
	$defs: {
		ObservedSupplier: z.toJSONSchema(observedSupplierSchema),
		CanonicalSupplier: z.toJSONSchema(canonicalSupplierSchema),
		SourceClaim: z.toJSONSchema(sourceClaimSchema),
		SupplierConflict: z.toJSONSchema(supplierConflictSchema),
		DocumentIngestionRequest: z.toJSONSchema(documentIngestionRequestSchema)
	}
};
