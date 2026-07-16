<svelte:head>
	<title>Cost forecast | procdork docs</title>
	<meta
		name="description"
		content="Standalone and reused-infra bill ranges for proving the harness before scaling platform spend."
	/>
</svelte:head>

<h1>Cost forecast</h1>

<blockquote><p><strong>Note:</strong> Prices are estimated from public pricing pages.</p></blockquote>

<p>
	The cost idea is simple. Keep the first bill small while the workflow is still being proven. The
	agent can use the harness without being locked to one data vendor, and the app stays as one small
	deployed service instead of several separate platform pieces.
</p>

<p>
	Assuming 1-3 maintainers, the standalone deployment is one AWS ALB, one AWS Fargate service, and
	MotherDuck for hosted analytics:
</p>

<ul>
	<li>Realistic range is in a $45-$110/month pricing envelope.</li>
	<li>Stress range sits at $100-$200/month.</li>
</ul>

<h2>Deeper Breakdown</h2>

<table>
	<thead>
		<tr>
			<th>Cost surface</th>
			<th>What it pays for</th>
			<th>Realistic range</th>
			<th>Stress range</th>
			<th>When it moves</th>
		</tr>
	</thead>
	<tbody>
		<tr>
			<td>AWS ALB</td>
			<td>The public front door for the service</td>
			<td>$20-$35/month</td>
			<td>$35-$60/month</td>
			<td>More visitors, requests, or data moving through the door.</td>
		</tr>
		<tr>
			<td>AWS Fargate</td>
			<td>The small always-on server running the harness</td>
			<td>$20-$55/month</td>
			<td>$50-$100/month</td>
			<td>A bigger server, more copies of the server, or longer worker jobs.</td>
		</tr>
		<tr>
			<td>MotherDuck Lite + Pulse</td>
			<td>The hosted database and query engine</td>
			<td>$4-$20/month</td>
			<td>$20-$50/month</td>
			<td>More stored data or more query time.</td>
		</tr>
		<tr>
			<td>Existing Claude/Codex subscriptions</td>
			<td><strong>The operator's AI assistant</strong></td>
			<td><strong>$0 incremental</strong></td>
			<td><strong>$0 incremental</strong></td>
			<td><strong>Already paid outside this project bill.</strong></td>
		</tr>
	</tbody>
</table>

<p>Readable total:</p>

<table>
	<thead>
		<tr>
			<th>Scenario</th>
			<th>Monthly project bill</th>
		</tr>
	</thead>
	<tbody>
		<tr><td>Realistic deployment</td><td>$45-$110/month</td></tr>
		<tr><td>Reusing an existing ALB</td><td>$25-$75/month</td></tr>
		<tr><td>Stress range for heavier use</td><td>$100-$200/month</td></tr>
	</tbody>
</table>

<p>
	If Waystation already has an application load balancer for internal web services, Procdork can
	likely reuse it with a separate listener rule or target group. That makes the incremental AWS bill
	mostly Fargate, as long as the existing ALB is not near its routing, TLS, security, or traffic
	limits.
</p>

<p>
	The realistic case assumes MotherDuck Lite fits the project limits: 1-3 internal maintainers, up
	to 2 service accounts, MCP included, and bursty Pulse query compute. Business pricing is an
	organizational upgrade path, not the default technical requirement.
</p>

<h2>Comparisons</h2>

<p>
	The comparison below is not vendor bashing. It asks the procurement-style question: how much do we
	have to buy before we know the workflow is worth scaling?
</p>

<p>
	Assumed workload: roughly 100 GB of analytical data, a few operators, scheduled refreshes,
	MCP/agent queries, and AI-assisted analysis.
</p>

<table>
	<thead>
		<tr>
			<th>Stack shape</th>
			<th>What sends the bill up</th>
			<th>Conservative monthly range</th>
			<th>Notes</th>
		</tr>
	</thead>
	<tbody>
		<tr>
			<td>Agent Harness</td>
			<td>AWS ALB, Fargate, MotherDuck Lite storage, Pulse compute</td>
			<td>$45-$110 realistic; $25-$75 if reusing an existing ALB; $100-$200 stress</td>
			<td>
				Smallest standalone shape for this project.
				<strong>Existing Claude/Codex subscriptions are not counted as project infra.</strong>
			</td>
		</tr>
		<tr>
			<td>Snowflake-centered stack</td>
			<td>Extraction service, Snowflake storage, warehouse credits, serverless/AI features</td>
			<td>$500-$2,000+</td>
			<td>Storage is not the hard part. Credits, refresh cadence, AI features, and ingestion volume drive the bill.</td>
		</tr>
		<tr>
			<td>Databricks-centered stack</td>
			<td>Extraction service, DBUs, cloud infra/serverless compute, SQL/AI features</td>
			<td>$500-$2,500+</td>
			<td>Forecast depends on jobs, SQL, serverless usage, and cloud runtime choices.</td>
		</tr>
		<tr>
			<td>Extraction-heavy managed ELT</td>
			<td>Fivetran active rows or Airbyte credits/capacity, plus destination compute</td>
			<td>$100-$500+ before warehouse/lakehouse compute</td>
			<td>Useful when connector management is the problem. Less compelling for one narrow operator loop.</td>
		</tr>
	</tbody>
</table>

<table>
	<thead>
		<tr>
			<th>Question</th>
			<th>Agent Harness answer</th>
			<th>Managed platform answer</th>
		</tr>
	</thead>
	<tbody>
		<tr>
			<td>What is the first real bill?</td>
			<td>A small service plus database query time.</td>
			<td>A full platform around ingestion, storage, compute, governance, and AI.</td>
		</tr>
		<tr>
			<td>What grows first?</td>
			<td>Server size, traffic, and MotherDuck query hours.</td>
			<td>Connector volume, warehouse/DBU compute, serverless features, and AI feature usage.</td>
		</tr>
		<tr>
			<td>What is the risk?</td>
			<td>The small harness may need to grow later.</td>
			<td>The team may buy too much platform before the workflow is proven.</td>
		</tr>
		<tr>
			<td>Best default</td>
			<td>Prove the loop cheaply.</td>
			<td>Graduate once usage, concurrency, and governance needs are stable.</td>
		</tr>
	</tbody>
</table>

<p>Pricing anchors used for the forecast:</p>

<ul>
	<li>Snowflake public pricing is credit-based and varies by edition and commitment.</li>
	<li>Databricks uses DBU-based pricing by workload and cloud.</li>
	<li>Fivetran prices around monthly active rows, with a free tier for small connections.</li>
	<li>Airbyte Cloud starts with a low monthly floor and credit-based usage.</li>
</ul>

<p>
	The defensible claim is narrow. Waystation keeps the first version below a bigger multi-service
	platform bill while it proves which procurement intelligence surfaces deserve heavier investment.
	This is possible because the harness design is vendor neutral.
</p>
