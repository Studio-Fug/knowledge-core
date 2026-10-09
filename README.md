# knowledge-core

A catalog of engineering Knowledge imports, analogous to nixpkgs: entries describe where to obtain objects; a cache holds the objects themselves. The Knowledge implementation remains in [Studio-Fug/knowledge](https://github.com/Studio-Fug/knowledge). Parts and their requirements, design files, validation evidence and signed artifacts remain in their own project repositories.

Each entry imports a GitHub `owner/repository` at a full commit revision. The project's root `knowledge.json` identifies its signed artifact by repository-relative path, SHA-256 byte hash and Knowledge address. The catalog does not copy part artifacts or generate verification claims. Updating a pin is an explicit reviewable catalog change.

## Derive a cache

Install Python 3.10+ and the Knowledge CLI, then run:

```sh
python3 reconcile.py --cache .knowledge --receipt cache-state.json
knowledge --cache .knowledge search '28 GHz combiner' --include-incomplete
```

The reconciler resolves every descriptor and artifact, checks byte hashes, and asks Knowledge to verify signatures and addresses before insertion. `knowledge put` provides validated, idempotent insertion. It emits a receipt listing the pinned inputs and imported addresses. Imports are additive: an empty cache obtains exactly the listed object set; existing unrelated objects are preserved. There is no destructive pruning or transactional rollback if an insertion fails midway. Successful earlier insertions remain valid and rerunning completes the import.

Importing does not imply engineering acceptance. Failed/incomplete objects are retained, and Knowledge's default search filters still apply. Source bundles are fetched and checked separately with `knowledge realize`; reconciliation does not rerun simulations or authenticate the publisher as a real-world organization. A pinned catalog revision plus pinned project revisions determines the imported object set. Cache receipts omit timestamps for deterministic successful output.

## Project self-description

`knowledge.json` uses `knowledge-project/1`:

```json
{
  "schema": "knowledge-project/1",
  "artifact": {
    "path": "knowledge/artifact.json",
    "sha256": "<64-character SHA-256 of artifact bytes>",
    "address": "<Knowledge content address>"
  }
}
```

Projects may also point to requirements, specification, validation reports and source commitments for discovery. The signed artifact owns the normative bindings; the catalog imports it without re-signing it. The first entry is the [public 28 GHz divider PoC](https://github.com/Studio-Fug/28ghz-2way-power-divider). Its signature is a prototype translation identity. Three requirements fail and five await evidence, including complete-assembly and physical qualification.

## Validation

```sh
python3 -m unittest discover -s tests -v
```

Three focused tests cover descriptor resolution, rejection of mismatched artifact hashes before cache writes, and rejection of mutable revisions/unsafe paths. The initial public entry was also imported over GitHub into an empty cache and re-imported successfully using Knowledge built from commit `25c50c9ac16f3195af54266eb8aae51b56b166e3`. Search with incomplete results enabled returned the expected failed object `9cdb703565b6e97f87064670c3646c4d566506af4e155964fe5069bd6695b88e`.
