> **External project — audit only.** This is the first project audited outside this
> repository, added to test the claim that `refactor-arch` is technology-agnostic against a
> stack none of the three delivered projects use (Go). The source was **not** modified: Phase 3
> is not applicable to a third-party codebase. Only Phase 1 (analysis) and Phase 2 (audit) ran.
>
> - **Source:** https://github.com/gothinkster/golang-gin-realworld-example-app
> - **Commit:** `626c372d259472148d93303f74aa9b9a1cdcef24` (branch `main`, shallow clone)
> - **Audited on:** 2026-09-19
> - **Skill version:** the copy in this repo at the time of the run, including the bundled
>   `scripts/arch-check.sh`.
>
> The Go repository was cloned into a scratch directory and is not vendored here.

```
================================
PHASE 1: PROJECT ANALYSIS
================================
Language:      Go
Framework:     Gin v1.10.0 (HTTP) + GORM v1.25.12 (ORM)
Dependencies:  gin-gonic/gin, gorm.io/gorm, gorm.io/driver/sqlite, golang-jwt/jwt/v5,
               golang.org/x/crypto (bcrypt), go-playground/validator/v10, gosimple/slug
Domain:        RealWorld ("Conduit") blogging API — users, profiles, follows, articles,
               tags, comments and favorites
Architecture:  Partial layering by feature package (models / routers / serializers /
               validators per package), with no controller or service layer between the
               route handlers and the model-level persistence functions
Source files:  12 files analyzed (tests, docs and vendor excluded)
DB tables:     user_models, follow_models, article_models, article_user_models,
               favorite_models, tag_models, comment_models, article_tags
================================
```

Files analyzed (excludes `*_test.go`, `doc.go`, `common/test_helpers.go`): `hello.go`,
`common/database.go`, `common/utils.go`, `users/models.go`, `users/routers.go`,
`users/middlewares.go`, `users/serializers.go`, `users/validators.go`, `articles/models.go`,
`articles/routers.go`, `articles/serializers.go`, `articles/validators.go` — ~1 670 lines of
non-test Go.

```
================================
ARCHITECTURE AUDIT REPORT
================================
Project: golang-gin-realworld-example-app (external)
Stack:   Go 1.21 + Gin 1.10.0 / GORM 1.25.12
Files:   12 analyzed | ~1670 lines of code

## Summary
CRITICAL: 1 | HIGH: 3 | MEDIUM: 3 | LOW: 3

## Findings

### [CRITICAL] JWT signing secret hardcoded and published
File: common/utils.go:41-42
Description: The token signing key is a source constant — `const JWTSecret = "A String Very
Very Very Strong!!@##$!@#$"` — alongside `RandomPassword`, both annotated `// #nosec G101` so
the static scanner stays quiet. The comment above them reads "Keep this two config private, it
should not expose to open source" while the file sits in a public repository. It is read by
`common.GenToken` (utils.go:51) to sign tokens and by `AuthMiddleware` (users/middlewares.go:60)
to verify them.
Impact: anyone who can read the repository can forge a valid token for any `id` claim and
authenticate as any user of any deployment running this code. The `#nosec` annotation means no
scanner will report it either.
Recommendation: AP-02 — move the secret to an environment variable read through a config
module, fail fast at boot when it is absent, and drop the `#nosec` suppression. See RP-02.

### [HIGH] Route handlers call persistence directly — no controller layer exists
File: users/routers.go:34,45,62,85,100,111,134 + articles/routers.go:46,61,78,90,101,108,131,135,142,151,157,167,173,183,195,210,214,221,230
Description: Every handler reaches the model layer itself instead of delegating: `FindOneUser(&UserModel{Username: username})`
(users/routers.go:34), `SaveOne(&articleModelValidator.articleModel)` (articles/routers.go:46),
`FindManyArticle(...)` (:61), `DeleteArticleModel(...)` (:142), `FindOneComment(...)` (:210).
There is no controller or service package anywhere in the project — routing, orchestration and
data access collapse into the `*routers.go` files.
Impact: no handler can be tested without a live SQLite database and the process-wide `common.DB`
handle; a change to a query signature ripples into the HTTP layer. 26 direct calls across 2
files, confirmed mechanically by the bundled checker (exit 1).
Recommendation: AP-16 — introduce a controller per feature package; the handler parses the
request, calls exactly one controller function, and serializes the result. See RP-14.

