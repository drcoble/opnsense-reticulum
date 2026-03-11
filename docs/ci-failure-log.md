# CI Failure Log
**Source:** GitHub Actions — `os-reticulum` repository, `development` branch
**Status:** final

## Failure Table

| Date | Run ID | Workflow | Step | Status | Root Cause | Fix | Commit |
|------|--------|----------|------|--------|------------|-----|--------|
| 2026-03-10 | 22921038989 | CI Pipeline (ci.yml) | PHP syntax check | Fixed | `use OPNsense\Base\IndexController` conflicted with `class IndexController` declaration in same namespace (`OPNsense\Reticulum`) | Removed redundant `use` statement from `IndexController.php` | e04b99b |

## Notes

**Run #22921038989 — 2026-03-10**

The PHP fatal error was triggered by a namespace collision in `os-reticulum/src/opnsense/mvc/app/controllers/OPNsense/Reticulum/IndexController.php`. The file contained:

```php
use OPNsense\Base\IndexController;

class IndexController extends \OPNsense\Base\IndexController
```

PHP imported `OPNsense\Base\IndexController` under the short alias `IndexController` into the current namespace. When PHP then encountered `class IndexController`, it treated it as a re-declaration of that same name and raised a fatal error. The `extends` clause already used the FQCN `\OPNsense\Base\IndexController`, so the `use` statement was entirely redundant. Removing it resolved the collision.

The Unit Tests workflow (pytest suite covering template rendering, model validation, and security checks) passed successfully on the same push. Only the PHP static analysis step was blocked; no test logic was affected.
