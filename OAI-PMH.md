# SHFA OAI-PMH Documentation

## Endpoint

```
https://shfa.dh.gu.se/api/OAICat/
```

All requests are either `GET` or `POST`. The `verb` parameter selects the operation.

---

## Metadata Formats

| Prefix | Description |
|---|---|
| `ksamsok-rdf` | K-samsök (Swedish cultural heritage) RDF format |
| `shfa-gen-rdf` | SHFA generic RDF (treated same as `ariadne-rdf`) |

## Sets

| Set Spec | Description |
|---|---|
| `shfa:images` | Only image records (per-image) |
| `shfa:models` | 3D model records (grouped by visualisation group) |
| `shfa:comp` | Combined / composite — same behaviour as no set (site-based) |

---

## Verbs

### 1. Identify

Returns repository information (name, base URL, protocol version, granularity, etc).

**Parameters:** None (besides `verb`).

**Example:**

```
?verb=Identify
```

**Response:** Repository name ("SHFA"), protocol version 2.0, granularity `YYYY-MM-DDThh:mm:ssZ`.

---

### 2. ListMetadataFormats

Lists all available metadata formats, or the formats available for a specific record.

**Parameters:**

| Parameter | Required | Description |
|---|---|---|
| `identifier` | Optional | If provided, returns formats available for that specific record |

**Examples:**

```
?verb=ListMetadataFormats
?verb=ListMetadataFormats&identifier=12345
?verb=ListMetadataFormats&identifier=3d:42
```

**Behaviour:**
- Without `identifier`: returns all registered metadata formats.
- With `identifier`: checks if the record exists (Image or SHFA3D) and returns the available format. Identifiers starting with `3d:` look up 3D models.

---

### 3. ListSets

Lists the available sets in the repository.

**Parameters:** None (besides `verb`).

**Example:**

```
?verb=ListSets
```

**Response:** Returns all `Set` objects with their `setSpec`, `setName`, and optional `setDescription`.

---

### 4. GetRecord

Retrieves a single record by its identifier.

**Parameters:**

| Parameter | Required | Description |
|---|---|---|
| `metadataPrefix` | **Yes** | One of `ksamsok-rdf`, `ariadne-rdf`, `shfa-gen-rdf` |
| `identifier` | **Yes** | Record ID. Prefix with `3d:` for 3D models |

**Examples:**

```
?verb=GetRecord&metadataPrefix=ksamsok-rdf&identifier=12345
?verb=GetRecord&metadataPrefix=ariadne-rdf&identifier=3d:42
```

**Behaviour:**
- Identifier starting with `3d:` → looks up `SHFA3D` model
- Otherwise → looks up `Image` model
- Template selection:

| Record type | `ksamsok-rdf` | `ariadne-rdf` / `shfa-gen-rdf` |
|---|---|---|
| Image | `bild.template.xml` | `records_ariadne.xml` |
| 3D Model | `3d.template.xml` | `records_3d_ariadne.xml` |

---

### 5. ListRecords

Retrieves paginated lists of records. This is the main harvesting verb.

**Parameters:**

| Parameter | Required | Description |
|---|---|---|
| `metadataPrefix` | **Yes** (or `resumptionToken`) | Metadata format to use |
| `set` | Optional | Filter by set: `shfa:images`, `shfa:models`, or `shfa:comp` |
| `from` | Optional | Start date filter (`YYYY-MM-DD` or `YYYY-MM-DDThh:mm:ssZ:`) |
| `until` | Optional | End date filter (same granularity as `from`) |
| `resumptionToken` | **Yes** (for page 2+) | Token from a previous response to get the next page |

**Page size:** 25 records per page.

#### Modes of operation

The combination of `metadataPrefix` and `set` determines what kind of records are returned and how they are grouped:

##### K-samsök (`ksamsok-rdf`)

| Set | Grouping | Record identifier | Template |
|---|---|---|---|
| *(none)* or `shfa:comp` | **Site-based** — one record per archaeological site, containing all its images and 3D models | `oai:shfa.dh.gu.se:site/{id}` | `listrecords_site_ksamsok.xml` |
| `shfa:models` | **Group-based** — one record per visualisation group, containing its 3D models and associated images | `oai:shfa.dh.gu.se:group/{id}` | `listrecords_group_ksamsok.xml` |
| `shfa:images` | **Per-image** — one record per image | `oai:shfa.dh.gu.se:objects/{id}` | `listrecords_images.xml` |

##### ARIADNE (`ariadne-rdf` / `shfa-gen-rdf`)

| Set | Grouping | Record identifier | Template |
|---|---|---|---|
| *(none)* or `shfa:comp` | **Site-based** — one record per site with unique merged keywords | `oai:shfa.dh.gu.se:site/{id}` | `listrecords_ariadne.xml` |
| `shfa:models` | **Group-based** — one record per visualisation group with unique merged keywords | `oai:shfa.dh.gu.se:group/{id}` | `listrecords_3d_ariadne.xml` |
| `shfa:images` | **Per-image** — one record per image with original keywords | `oai:shfa.dh.gu.se:objects/{id}` | `listrecords_images_ariadne.xml` |

#### Examples

```
# K-samsök, site-based (default)
?verb=ListRecords&metadataPrefix=ksamsok-rdf&set=shfa:comp

# K-samsök, group-based 3D models
?verb=ListRecords&metadataPrefix=ksamsok-rdf&set=shfa:models

# K-samsök, per-image
?verb=ListRecords&metadataPrefix=ksamsok-rdf&set=shfa:images

# ARIADNE, site-based (default)
?verb=ListRecords&metadataPrefix=ariadne-rdf&set=shfa:comp

# ARIADNE, group-based 3D models
?verb=ListRecords&metadataPrefix=ariadne-rdf&set=shfa:models

# ARIADNE, per-image
?verb=ListRecords&metadataPrefix=ariadne-rdf&set=shfa:images

# With date filtering
?verb=ListRecords&metadataPrefix=ksamsok-rdf&set=shfa:comp&from=2024-01-01&until=2025-12-31

# Resumption (page 2+)
?verb=ListRecords&metadataPrefix=ksamsok-rdf&resumptionToken=abc123
```

#### Resumption tokens

When a result set has more than 25 records, the response includes a `<resumptionToken>` element. To fetch subsequent pages, send a new request with the token value:

```
?verb=ListRecords&metadataPrefix=ksamsok-rdf&resumptionToken=<token_value>
```

The `set` parameter must be re-sent with each request (it is extracted from URL parameters, not stored in the token). The `metadataPrefix` is stored in the token.

---

## Error codes

| Code | Meaning |
|---|---|
| `badArgument` | Missing or invalid argument |
| `badVerb` | Illegal or missing verb |
| `cannotDisseminateFormat` | Unknown `metadataPrefix` |
| `idDoesNotExist` | No record with the given identifier |
| `badResumptionToken` | Invalid or expired resumption token |
| `noMetadataFormats` | No formats available |
| `noSetHierarchy` | Invalid set or sets not supported |
| `noRecordsMatch` | No records match the given criteria |