### [HIGH] Database handle is process-wide global mutable state
File: common/database.go:17,67,92,111
Description: `var DB *gorm.DB` is a package-level variable assigned by `Init()` (:67) and
reassigned by `TestDBInit()` (:92), then read through `GetDB()` (:111) by every model function
(`users/models.go:81,91,100,109,122,135,144`, `articles/models.go:59,68,77,91,116,129,139,145,151,158,165,171,178,267,316,353,359,365`).
Nothing accepts a database handle as a parameter.
Impact: tests mutate the same global the application uses, so test and production wiring are
indistinguishable at runtime and parallel tests interfere; there is no seam to inject a
transaction, a read replica, or a fake. `Init()` also logs and continues when `gorm.Open` fails
(:57-60), leaving a nil handle in the global.
Recommendation: AP-07 — pass the handle (or a repository holding it) explicitly through the
layers instead of reading a global. See RP-05.

### [HIGH] bcrypt error discarded in the password-hashing path
File: users/models.go:57-66
Description: `passwordHash, _ := bcrypt.GenerateFromPassword(bytePassword, bcrypt.DefaultCost)`
(:63) drops the error, then assigns the result unconditionally and returns `nil`. `bcrypt`
returns an error for any password longer than 72 bytes, in which case `passwordHash` is empty
and `setPassword` still reports success to its caller in `users/validators.go`.
Impact: registration with a >72-byte password returns 201 Created and persists a user whose
`password` column is the empty string. `checkPassword` (:71-75) then fails for every login
attempt, so the account is permanently unusable and nothing in the logs explains why.
Recommendation: AP-03 — return the bcrypt error from `setPassword` and reject the registration.
See RP-09.

### [MEDIUM] Persistence helpers duplicated across feature packages
File: users/models.go:90-94 + articles/models.go:144-148 (and users/models.go:99-103 + articles/models.go:352-356)
Description: `SaveOne` is defined twice with byte-identical bodies, once per package, and the
`Update` methods on `UserModel` and `ArticleModel` repeat the same `db.Model(x).Updates(data)`
shape. Neither copy knows about the other.
Impact: the copies diverge silently the first time only one is fixed — adding error wrapping,
a transaction, or an audit hook to one leaves the other behind, which is a correctness bug in
waiting rather than a style issue.
Recommendation: AP-06 — extract one shared persistence helper (or a small generic repository)
that both packages call. See RP-04.

### [MEDIUM] N+1 queries in single-item and comment serialization
File: articles/serializers.go:80-81,38 + users/serializers.go:35
Description: `ArticleSerializer.Response()` issues `GetArticleUserModel(...)` (a
`FirstOrCreate`), `isFavoriteBy(...)` and `favoritesCount()` — three queries per article. The
list path was already batched (`ResponseWithPreloaded` at :93, `BatchGetFavoriteCounts` at
articles/models.go:87), but `CommentsSerializer.Response()` (:173-179) still loops over comments
calling `CommentSerializer.Response()`, and each one reaches `ArticleUserSerializer.Response()`
(:38) → `ProfileSerializer.Response()` → `myUserModel.isFollowing(...)` (users/serializers.go:35),
which is one more query per comment.
Impact: `GET /api/articles/:slug/comments` costs one query per comment plus overhead; the
already-applied batching on the article list shows the pattern was recognized but not carried
through to the remaining collections.
Recommendation: AP-08 — extend the existing batch approach (`BatchGetFavoriteStatus`-style) to
comment authors and follow status. See RP-06.

### [MEDIUM] Pagination bounds are unvalidated and the default is duplicated
File: articles/models.go:182-190,271-278
Description: `limit`/`offset` arrive as raw query strings and are converted with
`strconv.Atoi`; on failure the error is discarded and a literal default is substituted
(`limit_int = 20` at :189 and again at :277). No upper bound is enforced, and a negative or
non-numeric value silently becomes the default rather than a 400.
Impact: `GET /api/articles?limit=100000` is served in full, so response size is controlled by
the client; and the two copies of the default will drift the moment one is tuned.
Recommendation: AP-09/AP-13 — one shared pagination helper with a named default and a hard
maximum, rejecting malformed input explicitly. See RP-07.

