## Description

The code graph viewer currently shows all functions as equal nodes with no indication of whether a function is ever called by other code. This makes it hard to spot dead code — functions that exist in the codebase but are never called and could be safely removed. Additionally, when a developer clicks on a node to see its details, there is no way to view its source code or jump to the file on GitHub.

## Expected Behavior

- The filters panel should display a count of dead code nodes (functions with no callers), shown as "X dead" next to the dead-code section.
- A toggle button labeled "Show only dead code" should be available. When activated, the graph should filter to display only unreachable functions, and a notice showing the original total node count (e.g., "filtered from N") should appear.
- In the node detail panel, a "Show code" button should appear for nodes with enough metadata. Clicking it should fetch and display the node's source code safely as literal text — the content must not be interpreted as HTML, so any markup in the source code is shown verbatim without executing or rendering as DOM elements.
- When a git remote is known, the node detail panel should display an "Open on GitHub" link that navigates directly to the correct file and line range. The link's URL must properly encode special characters in the file path (spaces, at-signs, etc.) and must open in a new tab with appropriate security attributes.

## Why This Matters

Without dead code detection, developers must manually trace call graphs to find unused functions. The current detail panel provides no way to view source code inline or navigate to GitHub, forcing context switching between tools. These features together make the graph viewer a more complete development aid.

I'm working on a code graph visualization tool and I need to add two new features to the frontend components.

First, the filter panel in the graph view needs to show dead code information. Right now it only filters by node label or edge type, but I want it to display a count of unreachable functions (shown as "X dead") and include a toggle button that, when clicked, filters the visible nodes down to only those marked as dead. When that filter is active, a notice should appear indicating the total number of nodes that existed before filtering (something like "filtered from N"). The node data already includes metadata indicating which nodes are dead, so the logic just needs to wire up the UI.

Second, when a developer clicks on a node and the detail panel opens, I want two new capabilities: the ability to view the source code inline, and a link to open the file on GitHub. For the source code, there should be a "Show code" button that fetches the source and displays it as literal text in a code block — it's important that the content is treated as plain text and not rendered as HTML, since source files could contain HTML-like content. For the GitHub link, the panel should show an "Open on GitHub" link when the repository's remote URL is known. The URL needs to correctly encode any special characters in the file path (like spaces or at-signs) and should include the line number range as an anchor. The link should open in a new tab with the appropriate security attributes for external links.
