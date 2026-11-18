# Promote immutable wheels for local releases

The application remains local-only. Delivery publishes Python wheels through GitHub Releases; a manual promotion workflow publishes the exact verified staging wheel without rebuilding it. Staging wheels already carry their intended production SemVer version, while commit SHA and workflow run identify distinct candidates externally. This deliberately avoids prerelease wheel versions because replacing a prerelease version during promotion would change the tested artifact.

Users may select any retained, eligible tagged release candidate, rather than only the latest default-branch build. GitHub Actions stores staging artifacts for 90 days subject to repository limits; production wheels remain attached to GitHub Releases. Expired artifacts require a newly verified build. Version collisions and the treatment of older candidates after intervening production releases remain to be settled before implementation.

Squash merges preserve Conventional Commit PR titles. Required CI checks gate merges. Since the last production release, `fix:` requests a patch increment, `feat:` a minor increment, and `!` a major increment (including during `0.x`); the largest increment wins. Other types alone do not create a release candidate, but their changes join a pending release. Promotion, rather than merging, makes a candidate a production release.