### [LOW] Operational logging via fmt.Println / fmt.Printf
File: common/database.go:54,59,63,77,84,88 + common/utils.go:53
Description: Database initialization failures and JWT signing failures are written to stdout
with `fmt.Println`/`fmt.Printf` and execution continues — `Init()` prints "db err: (Init)" and
still returns the (nil) handle.
Impact: no levels, no structured fields, no way to filter or alert; a failed database open is
indistinguishable from normal output and surfaces later as a nil-pointer panic far from its
cause.
Recommendation: AP-12 — use `log/slog` with levels, and return the error instead of printing
and continuing. See RP-08.

### [LOW] Hardcoded paths and repeated magic format strings
File: common/database.go:24,34 + articles/serializers.go:76,78,101,102,166,167
Description: The SQLite paths `./data/gorm.db` and `./data/gorm_test.db` are literals inside the
accessor functions (env-overridable, but the fallback is in code), and the timestamp layout
`"2006-01-02T15:04:05.999Z"` is repeated verbatim six times across three serializers.
Impact: changing the wire format of `createdAt`/`updatedAt` means finding six identical string
literals and missing none — exactly the edit that produces an inconsistent API response.
Recommendation: AP-13 — one config module for paths, one exported constant for the layout. See
RP-13.

### [LOW] Naming conventions mixed within the same files
File: articles/models.go:182,187,266 + users/middlewares.go:30,71 + common/utils.go:46 + users/serializers.go:24,52
Description: Go camelCase and snake_case coexist in the same functions (`offset_int`,
`limit_int`, `my_user_id`, `jwt_token`, `test_db`), and six methods use `self` as the receiver
name (`users/serializers.go:24,52`, `users/validators.go:26,71`, `articles/models.go:164,266`),
which Go's own style guidance explicitly advises against.
Impact: onboarding and review friction rather than a functional defect, but it makes the
codebase read as two conventions fighting, and `self` invites the assumption of Python-style
reference semantics on a value receiver.
Recommendation: AP-15 — apply one convention; `gofmt`-adjacent linters (`revive`, `golint`
successor) flag both automatically. See RP-15.

================================
Total: 10 findings
================================

Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]
```

## Mechanical AP-16 verification

Run against the cloned repository with the skill's bundled checker, no configuration:

```
$ scripts/arch-check.sh <clone>/go-gin-realworld
==========================================================
arch-check — go-gin-realworld
AP-16: routes must not touch persistence directly
Detected sources: go
==========================================================

  FAIL articles/routers.go — 19 inline call(s)
         46:	if err := SaveOne(&articleModelValidator.articleModel); err != nil {
         61:	articleModels, modelCount, err := FindManyArticle(tag, author, limit, offset, favorited)
         90:	articleModel, err := FindOneArticle(&ArticleModel{Slug: slug})
         142:	if err := DeleteArticleModel(&ArticleModel{Slug: slug}); err != nil {
         ...
  FAIL users/routers.go — 7 inline call(s)
         34:	userModel, err := FindOneUser(&UserModel{Username: username})
         85:	if err := SaveOne(&userModelValidator.userModel); err != nil {
         ...

==========================================================
FAIL: 26 inline persistence call(s) across 2 route file(s).
==========================================================
$ echo $?
1
```

## What this run exposed in the skill

The first run of the checker against this project returned **PASS with zero hits** — a false
negative, not a clean codebase. The AP-16 detection patterns had been written from the two
stacks the delivered projects use, where persistence is reached through a receiver
(`Model.query`, `db.session.add`, `Model.findOne(...)`). Go exposes it as package-level
functions, so `FindOneUser(...)` and `SaveOne(...)` matched nothing, and a route file with 26
violations reported as compliant.

Three changes followed, and they are the reason this audit is in the repository:

1. `scripts/arch-check.sh` gained a verb-first free-function pattern
   (`(Find|Save|Insert|Delete|...)[A-Z]...(`) plus `Get…Model(...)`, which is what produced the
   26 hits above.
2. AP-16 in `anti-patterns-catalog.md` now names the free-function shape explicitly, so Phase 2
   looks for it during the read-through rather than relying on the script alone.
3. `references/verification-recipes.md` documents the underlying rule — decide whether the stack
   exposes persistence as methods or as free functions *before* writing the pattern — and
   requires validating any new pattern against a known violation, because a pattern that never
   fires is not evidence of clean code.

A checker that cannot find the routing layer at all now exits 2 (INCONCLUSIVE) instead of 0, for
the same reason: silence is not a pass.
