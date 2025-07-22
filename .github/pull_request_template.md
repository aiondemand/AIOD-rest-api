<!--
Please carefully follow the instructions of the template, as they allow for more effective reviews with fewer back-and-forth, making a smoother process for everyone.
Prefer small, independent PRs over big monolithic ones when possible.
If you are only looking for feedback, clearly indicate this and open it as a "draft" instead (use the green "v" button next to "create pull request").
-->


## Change(s)
<!-- Briefly describe the change of this PR, if there are multiple changes, please describe them separately. -->
Change Type: <!-- Added/Changed/Deprecated/Removed/Fixed/Security -->

Change Category: <!-- Documentation/Interface/Internal/Other -->

Changelog Entry: <!-- Brief description of the change, possibly followed by more details in a separate paragraph. For example: -->

<!--
Added the `contacts` field to the `AIResource` `GET` endpoints with full contact information.

This field contains the full contact information of the contacts whose identifiers are currently already provided through the `contact` field.
-->



## How to Test
<!-- Describe a way to test the change of this PR if it requires special steps beyond CI/CD. You're writing this for the reviewer. -->

## Checklist
- [ ] Tests have been added or updated to reflect the changes, or their absence is explicitly explained. <!-- For code changes -->
- [ ] Documentation has been added or updated to reflect the changes, or their absence is explicitly explained.
- [ ] A self-review has been conducted checking:
  - No unintended changes have been committed.
  - The changes in isolation seem reasonable.
  - Anything that may be odd or unintuitive is provided with a GitHub comment explaining it (but consider if this should not be a code comment or in the documentation instead).
- [ ] All CI checks pass before pinging a reviewer, or provide an explanation if they do not.
- [ ] The PR title matches the changelog entry's one-line description.

## Related Issues
<!-- Provide a list of relevant issues and/or pull requests, if any. -->
<!-- If the pull request closes and issue, specify "Closes #X" (where X is the issue number). -->
